from __future__ import annotations
from typing import Mapping

import networkx as nx


def compute(graph: nx.digraph.DiGraph) -> Mapping[str, int]:

    # TODO: Xiaozihan
    # Implement the "partition and propagate" algorithm


    # step 1: Graph partitioning (section 3.2)
    ...

    # step 2: Derivation of the propagation matrix (section 3.3)
    ...

    # step 3: Propagation
    ...

    # step 4: Subgraph simulation for internal nodes
    ...

    # return the mapping from names to weights
    return ...
