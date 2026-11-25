import sys
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Type, TypeVar, Union, overload

import math
import itertools as it

from sxpat.graph import *
from sxpat.graph.node import *
from sxpat.utils.print import pprint
from sxpat.graph.components import IO, Parameter, Constraints, Values


__all__ = [
    # digest (to be moved to own sub/module)
    'unpack_ToInt',
    # optimization
    'crystallise',
    'prune_unused', 'prune_unused_keepio',
    # assignments
    'set_bool_constants',
    # non behavioural changes
    'set_prefix', 'set_prefix_new',
    # compute graph accessories
    'get_nodes_type', 'get_nodes_bitwidth',

    'get_unique_code',

    # others
    # (this could be in questions? or a new module? maybe called constraints::? or maybe something else)
    'prevent_assignment',
]


_N = TypeVar('_N', bound=Node)


def unpack_ToInt(graph: Graph) -> Graph:
    """
        Given a graph, returns a new graph with all ToInt nodes unpacked to a more primitive set of nodes.

        @authors: Marco Biasion
    """

    graph_builder = GraphBuilder()

    types_component = graph.base_components['Types']
    toint_nodes = tuple(
        node
        for node in graph.nodes
        if types_component.instance_of(node.name, [ToInt])
    )
    # skip if no ToInt node is present
    if len(toint_nodes) == 0: return graph

    # generate constants for each sum
    topology_component = graph.base_components['Topology']
    int_consts = {
        toint.name: {
            # n: IntConstant(f'{toint.name}_c{n}', value=n)
            n: graph_builder.add_node(f'{toint.name}_c{n}', IntConstant).add_extras(value=n).current
            for n in it.chain((0,), (2**i for i in range(len(topology_component.operands(toint)))))
        }
        for toint in toint_nodes
    }
    # for consts in int_consts.values():
    #     for node in consts.values():
    #         graph_copier.add_node(node)

    # create all if->int nodes (Dict[original_node_name, List[if_nodes_for_that_node]])
    ifs: Dict[str, List[If]] = {
        toint.name: [
            # If(f'if_{toint.name}_{i}', operands=(pred, int_consts[toint.name][2**i], int_consts[toint.name][0]))
            graph_builder.add_node(f'if_{toint.name}_{i}', If).add_operands([pred, int_consts[toint.name][2**i].name, int_consts[toint.name][0].name]).current
            for i, pred in enumerate(topology_component.operands(toint)) # type: ignore
        ]
        for toint in toint_nodes
    }
    # for ifs_list in ifs.values():
    #     for node in ifs_list:
    #         graph_copier.add_node(node)

    for toint in toint_nodes:
        # node = Sum(toint.name, operands=ifs[toint.name])
        graph_builder.add_node(toint.name, Sum).add_operands(operands=[n.name for n in ifs[toint.name]])
        if graph.has_base_component('Subgraph'):
            # graph_copier.add_node(node, in_subgraph=graph.base_components['Subgraph'].in_subgraph(toint.name))
            graph_builder.add_extras(in_subgraph=graph.base_components['Subgraph'].in_subgraph(toint.name))

    types_component = graph.base_components['Types']
    for node in graph.nodes:
        if not types_component.instance_of(node.name, [ToInt]):
            graph_builder.add_node_from(node, graph)

    return graph_builder.create()


def prune_unused(graph: Graph, reserved_names: Iterable[str]) -> Graph:
    """
        Given a graph, returns a new graph without any dangling nodes (recursively).  
        `reserved_names` represents the nodes that root the graph and that must be kept even if not used.

        @authors: Marco Biasion
    """

    graph_copier = GraphCopier(graph)
    types_component = graph.base_components['Types']
    
    # convert to stack
    valid_terminations = list(reserved_names)

    # find reachable nodes from the reserved ones and add only visited nodes
    while valid_terminations:
        node_name = valid_terminations.pop()
        graph_copier.add_node(node_name, types_component.get(node_name))
        valid_terminations.extend(_n.name for _n in graph.predecessors(node_name))

    # nodes = list(graph[name] for name in visited_nodes)
    # return graph.copy(nodes)
    
    return graph_copier.copy() 


def prune_unused_keepio(graph: Graph, reserved_names: Iterable[str] = tuple()) -> Graph:
    """
        Given a graph, returns a new graph without any dangling nodes (recursively).  
        By default all inputs and outputs root the graph and will be kept,
        optionally `reserved_names` can be used to select more nodes.

        @authors: Marco Biasion
    """

    return prune_unused(
        graph,
        it.chain(
            graph.base_components['IO'].inputs_names,
            graph.base_components['IO'].outputs_names,
            reserved_names,
        )
    )


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
        types_component = graph.base_components['Types']
        for node in graph.nodes:
            # skip if already computed
            if node.name in type_of: continue

            # direct cases
            elif types_component.instance_of(node, [BoolResType]): type_of[node.name] = bool
            elif types_component.instance_of(node, [IntResType]): type_of[node.name] = int

            # dynamic cases
            elif types_component.instance_of(node, [DynamicResType]):
                last_pred = graph.predecessors(node)[-1]
                type_of[node.name] = type_of[last_pred.name]

            # special cases
            elif types_component.instance_of(node, [PlaceHolder]): continue
            elif types_component.instance_of(node, [Objective]): continue
            else: raise TypeError(f'Node {node.name} has an invalid type ({types_component.get(node)}).')

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
    graphs = tuple(graphs)

    def manage_node(node: Node, graph: Graph):
        types_component = graph.base_components['Types']
        topology_component = graph.base_components['Topology']
        # skippable
        if types_component.instance_of(node, [Target, Constraint]): return

        # deferred case (all predecessors of a node should have the same bitwidth)
        elif nodes_types[node.name] is not int:
            if types_component.instance_of(node, [Operation]):
                max_bitwidth = max(bitwidth_of.get(n.name, 0) for n in graph.predecessors(node))
                for n in graph.predecessors(node):
                    bitwidth_of[n.name] = max_bitwidth

        # trivial cases
        elif types_component.instance_of(node, [IntConstant]) and node.name not in bitwidth_of:
            bitwidth_of[node.name] = max(1, math.ceil(math.log(graph.base_components['Values'].get(node) + 1, 2)))
        elif types_component.instance_of(node, [ToInt]) and node.name not in bitwidth_of:
            bitwidth_of[node.name] = len(topology_component.operands(node))

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
            manage_node(node, graph)

    # backward update (optimally updates backward chains)
    for graph in reversed(graphs):
        for node in reversed(graph.nodes):
            manage_node(node, graph)

    if bitwidth_of == initial_mapping:
        return {  # remove null pairs (name:0)
            k: v
            for k, v in bitwidth_of.items()
            if v != 0
        }
    else:
        return get_nodes_bitwidth(graphs, nodes_types, bitwidth_of)


def set_bool_constants(graph: Graph, constants: Mapping[str, bool], skip_missing: bool = False) -> Graph:
    """
        Takes a graph and a mapping from names to bool in input
        and returns a new graph with the nodes corresponding to the given names replaced with the wanted constant.

        @note: Placeholder nodes are not replaced, to preserve the inter-graph connections.

        @note: *TODO: can be expanded to manage also IntConstant nodes*  
        @note: *TODO: add guard to prevent assigning the wrong type*  

        @authors: Marco Biasion
    """
    graph_copier = GraphCopier(graph)
    types_component = graph.base_components['Types']

    for (name, value) in constants.items():
        if skip_missing and name not in graph: continue
        if types_component.instance_of(graph[name], [PlaceHolder]): continue

        # new_nodes[name] = BoolConstant(node.name, value)
        graph_copier.add_node(name, BoolConstant).add_extras(value=value)

    for n in graph.nodes:
        if not n.name in constants:
            graph_copier.add_node_from_node(n)

    return graph_copier.copy()


def set_prefix(graph: Graph, prefix: str) -> Graph:
    """
        # DEPRECATED
        # Use `set_prefix_new` instead

        Given a graph and the wanted prefix, returns a new graph with all operation nodes updated with the prefix.

        @authors: Marco Biasion
    """

    to_be_updated = frozenset(n.name for n in it.chain(graph.expressions, graph.constants))
    updated_names: Mapping[str, str] = {
        n.name: f'{prefix}{n.name}' if n.name in to_be_updated else n.name
        for n in graph.nodes
    }

    graph_copier = GraphCopier(graph)
    if graph.has_base_component('Constraints'):
        graph_copier.add_autofill_component('Constraints')
    if graph.has_base_component('IO'):
        graph_copier.add_base_component(
            IO({'inputs_names': [updated_names[name] for name in graph.base_components['IO'].inputs_names],
                'outputs_names': [updated_names[name] for name in graph.base_components['IO'].outputs_names]
            })
        )
    if graph.has_base_component('Parameter'):
        graph_copier.add_base_component(
            Parameter(parameters_names=[updated_names[name] for name in graph.base_components['Parameter'].parameters_names])
        )

    types_component = graph.base_components['Types']
    topology_component = graph.base_components['Topology']
    for node in graph.nodes:
        if types_component.instance_of(node.name, [Operation]):
            operands = [updated_names[name] for name in topology_component.operands(node.name)]
            graph_copier.add_node_from_node(node, name=updated_names[node.name], operands=operands)
        else:
            graph_copier.add_node_from_node(node, name=updated_names[node.name])

    return graph_copier.copy()


def set_prefix_new(graph: Graph, prefix: str, preserve_names: Optional[Iterable[str]] = None) -> Graph:
    """
        Given a graph and the wanted prefix, returns a new graph with all nodes names updated with the prefix.  
        If `preserve_names` is given, the nodes matching those names will not be renamed.

        @authors: Marco Biasion
    """

    if preserve_names is None: preserve_names = frozenset()
    else: preserve_names = frozenset(preserve_names)

    # compute new names
    new_name_of: Mapping[str, str] = {
        n.name: n.name if n.name in preserve_names else f'{prefix}{n.name}'
        for n in graph.nodes
    }

    graph_copier = GraphCopier(graph)
    if graph.has_base_component('Constraints'):
        graph_copier.add_autofill_component('Constraints')
    if graph.has_base_component('IO'):
        graph_copier.add_base_component(
            IO({'inputs_names': [new_name_of[name] for name in graph.base_components['IO'].inputs_names],
                'outputs_names': [new_name_of[name] for name in graph.base_components['IO'].outputs_names]
            })
        )
    if graph.has_base_component('Parameter'):
        graph_copier.add_base_component(
            Parameter(parameters_names=[new_name_of[name] for name in graph.base_components['Parameter'].parameters_names])
        )

    # add updated nodes
    types_component = graph.base_components['Types']
    topology_component = graph.base_components['Topology']
    for node in graph.nodes:
        if types_component.instance_of(node.name, [Operation]):
            operands = [new_name_of[name] for name in topology_component.operands(node.name)]
            graph_copier.add_node_from_node(node, name=new_name_of[node.name], operands=operands)
        else:
            graph_copier.add_node_from_node(node, name=new_name_of[node.name])

    return graph_copier.copy()


def prevent_assignment(assignments: Mapping[str, bool],
                       assignment_id: Union[str, int]) -> Graph:
    """
        Returns a Graph with constraints preventing the given assignment.

        @authors: Marco Biasion
    """
    graph_builder = GraphBuilder()
    graph_builder.add_autofill_component('Constraints')

    # placeholders
    for name in assignments:
        graph_builder.add_node(name, PlaceHolder)

    #
    prass_name: Mapping[bool, Callable[[str], str]] = {
        True: lambda name: f'prass_{assignment_id}_not_{name}',
        False: lambda name: name,
    }

    # create required negations
    for (name, value) in assignments.items():
        if value is True:
            graph_builder.add_node(prass_name[True](name), Not).add_operands([name])

    # create aggregation (and relative constraint)
    prevent = graph_builder.add_node(
        f'prass_{assignment_id}_prevent', 
        Or
        ).add_operands([prass_name[value](name) for (name, value) in assignments.items()]).current
    graph_builder.add_node(f'prass_{assignment_id}_prevent_constr', Constraint).add_operands([prevent.name])
    
    return graph_builder.create()


class crystallise:
    """
        Takes a graph and and reduces it.
        I.E. simplifies the graph by evaluating nodes with constant inputs.

        Complexity: O(V + E)

        #TODO: What to do with Objective where their operand is a constant?

        @authors: Marco Biasion, Lorenzo Spada
    """

    T_ib = TypeVar('T_ib', int, bool)
    T_nary_bool = TypeVar('T_nary_bool', And, Or)
    T_all_or_nothing = TypeVar(
        'T_all_or_nothing',
        Not,
        Sum, AbsDiff, Mul, Div, ToInt,
        Equals, NotEquals, LessThan, LessEqualThan, GreaterThan, GreaterEqualThan,
        Identity,
    )

    @classmethod
    def graph(cls, graph: Graph, pre_crystallised_graphs: Iterable[Graph]) -> Graph:
        _crystalliser_for = {  # concrete node type -> crystallizing function
            # > variables
            BoolVariable: cls._as_is,
            IntVariable: cls._as_is,
            # > constants
            BoolConstant: cls._as_is,
            IntConstant: cls._as_is,
            # > placeholder
            PlaceHolder: cls._as_is,
            # > expressions
            # bool to bool
            Not: cls._all_or_nothing_node,
            And: cls._nary_bool,
            Or: cls._nary_bool,
            Xor: cls._xor,
            Xnor: cls._xnor,
            Implies: cls._implies,
            # int to int
            Sum: cls._all_or_nothing_node,
            AbsDiff: cls._all_or_nothing_node,
            Mul: cls._all_or_nothing_node,
            Div: cls._all_or_nothing_node,
            RightShift: cls._all_or_nothing_node,
            LeftShift: cls._all_or_nothing_node,
            # bool to int
            ToInt: cls._all_or_nothing_node,
            # int to bool
            Equals: cls._all_or_nothing_node,
            NotEquals: cls._all_or_nothing_node,
            LessThan: cls._all_or_nothing_node,
            LessEqualThan: cls._all_or_nothing_node,
            GreaterThan: cls._all_or_nothing_node,
            GreaterEqualThan: cls._all_or_nothing_node,
            # identity
            Identity: cls._all_or_nothing_node,
            # branch
            Multiplexer: cls._multiplexer,
            If: cls._if,
            # quantify
            AtLeast: cls._at_least,
            AtMost: cls._at_most,
            # special
            Target: cls._as_is,
            Constraint: cls._as_is,
        }

        graph_copier = GraphCopier(graph)
        new_nodes = dict()
        # new_nodes_attributes: dict[str, tuple[bool, int | None]] = dict()
        type_component = graph.base_components['Types']
        topology_component = graph.base_components['Topology']
        for node in graph.nodes:
            # select crystalliser
            try:
                crystallise = _crystalliser_for[type_component.get(node)]
            except KeyError as err:
                pprint.error(f'No crystalliser for {type_component.get(node)} is implemented')
                raise err

            # get operands
            if type_component.instance_of(node, [Operation]):
                operands = []
                for operand_name in topology_component.operands(node):
                    operand = new_nodes.get(operand_name, graph[operand_name])

                    if isinstance(operand, PlaceHolder):
                        operand = cls._find_non_placeholder(operand_name, pre_crystallised_graphs) or operand

                    operands.append(operand)
            else:
                operands = []

            # crystallise node
            new_nodes[node.name] = crystallise(graph, graph_copier, node, operands, pre_crystallised_graphs)

        #     if not new_nodes[node.name] is node:
        #         in_subgraph = False
        #         weight = None
        #         if graph.has_base_component('Subgraph'):
        #             in_subgraph = graph.base_components['Subgraph'].in_subgraph(node.name)
        #         if graph.has_base_component('Weight'):
        #             weight = graph.base_components['Weight'].get(node.name)
        #         new_nodes_attributes[node.name] = (in_subgraph, weight)

        # type_component = graph.base_components['Types']
        # for node in new_nodes.values():
        #     graph_copier.add_node(node.name, type_component.get(node.name))
        #     if node.name in new_nodes_attributes:
        #         graph_copier.add_extras(
        #             in_subgraph=new_nodes_attributes[node.name][0],
        #             weight=new_nodes_attributes[node.name][1]
        #         )

        return graph_copier.copy()

    @classmethod
    def graphs(cls, graphs: Sequence[Graph]) -> Sequence[Graph]:
        cry_graphs = []
        for g in graphs: cry_graphs.append(cls.graph(g, cry_graphs))
        return tuple(cry_graphs)

    @staticmethod
    @overload
    def as_constant(graph_copier: GraphCopier, node: Node, value: bool) -> BoolConstant: ...

    @staticmethod
    @overload
    def as_constant(graph_copier: GraphCopier, node: Node, value: int) -> IntConstant: ...

    @staticmethod
    def as_constant(graph_copier: GraphCopier, node: Node, value: T_ib) -> Constant[T_ib]:
        node_type = {bool: BoolConstant, int: IntConstant}[type(value)]
        return graph_copier.add_node(node.name, node_type).add_extras(value=value).current
        # return node_from_node(node_type, node, {'value': value})

    @staticmethod
    def as_other(cls: Type[_N], 
                 graph_copier: GraphCopier,
                 node: Node,
                 /, *,
                 operand: AnyNode = ...,
                 operands: Sequence[AnyNode] = ...,
                 value: Union[bool, int] = ...
                 ) -> _N:
        graph_copier.add_node(node.name, cls)
        if operand is not Ellipsis: graph_copier.add_operands([operand.name])
        if operands is not Ellipsis: graph_copier.add_operands([n.name for n in operands])
        if value is not Ellipsis: graph_copier.add_extras(value=value)
        return graph_copier.current
        # return node_from_node(cls, node, override)

    @staticmethod
    def _find_non_placeholder(name: str, graphs: Iterable[Graph]) -> Union[None, Node, Operation, Valued]:
        for graph in graphs:
            types_component = graph.base_components['Types']
            if name in graph:
                node = graph[name]
                if not types_component.instance_of(node, [PlaceHolder]): return node
        return None

    @classmethod
    def _as_is(cls, graph: Graph, graph_copier: GraphCopier, node: Node, _0, _1) -> Node:
        return graph_copier.add_node(node.name, type(node)).current

    @classmethod
    def _nary_bool(cls, graph: Graph, graph_copier: GraphCopier, node: T_nary_bool, operands: Sequence[Node], _) -> Union[T_nary_bool, BoolConstant]:
        """@authors: Marco Biasion, Lorenzo Spada"""
        values_component = graph.base_components['Values']

        # select unit and zero values
        unit_value, zero_value = {
            And: (True, False),
            Or: (False, True),
        }[type(node)]

        # one operand is the zero value
        # a & 0 : 0
        # a | 1 : 1
        if any(isinstance(op, BoolConstant) and values_component.get(op) is zero_value for op in operands):
            return cls.as_constant(graph_copier, node, zero_value)

        # get non-constant operands
        nc_operands = [
            op.name for op in operands
            if not isinstance(op, BoolConstant)
        ]

        # all operands are the unit value
        # 1 & 1 : 1
        # 0 | 0 : 0
        if len(nc_operands) == 0:
            return cls.as_constant(graph_copier, node, unit_value)

        # only one non-constant operand left
        # a & 1 : a
        # a | 0 : a
        elif len(nc_operands) == 1:
            return cls.as_other(Identity, graph_copier, node, operand=nc_operands[0])

        # multiple non-constant operands left
        # a & b & 1 : a & b
        # a | b | 0 : a | b
        else:
            if len(nc_operands) == len(operands): return node
            else: return cls.as_other(type(node), graph_copier, node, operands=nc_operands)

    @classmethod
    def _xor(cls, graph: Graph, graph_copier: GraphCopier, node: Xor, operands: Sequence[Node], _) -> Union[Xor, BoolConstant, Identity, Not]:
        """@authors: Marco Biasion"""

        op_a, op_b = operands
        values_component = graph.base_components['Values']

        # both operands are constant
        # # ^ # : #
        if isinstance(op_a, Constant) and isinstance(op_b, Constant):
            return cls.as_constant(graph_copier, node, values_component.get(op_a) != values_component.get(op_b))

        # no operand is constant
        # a ^ b
        elif not isinstance(op_a, Constant) and not isinstance(op_b, Constant):
            return graph_copier.add_node(node.name, type(node)).current

        # one operand is constant
        # z ^ #
        else:
            if isinstance(op_a, Constant):
                const_op, var_op = op_a, op_b
            else:
                const_op, var_op = op_b, op_a

            # z ^ 0 :  z
            # z ^ 1 : !z
            if values_component.get(const_op) is False:
                return cls.as_other(Identity, graph_copier, node, operand=var_op)
            else:
                return cls.as_other(Not, graph_copier, node, operand=var_op)

    @classmethod
    def _xnor(cls, graph: Graph, graph_copier: GraphCopier, node: Implies, operands: Sequence[Node], _) -> Union[Xnor, BoolConstant, Identity, Not]:

        op_a, op_b = operands
        values_component = graph.base_components['Values']

        # both operands are constant
        # # ≡ # : #
        if isinstance(op_a, Constant) and isinstance(op_b, Constant):
            return cls.as_constant(graph_copier, node, values_component.get(op_a) == values_component.get(op_b))

        # no operand is constant
        # a ≡ b
        elif not isinstance(op_a, Constant) and not isinstance(op_b, Constant):
            return graph_copier.add_node(node.name, type(node)).current

        # one operand is constant
        # z ≡ #
        else:
            if isinstance(op_a, Constant):
                const_op, var_op = op_a, op_b
            else:
                const_op, var_op = op_b, op_a

            # z ≡ 0 : !z
            # z ≡ 1 :  z
            if values_component.get(const_op) is False:
                return cls.as_other(Not, graph_copier, node, operand=var_op)
            else:
                return cls.as_other(Identity, graph_copier, node, operand=var_op)

    @classmethod
    def _implies(cls, graph: Graph, graph_copier: GraphCopier, node: Implies, operands: Sequence[Node], _) -> Union[Implies, BoolConstant, Not, Identity]:
        """@authors: Lorenzo Spada, Marco Biasion"""

        op_a, op_b = operands
        values_component = graph.base_components['Values']

        # both operands are constant
        # # => #
        if isinstance(op_a, Constant) and isinstance(op_b, Constant):
            value = {
                (False, False): True,  # 0 => 0 : 1
                (False, True): True,   # 0 => 1 : 1
                (True, True): False,   # 1 => 0 : 0
                (True, True): True,    # 1 => 1 : 1
            }[(values_component.get(op_a), values_component.get(op_b))]
            return cls.as_constant(graph_copier, node, value)

        # only right operand is constant
        # a => #
        elif isinstance(op_b, Constant):
            # a => 0 : ~a
            if values_component.get(op_b) is False:
                return cls.as_other(Not, graph_copier, node, operand=op_a)

            # a => 1 : 1
            else:
                return cls.as_constant(graph_copier, node, True)

        # only left operand is constant
        # # => b
        elif isinstance(op_a, Constant):
            # 0 => b : 1
            if values_component.get(op_a) is False:
                return cls.as_constant(graph_copier, node, True)

            # 1 => b : b
            else:
                return cls.as_other(Identity, graph_copier, node, operand=op_b)

        # no operand is constant
        # a => b
        else:
            return graph_copier.add_node(node.name, type(node)).current

    @classmethod
    def _all_or_nothing_node(cls, graph: Graph, graph_copier: GraphCopier, node: T_all_or_nothing, operands: Sequence[Node], _) -> Union[T_all_or_nothing, Constant]:
        """@authors: Marco Biasion, Lorenzo Spada"""

        values_component = graph.base_components['Values']

        # all operands are constant
        # !#       : #
        #  # +  #  : #
        # |# -  #| : #
        #  # == #  : #
        #  # != #  : #
        #  # <  #  : #
        #  # <= #  : #
        #  # >  #  : #
        #  # >= #  : #
        if all(isinstance(op, Constant) for op in operands):
            # select operation
            operation: Callable[[Sequence[Union[BoolConstant, IntConstant]], Values], Union[bool, int]] = {
                # bool to bool
                Not: lambda ops, values: not values.get(ops[0]),
                # int to int
                Sum: lambda ops, values: sum(values.get(op) for op in ops),  # possible todo: if an operand is const0, gets discarded. if any group of operands sum to 0, they get discarded, not work if unsigned.
                AbsDiff: lambda ops, values: abs(values.get(ops[0]) - values.get(ops[1])),  # possible todo: if one is 0, becomes identity of other
                Mul: lambda ops, values: math.prod(values.get(op) for op in ops),
                Div: lambda ops, values: values.get(ops[0]) // values.get(ops[1]),
                ToInt: lambda ops, values: sum(values.get(op) * (2 ** i) for (i, op) in enumerate(ops)),
                RightShift: lambda ops, values: values.get(ops[0]) // (2 ** values_component.get(node)),
                LeftShift: lambda ops, values: values.get(ops[0]) * (2 ** values_component.get(node)),
                # bool to int
                Equals: lambda ops, values: values.get(ops[0]) == values.get(ops[1]),
                NotEquals: lambda ops, values: values.get(ops[0]) != values.get(ops[1]),
                LessThan: lambda ops, values: values.get(ops[0]) < values.get(ops[1]),
                LessEqualThan: lambda ops, values: values.get(ops[0]) <= values.get(ops[1]),  # possible todo: if unsigned and left=0, becomes true
                GreaterThan: lambda ops, values: values.get(ops[0]) > values.get(ops[1]),
                GreaterEqualThan: lambda ops, values: values.get(ops[0]) >= values.get(ops[1]),  # possible todo:if unsigned and right=0, becomes true
                # identity
                Identity: lambda ops, values: values.get(ops[0]),
            }[type(node)]

            return cls.as_constant(graph_copier, node, operation(operands, graph.base_components['Values']))

        # some operand is variable
        # !a
        #  a +  #
        # |a -  #|
        #  a == #
        #  a != #
        #  a <  #
        #  a <= #
        #  a >  #
        #  a >= #
        else:
            return graph_copier.add_node(node.name, type(node)).current

    @classmethod
    def _multiplexer(cls, graph: Graph, graph_copier: GraphCopier, node: Multiplexer, operands: Sequence[Node], _) -> Union[Multiplexer, BoolConstant, Identity, Not, Implies]:
        """@authors: Marco Biasion, Lorenzo Spada"""

        a, b, c = operands
        a_const = isinstance(a, Constant)
        b_const = isinstance(b, Constant)
        c_const = isinstance(c, Constant)
        values_component = graph.base_components['Values']

        # - 0 variable
        # 0 (0,0) :  0
        # 0 (0,1) :  1
        # 0 (1,0) :  1
        # 0 (1,1) :  0
        # 1 (0,0) :  0
        # 1 (0,1) :  1
        # 1 (1,0) :  0
        # 1 (1,1) :  1
        if a_const and b_const and c_const:
            return {  # (a, b, c)
                (0, 0, 0): lambda: cls.as_constant(graph_copier, node, False),
                (0, 0, 1): lambda: cls.as_constant(graph_copier, node, True),
                (0, 1, 0): lambda: cls.as_constant(graph_copier, node, True),
                (0, 1, 1): lambda: cls.as_constant(graph_copier, node, False),
                (1, 0, 0): lambda: cls.as_constant(graph_copier, node, False),
                (1, 0, 1): lambda: cls.as_constant(graph_copier, node, True),
                (1, 1, 0): lambda: cls.as_constant(graph_copier, node, False),
                (1, 1, 1): lambda: cls.as_constant(graph_copier, node, True),
            }[(values_component.get(a), values_component.get(b), values_component.get(c))]()

        # - 1 variable
        # a (0,0) :  0
        # a (0,1) :  1
        # a (1,0) : !a
        # a (1,1) :  a
        elif b_const and c_const:
            return {  # (b, c)
                (0, 0): lambda: cls.as_constant(graph_copier, node, False),
                (0, 1): lambda: cls.as_constant(graph_copier, node, True),
                (1, 0): lambda: cls.as_other(Not, graph_copier, node, operand=a),
                (1, 1): lambda: cls.as_other(Identity, graph_copier, node, operand=a),
            }[(values_component.get(b), values_component.get(c))]()

        # 0 (b,0) :  b
        # 0 (b,1) : !b
        # 1 (b,0) :  0
        # 1 (b,1) :  1
        elif a_const and c_const:
            return {  # (a, c)
                (0, 0): lambda: cls.as_other(Identity, graph_copier, node, operand=b),
                (0, 1): lambda: cls.as_other(Not, graph_copier, node, operand=b),
                (1, 0): lambda: cls.as_constant(graph_copier, node, False),
                (1, 1): lambda: cls.as_constant(graph_copier, node, True),
            }[(values_component.get(a), values_component.get(c))]()

        # 0 (0,c) :  c
        # 0 (1,c) : !c
        # 1 (0,c) :  c
        # 1 (1,c) :  c
        elif a_const and b_const:
            return {  # (a, b)
                (0, 0): lambda: cls.as_other(Identity, graph_copier, node, operand=c),
                (0, 1): lambda: cls.as_other(Not, graph_copier, node, operand=c),
                (1, 0): lambda: cls.as_other(Identity, graph_copier, node, operand=c),
                (1, 1): lambda: cls.as_other(Identity, graph_copier, node, operand=c),
            }[(values_component.get(a), values_component.get(b))]()

        # - 2 variables
        # a (b,0) : !a & b (or !(b => a))
        # a (b,1) : b => a
        elif c_const:
            return {  # c
                0: lambda: graph_copier.add_node(node.name, type(node)).current,  # would require the creation of new nodes
                1: lambda: cls.as_other(Implies, graph_copier, node, operands=(b, a)),
            }[values_component.get(c)]()

        # a (0,c) : c
        # a (1,c) : a xnor c
        elif b_const:
            return {  # b
                0: lambda: cls.as_other(Identity, graph_copier, node, operand=c),
                1: lambda: cls.as_other(Xnor, graph_copier, node, operands=(a, c)),
            }[values_component.get(b)]()

        # 0 (b,c) : b ^ c
        # 1 (b,c) : c
        elif a_const:
            return {  # a
                0: lambda: cls.as_other(Xor, graph_copier, node, operands=(b, c)),
                1: lambda: cls.as_other(Identity, graph_copier, node, operand=c),
            }[values_component.get(a)]()

        # - 3 variables
        # a (b,c) : a (b,c)
        else:
            return graph_copier.add_node(node.name, type(node)).current

    @classmethod
    def _if(cls, graph: Graph, graph_copier: GraphCopier, node: If, operands: Sequence[Node], _) -> Node:
        """@authors: Marco Biasion, Lorenzo Spada"""

        a, b, c = operands
        values_component = graph.base_components['Values']

        # condition is constant false
        # (0) ?,c : c
        if node_is_false(a, graph):
            # (0) ?,# : #
            if isinstance(c, Constant):
                return cls.as_constant(graph_copier, node, values_component.get(c))

            # (0) ?,c : c
            else:
                return cls.as_other(Identity,graph_copier, node, operand=c)

        # condition is constant true
        # (1) b,? : b
        elif node_is_true(a, graph):
            # (1) #,? : #
            if isinstance(b, Constant):
                return cls.as_constant(graph_copier, node, values_component.get(b))

            # (1) b,? : b
            else:
                return cls.as_other(Identity, graph_copier, node, operand=b)

        # branches are constant and equal
        # (?) k,k : k
        elif isinstance(b, Constant) and isinstance(c, Constant) and values_component.get(b) == values_component.get(c):
            return cls.as_constant(graph_copier, node, values_component.get(b))

        # (a) b,c
        # (a) #,#
        else:
            return graph_copier.add_node(node.name, type(node)).current

    @classmethod
    def _at_least(cls, graph: Graph, graph_copier: GraphCopier, node: AtLeast, operands: Sequence[Node], _) -> Union[AtLeast, BoolConstant]:
        """@authors: Lorenzo Spada, Marco Biasion"""

        values_component = graph.base_components['Values']

        # no operand is constant
        if not any(isinstance(op, Constant) for op in operands):
            return graph_copier.add_node(node.name, type(node)).current

        # get non-constant operands and updated value (-1 for each true constant)
        nc_operands = []
        new_value = values_component.get(node)
        for operand in operands:
            if not isinstance(operand, Constant): nc_operands.append(operand)
            elif values_component.get(operand) == True: new_value -= 1

        # enough true constants are present
        if new_value <= 0:
            return cls.as_constant(graph_copier, node, True)

        # `new_value` cannot be surpassed by the non-constant operands
        elif len(nc_operands) < new_value:
            return cls.as_constant(graph_copier, node, False)

        # shrink the node
        # possible todo: if only one is left and new_value=1, return identity of operand
        #                (maybe something similar can be done for _at_most too)
        else:
            return cls.as_other(AtLeast, graph_copier, operands=nc_operands, value=new_value)

    @classmethod
    def _at_most(cls, graph: Graph, graph_copier: GraphCopier, node: AtMost, operands: Sequence[Node], _) -> Union[AtMost, BoolConstant]:
        """@authors: Lorenzo Spada, Marco Biasion"""

        values_component = graph.base_components['Values']

        # no operand is constant
        if not any(isinstance(op, Constant) for op in operands):
            return graph_copier.add_node(node.name, type(node)).current

        # get non-constant operands and updated value (-1 for each true constant)
        nc_operands = []
        new_value = values_component.get(node)
        for operand in operands:
            if not isinstance(operand, Constant): nc_operands.append(operand)
            elif values_component.get(operand) is True: new_value -= 1

        # too many true constants are present
        if new_value < 0:
            return cls.as_constant(graph_copier, node, False)

        # `new_value` can accomodate all non-constant operands
        if len(nc_operands) <= new_value:
            return cls.as_constant(graph_copier, node, True)

        # shrink the node
        else:
            return cls.as_other(AtMost, graph_copier, node, operands=nc_operands, value=new_value)

# fino a qui funzioni in _crystalliser_for

def node_is_true(node: Union[Node, BoolConstant], graph: Graph) -> bool:
    values_component = graph.base_components['Values']
    return isinstance(node, BoolConstant) and values_component.get(node) is True


def node_is_false(node: Union[Node, BoolConstant], graph: Graph) -> bool:
    values_component = graph.base_components['Values']
    return isinstance(node, BoolConstant) and values_component.get(node) is False


# def node_from_node(cls: Type[_N], node: Node, override: Mapping[str, Any]) -> _N:
#     # get common fields
#     kwargs = {'name': node.name}
#     if issubclass(cls, Operation) and isinstance(node, Operation):
#         kwargs['operands'] = node.operands
#     if issubclass(cls, Valued) and isinstance(node, Valued):
#         kwargs['value'] = node.value

#     # override with custom
#     kwargs.update(override)

#     # create new node
#     return cls(**kwargs)


class get_unique_code:
    """
        Returns a unique alphabetical code made of upper and lower case letters.

        The first 2704 calls use a two-letter format (AA..zz).
        After that, the code grows to three letters, then four, and so on.
    """

    _chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    _size = 2

    def __new__(cls):
        if not hasattr(cls, '_idx'): cls._idx = -1
        cls._idx += 1
        return cls.prefix_for_index(cls._idx)

    @classmethod
    def prefix_for_index(cls, idx: int) -> str:
        if idx < 0:
            raise ValueError('idx must be non-negative')

        base = len(cls._chars)
        size = cls._size
        span = base ** size

        # Keep the historical AA..zz sequence for the first two-letter block,
        # then extend to longer codes instead of overflowing the alphabet.
        while idx >= span:
            idx -= span
            size += 1
            span = base ** size

        digits = []
        for _ in range(size):
            idx, rem = divmod(idx, base)
            digits.append(cls._chars[rem])

        return ''.join(reversed(digits))
