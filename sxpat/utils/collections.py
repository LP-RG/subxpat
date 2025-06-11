from __future__ import annotations
from collections import UserDict
from typing import Generic, Iterable, Iterator, Mapping, Tuple, Type, TypeVar, Union

import itertools as it


__all__ = [
    # methods
    'mapping_inv', 'flat', 'pairwise',
    # classes
    'MultiDict', 'InheritanceMapping',
]


NOTHING = object()
K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')


def mapping_inv(mapping: Mapping[K, V], value: V, default: K = NOTHING) -> K:
    """
        Given a mapping, returns the key associated to the first occurrance of the value.
        If the value never occurs in the mapping, returns the default if given or raise an exception.

        @note: if we move to an invertible mapping (eg. bidict) this will not be needed anymore

        @authors: Marco Biasion
    """
    key = next((k for (k, v) in mapping.items() if v == value), default)
    if key is NOTHING: raise ValueError('The value does not match with any pair in the mapping.')
    return key


def iterable_replace(iterable: Iterable[T], index: int, value: T) -> Iterator[T]:
    """
        Given an iterable, and a value to be replaced at a certain index, 
        returns an iterator with the value at the index replaced with the given one.  
        If the iterable ends before reaching index, the given value is appended at the end.

        @authors: Marco Biasion
    """
    iterable = iter(iterable)
    yield from it.islice(iterable, index)  # yield from the iterable up to index (excluded)
    yield value  # yield the value
    next(iterable)  # skip a value from the iterable
    yield from iterable  # yield the remaining from the iterable (restarts at index + 1)


def flat(iterable:
         Iterable[  # this abomination is to allow type hinting, recursive types don't really work (eg. R = Union[T, Iterable['R']) (maybe with newer python versions?)
             Union[T, Iterable[
                 Union[T, Iterable[
                     Union[T, Iterable[
                         Union[T, Iterable[
                             Union[T, Iterable[
                                 Union[T, Iterable[
                                     Union[T, Iterable[
                                         Union[T, Iterable[
                                             T]]]]]]]]]]]]]]]]]
         ) -> Iterator[T]:
    for i in iterable:
        if isinstance(i, Iterable): yield from flat(i)
        else: yield i


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


class MultiDict(UserDict, Generic[K, V]):
    """
        A dictionary-like mapping that allows multiple keys to be associated with the same value.

        @authors: Marco Biasion
    """

    def __init__(self, mapping: Mapping[Iterable[K], V] = None) -> None:
        super().__init__()

        if mapping is None: return
        for ks, v in mapping.items(): self.__setitem__(ks, v)

    def __setitem__(self, key: Iterable[K], value: V) -> None:
        for k in key: self.data[k] = value


class InheritanceMapping(MultiDict[Type, V]):
    """
        A dictionary-like mapping from a type to a value, implicitly mapping all subclasses to the same value.

        @authors: Marco Biasion
    """

    def __init__(self, mapping: Mapping[Type, V] = None) -> None:
        super().__init__(mapping)

    def __setitem__(self, key: Type, value: V) -> None:
        subtypes = [key]
        for t in subtypes: subtypes.extend(t.__subclasses__())
        super().__setitem__(frozenset(subtypes), value)
