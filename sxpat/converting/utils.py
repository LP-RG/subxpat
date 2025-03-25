from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, TypeVar, Union

import re
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


G = TypeVar('G', Graph, IOGraph, SGraph, PGraph, CGraph)


def unpack_ToInt(graph: Union[Graph, IOGraph, SGraph, PGraph, CGraph]):
    toint_nodes = tuple(
        node
        for node in graph.nodes
        if isinstance(node, ToInt)
    )
    if len(toint_nodes) == 0:  # nothing to do
        return graph

    # generate constants for each sum
    int_consts = {
        toint.name: {
            n: IntConstant(f'{toint.name}_c{n}', value=n)
            for n in it.chain((0,), (2**i for i in range(len(toint.items))))
        }
        for toint in toint_nodes
    }

    # create all if->int nodes (Dict[original_node_name, List[if_nodes_for_that_node]])
    ifs: Dict[str, List[If]] = {
        toint.name: [
            If(f'if_{toint.name}_{i}', items=(pred, int_consts[toint.name][2**i], int_consts[toint.name][0]))
            for i, pred in enumerate(toint.items)
        ]
        for toint in toint_nodes
    }
    # create the Sum nodes
    sums = [
        Sum(
            toint.name,
            in_subgraph=toint.in_subgraph,
            items=ifs[toint.name]
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

    return type(graph)(nodes, **{extra: getattr(graph, extra) for extra in graph.EXTRA})


def prune_unused(graph: Union[Graph, IOGraph, SGraph, PGraph, CGraph]):
    """This function takes a graph and returns a new graph without any dangling nodes (recursive).
        Nodes counted as correct terminations are nodes of class `Copy` (or of subclasses) or of class Bool/IntVariable.
    """

    # TODO:MARCO: do we want to keep also the variables (probably yes)
    termination_nodes = [node.name for node in graph.nodes if isinstance(node, (Copy, BoolVariable, IntVariable))]
    # termination_nodes = [node.name for node in graph.nodes if isinstance(node, (Copy, ))]

    # find reachable nodes from the terminations
    visited_nodes = set()
    while len(termination_nodes) > 0:
        node_name = termination_nodes.pop()
        visited_nodes.add(node_name)
        termination_nodes.extend(_n.name for _n in graph.predecessors(node_name))

    # filter out non visited nodes
    nodes = (node for node in graph.nodes if node.name in visited_nodes)

    return type(graph)(nodes, **{extra: getattr(graph, extra) for extra in graph.EXTRA})


def get_nodes_type(graphs: Iterable[Union[Graph, IOGraph, SGraph, PGraph, CGraph]],
                   initial_mapping: Mapping[str, type] = dict()
                   ) -> Dict[str, type]:

    type_of = dict(initial_mapping)

    for graph in graphs:
        for node in graph.nodes:
            # skip if already computed
            if node.name in type_of:
                continue

            # direct cases
            if isinstance(node, boolean_nodes):
                type_of[node.name] = bool
            elif isinstance(node, integer_nodes):
                type_of[node.name] = int

            # dynamic cases
            elif isinstance(node, untyped_nodes):
                last_pred = graph.predecessors(node)[-1]
                type_of[node.name] = type_of[last_pred.name]

            # special cases
            elif isinstance(node, contact_nodes):
                continue
            else:
                raise TypeError("The node has an invalid type")

    return type_of


def get_nodes_bitwidth(graphs: Iterable[Graph],
                       nodes_types: Mapping[str, type],
                       initial_mapping: Mapping[str, int] = dict()
                       ) -> Dict[str, int]:
    """
        Computes the bitwidth of each node.

        The function will repeat itself if any width changes, 
        this is to force all nodes that are part of the same chains to have the same bitwidth.
    """

    bitwidth_of = dict(initial_mapping)

    def manage_node(node: Node):
        # deferred case (all predecessors of a node should have the same bitwidth)
        if nodes_types[node.name] is not int:
            if isinstance(node, OperationNode):
                max_bitwidth = max(bitwidth_of.get(n.name, 0) for n in graph.predecessors(node))
                for n in graph.predecessors(node):
                    bitwidth_of[n.name] = max_bitwidth

        # trivial case
        elif isinstance(node, ToInt) and node.name not in bitwidth_of:
            bitwidth_of[node.name] = len(graph.predecessors(node))

        # dynamic case
        else:
            max_bitwidth = max(
                bitwidth_of.get(n.name, 0)
                for n in it.chain(graph.predecessors(node), graph.successors(node), (node,))
            )
            bitwidth_of[node.name] = max_bitwidth

    # forward update (optimally updates decreasing chains)
    for graph in graphs:
        for node in graph.nodes:
            manage_node(node)

    # backward update (optimally updates increasing chains)
    for graph in reversed(graphs):
        for node in reversed(graph.nodes):
            manage_node(node)

    if bitwidth_of == initial_mapping:
        # remove 0
        return {
            k: v
            for k, v in bitwidth_of.items()
            if v != 0
        }
    else:
        return get_nodes_bitwidth(graphs, nodes_types, bitwidth_of)


def set_bool_constants(graph: G, constants: Mapping[str, bool]) -> G:
    """
    Takes a graph and a mapping from names to bool in input
    and returns a new graph with the nodes corresponding to the given names replaced with the wanted constant.

    (*TODO: can be expanded to manage also int constansts*)
    """

    new_nodes = {n.name: n for n in graph.nodes}
    for (name, value) in constants.items():
        node = graph[name]
        if isinstance(node, OperationNode):
            # TODO: can be implemented using prune_unused()
            raise NotImplementedError('The logic to replace an OperationNode with a constant has not been implemented yet.')
        else:
            new_nodes[node.name] = BoolConstant(node.name, node.weight, node.in_subgraph, value)

    return type(graph)(new_nodes.values(), **{extra: getattr(graph, extra) for extra in graph.EXTRA})


def set_prefix(graph: G, prefix: str) -> G:
    """
    Takes a graph and a prefix as input and returns a new graph with all operation nodes updated with the prefix.
    """

    operations_names = frozenset(n.name for n in graph.operations)
    update_name: Callable[[str], str] = lambda name: f'{prefix}{name}' if name in operations_names else name

    nodes = []
    for node in graph.nodes:
        # if node in graph.inputs:
        #     nodes.append(node)
        if isinstance(node, OperationNode):
            items = (update_name(name) for name in node.items)
            nodes.append(node.copy(name=update_name(node.name), items=items))
        else:
            # nodes.append(node)
            nodes.append(node.copy(name=update_name(node.name)))

    outputs_names = (f'{prefix}{name}' for name in graph.outputs_names)

    return type(graph)(nodes, graph.inputs_names, outputs_names)


def prevent_combination(c_graph: CGraph,
                        assignments: Mapping[str, bool],
                        assignment_id: Optional[Any] = None) -> CGraph:
    """
    Takes a constraints graph and expands it to prevent the given assignment.  
    It will allow any change, but at least one change is required.

    (*TODO: can be expanded to manage also integers (be careful of bitwidth)*)
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
        NotEquals(f'{name}_neq_{value}', items=(name, const[value]))
        for name, value in assignments.items()
    )
    nodes.extend(old_assignment)

    # add Or aggregate
    if assignment_id is None:
        assignment_id = max(it.chain((
            int(m.group(1))
            for n in c_graph.nodes
            if (m := re.match(r'prevent_assignment_(\d+)', n.name))
        ), (0,)))
    nodes.append(Or(f'prevent_assignment_{assignment_id}', items=old_assignment))

    return CGraph(nodes)
