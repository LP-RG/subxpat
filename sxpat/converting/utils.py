from typing import Any, Dict, Iterable, List, Mapping, Optional

import re
import math
import itertools as it

from sxpat.graph import *


__all__ = [
    # digest/update graph
    'unpack_ToInt', 'prune_unused', 'set_bool_constants', 'set_prefix',
    # compute graph accessories
    'get_nodes_type', 'get_nodes_bitwidth',

    # expand constraints
    'prevent_combination',
]


def unpack_ToInt(graph: _Graph) -> _Graph:
    """
        Given a graph, returns a new graph with all ToInt nodes unpacked to a more primitive set of nodes.

        @authors: Marco Biasion 
    """

    toint_nodes = tuple(
        node
        for node in graph.nodes
        if isinstance(node, ToInt)
    )
    # skip if no ToInt node is present
    if len(toint_nodes) == 0: return graph

    # generate constants for each sum
    int_consts = {
        toint.name: {
            n: IntConstant(f'{toint.name}_c{n}', value=n)
            for n in it.chain((0,), (2**i for i in range(len(toint.operands))))
        }
        for toint in toint_nodes
    }

    # create all if->int nodes (Dict[original_node_name, List[if_nodes_for_that_node]])
    ifs: Dict[str, List[If]] = {
        toint.name: [
            If(f'if_{toint.name}_{i}', operands=(pred, int_consts[toint.name][2**i], int_consts[toint.name][0]))
            for i, pred in enumerate(toint.operands)
        ]
        for toint in toint_nodes
    }
    # create the Sum nodes
    sums = [
        Sum(
            toint.name,
            in_subgraph=toint.in_subgraph,
            operands=ifs[toint.name]
        )
        for toint in toint_nodes
    ]

    nodes = it.chain(
        *(consts.values() for consts in int_consts.values()),
        (
            node
            for node in graph.nodes
            if not isinstance(node, ToInt)
        ),
        *ifs.values(),
        sums,
    )

    return graph.copy(nodes)


def prune_unused(graph: _Graph) -> _Graph:
    """
        Given a graph, returns a new graph without any dangling nodes (recursive).
        Nodes counted as correct terminations are nodes of class `Identity` or of subclasses of `Variable`.

        @authors: Marco Biasion
    """

    # TODO: better to match termination by input/outputs instead of Variable/Identity
    termination_nodes = [node.name for node in graph.nodes if isinstance(node, (Variable, Identity))]

    # find reachable nodes from the terminations
    visited_nodes = set()
    while len(termination_nodes) > 0:
        node_name = termination_nodes.pop()
        visited_nodes.add(node_name)
        termination_nodes.extend(_n.name for _n in graph.predecessors(node_name))

    # filter out non visited nodes
    nodes = (node for node in graph.nodes if node.name in visited_nodes)

    return graph.copy(nodes)


def get_nodes_type(graphs: Iterable[Graph],
                   initial_mapping: Mapping[str, type] = dict()
                   ) -> Dict[str, type]:
    """
        Given some graphs, compute the type of each node, returning a mapping from node name to type.
        If an `initial_mapping` is given, it will be used as the starting point for the computations, and the contained nodes will be skipped.

        @authors: Marco Biasion
    """

    type_of = dict(initial_mapping)

    for graph in graphs:
        for node in graph.nodes:
            # skip if already computed
            if node.name in type_of: continue

            # direct cases
            if isinstance(node, BoolResType): type_of[node.name] = bool
            elif isinstance(node, IntResType): type_of[node.name] = int

            # dynamic cases
            elif isinstance(node, DynamicResType):
                last_pred = graph.predecessors(node)[-1]
                type_of[node.name] = type_of[last_pred.name]

            # special cases
            elif isinstance(node, PlaceHolder): continue
            elif isinstance(node, Objective): continue
            else: raise TypeError(f'Node {node.name} has an invalid type ({type(node)}).')

    return type_of


def get_nodes_bitwidth(graphs: Iterable[Graph],
                       nodes_types: Mapping[str, type],
                       initial_mapping: Mapping[str, int] = dict()
                       ) -> Dict[str, int]:
    """
        Given some graphs and a mapping of nodes types, compute the bitwidth of each node, returning a mapping from node name to the bitwidth.
        If an `initial_mapping` is given, it will be used as the starting point for the computations.

        @note: the function will recursively repeat itself if needed (eg. for some complex nodes interactions), this could change in the future.

        @authors: Marco Biasion
    """

    bitwidth_of = dict(initial_mapping)

    def manage_node(node: Node):
        # skippable
        if isinstance(node, (Target, Constraint)): return

        # deferred case (all predecessors of a node should have the same bitwidth)
        elif nodes_types[node.name] is not int:
            if isinstance(node, Operation):
                max_bitwidth = max(bitwidth_of.get(n.name, 0) for n in graph.predecessors(node))
                for n in graph.predecessors(node):
                    bitwidth_of[n.name] = max_bitwidth

        # trivial cases
        elif isinstance(node, IntConstant) and node.name not in bitwidth_of:
            bitwidth_of[node.name] = math.ceil(math.log(node.value + 1, 2))
        elif isinstance(node, ToInt) and node.name not in bitwidth_of:
            bitwidth_of[node.name] = len(node.operands)

        # dynamic case (the bitwidth of the current node must be larger or equal to that of the largest predecessor/successor)
        else:
            max_bitwidth = max(
                bitwidth_of.get(n.name, 0)
                for n in it.chain(graph.predecessors(node), graph.successors(node), (node,))
            )
            bitwidth_of[node.name] = max_bitwidth

    # forward update (optimally updates forward chains)
    for graph in graphs:
        for node in graph.nodes:
            manage_node(node)

    # backward update (optimally updates backward chains)
    for graph in reversed(graphs):
        for node in reversed(graph.nodes):
            manage_node(node)

    if bitwidth_of == initial_mapping:
        return {  # remove null pairs (name:0)
            k: v
            for k, v in bitwidth_of.items()
            if v != 0
        }
    else:
        return get_nodes_bitwidth(graphs, nodes_types, bitwidth_of)


def set_bool_constants(graph: _Graph, constants: Mapping[str, bool]) -> _Graph:
    """
        Takes a graph and a mapping from names to bool in input
        and returns a new graph with the nodes corresponding to the given names replaced with the wanted constant.

        @note: *TODO: can be expanded to manage also IntConstant nodes*  
        @note: *TODO: can be expanded to replace also inner nodes, and not only Variable/Constant nodes*

        @authors: Marco Biasion
    """

    new_nodes = {n.name: n for n in graph.nodes}
    for (name, value) in constants.items():
        node = graph[name]
        if isinstance(node, Operation):
            # TODO: could be implemented using prune_unused()
            # NOTE: we do not really need prune_unused as this function should only care about setting constants
            raise NotImplementedError('The logic to replace an Operation with a constant has not been implemented yet.')
        else:
            new_nodes[node.name] = BoolConstant(node.name, node.weight, node.in_subgraph, value)

    return graph.copy(new_nodes.values())


def set_prefix(graph: _Graph, prefix: str) -> _Graph:
    """
        Given a graph and the wanted prefix, returns a new graph with all operation nodes updated with the prefix.

        @authors: Marco Biasion
    """

    to_be_updated = frozenset(n.name for n in it.chain(graph.expressions, graph.constants))
    updated_names: Mapping[str, str] = {
        n.name: f'{prefix}{n.name}' if n.name in to_be_updated else n.name
        for n in graph.nodes
    }

    nodes = []
    for node in graph.nodes:
        if isinstance(node, Operation):
            operands = (updated_names[name] for name in node.operands)
            nodes.append(node.copy(name=updated_names[node.name], operands=operands))
        else:
            nodes.append(node.copy(name=updated_names[node.name]))

    outputs_names = (f'{prefix}{name}' for name in graph.outputs_names)

    return graph.copy(nodes, outputs_names=outputs_names)


def prevent_combination(c_graph: CGraph,
                        assignments: Mapping[str, bool],
                        assignment_id: Optional[Any] = None) -> CGraph:
    """
        Takes a constraints graph and expands it to prevent the given assignment.  
        It will allow any change, but at least one change is required.

        @note: *TODO: can be expanded to manage also integers (be careful of bitwidth)*  
        @note: *TODO: can be changed to return new CGraph containing only the assignment prevention logic, instead of returning an updated copy*

        @authors: Marco Biasion
    """

    # get initial nodes
    nodes = list(c_graph.nodes)

    # add constants (duplicates will be removed internally by the graph)
    const = ['ccF', 'ccT']  # False/0, True:1
    nodes.append(BoolConstant(f'ccT', value=True))
    nodes.append(BoolConstant(f'ccF', value=False))

    # add placeholders (duplicates will be removed internally by the graph)
    nodes.extend(PlaceHolder(name) for name in assignments)

    # add NotEquals nodes (duplicates will be removed internally by the graph)
    old_assignment = tuple(
        NotEquals(f'{name}_neq_{value}', operands=(name, const[value]))
        for (name, value) in assignments.items()
    )
    nodes.extend(old_assignment)

    # add Or aggregate
    if assignment_id is None:
        assignment_id = max(it.chain((
            int(m.group(1))
            for n in c_graph.nodes
            if (m := re.match(r'prevent_assignment_(\d+)', n.name))
        ), (0,)))
    nodes.append(Or(f'prevent_assignment_{assignment_id}', operands=old_assignment))

    return CGraph(nodes)
