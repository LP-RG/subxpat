from typing import Callable, TypeVar

import functools as ft

from .functions import get_raiser


__all__ = [
    'make_uninstantiable', 'make_utility_class',
]


T = TypeVar('T', bound=type)


def make_uninstantiable(message: str) -> Callable[[T], T]:
    def wrapper(cls: T) -> T:
        # format message
        _message = message.format(
            qualname=cls.__qualname__,
            name=cls.__name__,
        )

        # assign raiser to the __new__ method
        setattr(cls, '__new__', get_raiser(NotImplementedError(_message)))

        return cls

    return wrapper


def make_utility_class(cls: T) -> T:
    return make_uninstantiable('{qualname} is a utility class and as such cannot be instantiated')(cls)


def static_storage(with_self_arg: bool = False, /, **vars):
    """
        Assigns the keyword arguments to the function object, allowing persistent storage for these variables and values.

        If `with_self_arg` is `True`, the first argument of the decorated function must be reserved for the function object, which will be used by the decorator to pass a reference to the function.
        To improve the typing of the decorated function, `typing.overload` helps in hiding the reserved first argument.
    """

    def decorate(func):
        # assign `vars` to the function object
        for (k, v) in vars.items(): setattr(func, k, v)

        if with_self_arg:
            return ft.partial(func, func)
        else:
            return func

    return decorate
