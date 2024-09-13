from __future__ import annotations
from collections import UserDict
from typing import Iterable, Iterator, Mapping, Tuple, Type, TypeVar


__all__ = ['mapping_inv', 'flat', 'pairwise', 'MultiDict', 'InheritanceMapping']


NOTHING = object()
K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')


def mapping_inv(mapping: Mapping[K, V], value: V, default: K = NOTHING) -> K:
    key = next((k for (k, v) in mapping.items() if v == value), default)
    if key is NOTHING:
        raise ValueError('The value does not match with any pair in the mapping.')
    return key


def flat(iterable: Iterable) -> Iterator:
    for i in iterable:
        if isinstance(i, Iterable):
            yield from flat(i)
        else:
            yield i


def pairwise(iterable: Iterable[T]) -> Iterator[Tuple[T, T]]:
    """
    example: `pairwise((1,2,3,4))` -> `(1,2) (2,3) (3,4)`.  
    credits: https://docs.python.org/3.12/library/itertools.html#itertools.pairwise
    """

    iterator = iter(iterable)
    a = next(iterator, None)
    for b in iterator:
        yield a, b
        a = b


def unzip(iterable: Iterable) -> Iterable:
    return zip(*iterable)


class MultiDict(UserDict, Mapping[K, V]):
    def __init__(self, mapping: Mapping[Iterable[K], V] = None) -> None:
        super().__init__()

        if mapping is not None:
            for ks, v in mapping.items():
                self.__setitem__(ks, v)

    def __setitem__(self, key: Iterable[K], value: V) -> None:
        for k in key:
            self.data[k] = value


class InheritanceMapping(MultiDict[Type, V]):
    def __init__(self, mapping: Mapping[Type, V] = None) -> None:
        super().__init__(mapping)

    def __setitem__(self, key: Type, value: V) -> None:
        subtypes = [key]
        for t in subtypes:
            subtypes.extend(t.__subclasses__())

        super().__setitem__(subtypes, value)
