from __future__ import annotations

from utils import singleton

import functools
import itertools

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


class StepEventRegistry:
    __slots__ = ('on_success', 'on_fail')

    def __repr__(self) -> str:
        events = []
        for name in self.__slots__:
            value = getattr(self, name, None)
            if value is not None:
                value = hex(id(value))
            events.append(f'{name}={value}')
        return 'StepEventRegistry({})'.format(', '.join(events))


class StepRunner:
    def __init__(self, name: str, callback: _StepFunction, step_type: str) -> None:
        self.event = StepEventRegistry()
        self.__callback = callback
        self.step_type = step_type
        self.name = name

    def __hash__(self) -> int:
        return hash(self.name) + hash(self.step_type)

    def __register_event(self, func: _StepEventHandler, name: str):
        if not isinstance(func, FunctionType):
            raise TypeError('argument is not a function')
        if hasattr(self.event, name):
            raise ValueError(f"event '{name}' already registered")
        setattr(self.event, name, func)

    def __getattr__(self, name: str) -> Any:
        if name in self.event.__slots__:
            return functools.partial(self.__register_event, name=name)
        elif not hasattr(self, name):
            raise AttributeError(f'{name=}')
        return getattr(super(), name)

    def run(self) -> bool:
        ok = self.__callback()
        if not isinstance(ok, bool):
            raise StepCallbackError('returned value is not boolean type')
        try:
            if ok:
                self.event.on_success()
            else:
                self.event.on_fail()
        except AttributeError:
            pass
        return ok

    def __repr__(self) -> str:
        return 'StepRunner(name="{}", step_type="{}", callback={}, events={})'.format(
            self.name, self.step_type, hex(id(self.__callback)), repr(self.event)
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
        if not isinstance(func, FunctionType):
            raise TypeError(f'value is not function {func=}')
        if step_type not in _GlobalState_StepRegistry.keys():
            raise ValueError(f'value unknown {step_type=}')
        if name in _GlobalState_StepRegistry:
            raise ValueError(f"step '{name}' already registered as '{step_type}'")
        instance = StepRunner(name, func, step_type)
        _GlobalState_StepRegistry.register(instance)
        return instance

    def __call__(self, func: _StepFunction, name: str):
        return self.__create_step(func, name, 'primary')

    def __getattr__(self, name: str):
        if name in _GlobalState_StepRegistry.keys() and name != 'primary':
            return functools.partial(self.__create_step, step_type=name)
        if hasattr(self, name):
            return getattr(super(), name)
        raise AttributeError(name)
