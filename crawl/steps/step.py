from __future__ import annotations

from utils import singleton

import inspect
import functools
import itertools

from multiprocessing import Value
from types import FunctionType
from typing import Any, Callable, Never


_StepFunction = Callable[..., bool]
_StepEventHandler = Callable[..., None | Never]


class StepCallbackError(ValueError): ...


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
        self.step = parent

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

    def __call__(self):
        if self.callback is None:
            raise ValueError('event is empty, has no callback')
        self.callback(self)

    def __repr__(self) -> str:
        value = None
        if self.callback is not None:
            value = hex(id(self.callback))
        return f'Event(name={self.name}, callback={value})'


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

    def run(self) -> bool:
        ok = self.__callback(self)
        if not isinstance(ok, bool):
            raise StepCallbackError('returned value is not boolean type')
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
    def execute_in_order(self, *names: str):
        registry = _GlobalState_StepRegistry
        if len(registry.primary) == 0:
            raise RuntimeError('no steps defined yet')
        if len(names) > len(registry.primary):
            raise RuntimeError('more steps specified than exist')
        for name in names:
            if name not in registry.primary:
                raise RuntimeError(f'step {name=} is unknown')
        for stp in registry.before_all:
            stp.run()
        for name in names:
            for stp in registry.before_every:
                stp.run()
            registry.primary[name].run()
            for stp in registry.after_every:
                stp.run()
        for stp in registry.after_all:
            stp.run()

    def get(self, name: str) -> StepRunner | None:
        for step_type, registry in _GlobalState_StepRegistry.items():
            if step_type == 'primary':
                return registry.get(name, None)
            for step in registry:
                if step.name == name:
                    return step

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
