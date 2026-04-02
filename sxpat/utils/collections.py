from __future__ import (
    annotations,
)
from typing import (
    Callable,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Literal,
    Mapping,
    MutableMapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)
from collections import (
    UserDict,
)

import itertools as it
import math

from sxpat.utils.decorators import (
    static_storage,
)


__all__ = [
    # mappings
    'mapping_inv',
    'MultiDict', 'InheritanceMapping',
    # iterables update
    'iterable_replace', 'iterable_replace_index',
    # iterables transform
    'flat', 'pairwise', 'unzip',
    # iterables extract
    'first',
]


NOTHING = object()
K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')


@overload
def mapping_inv(mapping: Mapping[K, V], value: V) -> K:
    """
        Given a mapping, returns the key associated to the first occurrance of the value.
        If the value never occurs in the mapping, raises an exception.
    """


@overload
def mapping_inv(mapping: Mapping[K, V], value: V, default: T) -> Union[K, T]:
    """
        Given a mapping, returns the key associated to the first occurrance of the value.
        If the value never occurs in the mapping, returns the given default.
    """


def mapping_inv(mapping: Mapping[K, V], value: V, default=NOTHING) -> Union[K, T]:
    """
        @note: if we move to an invertible mapping (eg. `bidict`) this will not be needed anymore

        @authors: Marco Biasion
    """

    key = next((k for (k, v) in mapping.items() if v == value), default)
    if key is NOTHING: raise ValueError('The value does not match with any pair in the mapping.')
    return key


def iterable_replace(iterable: Iterable[T], to_be_replace: T, replacement: T) -> Iterator[T]:
    """
        Given an iterable, a value to be replaced, and a value to replace it with,
        returns an iterator with all occurrences of `to_be_replaced` replaced with `replacement`.

        @authors: Marco Biasion
    """
    for value in iterable:
        if value == to_be_replace:
            yield replacement
        else:
            yield value


def iterable_replace_index(iterable: Iterable[T], index: int, value: T) -> Iterator[T]:
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


def pairwise(iterable: Iterable[T]) -> Generator[Tuple[T, T]]:
    """
        example: `pairwise((1,2,3,4))` -> `(1,2) (2,3) (3,4)`.  
        credits: https://docs.python.org/3.12/library/itertools.html#itertools.pairwise
    """

    iterator = iter(iterable)

    # get first element or terminate
    try: a = next(iterator)
    except StopIteration: return

    # generate all pairs
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

    def __init__(self, mapping: Optional[Mapping[Iterable[K], V]] = None) -> None:
        super().__init__()

        if mapping is None: return
        for (ks, v) in mapping.items(): self.__setitem__(ks, v)

    def __setitem__(self, key: Iterable[K], value: V) -> None:
        for k in key: self.data[k] = value


class InheritanceMapping(MutableMapping[Type, V]):
    """
        A dictionary-like mapping from a type to a value, implicitly mapping all subclasses to the same value.

        @authors: Marco Biasion
    """

    def __init__(self, mapping: Optional[Mapping[Type, V]] = None) -> None:
        self.data: MultiDict[Type, V] = MultiDict()

        if mapping is None: return
        for (k, v) in mapping.items(): self.__setitem__(k, v)

    # custom implementations

    def __setitem__(self, key: Type, value: V) -> None:
        """Adds a mapping from the given type (and all subtypes) to the given value."""
        # note: after a bit of testing this is still one of the most efficient approaches (tried: list, queue+set, stack+set)
        #       if the overlapping of subtypes is low, the `list`` approach is faster
        #       if the overlapping of subtypes is relevant, the `stack+set`` approach is faster

        # list
        seen = [key]
        for t in seen: seen.extend(t.__subclasses__())
        self.data[frozenset(seen)] = value

        # stack+set
        # to_check = [first]
        # seen = set()
        # while len(to_check) > 0:
        #     t = to_check.pop()
        #     if t in seen: continue
        #     seen.add(t)
        #     to_check.extend(next(t))
        # self.data[seen] = value

    # composed from MultiDict(UserDict)
    def __len__(self) -> int: return self.data.__len__()
    def __getitem__(self, key: Type) -> V: return self.data.__getitem__(key)
    # def __setitem__(...) # custom implemented
    def __delitem__(self, key: Type) -> None: return self.data.__delitem__(key)
    def __iter__(self) -> Iterator[Type]: return self.data.__iter__()
    def __contains__(self, key) -> bool: return self.data.__contains__(key)
    def __repr__(self) -> str: return self.data.__repr__()

    # inherited from abc.Mapping
    # def get(...)           # default implementation is acceptable
    # def __contains__(...)  # composed from MultiDict
    # def keys(...)          # default implementation is acceptable
    # def items(...)         # default implementation is acceptable
    # def values(...)        # default implementation is acceptable
    # def __eq__(...)        # default implementation is acceptable
    # def __ne__(...)        # default implementation is acceptable

    # inherited from abc.MutableMapping
    # def pop(...)         # default implementation is acceptable
    # def popitem(...)     # default implementation is acceptable
    # def clear(...)       # default implementation is acceptable
    # def update(...)      # default implementation is acceptable
    # def setdefault(...)  # default implementation is acceptable


class MatchingElementError(LookupError): """Matching element not found."""


@overload
def first(predicate: Callable[[T], bool], iterable: Iterable[T]) -> T:
    """
        Returns the first element in the iterable matching the predicate.  
        `MatchingElementError` is raised if no element matches.
    """


@overload
def first(predicate: Callable[[T], bool], iterable: Iterable[T], default: V) -> Union[T, V]:
    """
        Returns the first element in the iterable matching the predicate.  
        `default` is returned if no element matches.
    """


def first(predicate: Callable[[T], bool], iterable: Iterable[T], default=NOTHING) -> Union[T, V]:
    """@authors: Marco Biasion"""

    element = next(filter(predicate, iterable), default)
    if element is NOTHING: raise MatchingElementError('No matching element was found.')
    return element


@overload
def formatted_int_range(stop: int,
                        /, *, base: Literal['b', 'o', 'd', 'x', 'X'] = 'd') -> Generator[str]:
    """
        Returns a generator of formatted integers from 0 to `stop` (exclusive) with step 1.

        `stop` cannot be negative.
    """


@overload
def formatted_int_range(start: int, stop: int, step: int = 1,
                        /, *, base: Literal['b', 'o', 'd', 'x', 'X'] = 'd') -> Generator[str]:
    """
        Returns a generator of formatted integers from `start` (inclusive) to `stop` (exclusive) with step `step`.

        `start` and `stop` cannot be negative.
    """


@static_storage(True, mapping={'b': 2, 'o': 8, 'd': 10, 'x': 16, 'X': 16})
def formatted_int_range(self, start: int = 0, stop: Optional[int] = None, step: int = 1,
                        /, *, base: Literal['b', 'o', 'd', 'x', 'X'] = 'd') -> Generator[str]:

    # set limits if partial
    if stop is None:
        stop = start
        start = 0

    # find largest limit
    maximum = start
    if (stop is not None) and (stop > maximum): maximum = stop

    # compute adjustment length
    length = math.ceil(math.log(maximum, self.mapping[base]))

    # generate numbers
    yield from (f'{i:0{length}{base}}' for i in range(start, stop, step))
