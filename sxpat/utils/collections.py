from __future__ import annotations
from collections import UserDict
from typing import Iterable, Iterator, Mapping, Sequence, Tuple, Type, TypeVar, Union

import itertools


NOTHING = object()
K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')


def mapping_inv(mapping: Mapping[K, V], value: V, default: K = NOTHING) -> K:
    key = next((k for (k, v) in mapping.items() if v == value), default)
    if key is NOTHING:
        raise ValueError('The value does not match with any pair in the mapping.')
    return key


def pairwise_iter(sequence: Sequence[T]) -> Iterator[Tuple[T, T]]:
    """iterate pair-wise (AB, BC, CD, ...)"""
    return zip(sequence, itertools.islice(sequence, 1, None))


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
