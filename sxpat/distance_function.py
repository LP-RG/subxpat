from __future__ import annotations
from typing import List, Optional, Sequence, Tuple
from abc import abstractmethod

from sxpat.utils.utils import call_z3_function, declare_z3_function, declare_z3_gate


class DistanceFunction:
    def __init__(self) -> None:
        raise NotImplementedError(f"Class `{self.__class__.__name__}` is an abstract class.")

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError(f"Property `{self.__class__.__name__}.name` is an abstract property.")

    @property
    @abstractmethod
    def abbreviation(self):
        raise NotImplementedError(f"Property `{self.__class__.__name__}.abbreviation` is an abstract property.")

    @property
    @abstractmethod
    def min_distance(self) -> int:
        """The minimum value above 0 this function can be."""
        raise NotImplementedError(f"Property `{self.__class__.__name__}.min_distance` is an abstract property.")

    @abstractmethod
    def with_no_input(self):
        raise NotImplementedError(f"Method `{self.__class__.__name__}.with_no_input` is an abstract method.")

    @abstractmethod
    def declare(self, prefix: str = None) -> List[str]:
        raise NotImplementedError(f"Method `{self.__class__.__name__}.declare` is an abstract method.")

    @abstractmethod
    def assign(self, vars_1: Sequence[str], vars_2: Sequence[str], prefix: str = None) -> List[str]:
        raise NotImplementedError(f"Method `{self.__class__.__name__}.assign` is an abstract method.")

    @staticmethod
    def _prefix(prefix: Optional[str]) -> str:
        return f"{prefix}_" if prefix else ""


class HammingDistance(DistanceFunction):
    def __init__(self, inputs: Sequence[str]) -> None:
        self._inputs: Tuple[str] = tuple(inputs)

    name = property(lambda s: "Hamming Distance")
    abbreviation = property(lambda s: "HamD")

    min_distance = property(lambda s: 1)

    def with_no_input(self):
        return type(self)([])

    @classmethod
    def _declare(cls, inputs: Sequence[str], prefix: str) -> List[str]:
        return [
            declare_z3_function(
                f"{prefix}val", len(inputs),
                "z3.BoolSort()", "z3.IntSort()"
            ),
            (
                f"{prefix}out_dist = "
                + call_z3_function(f"{prefix}val", inputs)
            )
        ]

    @classmethod
    def _assign(cls,
                inputs: Sequence[str],
                vars_1: Sequence[str], vars_2: Sequence[str],
                prefix: str):
        parts = [
            f"{call_z3_function(v1, inputs)} != {call_z3_function(v2, inputs)}"
            for v1, v2 in zip(vars_1, vars_2)
        ]
        return [
            "# Function: hamming distance",
            call_z3_function(f"{prefix}val", inputs) + f" == z3.Sum({', '.join(parts)}),"
        ]

    def declare(self, prefix: str = None) -> List[str]:
        return self._declare(self._inputs, self._prefix(prefix))

    def assign(self,
               vars_1: Sequence[str], vars_2: Sequence[str],
               prefix: str = None) -> List[str]:
        return self._assign(
            self._inputs,
            vars_1, vars_2,
            self._prefix(prefix),
        )


class WeightedHammingDistance(DistanceFunction):
    def __init__(self, inputs: Sequence[str], weights: Sequence[int]) -> None:
        self._inputs: Tuple[str] = tuple(inputs)
        self._weights: Tuple[int] = tuple(weights)

    name = property(lambda s: "Weighted Hamming Distance")
    abbreviation = property(lambda s: "WHamD")

    min_distance = property(lambda s: min(s._weights))

    def with_no_input(self):
        return type(self)([], self._weights)

    @classmethod
    def _declare(cls, inputs: Sequence[str], prefix: str) -> List[str]:
        return [
            declare_z3_function(
                f"{prefix}val", len(inputs),
                "z3.BoolSort()", "z3.IntSort()"
            ),
            (
                f"{prefix}out_dist = "
                + call_z3_function(f"{prefix}val", inputs)
            )
        ]

    @classmethod
    def _assign(cls,
                inputs: Sequence[str],
                vars_1: Sequence[str], vars_2: Sequence[str],
                weights: Sequence[int], prefix: str):
        parts = [
            f"z3.If({call_z3_function(v1, inputs)} != {call_z3_function(v2, inputs)}, {w}, 0)"
            for v1, v2, w in zip(vars_1, vars_2, weights)
        ]
        return [
            "# Function: weighted hamming distance",
            call_z3_function(f"{prefix}val", inputs) + f" == z3.Sum({', '.join(parts)}),"
        ]

    def declare(self, prefix: str = None) -> List[str]:
        return self._declare(self._inputs, self._prefix(prefix))

    def assign(self,
               vars_1: Sequence[str], vars_2: Sequence[str],
               prefix: str = None) -> List[str]:
        return self._assign(
            self._inputs,
            vars_1, vars_2,
            self._weights,
            self._prefix(prefix),
        )


class WeightedAbsoluteDifference(DistanceFunction):
    def __init__(self,
                 inputs: Sequence[str], weights: Sequence[int]
                 ) -> None:
        self._inputs: Tuple[str] = tuple(inputs)
        self._weights: Tuple[int] = tuple(weights)

    name = property(lambda s: "Absolute Difference of Weighted Sums")
    abbreviation = property(lambda s: "WAD")

    min_distance = property(lambda s: min(s._weights))

    def with_no_input(self):
        return type(self)([], self._weights)

    @classmethod
    def _declare(cls,
                 inputs: Sequence[str], prefix: str
                 ) -> List[str]:
        return [
            *[
                declare_z3_function(
                    f"{prefix}val1", len(inputs),
                    "z3.BoolSort()", "z3.IntSort()"
                ),
                declare_z3_function(
                    f"{prefix}val2", len(inputs),
                    "z3.BoolSort()", "z3.IntSort()"
                ),
            ],
            (
                f"{prefix}out_dist = z3.Abs("
                + call_z3_function(f"{prefix}val1", inputs)
                + " - "
                + call_z3_function(f"{prefix}val2", inputs)
                + ")"
            )
        ]

    @classmethod
    def _assign_one(cls,
                    val_name: str, inputs: Sequence[str],
                    vars: Sequence[str], weights: Sequence[int]
                    ) -> str:
        vars = [
            call_z3_function(v, inputs) + f'*{w}'
            for v, w in zip(vars, weights)
        ]
        return (
            f"{call_z3_function(val_name, inputs)} == "
            + f"z3.Sum({', '.join(vars)})"
        )

    @classmethod
    def _assign(cls,
                inputs: Sequence[str],
                vars_1: Sequence[str], vars_2: Sequence[str],
                weights: Sequence[int], prefix: str
                ) -> List[str]:
        return [
            "# Function: weighted sum absolute difference",
            cls._assign_one(f"{prefix}val1", inputs, vars_1, weights) + ",",
            cls._assign_one(f"{prefix}val2", inputs, vars_2, weights) + ",",
        ]

    def declare(self, prefix: str = None) -> List[str]:
        return self._declare(self._inputs, self._prefix(prefix))

    def assign(self,
               vars_1: Sequence[str], vars_2: Sequence[str],
               prefix: str = None) -> List[str]:
        return self._assign(
            self._inputs,
            vars_1, vars_2,
            self._weights,
            self._prefix(prefix),
        )

# class IntegerAbsoluteDifference(WeightedAbsoluteDifference):
#     def __init__(self) -> None:
#         super().__init__([])

#     name = property(lambda s: "Integer Absolute Difference")
#     abbreviation = property(lambda s: "IAD")

#     @classmethod
#     def _declare(cls,
#                  vars_1: Iterable[str], vars_2: Iterable[str],
#                  prefix: str) -> List[str]:
#         lines = super()._declare(
#             vars_1, vars_2, prefix,
#             [2**i for i in range(len(vars_1))]
#         )
#         lines[0] = "# Function: integer sum absolute difference"
#         return lines

#     def declare(self,
#                 vars_1: Iterable[str], vars_2: Iterable[str],
#                 prefix: str = None) -> List[str]:
#         return self._declare(
#             vars_1, vars_2,
#             self._prefix(prefix)
#         )
