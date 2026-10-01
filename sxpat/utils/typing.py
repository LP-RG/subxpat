from typing import Protocol, Self


class SupportsAdd(Protocol):
    def __add__(self, other: Self, /) -> Self: ...


class SupportsSub(Protocol):
    def __sub__(self, other: Self, /) -> Self: ...


class SupportsAddSub(SupportsAdd, SupportsSub, Protocol): ...


class SupportsWrite[T](Protocol):
    def write(self, s: T, /) -> object: ...
