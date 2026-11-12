import itertools
import math
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple

import re
import networkx as nx

from z3 import (
    BitVecRef,
    BitVecVal,
    If,
    Optimize,
    Bool, And, Or, Not, Implies, Sum, BoolVal,
    Datatype, BitVecSort, BoolSort, ULE,
    BoolRef, DatatypeSortRef, DatatypeRef,
    sat, is_true
)

from sxpat.constants.misc import WEIGHT
from sxpat.graph.graph import IOGraph
from sxpat.graph.node import BoolConstant, Identity, BoolVariable
from sxpat.specifications import Specifications

from sxpat.utils.graph import is_selection_convex


__all__ = [
    'find_subgraph_feasible_hard_datatype_bitvec',
    'find_subgraph_feasible_hard_datatype_bitvec_mintreshold',
    'slash_to_kill',
    'find_subgraph_output_nodes_ascendant',
]


class NodeDatatype(DatatypeRef): ...
class EdgeDatatype(DatatypeRef): ...


class NodeSortDatatype(DatatypeSortRef):
    @staticmethod
    def mk_node(id: BitVecRef, weight: BitVecRef, in_subgraph: BoolRef) -> NodeDatatype: ...
    @staticmethod
    def id(node: NodeDatatype) -> BitVecRef: ...
    @staticmethod
    def weight(node: NodeDatatype) -> BitVecRef: ...
    @staticmethod
    def in_subgraph(node: NodeDatatype) -> BoolRef: ...


class EdgeSortDatatype(DatatypeSortRef):
    @staticmethod
    def mk_edge(source: NodeDatatype, target: NodeDatatype) -> EdgeDatatype: ...
    @staticmethod
    def source(edge: EdgeDatatype) -> NodeDatatype: ...
    @staticmethod
    def target(edge: EdgeDatatype) -> NodeDatatype: ...


def _declare_datatypes(bit_width: int) -> Tuple[NodeSortDatatype, EdgeSortDatatype]:
    # define Node datatype
    Node = Datatype('Node')
    Node.declare(
        'mk_node',
        ('id', BitVecSort(bit_width)),
        ('weight', BitVecSort(bit_width)),
        ('in_subgraph', BoolSort()),
    )
    Node = Node.create()

    # define Edge datatype
    Edge = Datatype('Edge')
    Edge.declare(
        'mk_edge',
        ('source', Node),
        ('target', Node),
    )
    Edge = Edge.create()

    return (Node, Edge)


def _encode_nodes(
    available_nodes: Iterable[str],
    unavailable_nodes: Iterable[str],
    gates_weight: Mapping[str, int],
    bit_width: int,
    Node: NodeSortDatatype,
    candidates: Optional[Set[str]] = None,
) -> Tuple[Dict[str, NodeDatatype], List[BoolRef]]:
    """
    Encodes all available and unavailable nodes.

    :param candidates: if not `None`, every node outside this set is forced out of the subgraph.
    :return: the mapping of `str->Node` and the constraints for the unavailable nodes
    """

    z3_nodes: Dict[str, NodeDatatype] = dict()
    constraints: List[BoolRef] = list()
    ids = itertools.count()

    for _name, _id in zip(unavailable_nodes, ids):
        _w = gates_weight[_name]
        z3_nodes[_name] = _node = Node.mk_node(  # pyright: ignore[reportAttributeAccessIssue]
            BitVecVal(_id, bit_width),
            BitVecVal(_w, bit_width),
            Bool(_name),
        )
        constraints.append(Node.in_subgraph(_node) == BoolVal(False))  # pyright: ignore

    for _name, _id in zip(available_nodes, ids):
        _w = gates_weight[_name]
        z3_nodes[_name] = _node = Node.mk_node(  # pyright: ignore[reportAttributeAccessIssue]
            BitVecVal(_id, bit_width),
            BitVecVal(_w, bit_width),
            Bool(_name),
        )
        if _w == -1 or (candidates is not None and _name not in candidates):
            constraints.append(Node.in_subgraph(_node) == BoolVal(False))  # pyright: ignore

    return (z3_nodes, constraints)


def _candidates_from_outputs(
    circuit: IOGraph,
    threshold: int,
) -> Optional[Set[str]]:
    """
    Candidates for mode 55: the gates in the input cone of the outputs that can absorb
    the error, i.e. the outputs whose weight `2**i` is not above the threshold.

    Outputs are treated as LSB first, so the scan stops at the first output that is
    already too heavy (the following ones are heavier still).
    """

    graph = circuit._inner

    candidates: Set[str] = set()
    for (i, _name) in enumerate(circuit.outputs_names):
        if (1 << i) > threshold:
            break
        candidates.update(nx.ancestors(graph, _name))

    return candidates


def _candidates_above_cheapest_gates(
    circuit: IOGraph,
    gates_weight: Mapping[str, int],
    threshold: int,
) -> Optional[Set[str]]:
    """
    Candidates for mode 6: the ancestors-or-self of the gates that may legally be cut,
    i.e. `AncestorsOrSelf({n | 0 <= weight(n) <= threshold})`.

    With mode 6 setting the threshold to the minimum weight, this is the cone above the
    minimum-weight gates. Nodes outside it are `False` in every feasible model: a node
    of a convex selection always reaches a primary output, outputs are never selectable,
    so the path out of the selection must cross a cut edge whose source is within the
    threshold -- which only exists inside this cone.

    Returns `None` (no restriction) when the argument does not hold, i.e. when a
    weighted gate does not reach a primary output and could therefore sit in the
    selection without ever being cut.
    """

    graph = circuit._inner

    # only gates count: ports and constants are never selectable, and the outputs carry
    # the `2**i` weights added by `iograph_with_weights`, which must not be mistaken for
    # gate weights (otherwise this guard rejects every circuit and the restriction dies)
    excluded = (
        set(circuit.inputs_names)
        | set(circuit.outputs_names)
        | {node.name for node in circuit.constants}
    )
    gate_weight = {n: w for n, w in gates_weight.items() if n not in excluded}

    live: Set[str] = set()
    for _name in circuit.outputs_names:
        live.update(nx.ancestors(graph, _name))
    if not all(_name in live for _name, _weight in gate_weight.items() if _weight >= 0):
        return None

    eligible = {n for n, w in gate_weight.items() if 0 <= w <= threshold}

    candidates = set(eligible)
    for _name in eligible:
        candidates.update(nx.ancestors(graph, _name))

    return candidates



def _encode_edges(
    edges: Iterable[Tuple[str, str]],
    z3_nodes: Mapping[str, NodeDatatype],
    Edge: EdgeSortDatatype,
) -> List[EdgeDatatype]:

    z3_edges: List[EdgeDatatype] = list()

    for (_src, _des) in edges:
        _edge = Edge.mk_edge(z3_nodes[_src], z3_nodes[_des])
        z3_edges.append(_edge)

    return z3_edges


def _setup_problem(
    circuit: IOGraph,
    specs: Specifications,
    candidates: Optional[Set[str]] = None,
):
    graph = circuit._inner
    feasibility_threshold = specs.et

    bit_width = max(
        len(circuit.outputs) + math.ceil(math.log2(len(circuit.nodes))),
        math.ceil(math.log2(max(1, feasibility_threshold))) + 1
    )

    optimizer = Optimize()
    Node, Edge = _declare_datatypes(bit_width)

    available_nodes = [node.name for node in circuit.nodes]
    unavailable_nodes = itertools.chain(
        [name for name in circuit.inputs_names],
        [name for name in circuit.outputs_names],
        [node.name for node in circuit.constants],
    )

    z3_nodes, base_constraints = _encode_nodes(
        available_nodes,
        unavailable_nodes,
        {node.name: (getattr(node, WEIGHT, None) or -1) for node in circuit.nodes},
        bit_width,
        Node,
        candidates,
    )

    z3_edges = _encode_edges(graph.edges(), z3_nodes, Edge)

    optimizer.add(base_constraints)

    return optimizer, Node, Edge, z3_nodes, z3_edges, graph, bit_width


def _add_boundary_edges(graph, Node, z3_nodes, bit_width, candidates=None):
    z3_bitvec_0 = BitVecVal(0, bit_width)
    z3_bitvec_1 = BitVecVal(1, bit_width)

    z3_subinput_edges = []
    z3_suboutput_edges = []

    for name in z3_nodes:
        incoming_conditions = []
        outgoing_conditions = []

        for src, dst in graph.out_edges(name):
            src_in = Node.in_subgraph(z3_nodes[src])
            dst_in = Node.in_subgraph(z3_nodes[dst])

            incoming_conditions.append(And(Not(src_in), dst_in))
            outgoing_conditions.append(And(src_in, Not(dst_in)))

        if incoming_conditions:
            # a node that cannot be selected still counts as a subgraph input when it
            # feeds a selected node (the indicator is attributed to the edge source),
            # so this term must be kept even when `candidates` is given
            z3_subinput_edges.append(
                If(Or(incoming_conditions), z3_bitvec_1, z3_bitvec_0)
            )
            # an unselectable node can never be the source of a cut, so its sub-output
            # term is constantly 0 and can be dropped
            if candidates is None or name in candidates:
                z3_suboutput_edges.append(
                    If(Or(outgoing_conditions), z3_bitvec_1, z3_bitvec_0)
                )

    return z3_subinput_edges, z3_suboutput_edges


def _add_convexity(optimizer, graph, Node, z3_nodes, candidates=None):
    # only selectable nodes need constraints, and only selectable nodes matter inside
    # the conjunctions (the others are pinned to False, so `Not(in_subgraph(x))` is a
    # tautology that would only cost literals)
    def _keep(names):
        return [n for n in names if candidates is None or n in candidates]

    names = _keep(list(z3_nodes))

    ancestors = {n: sorted(_keep(nx.ancestors(graph, n))) for n in names}
    # a successor of a selectable node may itself be unselectable, but its selectable
    # descendants still have to be enumerated, so cache them lazily
    descendants: Dict[str, List[str]] = {}

    def _descendants(node: str) -> List[str]:
        if node not in descendants:
            descendants[node] = sorted(_keep(nx.descendants(graph, node)))
        return descendants[node]

    for src in names:
        for dst in graph.successors(src):

            # an empty descendant/ancestor list makes the implication a tautology
            _desc = _descendants(dst)
            if len(_desc) > 0:
                optimizer.add(
                    Implies(
                        And(
                            Node.in_subgraph(z3_nodes[src]),
                            Not(Node.in_subgraph(z3_nodes[dst]))
                        ),
                        And([Not(Node.in_subgraph(z3_nodes[n])) for n in _desc]
                            + [Not(Node.in_subgraph(z3_nodes[dst]))])
                    )
                )

            _anc = ancestors[src]
            if len(_anc) > 0:
                optimizer.add(
                    Implies(
                        And(
                            Not(Node.in_subgraph(z3_nodes[src])),
                            Node.in_subgraph(z3_nodes[dst])
                        ),
                        And([Not(Node.in_subgraph(z3_nodes[n])) for n in _anc]
                            + [Not(Node.in_subgraph(z3_nodes[src]))])
                    )
                )


def _solve_and_extract(optimizer, max_nodes, h, circuit: IOGraph) -> List[str]:
    graph = circuit._inner

    if optimizer.check() != sat:
        return []

    model = optimizer.model()

    found = model.eval(Sum(max_nodes), model_completion=True).as_long()
    max_ = h.upper().as_long()

    if found != max_:
        optimizer.add(Sum(max_nodes) == max_)
        assert optimizer.check() == sat
        model = optimizer.model()

    node_partition = [
        str(d) for d in model.decls()
        if is_true(model[d]) and str(d).startswith('g')
    ]

    if not is_selection_convex(graph, node_partition):
        raise RuntimeError("non-convex subgraph")

    return node_partition

def _declare_ancestor_datatypes():
    Node = Datatype("Node")
    Node.declare(
        "mk_node",
        ("id", BitVecSort(32)),
        ("in_subgraph", BoolSort()),
    )
    Node = Node.create()

    Edge = Datatype("Edge")
    Edge.declare(
        "mk_edge",
        ("source", Node),
        ("target", Node),
    )
    Edge = Edge.create()

    return Node, Edge

def _setup_output_ancestor_problem(
    circuit: IOGraph,
    specs: Specifications,
):
    graph = circuit._inner

    optimizer = Optimize()

    Node, Edge = _declare_ancestor_datatypes()

    output_name = circuit.outputs_names[specs.out_node]

    if output_name not in graph:
        return None

    ancestors_output = sorted(nx.ancestors(graph, output_name))

    available_nodes = {
        n for n in ancestors_output
        if n.startswith("g")
    }

    z3_nodes = {}
    constraints = []

    ids = itertools.count()

    all_nodes = (
        list(circuit.inputs_names)
        + [n.name for n in circuit.nodes]
        + list(circuit.outputs_names)
        + [n.name for n in circuit.constants]
    )

    for name, idx in zip(all_nodes, ids):
        z3_nodes[name] = node = Node.mk_node(
            BitVecVal(idx, 32),
            Bool(name)
        )

        if (
            name in circuit.inputs_names
            or name in circuit.outputs_names
            or name in [n.name for n in circuit.constants]
            or name not in available_nodes
        ):
            constraints.append(
                Node.in_subgraph(node) == BoolVal(False)
            )

    optimizer.add(constraints)

    z3_edges = [
        Edge.mk_edge(z3_nodes[src], z3_nodes[dst])
        for src, dst in graph.edges()
    ]

    return (
        optimizer,
        Node,
        Edge,
        z3_nodes,
        z3_edges,
        graph,
        ancestors_output,
    )

def _find_subgraph_in_candidates(
    circuit: IOGraph,
    specs: Specifications,
    candidates: Optional[Set[str]],
) -> List[str]:
    """
    Largest convex subgraph whose boundary is within the error threshold, restricted to
    `candidates`.

    This is the body shared by extraction modes 55 and 6, which differ only in how the
    candidate set is chosen. It is not an extraction mode itself and must not be
    dispatched to: `candidates` is the whole point of the parameter, and `None` means
    "no restriction", i.e. every node that carries a weight.
    """

    optimizer, Node, Edge, z3_nodes, z3_edges, graph, bit_width = _setup_problem(
        circuit, specs, candidates)

    z3_subinput_edges, z3_suboutput_edges = _add_boundary_edges(
        graph, Node, z3_nodes, bit_width, candidates)

    _add_convexity(optimizer, graph, Node, z3_nodes, candidates)

    # maximize
    z3_bitvec_1 = BitVecVal(1, bit_width)
    max_nodes = [
        If(Node.in_subgraph(n), z3_bitvec_1, BitVecVal(0, bit_width))
        for _name, n in z3_nodes.items()
        if candidates is None or _name in candidates
    ]
    # no candidate at all means the only feasible selection is the empty one
    if len(max_nodes) == 0:
        return []
    h = optimizer.maximize(Sum(max_nodes))

    # feasibility (edge-wise)
    optimizer.add(And([
        Implies(
            And(
                Node.in_subgraph(Edge.source(e)),
                Not(Node.in_subgraph(Edge.target(e)))
            ),
            ULE(
                Node.weight(Edge.source(e)),
                BitVecVal(specs.et, bit_width)
            )
        )
        for e in z3_edges
    ]))

    # imax / omax
    if specs.imax is not None:
        optimizer.add(Sum(z3_subinput_edges) <= specs.imax)
    if specs.omax is not None:
        optimizer.add(Sum(z3_suboutput_edges) <= specs.omax)

    return _solve_and_extract(optimizer, max_nodes, h, circuit)


def find_subgraph_feasible_hard_datatype_bitvec(circuit: IOGraph, specs):
    """
    Extraction mode 55: the candidate gates are the input cone of the outputs that can
    absorb the error, i.e. the outputs whose weight is not above the threshold.
    """

    candidates = _candidates_from_outputs(circuit, specs.et)

    return _find_subgraph_in_candidates(circuit, specs, candidates)


def find_subgraph_feasible_hard_datatype_bitvec_mintreshold(
    circuit: IOGraph,
    specs: Specifications,
) -> List[str]:
    """
    Extraction mode 6: the candidate gates are the cone above the gates with the minimum
    weight, i.e. the only gates that may legally be cut when the threshold is the
    minimum weight itself.
    """

    # prepare
    feasibility_threshold = specs.et
    weights = [getattr(node, "weight") for node in circuit.nodes if getattr(node, "weight", None) is not None and not isinstance(node, BoolConstant) and not isinstance(node, Identity) and not isinstance(node, BoolVariable)] # TODO: find better way to get needed weights
    min_weight = min(weights) if len(weights) else 0

    specs.et = min_weight
    try:
        gates_weight = {
            node.name: (getattr(node, WEIGHT, None) or -1) for node in circuit.nodes
        }
        candidates = _candidates_above_cheapest_gates(circuit, gates_weight, min_weight)

        subgraph_nodes = _find_subgraph_in_candidates(circuit, specs, candidates)
    finally:
        # restore the updated parameter also on failure
        specs.et = feasibility_threshold

    return subgraph_nodes


def slash_to_kill(
    circuit: IOGraph,
    specs: Specifications,
) -> List[str]:
    # No candidate restriction here: the summed feasibility is computed in bit-vector
    # arithmetic that can wrap, so `sum <= et` does not provably bound each cut source,
    # and the slash pass runs once per run anyway.
    optimizer, Node, Edge, z3_nodes, z3_edges, graph, bit_width = _setup_problem(circuit, specs)

    _add_convexity(optimizer, graph, Node, z3_nodes)

    # maximize
    z3_bitvec_1 = BitVecVal(1, bit_width)
    max_nodes = [
        If(Node.in_subgraph(n), z3_bitvec_1, BitVecVal(0, bit_width))
        for n in z3_nodes.values()
    ]
    h = optimizer.maximize(Sum(max_nodes))

    # child closure
    for parent in z3_nodes:
        children = list(graph.successors(parent))
        if not children:
            continue

        children_in = [
            Node.in_subgraph(z3_nodes[c])
            for c in children
        ]

        optimizer.add(Implies(
            And(Node.in_subgraph(z3_nodes[parent]), Or(children_in)),
            And(children_in)
        ))

    # feasibility (sum)
    feasibility_sum = Sum([
        If(
            And(
                Node.in_subgraph(Edge.source(e)),
                Not(Node.in_subgraph(Edge.target(e)))
            ),
            Node.weight(Edge.source(e)),
            BitVecVal(0, bit_width)
        )
        for e in z3_edges
    ])

    optimizer.add(ULE(feasibility_sum, BitVecVal(specs.et, bit_width)))

    return _solve_and_extract(optimizer, max_nodes, h, circuit)

def find_subgraph_output_nodes_ascendant(
    circuit: IOGraph,
    specs: Specifications,
) -> List[str]:

    graph = circuit._inner

    output_name = circuit.outputs_names[specs.out_node]

    if output_name not in graph:
        return []

    constants = {n.name for n in circuit.constants}

    ancestors_output = sorted(nx.ancestors(graph, output_name))

    gate_ancestors = [
        n
        for n in ancestors_output
        if n.startswith("g")
    ]

    if (
        len(gate_ancestors) == 1
        and gate_ancestors[0] in constants
    ):
        specs.out_node += 1
        specs.persistance_counter = 0
        if specs.out_node >= specs.outputs:
            return []

        output_name = circuit.outputs_names[specs.out_node]
        ancestors_output = sorted(nx.ancestors(graph, output_name))
        gate_ancestors = [
            n
            for n in ancestors_output
            if n.startswith("g")
        ]

    print(circuit.outputs_names)
    print(specs.out_node, gate_ancestors)
    setup = _setup_output_ancestor_problem(
        circuit,
        specs,
    )

    if setup is None:
        return []

    (
        optimizer,
        Node,
        Edge,
        z3_nodes,
        z3_edges,
        graph,
        ancestors_output,
    ) = setup

    z3_subinputs, z3_suboutputs = _add_boundary_edges(
        graph,
        Node,
        z3_nodes,
        32,
    )

    _add_convexity(
        optimizer,
        graph,
        Node,
        z3_nodes,
    )

    optimizer.add(Sum(z3_subinputs) <= specs.imax)
    optimizer.add(Sum(z3_suboutputs) <= specs.omax)

    max_nodes = [
        If(
            Node.in_subgraph(n),
            BitVecVal(1, 32),
            BitVecVal(0, 32),
        )
        for n in z3_nodes.values()
    ]

    h = optimizer.maximize(Sum(max_nodes))

    node_partition = _solve_and_extract(
        optimizer,
        max_nodes,
        h,
        circuit,
    )

    if specs.persistance_counter == specs.persistance:
        specs.out_node += 1
        specs.persistance_counter = 0
    else:
        specs.persistance_counter += 1

    return node_partition