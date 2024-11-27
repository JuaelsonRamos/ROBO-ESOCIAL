from __future__ import annotations

from src.utils import Singleton

import inspect
import functools
import itertools

from types import FunctionType
from typing import Any, Callable, Never, Sequence

from playwright.async_api import Browser, BrowserContext, Page


_StepFunction = Callable[..., bool]
_StepEventHandler = Callable[..., None | Never]


class _GlobalState_StepRegistry(metaclass=Singleton):
    __slots__ = ('primary', 'before_all', 'after_all', 'before_every', 'after_every')

    def __init__(self) -> None:
        self.primary: dict[str, StepRunner] = {}
        self.before_all: list[StepRunner] = []
        self.before_every: list[StepRunner] = []
        self.after_all: list[StepRunner] = []
        self.after_every: list[StepRunner] = []

    def keys(self):
        return iter(self.__slots__)

    def values(self):
        for attr in self.__slots__:
            yield getattr(self, attr)

    def items(self):
        for attr in self.__slots__:
            yield attr, getattr(self, attr)

    def __iter__(self):
        return itertools.chain(
            self.primary.values(),
            self.before_all,
            self.before_every,
            self.after_every,
            self.after_all,
        )

    def __contains__(self, other):
        if isinstance(other, str):
            return any(step.name == other for step in self)
        return any(step == other for step in self)

    def __len__(self):
        return sum(len(entry) for entry in self.values())

    def __getitem__(self, name: str) -> StepRunner | Never:
        if name in self.primary:
            return self.primary[name]
        for step in itertools.chain(
            self.before_all,
            self.before_every,
            self.after_every,
            self.after_all,
        ):
            if step.name == name:
                return step
        raise IndexError(name)

    def register(self, step: StepRunner) -> None | Never:
        if step.step_type == 'primary':
            self.primary[step.name] = step
        elif hasattr(self, step.step_type):
            getattr(self, step.step_type).append(step)
        else:
            raise ValueError(f'invalid step {repr(step)}')

    def remove(self, step: StepRunner) -> None:
        if step.step_type == 'primary':
            del self.primary[step.name]
            return
        registry: list = getattr(self, step.step_type)
        registry.remove(step)


def validate_function_signature(
    func: _StepEventHandler | _StepFunction,
    kwargs: dict[str, Any],
    /,
    err_prefix: str = '',
) -> dict[str, Any] | Never:
    params = inspect.signature(func).parameters
    if len(params) == 0:
        return {}
    args = {}
    for p in params.values():
        if p.name not in kwargs:
            raise RuntimeError(err_prefix + f'missing argument {p.name}')
        if p.kind == p.POSITIONAL_ONLY or p.kind == p.VAR_POSITIONAL:
            raise RuntimeError(
                err_prefix + f'argument {p.name} is {p.kind.description}'
            )
        if p.default is p.empty:
            raise RuntimeError(err_prefix + f'argument {p.name} has default value')
        args[p.name] = kwargs[p.name]
    return args


class Event:
    def __init__(self, name: str, parent: StepRunner) -> None:
        self.name = name
        self.callback: _StepEventHandler | None = None
        self.parent = parent

    def unbind(self):
        if self.callback is None:
            raise RuntimeError('trying to unbind already empty event')
        self.callback = None

    def bind(self, func: _StepEventHandler) -> None | Never:
        if not isinstance(func, FunctionType):
            raise TypeError(f'value is not function {func=}')
        if self.callback is not None:
            raise ValueError(f"event '{self.name}' already registered")
        self.callback = func

    def is_set(self):
        return self.callback is not None

    def is_async(self):
        return inspect.iscoroutinefunction(self.callback)

    async def run(self, **kwargs):
        if self.callback is None:
            return
        if 'event' in kwargs:
            raise RuntimeError('event is a reserved argument name')
        kwargs['event'] = self
        prefix = f'{repr(self)}: '
        valid_args = validate_function_signature(self.callback, kwargs, prefix)
        if inspect.iscoroutinefunction(self.callback):
            await self.callback(**valid_args)
        else:
            self.callback(**valid_args)

    def __repr__(self) -> str:
        value = None
        if self.callback is not None:
            value = hex(id(self.callback))
        return f'Event(step={self.parent.name}, name={self.name}, callback={value})'

    def __hash__(self) -> int:
        return hash(self.parent) + hash(self.name)


class StepRunner:
    def __init__(self, name: str, callback: _StepFunction, step_type: str) -> None:
        self.events = ('on_success', 'on_fail')
        self.on_success = Event('on_success', self)
        self.on_fail = Event('on_fail', self)
        self.__callback = callback
        self.step_type = step_type
        self.name = name

    def __hash__(self) -> int:
        return hash(self.name) + hash(self.step_type)

    def unbind(self):
        _GlobalState_StepRegistry().remove(self)

    async def run(self, **kwargs: Any) -> bool:
        if 'step' in kwargs:
            raise RuntimeError('step is a reserverd argument name')
        kwargs['step'] = self
        prefix = f'{repr(self)}: '
        args = validate_function_signature(self.__callback, kwargs, prefix)
        ok: Any = None
        if inspect.iscoroutinefunction(self.__callback):
            ok = await self.__callback(**args)
        else:
            ok = self.__callback(**args)
        if not isinstance(ok, bool):
            raise RuntimeError(prefix + 'returned value is not boolean type')
        if ok:
            await self.on_success.run(**args)
        else:
            await self.on_fail.run(**args)
        return ok

    def __repr__(self) -> str:
        return 'StepRunner(name={}, step_type={}, callback={}, on_success={}, on_fail={})'.format(
            self.name,
            self.step_type,
            hex(id(self.__callback)),
            repr(self.on_success),
            repr(self.on_fail),
        )


class step(metaclass=Singleton):
    def get(self, name: str) -> StepRunner | None:
        registry = _GlobalState_StepRegistry()
        return registry[name] if name in registry else None

    def __create_step(
        self, func: _StepFunction, name: str, step_type: str
    ) -> StepRunner | Never:
        registry = _GlobalState_StepRegistry()
        if step_type not in registry.keys():
            raise ValueError(f'value unknown {step_type=}')
        if name in registry:
            raise ValueError(f"step '{name}' already registered as '{step_type}'")
        instance = StepRunner(name, func, step_type)
        registry.register(instance)
        return instance

    def __call__(self, func: _StepFunction, name: str) -> StepRunner | Never:
        return self.__create_step(func, name, 'primary')

    @property
    def before_all(self):
        return functools.partial(self.__create_step, step_type='before_all')

    @property
    def before_every(self):
        return functools.partial(self.__create_step, step_type='before_every')

    @property
    def after_all(self):
        return functools.partial(self.__create_step, step_type='after_all')

    @property
    def after_every(self):
        return functools.partial(self.__create_step, step_type='after_every')


async def execute_in_order(
    browser: Browser,
    context: BrowserContext,
    page: Page,
    names: Sequence[str],
) -> None:
    registry = _GlobalState_StepRegistry()
    if len(registry.primary) == 0:
        raise RuntimeError('no steps defined yet')
    if len(names) > len(registry.primary):
        raise RuntimeError('more steps specified than currently exist')
    for name in names:
        if name not in registry.primary:
            raise RuntimeError(f'step {name=} is unknown')
    kwargs = dict(browser=browser, context=context, page=page)
    for stp in registry.before_all:
        await stp.run(**kwargs)
    for name in names:
        for stp in registry.before_every:
            await stp.run(**kwargs)
        await registry.primary[name].run(**kwargs)
        for stp in registry.after_every:
            await stp.run(**kwargs)
    for stp in registry.after_all:
        await stp.run(**kwargs)
