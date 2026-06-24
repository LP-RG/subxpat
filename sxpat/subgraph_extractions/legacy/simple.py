from collections import defaultdict
import enum
from typing import Callable, Collection, Container, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple
from typing_extensions import Self

import re
import networkx as nx
import functools

from z3 import (
    Optimize,
    Bool, And, Or, Not, Implies, Sum, BoolVal, Int, If, IntVal,
    BoolRef,
    sat, is_true, Context
)

from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.graph.graph import IOGraph

from sxpat.config.config import WEIGHT
from sxpat.specifications import Specifications

from sxpat.utils.graph import is_selection_convex

NUMBER_PATTERN = re.compile(r'\d+')
NAME_PATTERN = re.compile(r'(g|in|out)(\d+)')


class NodeType(enum.Enum):
    GATE = 'g'
    INPUT = 'in'
    OUTPUT = 'out'

    @classmethod
    def from_prefix(cls, prefix: str):
        if prefix == 'g': return cls.GATE
        elif prefix == 'in': return cls.INPUT
        elif prefix == 'out': return cls.OUTPUT
        raise RuntimeError(f'invalid prefix: {prefix}')


def _parse_node_name(gate_name: str) -> Tuple[str, int, NodeType]:
    m = NAME_PATTERN.match(gate_name)
    if m is None: raise RuntimeError(f'unexpected gate name: {gate_name}')

    return (
        f'{m.group(1)}_{m.group(2)}',
        int(m.group(2)),
        NodeType.from_prefix(m.group(1))
    )


def _encode_literals(
    graph: nx.DiGraph,
    constants: Container[int],
) -> Tuple[
    Dict[int, BoolRef],
    Dict[int, BoolRef],
    Dict[int, BoolRef],
]:
    input_literals: Dict[int, BoolRef] = dict()  # literals associated with the input nodes
    gate_literals: Dict[int, BoolRef] = dict()  # literals associated with the gates
    output_literals: Dict[int, BoolRef] = dict()  # literals associated with the output nodes

    for (_src, _dst) in graph.edges:
        # input/gate (non const)
        (_name, _id, _type) = _parse_node_name(_src)
        if _type == NodeType.INPUT:
            input_literals[_id] = Bool(_name)
        elif _type == NodeType.GATE and _id not in constants:  # only valid for gates
            gate_literals[_id] = Bool(_name)
        # output
        (_name, _id, _type) = _parse_node_name(_dst)
        if _type == NodeType.OUTPUT:
            output_literals[_id] = Bool(_name)

    return (
        input_literals,
        gate_literals,
        output_literals,
    )


def _extract_edges(
    graph: nx.DiGraph,
    constants: Container[int],
) -> Tuple[
    Dict[int, List[int]],
    Dict[int, List[int]],
    Dict[int, int],
]:
    input_edges: Dict[int, List[int]] = defaultdict(list)  # input -> successors of input
    gate_edges: Dict[int, List[int]] = defaultdict(list)  # gate -> successors of gate
    output_edges: Dict[int, int] = dict()  # output -> predecessor of output

    for (_src, _dst) in graph.edges:
        if 'in' in _src:  # input to ???
            _id_s = int(_src[2:])

            # TODO:preexisting: input_edges[in_id].append(int(e[1][1:])) # this is a bug for a case where e = (in1, out1)
            try:
                input_edges[_id_s].append(int(_dst[1:]))
            except:
                # TODO: should this be then NUMBER_PATTERN
                if _m := re.search(r'g(\d+)', _dst):
                    _id_d = int(_m.group(1))
                    input_edges[_id_s].append(_id_d)

        if 'g' in _src and 'g' in _dst:  # gate to gate
            _id_s = int(_src[1:])
            _id_d = int(_dst[1:])
            if _id_s in constants: raise RuntimeError('Constants should only be connected to output nodes')

            gate_edges[_id_s].append(_id_d)

        if 'out' in _dst:  # output from ???
            _id_d = int(_dst[3:])
            try:
                output_edges[_id_d] = int(_src[1:])
            except:
                _id_s = int(NUMBER_PATTERN.search(_src).group())
                output_edges[_id_d] = _id_s

    return (
        input_edges,
        gate_edges,
        output_edges,
    )


def _encode_subgraph_edges(
    input_literals: Mapping[int, BoolRef],
    gate_literals: Mapping[int, BoolRef],
    output_literals: Mapping[int, BoolRef],
    #
    input_edges: Mapping[int, Sequence[int]],
    gate_edges: Mapping[int, Sequence[int]],
    output_edges: Mapping[int, int],
) -> Tuple[
    List[BoolRef],
    Dict[int, BoolRef],
]:
    z3_subinput_edges: List[BoolRef] = list()
    z3_suboutput_edges: Dict[int, BoolRef] = dict()

    # input edges encoding
    for (_src, _dsts) in input_edges.items():
        _edges_in: List[BoolRef] = list()

        for _dst in _dsts:
            _edges_in.append(And(Not(input_literals[_src]), gate_literals[_dst]))  # type: ignore

        z3_subinput_edges.append(Or(_edges_in))  # type: ignore

    # gate edges encoding
    for (_src, _dsts) in gate_edges.items():
        _edges_in: List[BoolRef] = list()
        _edges_out: List[BoolRef] = list()

        for _dst in _dsts:
            _edges_in.append(And(Not(gate_literals[_src]), gate_literals[_dst]))  # type: ignore
            _edges_out.append(And(gate_literals[_src], Not(gate_literals[_dst])))  # type: ignore

        z3_subinput_edges.append(Or(_edges_in))  # type: ignore
        z3_suboutput_edges[_src] = Or(_edges_out)  # type: ignore

    # output edges encoding
    for _dst, _src in output_edges.items():
        # ignore if input->output
        if _src not in gate_literals: continue

        _edge_out = And(gate_literals[_src], Not(output_literals[_dst]))
        z3_suboutput_edges[_src] = _edge_out  # type: ignore

    return (
        z3_subinput_edges,
        z3_suboutput_edges,
    )


def _generate_gates_graph(
    graph: nx.DiGraph,
    constants: Container[int],
) -> nx.DiGraph:
    gates_graph: nx.DiGraph = nx.DiGraph()

    for (_src, _dst) in graph.edges:
        # add nodes and edge
        if 'g' in _src and 'g' in _dst:
            _id_s = int(_src[1:])
            _id_d = int(_dst[1:])
            gates_graph.add_edge(_id_s, _id_d)
        # add node
        elif 'g' in str(_src):
            _id_s = int(_src[1:])
            if _id_s in constants: continue
            gates_graph.add_node(_id_s)

    return gates_graph


def _encode_convexity_constraints(
    gate_literals: Mapping[int, BoolRef],
    gate_edges: Mapping[int, Sequence[int]],
    gates_graph: nx.DiGraph,
) -> List[BoolRef]:

    # extract ancestors and descendants
    ancestors: Dict[int, List[int]] = dict()
    descendants: Dict[int, List[int]] = dict()
    for n in gates_graph.nodes:
        ancestors[n] = sorted(nx.ancestors(gates_graph, n))
        descendants[n] = sorted(nx.descendants(gates_graph, n))

    # convexity constraints
    constraints: List[BoolRef] = list()
    for (_src, _dsts) in gate_edges.items():
        for _dst in _dsts:
            if len(ancestors[_src]) > 0:  # constraints on incoming edges
                _not_ancestor = [Not(gate_literals[l]) for l in ancestors[_src]]
                _not_ancestor.append(Not(gate_literals[_src]))
                constraints.append(Implies(
                    And(Not(gate_literals[_src]), gate_literals[_dst]),
                    And(_not_ancestor),
                ))
            if len(descendants[_dst]) > 0:  # constraints on outgoing edges
                _not_descendants = [Not(gate_literals[_l]) for _l in descendants[_dst]]
                _not_descendants.append(Not(gate_literals[_dst]))
                constraints.append(Implies(
                    And(gate_literals[_src], Not(gate_literals[_dst])),
                    And(_not_descendants),
                ))

    return constraints


def _extract_gates_weights(
    graph: nx.DiGraph,
    gates_graph: nx.DiGraph,
    id_to_gate: Mapping[int, str],
) -> Dict[int, int]:
    return {
        _id: graph.nodes[id_to_gate[_id]][WEIGHT]
        for _id in gates_graph.nodes
    }


def _encode_iomax_constraints(
    z3_subinput_edges: Collection[BoolRef],
    z3_suboutput_edges: Collection[BoolRef],
    specs: Specifications,
) -> List[BoolRef]:
    constraints: List[BoolRef] = list()

    # TODO:marco: should this be an AtMost?
    if specs.imax is not None:
        constraints.append(Sum(tuple(z3_subinput_edges)) <= specs.imax)  # type: ignore
    if specs.omax is not None:
        constraints.append(Sum(tuple(z3_suboutput_edges)) <= specs.omax)  # type: ignore

    return constraints


def _encode_not_in_subgraph(
    excluded_literals: Iterable[BoolRef],
) -> List[BoolRef]:
    return [
        _lit == BoolVal(False)  # type: ignore
        for _lit in excluded_literals
    ]


def _solve_and_verify(
    optimizer: Optimize,
    gates_graph: nx.DiGraph,
) -> List[int]:
    # solve
    _status = optimizer.check()
    if _status != sat: return list()

    # TODO: should we rerun if .upper() != .eval() ?

    # extract model
    _model = optimizer.model()
    node_partition: List[int] = list()
    for _decl in _model.decls():
        # select true gates
        if 'g' in str(_decl) and is_true(_model[_decl]):
            _id = int(str(_decl)[2:])
            node_partition.append(_id)

    # TODO: should we remove this? this check seems to be redundant (the constraints force this already)
    # verify partition convexity
    if not is_selection_convex(gates_graph, node_partition):
        raise RuntimeError('the subgraph extraction resulted in a non-convex subgraph')

    return node_partition


def find_subgraph(circuit: AnnotatedGraph, specs: Specifications) -> List[str]:
    """
    Extract a subgraph, maximising the number of nodes in the subgraph (1).  
        (1) does this only if all weights are equal.

    :return: the sequence of nodes composing the subgraph
    """

    # prepare
    graph: nx.DiGraph = circuit.graph
    constants_ids: Container[int] = circuit.constant_dict.keys()
    g_gates: Mapping[int, str] = circuit.gate_dict

    # literals
    (input_literals, gate_literals, output_literals) = literals = _encode_literals(graph, constants_ids)
    # edges
    (input_edges, gate_edges, output_edges) = edges = _extract_edges(graph, constants_ids)

    # z3 encoded partition edges
    (z3_subinput_edges, z3_suboutput_edges) = z3_subgraph_edges = _encode_subgraph_edges(*literals, *edges)

    # Optimizer
    opt = Optimize()

    # create graph containing only inner logic (excludes inputs, outputs, and constants)
    G = _generate_gates_graph(graph, constants_ids)

    # extract weights
    gates_weight = _extract_gates_weights(graph, G, g_gates)
    # find max weight
    max_weight = max(gates_weight.values())
    # update weights with their complement (max_weight - gates_weight)
    for _id, _g_weight in gates_weight.items():
        # TODO:preexisting: + 1 must be removed, I'm leaving it just for the initial debugging phase
        gates_weight[_id] = max_weight - _g_weight + 1

    # convexity constraints
    opt.add(_encode_convexity_constraints(gate_literals, gate_edges, G))

    # limit input/output subgraph nodes if wanted
    opt.add(_encode_iomax_constraints(z3_subinput_edges, z3_suboutput_edges.values(), specs))

    # generate function to maximize
    max_func: List[...] = list()
    for _id in gate_literals:
        # TODO: should this be If(gate_literals[_id], gates_weight[_id], 0) ?
        max_func.append(gate_literals[_id] * gates_weight[_id])
    # add function to maximize to solver
    opt.maximize(Sum(max_func))

    # force inputs/outputs to not be in the subgraph
    opt.add(_encode_not_in_subgraph(input_literals.values()))
    opt.add(_encode_not_in_subgraph(output_literals.values()))
    # force unlabelled nodes to not be in the subgraph
    opt.add(_encode_not_in_subgraph(
        Bool(_parse_node_name(node)[0])
        for node in graph.nodes()
        if (_w := graph.nodes[node][WEIGHT] is None) or (_w <= -1)
    ))

    # solve, verify and extract partition
    _partition = _solve_and_verify(opt, G)
    return [g_gates[_i] for _i in _partition]


def find_subgraph_sensitivity(circuit: AnnotatedGraph, specs: Specifications) -> List[str]:
    """
    Extract a subgraph, enforcing the sum of the weights of subgraph ouputs to be upper bounded by the `sensitivity`.

    :return: the sequence of nodes composing the subgraph
    """

    # prepare
    sensitivity_threshold = specs.sensitivity
    graph: nx.DiGraph = circuit.graph
    constants_ids: Container[int] = circuit.constant_dict.keys()
    g_gates: Mapping[int, str] = circuit.gate_dict

    # literals
    (input_literals, gate_literals, output_literals) = literals = _encode_literals(graph, constants_ids)
    # edges
    (input_edges, gate_edges, output_edges) = edges = _extract_edges(graph, constants_ids)

    # z3 encoded subgraph edges and weights
    (z3_subinput_edges, z3_suboutput_edges) = z3_subgraph_edges = _encode_subgraph_edges(*literals, *edges)

    # Optimizer
    opt = Optimize()

    # create graph containing only inner logic (excludes inputs, outputs, and constants)
    G = _generate_gates_graph(graph, constants_ids)

    # extract weights
    gates_weight = _extract_gates_weights(graph, G, g_gates)
    # find max weight
    max_weight = max(gates_weight.values())
    # update weights with their complement (max_weight - gates_weight)
    for _id, _g_weight in gates_weight.items():
        # TODO:preexisting: + 1 must be removed, I'm leaving it just for the initial debugging phase
        gates_weight[_id] = max_weight - _g_weight + 1

    # convexity constraints
    opt.add(_encode_convexity_constraints(gate_literals, gate_edges, G))

    # limit input/output subgraph nodes if wanted
    opt.add(_encode_iomax_constraints(z3_subinput_edges, z3_suboutput_edges.values(), specs))

    # sensitivity constraints
    _weighted_subout_edges = [
        _edge * gates_weight[_id]  # TODO:marco: should this be If(_edge, ..., 0) ?
        for (_id, _edge) in z3_suboutput_edges.items()
    ]
    opt.add(Sum(_weighted_subout_edges) <= sensitivity_threshold)

    # generate function to maximize
    max_func: List[...] = list()
    for _id in gate_literals:
        max_func.append(gate_literals[_id])
    # add function to maximize to solver
    opt.maximize(Sum(max_func))

    # force inputs/outputs to not be in the subgraph
    opt.add(_encode_not_in_subgraph(input_literals.values()))
    opt.add(_encode_not_in_subgraph(output_literals.values()))
    # force unlabelled nodes to not be in the subgraph
    opt.add(_encode_not_in_subgraph(
        Bool(_parse_node_name(node)[0])
        for node in graph.nodes()
        if ((_w := graph.nodes[node][WEIGHT]) is None) or (_w <= -1)
    ))

    # solve, verify and extract partition
    _partition = _solve_and_verify(opt, G)
    return [g_gates[_i] for _i in _partition]


def find_subgraph_sensitivity_no_io_constraints(
    circuit: AnnotatedGraph,
    specs: Specifications,
) -> List[str]:
    """
    Extract a subgraph, enforcing the sum of the weights of subgraph ouputs to be upper bounded by the `sensitivity`.
    Forces no limits on the number of subgraph inputs/outputs.

    :return: the sequence of nodes composing the subgraph
    """

    imax, omax = specs.imax, specs.omax
    specs.imax, specs.omax = None, None  # type: ignore
    _res = find_subgraph_sensitivity(circuit, specs)
    specs.imax, specs.omax = imax, omax
    return _res


def _find_subgraph_feasible(
    circuit: AnnotatedGraph,
    specs: Specifications,
    required_feasible_outputs: Optional[int] = None,
) -> List[str]:
    """
    Extract a subgraph, enforcing the feasibility of the subgraph outputs.

    :param required_feasible_outputs: the number of feasible outputs required for the subgraph to be valid; 
        `None` means that all subgraph outputs must be fasible
    :return: the sequence of nodes composing the subgraph
    """

    # prepare
    feasibility_threshold = specs.et
    graph: nx.DiGraph = circuit.graph
    constants_ids: Container[int] = circuit.constant_dict.keys()
    g_gates: Mapping[int, str] = circuit.gate_dict

    # literals
    (input_literals, gate_literals, output_literals) = literals = _encode_literals(graph, constants_ids)
    # edges
    (input_edges, gate_edges, output_edges) = edges = _extract_edges(graph, constants_ids)

    # z3 encoded subgraph edges and weights
    (z3_subinput_edges, z3_suboutput_edges) = z3_subgraph_edges = _encode_subgraph_edges(*literals, *edges)

    # Optimizer
    opt = Optimize()

    # create graph containing only inner logic (excludes inputs, outputs, and constants)
    G = _generate_gates_graph(graph, constants_ids)

    # extract weights
    gates_weight = _extract_gates_weights(graph, G, g_gates)

    # convexity constraints
    opt.add(_encode_convexity_constraints(gate_literals, gate_edges, G))

    # limit input/output subgraph nodes if wanted
    opt.add(_encode_iomax_constraints(z3_subinput_edges, z3_suboutput_edges.values(), specs))

    # feasibility constraints
    _feasible_subgraph_edges = [
        z3_suboutput_edges[_id]
        for _id, _w in gates_weight.items()
        if _w <= feasibility_threshold
    ]
    if required_feasible_outputs is None:
        opt.add(Sum(_feasible_subgraph_edges) == Sum(list(z3_suboutput_edges.values())))
    else:
        # TODO:marco: should this be an AtLeast(_feasible_subgraph_edges, required_feasible_outputs) ?
        opt.add(Sum(_feasible_subgraph_edges) >= required_feasible_outputs)

    # generate function to maximize
    max_func: List[...] = list()
    for _id in gate_literals:
        max_func.append(gate_literals[_id])
    # add function to maximize to solver
    opt.maximize(Sum(max_func))

    # force inputs/outputs to not be in the subgraph
    opt.add(_encode_not_in_subgraph(input_literals.values()))
    opt.add(_encode_not_in_subgraph(output_literals.values()))
    # force unlabelled nodes to not be in the subgraph
    opt.add(_encode_not_in_subgraph(
        Bool(_parse_node_name(node)[0])
        for node in graph.nodes()
        if ((_w := graph.nodes[node][WEIGHT]) is None) or (_w <= -1)
    ))

    # solve, verify and extract partition
    _partition = _solve_and_verify(opt, G)
    return [g_gates[_i] for _i in _partition]


def find_subgraph_feasible(
    circuit: AnnotatedGraph,
    specs: Specifications,
) -> List[str]:
    """
    Extract a subgraph, enforcing the feasibility of at least one subgraph output.

    :return: the sequence of nodes composing the subgraph
    """

    return _find_subgraph_feasible(circuit, specs, 1)


def find_subgraph_feasible_hard(
    circuit: AnnotatedGraph,
    specs: Specifications,
) -> List[str]:
    """
    Extract a subgraph, enforcing the feasibility of all the subgraph outputs.

    :return: the sequence of nodes composing the subgraph
    """

    return _find_subgraph_feasible(circuit, specs, None)

def find_subgraph_feasible_soft(
    circuit: AnnotatedGraph,
    specs: Specifications,
    required_feasible_outputs: Optional[int] = None,
) -> List[str]:
    """
    Extract a subgraph, enforcing the feasibility of the subgraph outputs.

    :param required_feasible_outputs: the number of feasible outputs required for the subgraph to be valid; 
        `None` means that all subgraph outputs must be fasible
    :return: the sequence of nodes composing the subgraph
    """

    # prepare
    feasibility_threshold = specs.et
    count = specs.num_subgraphs
    graph: nx.DiGraph = circuit.graph
    constants_ids: Container[int] = circuit.constant_dict.keys()
    g_gates: Mapping[int, str] = circuit.gate_dict

    # literals
    (input_literals, gate_literals, output_literals) = literals = _encode_literals(graph, constants_ids)
    # edges
    (input_edges, gate_edges, output_edges) = edges = _extract_edges(graph, constants_ids)

    # z3 encoded subgraph edges and weights
    (z3_subinput_edges, z3_suboutput_edges) = z3_subgraph_edges = _encode_subgraph_edges(*literals, *edges)

    # Optimizer
    opt = Optimize()

    # create graph containing only inner logic (excludes inputs, outputs, and constants)
    G = _generate_gates_graph(graph, constants_ids)

    # extract weights
    gates_weight = _extract_gates_weights(graph, G, g_gates)

    # convexity constraints
    opt.add(_encode_convexity_constraints(gate_literals, gate_edges, G))

    # limit input/output subgraph nodes if wanted
    opt.add(_encode_iomax_constraints(z3_subinput_edges, z3_suboutput_edges.values(), specs))

    # feasibility constraints
    _feasible_subgraph_edges = [
        z3_suboutput_edges[_id]
        for _id, _w in gates_weight.items()
        if _w <= feasibility_threshold
    ]
    if required_feasible_outputs is None:
        opt.add(Sum(_feasible_subgraph_edges) == Sum(list(z3_suboutput_edges.values())))
    else:
        # TODO:marco: should this be an AtLeast(_feasible_subgraph_edges, required_feasible_outputs) ?
        opt.add(Sum(_feasible_subgraph_edges) >= required_feasible_outputs)

    # generate function to maximize
    max_func: List[...] = list()
    for _id in gate_literals:
        max_func.append(gate_literals[_id])
    # add function to maximize to solver
    opt.maximize(Sum(max_func))

    # force inputs/outputs to not be in the subgraph
    opt.add(_encode_not_in_subgraph(input_literals.values()))
    opt.add(_encode_not_in_subgraph(output_literals.values()))
    # force unlabelled nodes to not be in the subgraph
    opt.add(_encode_not_in_subgraph(
        Bool(_parse_node_name(node)[0])
        for node in graph.nodes()
        if ((_w := graph.nodes[node][WEIGHT]) is None) or (_w <= -1)
    ))

    # =========================== Coming up with a penalty for each subgraph =============================
    penalty = Int('penalty')

    output_individual_penalty = []
    penalty_coefficient = 1
    for s in gates_weight:
        if gates_weight[s] > feasibility_threshold:
            output_individual_penalty.append(If(gate_literals[s],
                                                penalty_coefficient * (gates_weight[s] - feasibility_threshold),
                                                0))
    opt.add(penalty == Sum(output_individual_penalty))
    opt.add_soft(Sum(output_individual_penalty) <= 2 * feasibility_threshold, weight=1)

    # ========================================================

    # opt.add(Sum(max_func) > 1)
    # ======================== Check for multiple subgraphs =======================================
    all_partitions = {}
    while count > 0:
        node_partition = []
        c = opt.check()
        if c == sat:
            # print(opt.model())
            m = opt.model()
            # print(f'{m = }')
            for t in m.decls():
                if 'penalty' in str(t):
                    print(f'{t} = {m[t]}')
                if 'g' not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition

        else:
            count = 0

        # Check partition convexity
        if not is_selection_convex(G, node_partition):
            raise RuntimeError('the subgraph extraction resulted in a non-convex subgraph')

        # ========================================================================
        if c == sat:
            block_clause = [d() == True if m[d] else d() == False for d in m.decls() if 'g' in d.name()]
            opt.add(Not(And(block_clause)))
            current_penalty = m[penalty].as_long()
            print(f'{current_penalty}, {node_partition}')
            all_partitions[count] = (current_penalty, node_partition)
        count -= 1
    # ================================================================
    # =======================Pick the Subgraph with the lowest penalty ==============================
    if all_partitions:
        sorted_partitions = dict(
            sorted(
                all_partitions.items(),
                key=lambda item: (-len(item[1][1]), item[1][0])
            )
        )

        for par in sorted_partitions:
            print(f'{sorted_partitions[par] = }')
        penalty, node_partition = next(iter(sorted_partitions.values()))
        print(f'{penalty, node_partition}')

    return [g_gates[_i] for _i in node_partition]

def find_subgraph_feasible_soft_outputs(
    circuit: AnnotatedGraph,
    specs: Specifications,
    required_feasible_outputs: Optional[int] = None,
) -> List[str]:
    """
    Extract a subgraph, enforcing the feasibility of the subgraph outputs.

    :param required_feasible_outputs: the number of feasible outputs required for the subgraph to be valid; 
        `None` means that all subgraph outputs must be fasible
    :return: the sequence of nodes composing the subgraph
    """

    # prepare
    feasibility_threshold = specs.et
    count = specs.num_subgraphs
    imax = specs.imax
    omax = specs.omax
    graph: nx.DiGraph = circuit.graph
    constants_ids: Container[int] = circuit.constant_dict.keys()
    g_gates: Mapping[int, str] = circuit.gate_dict

    # literals
    (input_literals, gate_literals, output_literals) = literals = _encode_literals(graph, constants_ids)
    # edges
    (input_edges, gate_edges, output_edges) = edges = _extract_edges(graph, constants_ids)

    # z3 encoded subgraph edges and weights
    (z3_subinput_edges, z3_suboutput_edges) = z3_subgraph_edges = _encode_subgraph_edges(*literals, *edges)

    # Optimizer
    opt = Optimize()

    # create graph containing only inner logic (excludes inputs, outputs, and constants)
    G = _generate_gates_graph(graph, constants_ids)

    # extract weights
    gates_weight = _extract_gates_weights(graph, G, g_gates)

    # convexity constraints
    opt.add(_encode_convexity_constraints(gate_literals, gate_edges, G))

    # limit input/output subgraph nodes if wanted
    opt.add(_encode_iomax_constraints(z3_subinput_edges, z3_suboutput_edges.values(), specs))

    # feasibility constraints
    _feasible_subgraph_edges = [
        z3_suboutput_edges[_id]
        for _id, _w in gates_weight.items()
        if _w <= feasibility_threshold
    ]
    if required_feasible_outputs is None:
        opt.add(Sum(_feasible_subgraph_edges) == Sum(list(z3_suboutput_edges.values())))
    else:
        # TODO:marco: should this be an AtLeast(_feasible_subgraph_edges, required_feasible_outputs) ?
        opt.add(Sum(_feasible_subgraph_edges) >= required_feasible_outputs)

    # generate function to maximize
    max_func: List[...] = list()
    for _id in gate_literals:
        max_func.append(gate_literals[_id])
    # add function to maximize to solver
    opt.maximize(Sum(max_func))

    # force inputs/outputs to not be in the subgraph
    opt.add(_encode_not_in_subgraph(input_literals.values()))
    opt.add(_encode_not_in_subgraph(output_literals.values()))
    # force unlabelled nodes to not be in the subgraph
    opt.add(_encode_not_in_subgraph(
        Bool(_parse_node_name(node)[0])
        for node in graph.nodes()
        if ((_w := graph.nodes[node][WEIGHT]) is None) or (_w <= -1)
    ))

    # =========================== Coming up with a penalty for each subgraph =============================

    partition_output_edges_penalty = []
    for output_id in output_edges:
        predecessor = output_edges[output_id][
            0]  # Output nodes have only one predecessor  (it could be a gate or it could be an input)

        if predecessor not in gate_literals:  # This handle cases where input and output are directly connected
            continue
        e_out = And(gate_literals[predecessor], Not(output_literals[output_id]))

        if graph.nodes[g_gates[predecessor]][WEIGHT] > feasibility_threshold:
            this_output_penalty = graph.nodes[g_gates[predecessor]][WEIGHT] - feasibility_threshold
            partition_output_edges_penalty.append(e_out * this_output_penalty)

    penalty_output = Int('penalty_output')
    penalty_gate = Int('penalty_gate')

    output_individual_penalty = []
    penalty_coefficient = 1
    for s in gates_weight:
        if gates_weight[s] > feasibility_threshold:
            output_individual_penalty.append(If(gate_literals[s],
                                                penalty_coefficient * (gates_weight[s] - feasibility_threshold),
                                                0))

    opt.add(penalty_output == Sum(partition_output_edges_penalty))
    # Why IntVal(1)? => Because sometimes the Sum results into an integer "Python number (e.g., int)", but we need a "Z3 number (e.g., ArithRef)"
    opt.add_soft(IntVal(1) * Sum(partition_output_edges_penalty) <= omax * feasibility_threshold, weight=100)
    opt.add(penalty_gate == Sum(output_individual_penalty))
    opt.add_soft(IntVal(1) * Sum(output_individual_penalty) <= omax * feasibility_threshold, weight=1)

    # ========================================================
    # ======================== Check for multiple subgraphs =======================================
    all_partitions = {}
    count = specs.num_subgraphs
    while count > 0:
        node_partition = []
        c = opt.check()
        if c == sat:
            # print(opt.model())
            m = opt.model()
            # print(f'{m = }')
            for t in m.decls():
                if 'penalty_output' in str(t):
                    # print(f'{t} = {m[t]}')
                    penalty_output = m[t].as_long()
                    pass
                if 'penalty_gate' in str(t):
                    # print(f'{t} = {m[t]}')
                    penalty_gate = m[t].as_long()
                if 'g' not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition

        else:
            count = 0

        # Check partition convexity
        if not is_selection_convex(G, node_partition):
            raise RuntimeError('the subgraph extraction resulted in a non-convex subgraph')

        # ========================================================================
        if c == sat:
            block_clause = [d() == True if m[d] else d() == False for d in m.decls() if 'g_' in d.name()]
            opt.add(Not(And(block_clause)))

            all_partitions[count] = (penalty_output, penalty_gate, node_partition)
        count -= 1
    # ================================================================
    # =======================Pick the Subgraph with the lowest penalty ==============================2
    sorted_partitions = {}
    if all_partitions:
        sorted_partitions = dict(
            sorted(
                all_partitions.items(),
                key=lambda item: (-len(item[1][2]), item[1][0], item[1][1])
            )
        )

        for par in sorted_partitions:
            print(f'{sorted_partitions[par] = }')

        first_key = next(iter(sorted_partitions))
        penalty_output, penalty_gate, node_partition = sorted_partitions.pop(first_key)

    # ================================================================
    subgraph_candidates = sorted_partitions

    return [g_gates[_i] for _i in node_partition]