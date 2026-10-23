__all__ = ['Timer']

from abc import ABC, abstractmethod
from typing import (
    Literal,
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


class TimeRecorder[T:_SupportsAddSub](ABC):
    """
    :authors: Marco Biasion
    """

    @abstractmethod
    def tick(self) -> T:
        """
        Returns the difference between now and the previous tick or the start, whichever is closest.

        :raises RuntimeError: if the timer is not running.
        """
        raise NotImplementedError()

    def total(self) -> T | None:
        """
        If the timer is running, returns the difference since the start, summed with all totals from previous measurements.  
        If the timer is *not* running, returns the sum of all totals from the measurements.
        """
        raise NotImplementedError()

    def start(self) -> _Self:
        """
        Starts the timer. This is required for updating the measurements.

        :raises RuntimeError: if the timer is alrady running.
        """
        raise NotImplementedError()

    def stop(self) -> T:
        """
        Stops the timer.

        :raises RuntimeError: if the timer is alrady stopped.
        """
        raise NotImplementedError()

    def __enter__(self): return self.start()
    def __exit__(self, exc_type, exc, tb): self.stop()


@_final
class Timer2[T:_SupportsAddSub](TimeRecorder[T]):
    """
    :authors: Marco Biasion
    """
    __slots__ = ['_clock_counter', '_start', '_previous', '_total', '_running']

    @classmethod
    def default(cls: type[Timer2]) -> Timer2: return cls(default_counter)
    @classmethod
    def perf(cls: type[Timer2[float]]) -> Timer2[float]: return cls(perf_counter)
    @classmethod
    def perf_ns(cls: type[Timer2[int]]) -> Timer2[int]: return cls(perf_counter_ns)
    @classmethod
    def rusage(cls: type[Timer2[float]]) -> Timer2[float]: return cls(rusage_counter)

    def __init__(
        self,
        counter: _Callable[[], T],
        stopped_callback: _Callable[[T], None] = lambda t: None,
    ):
        self._clock_counter = counter
        self._stopped_callback = stopped_callback
        #
        self._start: T
        self._previous: T
        self._total: T | None = None
        self._running: bool = False

    def tick(self) -> T:
        """
        Returns the difference between now and the previous tick or the start, whichever is closest.

        :raises RuntimeError: if the timer is not running.
        """

        now = self._clock_counter()
        if not self._running: raise RuntimeError('The timer is not running.')

        delta = now - self._previous
        self._previous = now
        return delta

    def total(self) -> T | None:
        """
        If the timer is running, returns the difference since the start summed with all totals from previous measurements.  
        If the timer is *not* running, returns the sum of all totals from the measurements.  
        If the timer never run, returns `None`.
        """
        now = self._clock_counter()
        # action
        if self._running:
            delta = now - self._start
            if self._total is None: return delta
            else: return self._total + delta
        else:
            return self._total

    def start(self) -> _Self:
        """
        Starts the timer. This is required for updating the measurements.

        :raises RuntimeError: if the timer is alrady running.
        """
        now = self._clock_counter()
        # action
        if self._running:
            raise RuntimeError('The timer is already running.')
        else:
            self._start = now
            self._previous = now
            self._running = True
        return self

    def stop(self) -> T:
        """
        Stops the timer.

        :raises RuntimeError: if the timer is alrady stopped.
        """
        now = self._clock_counter()
        if not self._running: raise RuntimeError('The timer is already stopped.')
        # action
        delta = now - self._start
        if self._total is None: self._total = delta
        else: self._total += delta
        self._previous = now
        self._running = False
        self._stopped_callback(delta)
        return self._total

    def get_subtimer(self) -> Timer2:
        """
        Creates and returns a timer that, when stopped, will add its total to this one.
        """

        def increment_total(t: T):
            if self._total is None: self._total = t
            else: self._total += t
        return Timer2(self._clock_counter, increment_total)


class DummyTimer(TimeRecorder[int]):
    def tick(self) -> Literal[0]: return 0
    def total(self) -> Literal[0]: return 0
    def start(self) -> _Self: return self
    def stop(self) -> Literal[0]: return 0
