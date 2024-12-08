"""
Procedural utilities to abstract multi-line pieces of code that are repetitive and
trivial.

Implementations are encouraged to be checked since they should be simple, with the
logical reasoning and mental overhead being done by documentation.
"""

from __future__ import annotations

from multiprocessing import Value
from tkinter import ttk
from typing import Never


def _doest_exist_error(widget: ttk.Widget, state_option: str) -> Exception:
    return ValueError(f"{state_option=} doesn't exist in widget {widget=}")


def toggle_state(widget: ttk.Widget, state_option: str, /) -> bool | Never:
    """Returns bool to indicate the logical value of the state in the widget, or raises
    :ref:`ValueError` if it doesn't exist.
    """
    state_option = state_option.strip('!')
    statespec: list[str] = widget.state()
    if len(statespec) == 0:
        # may be empty string or list, not sure which one, but in cases like this, an
        # empty string is only returned if the value is empty under the hood as well
        raise _doest_exist_error(widget, state_option)
    for i in range(len(statespec)):
        option = statespec[i]
        if not option.endswith(state_option):
            continue
        if option == state_option:
            # current state is True
            statespec[i] = '!' + option
            widget.state(statespec)
            return False
        if option == '!' + state_option:
            # current state is False
            statespec[i] = state_option
            widget.state(statespec)
            return True
    raise _doest_exist_error(widget, state_option)


def remove_state(widget: ttk.Widget, state_option: str, /) -> None | Never:
    """Removes state from widget or raises :ref:`ValueError` if it doesn't exist."""
    state_option = state_option.strip('!')
    statespec: list[str] = widget.state()
    try:
        if len(statespec) == 0:
            raise ValueError
        statespec.remove(state_option)
    except ValueError:
        raise _doest_exist_error(widget, state_option)


def add_state(
    widget: ttk.Widget, state_option: str, /, *, value: bool | None = None
) -> None | Never:
    """
    Abstraction at it's finnest.

    Type checks the values, appends `state_option` to a list and passes that list to widget.state()

    If `value` is None, state will be added as is, otherwise, set it to the equivalent to that boolean value.
    """
    if value is None:
        pass
    elif value is True:
        state_option = state_option.strip('!')
    elif value is False:
        state_option = '!' + state_option
    statespec: list[str] = widget.state()
    if len(statespec) == 0:
        statespec = []
    elif not isinstance(statespec, list):
        raise ValueError(f"{widget=} .state() method doesn't return a list")
    elif state_option in statespec:
        raise ValueError(f'{state_option=} already exist in {widget=}')
    statespec.append(state_option)
    widget.state(statespec)


def get_state(
    widget: ttk.Widget, state_option: str, /, false_if_missing: bool = False
) -> bool | Never:
    """
    Retrieves boolean value of `state_option` if it exists, otherwise, raises
    ValueError.

    If the flag `false_if_missing` is True (sorry), it will never raise.
    """
    state_option.strip('!')
    statespec: list[str] = widget.state()
    if len(statespec) == 0:
        return False
    for option in statespec:
        if option == state_option:
            return True
        elif option == '!' + state_option:
            return False
    if false_if_missing:
        return False
    raise _doest_exist_error(widget, state_option)
