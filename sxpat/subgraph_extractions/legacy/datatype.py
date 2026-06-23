from typing import Protocol
from collections import defaultdict
import enum
import itertools
import math
from typing import Callable, Collection, Container, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple
from typing_extensions import Self

import re
import networkx as nx
import functools

from z3 import (
    BitVec,
    BitVecNumRef,
    BitVecRef,
    BitVecVal,
    ExprRef,
    If,
    Optimize,
    Bool, And, Or, Not, Implies, Sum, BoolVal,
    Datatype, BitVecSort, BoolSort,
    BoolRef, DatatypeSortRef, DatatypeRef,
    sat, is_true, Context
)

from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.graph.graph import IOGraph

from sxpat.config.config import WEIGHT
from sxpat.specifications import Specifications

from sxpat.utils.graph import is_selection_convex


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
        # TODO:marco: can we directly encode False?
        constraints.append(Node.in_subgraph(_node) == BoolVal(False))  # pyright: ignore

    for _name, _id in zip(available_nodes, ids):
        _w = gates_weight[_name]
        z3_nodes[_name] = _node = Node.mk_node(  # pyright: ignore[reportAttributeAccessIssue]
            BitVecVal(_id, bit_width),
            BitVecVal(_w, bit_width),
            Bool(_name),
        )
        if _w == -1:
            # TODO:marco: can we directly encode False?
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


def find_subgraph_feasible_hard_datatype_bitvec(
    circuit: AnnotatedGraph,
    specs: Specifications,
) -> List[str]:
    """
    Extract a subgraph, enforcing the feasibility of all the subgraph outputs.

    :return: the sequence of nodes composing the subgraph
    """

    # prepare
    feasibility_threshold = specs.et
    graph: nx.DiGraph = circuit.graph
    g_gates: Mapping[int, str] = circuit.gate_dict
    # loose bound but since it's logarithmic it's still ok
    bit_width = circuit.num_outputs + math.ceil(math.log2(circuit.num_gates))
    #
    available_nodes = circuit.gate_dict.values()
    unavailable_nodes = list(itertools.chain(
        circuit.input_dict.values(),
        circuit.output_dict.values(),
        circuit.constant_dict.values(),
    ))
    # consts
    z3_bitvec_0 = BitVecVal(0, bit_width)
    z3_bitvec_1 = BitVecVal(1, bit_width)

    # construct solver
    optimizer = Optimize()

    # declare Node and Edge datatypes
    Node, Edge = _declare_datatypes(bit_width)

    # encode nodes and edges
    z3_nodes, _c = _encode_nodes(
        available_nodes,
        unavailable_nodes,
        graph.nodes(WEIGHT, -1),  # type: ignore
        bit_width,
        Node,
    )
    z3_edges = _encode_edges(
        graph.edges(),
        z3_nodes,
        Edge
    )
    optimizer.add(_c)

    # ??? subgraph edges
    z3_subinput_edges: List[BitVecRef] = list()
    z3_suboutput_edges: List[BitVecRef] = list()
    for _name in z3_nodes.keys():
        # create partial subgraph edges
        _incoming_conditions: List[BoolRef] = list()
        _outgoing_conditions: List[BoolRef] = list()
        for (_src, _dst) in graph.out_edges(_name):
            _z3_src = Node.in_subgraph(z3_nodes[_src])
            _z3_dst = Node.in_subgraph(z3_nodes[_dst])
            _incoming_conditions.append(And(Not(_z3_src), _z3_dst))  # type: ignore
            _outgoing_conditions.append(And(_z3_src, Not(_z3_dst)))  # type: ignore

        # create subgraph edges
        if _incoming_conditions:
            z3_subinput_edges.append(If(Or(_incoming_conditions), z3_bitvec_1, z3_bitvec_0))  # type: ignore
            z3_suboutput_edges.append(If(Or(_outgoing_conditions), z3_bitvec_1, z3_bitvec_0))  # type: ignore

    # ??? maximise node count
    max_nodes = [
        If(Node.in_subgraph(_n), z3_bitvec_1, z3_bitvec_0)
        for _n in z3_nodes.values()
    ]
    h = optimizer.maximize(Sum(max_nodes))

    # ??? convexity constraint
    descendants: Dict[str, List[str]] = dict()
    ancestors: Dict[str, List[str]] = dict()
    for _n in z3_nodes.keys():
        descendants[_n] = sorted(nx.descendants(graph, _n))
        ancestors[_n] = sorted(nx.ancestors(graph, _n))
    for _src in z3_nodes.keys():
        for _dst in graph.successors(_src):
            if len(descendants[_dst]) > 0:
                not_descendants = [Not(Node.in_subgraph(z3_nodes[_n])) for _n in descendants[_dst]]
                not_descendants.append(Not(Node.in_subgraph(z3_nodes[_dst])))
                descendant_condition = Implies(
                    And(Node.in_subgraph(z3_nodes[_src]), Not(Node.in_subgraph(z3_nodes[_dst]))),
                    And(not_descendants)
                )
                optimizer.add(descendant_condition)
            if len(ancestors[_src]) > 0:
                not_ancestors = [Not(Node.in_subgraph(z3_nodes[_n])) for _n in ancestors[_src]]
                not_ancestors.append(Not(Node.in_subgraph(z3_nodes[_src])))
                ancestor_condition = Implies(
                    And(Not(Node.in_subgraph(z3_nodes[_src])), Node.in_subgraph(z3_nodes[_dst])),
                    And(not_ancestors)
                )
                optimizer.add(ancestor_condition)

    # imax/omax
    if specs.imax is not None:
        optimizer.add(Sum(z3_subinput_edges) <= specs.imax)
    if specs.omax is not None:
        optimizer.add(Sum(z3_suboutput_edges) <= specs.omax)

    # feasibility constraint
    _feasibility_constraints = [
        Implies(
            And(Node.in_subgraph(Edge.source(_edge)), Not(Node.in_subgraph(Edge.target(_edge)))),
            Node.weight(Edge.source(_edge)) <= BitVecVal(feasibility_threshold, bit_width)
        )
        for _edge in z3_edges
    ]
    optimizer.add(And(_feasibility_constraints))

    # solve problem
    _res = optimizer.check()
    if _res != sat: return list()
    _model = optimizer.model()
    # resolve if size is not maximal
    _found_size = _model.eval(Sum(max_nodes), model_completion=True).as_long()
    _maximal_size = h.upper().as_long() # type: ignore
    if _maximal_size != _found_size:
        print('second optimizer call')  # log
        #
        optimizer.add(Sum(max_nodes) == _maximal_size)
        _res = optimizer.check()
        if _res != sat: raise RuntimeError('Invalid z3py result')
        _model = optimizer.model()

    # extract partition
    node_partition = list()
    for _decl in _model.decls():
        # select true gates
        if is_true(_model[_decl]):
            _s = str(_decl)
            if _s.startswith('g'):
                node_partition.append(_s)

    # TODO: should not be needed as the constraints should enforce it
    # check partition convexity
    if not is_selection_convex(graph, node_partition):
        raise RuntimeError('the subgraph extraction resulted in a non-convex subgraph')

    node_partition_idx = [int(re.search(r'g(\d+)', node).group(1)) for node in node_partition]
    return [g_gates[idx] for idx in node_partition_idx]
