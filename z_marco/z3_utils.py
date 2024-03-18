from typing import List, Union
import z3


def weighted_sum(variables: List[z3.BoolRef], weights: int) -> z3.ArithRef:
    return z3.Sum([v * w for v, w in zip(variables, weights)])


def weighted_sum_difference(vars_a: List[z3.BoolRef], vars_b: List[z3.BoolRef], weights: List[int]) -> z3.ArithRef:
    return z3.Abs(weighted_sum(vars_a, weights) - weighted_sum(vars_b, weights))


def hamming_distance(vars_a: List[z3.BoolRef], vars_b: List[z3.BoolRef]) -> z3.ArithRef:
    return z3.Sum(*(
        a != b
        for a, b in zip(vars_a, vars_b)
    ))

# def template()