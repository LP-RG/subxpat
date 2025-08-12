from typing import Callable, TypeVar, Tuple
from typing_extensions import Self
import dataclasses as dc

import functools as ft
import resource

__all__ = ['timer']


@dc.dataclass(init=False, repr=False, eq=False, frozen=True)
class Timer:
    """
        This class is used to wrap functions to be able to time their execution.

        The counted time is the time in user mode and the time in system mode
        for the current process and all children from the start to the end of the function.

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

    _C = TypeVar('_C', bound=Callable)

    latest: float = 0
    """The time spent on the latest call of a wrapped function under this timer (in seconds)."""
    total: float = 0
    """The time spent in total on all calls of a wrapped functions under this timer (in seconds)."""

    def wrap(self, function: _C) -> _C:
        """
            Wraps the given function and return a timed alias under this timer.   
            Can be used as a decorator.
        """

        @ft.wraps(function)
        def wrapper(*args, **kwds):
            # get starting time data
            times_start = (
                resource.getrusage(resource.RUSAGE_SELF),
                resource.getrusage(resource.RUSAGE_CHILDREN),
            )

            # execute function
            result = function(*args, **kwds)

            # get ending time data
            times_end = (
                resource.getrusage(resource.RUSAGE_SELF),
                resource.getrusage(resource.RUSAGE_CHILDREN),
            )

            # compute delta
            time_delta = (
                + (times_end[0].ru_utime - times_start[0].ru_utime)  # process user level time
                + (times_end[0].ru_stime - times_start[0].ru_stime)  # process system level time
                + (times_end[1].ru_utime - times_start[1].ru_utime)  # children user level time
                + (times_end[1].ru_stime - times_start[1].ru_stime)  # children system level time
            )

            # update fields
            object.__setattr__(self, 'latest', time_delta)
            object.__setattr__(self, 'total', self.total + time_delta)

            return result

        return wrapper

    @classmethod
    def from_function(cls, function: _C) -> Tuple[Self, _C]:
        """Create a timer wrapping the given function."""

        timer = Timer()
        wrapped = timer.wrap(function)
        return (timer, wrapped)
