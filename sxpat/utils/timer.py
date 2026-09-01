__all__ = ['Timer']

from typing import (
    Tuple as _Tuple,
    Callable as _Callable,
    TypeVar as _TypeVar,
    Self as _Self,
    final as _final,
)
from sxpat.utils.typing import (
    SupportsAddSub as _SupportsAddSub,
)
from dataclasses import (
    dataclass as _dataclass,
)

import functools as _ft
import resource as _res
from time import (
    perf_counter,
    perf_counter_ns,
)

_C = _TypeVar('_C', bound=_Callable)


@_dataclass(init=False, repr=False, eq=False, frozen=True)
class Timer:
    """
        This class is used to wrap functions to be able to time their execution.
        The counted time is the cpu time for the current process and all children from the start to the end of the function.

        This class also exposes the `.now()` method, which returns the cycles spent on the cpu by the current process and all waited children.

        ---

        Simple example:
        ```python
        def my_function(...): ...

        timer, timed_my_function = Timer.from_function(my_function)

        ... = timed_my_function(...)
        print(timer.latest)

        ... = timed_my_function(...)
        print(timer.latest)

        print(timer.total)
        ```

        ---

        Advanced example:
        ```python
        timer = Timer()

        # wrapping after function definition
        def my_function_1(...): ...
        timed_my_function_1 = timer.wrap(my_function_1)

        # wrapping as decorator
        @timer.wrap
        def my_function_2(...): ...

        ... = timed_my_function_1(...)
        print(timer.latest)

        ... = my_function_2(...)
        print(timer.latest)

        print(timer.total)
        ```

        ---

        @authors: Marco Biasion
    """

    latest: float = 0
    """The time spent on the latest call of a wrapped function under this timer (in seconds)."""
    total: float = 0
    """The time spent in total on all calls of a wrapped functions under this timer (in seconds)."""

    def __post_init__(self):
        import sys
        print(
            f'[WARNING]: {self.__class__.__qualname__} is deprecated,'
            f' use {Timer2.__qualname__} instead.',
            file=sys.stderr,
        )

    def wrap(self, function: _C) -> _C:
        """
            Wraps the given function and return a timed alias under this timer.   
            Can be used as a decorator.
        """

        @_ft.wraps(function)
        def wrapper(*args, **kwds):
            time_start = self.now()
            result = function(*args, **kwds)
            time_end = self.now()

            object.__setattr__(self, 'latest', time_end - time_start)
            object.__setattr__(self, 'total', self.total + self.latest)

            return result

        return wrapper

    @classmethod
    def from_function(cls, function: _C) -> _Tuple[_Self, _C]:
        """Create a timer wrapping the given function."""

        timer = Timer()
        wrapped = timer.wrap(function)
        return (timer, wrapped)

    @staticmethod
    def now() -> float:
        """Returns the number of seconds spent by the current process and all waited children."""

        proc_rusage = _res.getrusage(_res.RUSAGE_SELF)
        chld_rusage = _res.getrusage(_res.RUSAGE_CHILDREN)

        return (
            + proc_rusage.ru_utime  # process user level time
            + proc_rusage.ru_stime  # process system level time
            + chld_rusage.ru_utime  # children user level time
            + chld_rusage.ru_stime  # children system level time
        )


def rusage_counter() -> float:
    """
        Returns the number of seconds spent by the current process and all waited children.
        :authors: Marco Biasion
    """
    proc_rusage = _res.getrusage(_res.RUSAGE_SELF)
    chld_rusage = _res.getrusage(_res.RUSAGE_CHILDREN)
    return (
        + proc_rusage.ru_utime  # process user level time
        + proc_rusage.ru_stime  # process system level time
        + chld_rusage.ru_utime  # waited children user level time
        + chld_rusage.ru_stime  # waited children system level time
    )


default_counter = rusage_counter


@_final
class Timer2[T:_SupportsAddSub]:
    """
        :authors: Marco Biasion
    """
    __slots__ = ['_clock_counter', '_start', '_previous', '_total', '_running']

    @classmethod
    def default(cls: type[Timer2]) -> Timer2: return cls(default_counter)
    @classmethod
    def perf(cls: type[Timer2]) -> Timer2[float]: return cls(perf_counter)
    @classmethod
    def perf_ns(cls: type[Timer2]) -> Timer2[int]: return cls(perf_counter_ns)
    @classmethod
    def rusage(cls: type[Timer2]) -> Timer2[float]: return cls(rusage_counter)

    def __init__(self, counter: _Callable[[], T]):
        self._clock_counter = counter
        #
        self._start: T
        self._previous: T
        self._total: T | None = None
        self._running: bool = False

    def tick(self) -> T:
        now = self._clock_counter()
        delta = now - self._previous
        self._previous = now
        return delta

    def total(self) -> T:
        now = self._clock_counter()
        # action
        if self._running:
            delta = now - self._start
            if self._total is None: return delta
            else: return self._total + delta
        else:
            return self._total  # pyright: ignore[reportReturnType] # always valid here

    def start(self) -> _Self:
        now = self._clock_counter()
        # action
        if self._running:
            raise RuntimeError('timer is already running.')
        else:
            self._start = now
            self._previous = now
            self._running = True
        return self

    def stop(self) -> T:
        now = self._clock_counter()
        # action
        if self._running:
            delta = now - self._start
            if self._total is None: self._total = delta
            else: self._total += delta
            self._previous = now
            self._running = False
        else:
            raise RuntimeError('timer is already stopped.')
        return self._total  # pyright: ignore[reportReturnType] # always valid here

    def __enter__(self): return self.start()
    def __exit__(self, exc_type, exc, tb): self.stop()
