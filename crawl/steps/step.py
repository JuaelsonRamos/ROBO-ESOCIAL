from __future__ import annotations

from utils import singleton

import inspect
import functools
import itertools

from multiprocessing import Value
from types import FunctionType, MappingProxyType
from typing import Any, Callable, Iterable, Never, Sequence, TypedDict, overload

from playwright.async_api import Browser, BrowserContext, Page


_StepFunction = Callable[..., bool]
_StepEventHandler = Callable[..., None | Never]


@singleton
class _GlobalState_StepRegistry:
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

    def __getitem__(self, name: str):
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

    def register(self, step: StepRunner):
        if step.step_type == 'primary':
            self.primary[step.name] = step
        elif hasattr(self, step.step_type):
            getattr(self, step.step_type).append(step)
        else:
            raise ValueError(f'invalid step {repr(step)}')

    def remove(self, step: StepRunner):
        if step.step_type == 'primary':
            del self.primary[step.name]
            return
        registry: list = getattr(self, step.step_type)
        registry.remove(step)


class Event:
    def __init__(self, name: str, parent: StepRunner) -> None:
        self.name = name
        self.callback: _StepEventHandler | None = None
        self.parent = parent

    def unbind(self):
        if self.callback is None:
            raise RuntimeError('trying to unbind already empty event')
        self.callback = None

    def bind(self, func: _StepEventHandler):
        if not isinstance(func, FunctionType):
            raise TypeError(f'value is not function {func=}')
        if self.callback is not None:
            raise ValueError(f"event '{self.name}' already registered")
        self.callback = func

    def is_set(self):
        return self.callback is not None

    def is_async(self):
        return inspect.iscoroutinefunction(self.callback)

    async def run(self):
        if self.callback is None:
            return
        if inspect.iscoroutinefunction(self.callback):
            await self.callback(self)
            return
        self.callback(self)

    def __repr__(self) -> str:
        value = None
        if self.callback is not None:
            value = hex(id(self.callback))
        return f'Event(name={self.name}, callback={value})'

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
        _GlobalState_StepRegistry.remove(self)

    async def run(self, **kwargs) -> bool:
        if 'step' in kwargs:
            raise RuntimeError('step is a reserverd argument name')
        kwargs['step'] = self
        params = inspect.signature(self.__callback).parameters
        func: Callable
        if len(params) == 0:
            func = self.__callback
        else:
            args = {}
            prefix = f"step '{self.name}': "
            for p in params.values():
                if p.name not in kwargs:
                    raise RuntimeError(prefix + f'missing argument {p.name}')
                if p.kind == p.POSITIONAL_ONLY or p.kind == p.VAR_POSITIONAL:
                    raise RuntimeError(
                        prefix + f'argument {p.name} is {p.kind.description}'
                    )
                if not p.empty:
                    raise RuntimeError(prefix + f'argument {p.name} has default value')
                args[p.name] = kwargs[p.name]
            func = functools.partial(self.__callback, **args)
        ok: Any
        if inspect.iscoroutinefunction(func):
            ok = await func()
        else:
            ok = func()
        if not isinstance(ok, bool):
            raise RuntimeError('returned value is not boolean type')
        if ok and self.on_success.is_set():
            self.on_success()
        elif not ok and self.on_fail.is_set():
            self.on_fail()
        return ok

    def __repr__(self) -> str:
        return 'StepRunner(name={}, step_type={}, callback={}, on_success={}, on_fail={})'.format(
            self.name,
            self.step_type,
            hex(id(self.__callback)),
            repr(self.on_success),
            repr(self.on_fail),
        )


@singleton
class step:
    def get(self, name: str) -> StepRunner | None:
        try:
            return _GlobalState_StepRegistry[name]
        except IndexError:
            return

    def __create_step(
        self, func: _StepFunction, name: str, step_type: str
    ) -> StepRunner:
        if step_type not in _GlobalState_StepRegistry.keys():
            raise ValueError(f'value unknown {step_type=}')
        if name in _GlobalState_StepRegistry:
            raise ValueError(f"step '{name}' already registered as '{step_type}'")
        instance = StepRunner(name, func, step_type)
        _GlobalState_StepRegistry.register(instance)
        return instance

    def __call__(self, func: _StepFunction, name: str):
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
):
    registry = _GlobalState_StepRegistry
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
