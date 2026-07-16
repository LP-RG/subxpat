import itertools
import math
from typing import Dict, Iterable, List, Mapping, Tuple

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
) -> Tuple[Dict[str, NodeDatatype], List[BoolRef]]:
    """
    Encodes all available and unavailable nodes.

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
        if _w == -1:
            constraints.append(Node.in_subgraph(_node) == BoolVal(False))  # pyright: ignore

    return (z3_nodes, constraints)


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


def _setup_problem(circuit: IOGraph, specs: Specifications):
    graph = circuit._inner
    feasibility_threshold = specs.et

    bit_width = max(
        len(circuit.outputs) + math.ceil(math.log2(len(circuit.nodes))),
        math.ceil(math.log2(feasibility_threshold)) + 1
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
    )

    z3_edges = _encode_edges(graph.edges(), z3_nodes, Edge)

    optimizer.add(base_constraints)

    return optimizer, Node, Edge, z3_nodes, z3_edges, graph, bit_width


def _add_boundary_edges(graph, Node, z3_nodes, bit_width):
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
            z3_subinput_edges.append(
                If(Or(incoming_conditions), z3_bitvec_1, z3_bitvec_0)
            )
            z3_suboutput_edges.append(
                If(Or(outgoing_conditions), z3_bitvec_1, z3_bitvec_0)
            )

    return z3_subinput_edges, z3_suboutput_edges


def _add_convexity(optimizer, graph, Node, z3_nodes):
    descendants = {n: sorted(nx.descendants(graph, n)) for n in z3_nodes}
    ancestors = {n: sorted(nx.ancestors(graph, n)) for n in z3_nodes}

    for src in z3_nodes:
        for dst in graph.successors(src):

            if len(descendants[dst]) > 0:
                optimizer.add(
                    Implies(
                        And(
                            Node.in_subgraph(z3_nodes[src]),
                            Not(Node.in_subgraph(z3_nodes[dst]))
                        ),
                        And([
                            Not(Node.in_subgraph(z3_nodes[n]))
                            for n in descendants[dst]
                        ] + [
                            Not(Node.in_subgraph(z3_nodes[dst]))
                        ])
                    )
                )

            if len(ancestors[src]) > 0:
                optimizer.add(
                    Implies(
                        And(
                            Not(Node.in_subgraph(z3_nodes[src])),
                            Node.in_subgraph(z3_nodes[dst])
                        ),
                        And([
                            Not(Node.in_subgraph(z3_nodes[n]))
                            for n in ancestors[src]
                        ] + [
                            Not(Node.in_subgraph(z3_nodes[src]))
                        ])
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

def find_subgraph_feasible_hard_datatype_bitvec(circuit: IOGraph, specs):
    optimizer, Node, Edge, z3_nodes, z3_edges, graph, bit_width = _setup_problem(circuit, specs)

    z3_subinput_edges, z3_suboutput_edges = _add_boundary_edges(graph, Node, z3_nodes, bit_width)

    _add_convexity(optimizer, graph, Node, z3_nodes)

    # maximize
    z3_bitvec_1 = BitVecVal(1, bit_width)
    max_nodes = [
        If(Node.in_subgraph(n), z3_bitvec_1, BitVecVal(0, bit_width))
        for n in z3_nodes.values()
    ]
    h = optimizer.maximize(Sum(max_nodes))


    #setting up zone weight constraints
    zone_constraints = []

    #iterating through gates of the graph
    for source, target in graph.edges():

        #looking up weights of a specific node
        source_zones = circuit.zone_weights.get(source, {})

        #check that for every zone of the node, the corrosponding weight is less then or equal to its corrosponding zone et
        zone_conditions = [
            ULE(
                BitVecVal(weight, bit_width),
                BitVecVal(specs.et[zone], bit_width)
            )
            for zone, weight in source_zones.items()
        ]

        #if the edge is an exit point then the zone condition must apply
        zone_constraints.append(Implies(
            And(
                Node.in_subgraph(z3_nodes[source]),
                Not(Node.in_subgraph(z3_nodes[target]))
            ),
            And(zone_conditions)
        ))

    # feasibility (edge-wise)
    optimizer.add(And(zone_constraints))

    # imax / omax
    if specs.imax is not None:
        optimizer.add(Sum(z3_subinput_edges) <= specs.imax)
    if specs.omax is not None:
        optimizer.add(Sum(z3_suboutput_edges) <= specs.omax)

    return _solve_and_extract(optimizer, max_nodes, h, circuit)


def find_subgraph_feasible_hard_datatype_bitvec_mintreshold(
    circuit: IOGraph,
    specs: Specifications,
) -> List[str]:

    # prepare
    feasibility_threshold = specs.et
    graph: nx.DiGraph = circuit._inner
    min_weight = min([getattr(node, "weight") for node in circuit.nodes if getattr(node, "weight", None) is not None])
    
    specs.et = min_weight
    subgraph_nodes = find_subgraph_feasible_hard_datatype_bitvec(circuit, specs)

    # restore updated parameters
    specs.et = feasibility_threshold

    return subgraph_nodes  # type: ignore


def slash_to_kill(
    circuit: IOGraph,
    specs: Specifications,
) -> List[str]:
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