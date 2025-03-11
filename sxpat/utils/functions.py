from typing import Callable, TypeVar


__all__ = ['get_producer', 'identity', 'str_to_bool']


T = TypeVar('T')


def get_producer(value: T) -> Callable[[], T]:
    return lambda: value


def identity(value: T) -> T:
    return value


STR_TO_BOOL = {
    'true': True,
    't': True,
    'false': False,
    'f': False,
}


def str_to_bool(string: str) -> bool:
    return STR_TO_BOOL[string.lower()]


def str_to_int_or_bool(string: str) -> bool:
    if string.isdigit():
        return int(string)
    else:
        return str_to_bool(string)
