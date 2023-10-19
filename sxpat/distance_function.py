from __future__ import annotations
from typing import Iterable, List, Optional
from abc import abstractmethod


class DistanceFunction:
    def __init__(self) -> None:
        raise NotImplementedError(f"Class `{self.__class__.__name__}` is an abstract class.")

    @abstractmethod
    def declare(self, vars_1: Iterable[str], vars_2: Iterable[str],
                prefix: str = None) -> List[str]:
        raise NotImplementedError(f"Method `{self.__class__.__name__}.declare` is an abstract method.")

    @staticmethod
    def _prefix(prefix: Optional[str]) -> str:
        return f"{prefix}_" if prefix else ""


class HammingDistance(DistanceFunction):
    def __init__(self) -> None: pass

    @classmethod
    def _declare(cls,
                 vars_1: Iterable[str], vars_2: Iterable[str],
                 prefix: str) -> List[str]:
        return [
            "# Function: hamming distance",
            f"{prefix}out_dist = " + " + ".join(
                f"z3.If({v1} == {v2}, 0, 1)"
                for v1, v2 in zip(vars_1, vars_2)
            )
        ]

    def declare(self,
                vars_1: Iterable[str], vars_2: Iterable[str],
                prefix: str = None) -> List[str]:
        return self._declare(
            vars_1, vars_2,
            self._prefix(prefix)
        )


class WeightedAbsoluteDifference(DistanceFunction):
    def __init__(self, weights: Iterable[int]) -> None:
        self._weights: List[int] = list(weights)

    @classmethod
    def _declare(cls,
                 vars_1: Iterable[str], vars_2: Iterable[str],
                 prefix: str,
                 weights: List[int]) -> List[str]:
        val1 = f"{prefix}val1"
        val2 = f"{prefix}val2"
        val1_parts = [f"{v}*{w}" for v, w in zip(vars_1, weights)]
        val2_parts = [f"{v}*{w}" for v, w in zip(vars_2, weights)]

        return [
            "# Function: weighted sum absolute difference",
            f"{val1} = {' + '.join(val1_parts)}",
            f"{val2} = {' + '.join(val2_parts)}",
            f"{prefix}out_dist = z3.If({val1} > {val2}, {val1} - {val2}, {val2} - {val1})"
        ]

    def declare(self,
                vars_1: Iterable[str], vars_2: Iterable[str],
                prefix: str = None) -> List[str]:
        return self._declare(
            vars_1, vars_2,
            self._prefix(prefix),
            self._weights
        )


class IntegerAbsoluteDifference(WeightedAbsoluteDifference):
    def __init__(self) -> None:
        super().__init__([])

    @classmethod
    def _declare(cls,
                 vars_1: Iterable[str], vars_2: Iterable[str],
                 prefix: str) -> List[str]:
        lines = super()._declare(
            vars_1, vars_2, prefix,
            [2**i for i in range(len(vars_1))]
        )
        lines[0] = "# Function: integer sum absolute difference"
        return lines

    def declare(self,
                vars_1: Iterable[str], vars_2: Iterable[str],
                prefix: str = None) -> List[str]:
        return self._declare(
            vars_1, vars_2,
            self._prefix(prefix)
        )
