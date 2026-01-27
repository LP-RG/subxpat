__all__ = ['Timer']

from typing_extensions import (
    Callable as _Callable,
    Self as _Self,
    TypeVar as _TypeVar,
    Tuple as _Tuple,
)
from dataclasses import (
    dataclass as _dataclass
)

import functools as _ft
import resource as _res

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
