from __future__ import annotations
from typing import Callable, Iterable, Type, TypeVar, Union


__all__ = ['get_producer', 'identity',
           'str_to_bool', 'str_to_int_or_bool',
           'is_exact_instance_of']


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


def is_exact_instance_of(obj: object, class_or_tuple: Union[Type, Iterable[Type]]) -> bool:
    if isinstance(class_or_tuple, tuple):
        return any(is_exact_instance_of(obj, cot) for cot in class_or_tuple)
    else:
        return issubclass(type(obj), class_or_tuple) and issubclass(class_or_tuple, type(obj))
