from typing import Callable, Type, TypeVar

from .functions import get_raiser


T = TypeVar('T', bound=Type)


def make_uninstantiable(message: str) -> Callable[[T], T]:
    def wrapper(cls: T) -> T:
        nonlocal message

        # format message
        message = message.format(
            qualname=cls.__qualname__,
            name=cls.__name__,
        )

        # assign raiser to the __new__ method
        setattr(cls, '__new__', get_raiser(NotImplementedError(message)))

        return cls

    return wrapper
