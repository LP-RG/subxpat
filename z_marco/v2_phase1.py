import dataclasses as dc
import time
from typing import Dict, Tuple
import z3

from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.config.config import *

from .z3_utils import weighted_sum_difference, hamming_distance
from .utils import augment


def is_annotated(node: Dict) -> bool:
    return node.get(SUBGRAPH, None) == 1


@augment(["timed"])
def find_smallest_invalid_distance(graph: AnnotatedGraph, max_distance: int) -> Tuple[int, float]:
    exact_outputs = [z3.Bool(n) for n in graph.output_dict.keys()]
    approx_outputs = [z3.Bool(f"y{i}") for i in len(exact_outputs)]

    print(graph.graph.nodes)
    exit()
    circuit = ...

    # distance variable
    if True:  # hamming distance
        distance = hamming_distance(exact_outputs, approx_outputs)
    else:  # weighted sum difference
        weights = ...
        distance = weighted_sum_difference(exact_outputs, approx_outputs, weights)

    # add circuit and constraints to optimizer
    optimizer = z3.Optimize()
    optimizer.add(circuit)
    optimizer.add(distance > max_distance)

    # setup objective
    objective = optimizer.minimize(distance)

    # optimize
    optimizer.check()
    optimizer.lower(objective)

    # extract wanted distance
    model = optimizer.model()
    return model[distance]
