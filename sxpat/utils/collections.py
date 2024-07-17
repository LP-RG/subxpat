from typing import Iterator, Mapping, Sequence, Tuple, TypeVar

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
