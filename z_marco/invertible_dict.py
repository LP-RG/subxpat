from __future__ import annotations

from collections.abc import MutableMapping, Mapping
from typing import Dict, TypeVar, Generic


K = TypeVar("K")
V = TypeVar("V")


class InvertibleDict(MutableMapping, Generic[K, V]):

    __slots__ = ("_forward", "_backward", "__inv")

    def __init__(self, forward: Mapping[K, V], /, *,
                 _inv: InvertibleDict[V, K] = None
                 ) -> None:
        self._forward: Dict[K, V]
        self._backward: Dict[V, K]

        if _inv is not None:
            self._forward = _inv._backward
            self._backward = _inv._forward
            self.__inv = _inv

        else:
            self._forward = {k: v for k, v in (forward or dict()).items()}
            self._backward = {v: k for k, v in (forward or dict()).items()}
            self.__inv = self.__class__(None, _inv=self)

        self._check_correct()

    def _check_correct(self) -> None:
        if len(self._forward) != len(self._backward):
            raise ValueError("The relation must be one-to-one.")

    @property
    def inv(self) -> InvertibleDict[V, K]:
        return self.__inv

    def __getitem__(self, key: K) -> V:
        return self._forward[key]

    def __setitem__(self, key: K, value: V):
        self._forward[key] = value
        self._backward[value] = key
        self._check_correct()

    def __delitem__(self, key: K):
        value = self._forward[key]
        del self._forward[key]
        del self._backward[value]

    def __iter__(self):
        return iter(self._forward)

    def __len__(self):
        return len(self._forward)


if __name__ == "__main__":
    # TEST

    obj = InvertibleDict({1: 'a', 2: 'b', 3: 'c'})
    inv = obj.inv
    for k, v in obj.items():
        assert obj[k] == v and inv[v] == k, "Test failed"
        print(".", end="")
    print(" Success")

    obj[4] = 'd'
    inv['e'] = 5
    for k, v in obj.items():
        assert obj[k] == v and inv[v] == k, "Test failed"
        print(".", end="")
    print(" Success")

    del obj[1]
    del inv['b']
    assert (1 not in obj and 'a' not in inv) and ('b' not in inv and 2 not in obj)
    print(" Success")

    try:
        obj = InvertibleDict({1: 'a', 2: 'a'})
        assert False
    except ValueError as e:
        print(" Success")
