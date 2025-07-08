from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Type, TypeVar, Union, overload

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


T_type = TypeVar('T_type', bound=type)


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
            elif isinstance(node, BoolResType): type_of[node.name] = bool
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


def set_bool_constants(graph: _Graph, constants: Mapping[str, bool], skip_missing: bool = False) -> _Graph:
    """
        Takes a graph and a mapping from names to bool in input
        and returns a new graph with the nodes corresponding to the given names replaced with the wanted constant.

        @note: *TODO: can be expanded to manage also IntConstant nodes*  
        @note: *TODO: can be expanded to replace also inner nodes, and not only Variable/Constant nodes*

        @authors: Marco Biasion
    """

    new_nodes = {n.name: n for n in graph.nodes}
    for (name, value) in constants.items():
        if skip_missing and name not in graph: continue
        node = graph[name]

        if isinstance(node, Operation):
            # TODO: could be implemented using prune_unused()
            # NOTE: we do not really need prune_unused as this function should only care about setting constant
            raise NotImplementedError('The logic to replace an Operation with a constant has not been implemented yet.')
        else:
            new_nodes[node.name] = BoolConstant(node.name, value, node.weight, node.in_subgraph)

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


class crystallize:
    """
        Takes a graph and and reduces it.
        I.E. simplifies the graph by evaluating nodes with constant inputs.

        Complexity:
            Worst case: O(N²)
            Average case: O(N)

            where N is the number of nodes in the graph

        #TODO: What to do with global tasks where their operand is a constant
    """

    T_ib = TypeVar('T_ib', int, bool)
    T_nary_bool = TypeVar('T_int', And, Or)
    T_all_or_nothing = TypeVar(
        'T_int',
        Not,
        Sum, AbsDiff, ToInt,
        Equals, NotEquals, LessThan, LessEqualThan, GreaterThan, GreaterEqualThan,
        Identity,
    )

    @classmethod
    def graph(cls, graph: Graph, other_graphs: Iterable[Graph]) -> int:
        _mapping: Mapping[Type[Node], Callable[[Node, Sequence[Node], Sequence[Graph]], Node]] = {
            # > variables
            BoolVariable: cls.as_is,
            IntVariable: cls.as_is,
            # > constants
            BoolConstant: cls.as_is,
            IntConstant: cls.as_is,
            # > placeholder
            PlaceHolder: cls._placeholder,
            # > expressions
            # bool to bool
            Not: cls._all_or_nothing_node,
            And: cls._nary_bool,
            Or: cls._nary_bool,
            Implies: cls._implies,
            # int to int
            Sum: cls._all_or_nothing_node,
            AbsDiff: cls._all_or_nothing_node,
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
            Identity: cls._identity,
            # branch
            Multiplexer: cls._multiplexer,
            If: cls._if,
            # quantify
            AtLeast: cls._at_least,
            AtMost: cls._at_most,

            # special
            Objective: cls.as_is,
        }

        new_nodes = dict()
        for node in graph.nodes:
            # select crystallizer
            crystallize = _mapping.get(type(node), cls)
            if crystallize is cls: raise NotImplementedError(f'No crystallizer for {type(node)} is implemented.')

            # get operands
            # TODO: update with cry_graphs
            if isinstance(node, Operation): operands = tuple(new_nodes.get(op, graph[op]) for op in node.operands)
            else: operands = ()

            # crystallize node
            new_nodes[node.name] = crystallize(node, operands, other_graphs)

        return graph.copy(new_nodes.values())

    @classmethod
    def graphs(cls, graphs: Sequence[Graph]) -> Sequence[Graph]:
        cry_graphs = []
        for g in graphs: cry_graphs.append(cls.graph(g, cry_graphs))
        return tuple(cry_graphs)

    @staticmethod
    @overload
    def as_constant(node: Node, value: bool) -> BoolConstant: ...
    @staticmethod
    @overload
    def as_constant(node: Node, value: int) -> IntConstant: ...

    @staticmethod
    def as_constant(node: Node, value: T_ib) -> Constant[T_ib]:
        node_type = {bool: BoolConstant, int: IntConstant}[type(value)]
        return node_from_node(node_type, node, value=value)

    @staticmethod
    def as_other(cls: Type[T_type], node: Node, **kwargs: Mapping[str, Any]) -> T_type:
        if 'operand' in kwargs: kwargs['operands'] = (kwargs.pop('operand'),)
        return node_from_node(cls, node, kwargs)

    @classmethod
    def _as_is(cls, node: Node, _0, _1) -> Node:
        return node

    @classmethod
    def _placeholder(cls, node: PlaceHolder, _, cry_graphs: Sequence[Graph]) -> Union[PlaceHolder, BoolConstant]:
        for cg in cry_graphs:
            if node.name in cg:
                c_node = cg[node.name]
                if isinstance(c_node, Constant):
                    return cls.as_constant(node, c_node.value)
                else:
                    break
        return node

    @classmethod
    def _nary_bool(cls, node: T_nary_bool, operands: Sequence[Node], _) -> Union[T_nary_bool, BoolConstant]:
        """@authors: Marco Biasion, Lorenzo Spada"""

        # select unit and zero values
        unit_value, zero_value = {
            And: (True, False),
            Or: (False, True),
        }[type(node)]

        # one operand is the zero value
        # a & 0 : 0
        # a | 1 : 1
        if any(isinstance(op, BoolConstant) and op.value is zero_value for op in operands):
            return cls.as_constant(node, zero_value)

        # get non-constant operands
        nc_operands = [
            op.name for op in operands
            if not isinstance(op, BoolConstant)
        ]

        # all operands are the unit value
        # 1 & 1 : 1
        # 0 | 0 : 0
        if len(nc_operands) == 0:
            return cls.as_constant(node, unit_value)

        # only one non-constant operand left
        # a & 1 : a
        # a | 0 : a
        elif len(nc_operands) == 1:
            return cls.as_other(Identity, node, operand=nc_operands[0])

        # multiple non-constant operands left
        # a & b & 1 : a & b
        # a | b | 0 : a | b
        else:
            return And(node.name, operands=nc_operands, weight=node.weight, in_subgraph=node.in_subgraph)

    @classmethod
    def _implies(cls, node: Implies, operands: Sequence[Node], _) -> Union[Implies, BoolConstant, Not, Identity]:
        """@authors: Lorenzo Spada, Marco Biasion"""

        op_a, op_b = operands

        # a => b
        if not isinstance(op_a, Constant) and not isinstance(op_b, Constant):
            return node

        # a => #
        elif not isinstance(op_a, Constant):
            # a => 0 : ~a
            if op_b.value is False:
                return cls.as_other(Not, node, operand=op_a)

            # a => 1 : 1
            else:
                return cls.as_constant(node, True)

        # # => b
        elif not isinstance(op_b, Constant):
            # 0 => b : 1
            if op_a.value is False:
                return cls.as_constant(node, True)

            # 1 => b : b
            else:
                return cls.as_other(Identity, node, operand=op_b)

        # # => #
        else:
            value = {
                (False, False): True,  # 0 => 0 : 1
                (False, True): True,   # 0 => 1 : 1
                (True, True): False,   # 1 => 0 : 0
                (True, True): True,    # 1 => 1 : 1
            }[(op_a.value, op_b.value)]
            return cls.as_constant(node, value)

    @classmethod
    def _all_or_nothing_node(cls, node: T_all_or_nothing, operands: Sequence[Node], _) -> Union[T_all_or_nothing, Constant]:
        """@authors: Marco Biasion, Lorenzo Spada"""

        # select operation
        operation = {
            # bool to bool
            Not: lambda ops: not ops[0].value,
            # int to int
            Sum: lambda ops: sum(op.value for op in ops),
            AbsDiff: lambda ops: abs(ops[0].value - ops[1].value),
            ToInt: lambda ops: sum(op.value * (2 ** i) for (i, op) in enumerate(ops)),
            # bool to int
            Equals: lambda ops: ops[0] == ops[1],
            NotEquals: lambda ops: ops[0] != ops[1],
            LessThan: lambda ops: ops[0] < ops[1],
            LessEqualThan: lambda ops: ops[0] <= ops[1],
            GreaterThan: lambda ops: ops[0] > ops[1],
            GreaterEqualThan: lambda ops: ops[0] >= ops[1],
            # identity
            Identity: lambda ops: ops[0].value,
        }[type(node)]

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
            return cls.as_constant(node, operation(operands))

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
            return node

    @classmethod
    def _multiplexer(cls, node: Multiplexer, operands: Sequence[Node], _) -> Union[Multiplexer, BoolConstant, Identity, Not, Implies]:
        """@authors: Marco Biasion, Lorenzo Spada"""

        a, b, c = operands
        a_const = isinstance(a, Constant)
        b_const = isinstance(b, Constant)
        c_const = isinstance(c, Constant)

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
                (0, 0, 0): lambda: cls.as_constant(node, False),
                (0, 0, 1): lambda: cls.as_constant(node, True),
                (0, 1, 0): lambda: cls.as_constant(node, True),
                (0, 1, 1): lambda: cls.as_constant(node, False),
                (1, 0, 0): lambda: cls.as_constant(node, False),
                (1, 0, 1): lambda: cls.as_constant(node, True),
                (1, 1, 0): lambda: cls.as_constant(node, False),
                (1, 1, 1): lambda: cls.as_constant(node, True),
            }[(a.value, b.value, c.value)]()

        # - 1 variable
        # a (0,0) :  0
        # a (0,1) :  1
        # a (1,0) : !a
        # a (1,1) :  a
        elif b_const and c_const:
            return {  # (b, c)
                (0, 0): lambda: cls.as_constant(node, False),
                (0, 1): lambda: cls.as_constant(node, True),
                (1, 0): lambda: cls.as_other(Not, node, operand=a),
                (1, 1): lambda: cls.as_other(Identity, node, operand=a),
            }[(b.value, c.value)]()

        # 0 (b,0) :  b
        # 0 (b,1) : !b
        # 1 (b,0) :  0
        # 1 (b,1) :  1
        elif a_const and c_const:
            return {  # (a, c)
                (0, 0): lambda: cls.as_other(Identity, node, operand=b),
                (0, 1): lambda: cls.as_other(Not, node, operand=b),
                (1, 0): lambda: cls.as_constant(node, False),
                (1, 1): lambda: cls.as_constant(node, True),
            }[(a.value, c.value)]()

        # 0 (0,c) :  c
        # 0 (1,c) : !c
        # 1 (0,c) :  c
        # 1 (1,c) :  c
        elif a_const and b_const:
            return {  # (a, b)
                (0, 0): lambda: cls.as_other(Identity, node, operand=c),
                (0, 1): lambda: cls.as_other(Not, node, operand=c),
                (1, 0): lambda: cls.as_other(Identity, node, operand=c),
                (1, 1): lambda: cls.as_other(Identity, node, operand=c),
            }[(a.value, b.value)]()

        # - 2 variables
        # a (b,0) : !a & b (or !(b => a))
        # a (b,1) : b => a
        elif c_const:
            return {  # c
                0: lambda: node,  # would require the creation of new nodes
                1: lambda: cls.as_other(Implies, node, operands=(b, a)),
            }[c.value]()

        # a (0,c) : c
        # a (1,c) : a == c (also: !(b^c) (^ is xor))
        elif b_const:
            return {  # b
                0: lambda: cls.as_other(Identity, node, operand=c),
                1: lambda: node,  # uses a non boolean operator, or would require the creation of new nodes
            }[b.value]()

        # 0 (b,c) : b != c (also: b^c (^ is xor))
        # 1 (b,c) : c
        elif a_const:
            return {  # a
                0: lambda: node,  # uses a non boolean operator
                1: lambda: cls.as_other(Identity, node, operand=c),
            }[a.value]()

        # - 3 variables
        # a (b,c) : a (b,c)
        else:
            return node

    @classmethod
    def _if(cls, node: If, operands: Sequence[Node], _) -> Node:
        """@authors: Marco Biasion, Lorenzo Spada"""

        a, b, c = operands

        # (0) ?,c : c
        if node_is_false(a):
            # (0) ?,# : #
            if isinstance(c, Constant):
                return cls.as_constant(node, c.value)

            # (0) ?,c : c
            else:
                return cls.as_other(Identity, node, operand=c)

        # (1) b,? : b
        elif node_is_true(a):
            # (1) #,? : #
            if isinstance(b, Constant):
                return cls.as_constant(node, b.value)

            # (1) b,? : b
            else:
                return cls.as_other(Identity, node, operand=b)

        # (?) k,k : k
        elif isinstance(b, Constant) and isinstance(c, Constant) and b.value == c.value:
            return cls.as_constant(node, b.value)

        # (a) b,c
        # (a) #,#
        else:
            return node

    @classmethod
    def _at_least(cls, node: AtLeast, operands: Sequence[Node], _) -> Union[AtLeast, BoolConstant]:
        """@authors: Lorenzo Spada, Marco Biasion"""

        # no operand is constant
        if not any(isinstance(op, Constant) for op in operands):
            return node

        # get non-constant operands and updated value (-1 for each true constant)
        nc_operands = []
        new_value = node.value
        for operand in operands:
            if not isinstance(operand, Constant): nc_operands.append(operand)
            elif operand.value == True: new_value -= 1

        # enough true constants are present
        if new_value <= 0:
            return cls.as_constant(node, True)

        # `new_value` cannot be surpassed by the non-constant operands
        elif len(nc_operands) < new_value:
            return cls.as_constant(node, False)

        # shrink the node
        else:
            return cls.as_other(AtLeast, operands=nc_operands, value=new_value)

    @classmethod
    def _at_most(cls, node: AtMost, operands: Sequence[Node], _) -> Union[AtMost, BoolConstant]:
        """@authors: Lorenzo Spada, Marco Biasion"""

        # no operand is constant
        if not any(isinstance(op, Constant) for op in operands):
            return node

        # get non-constant operands and updated value (-1 for each true constant)
        nc_operands = []
        new_value = node.value
        for operand in operands:
            if not isinstance(operand, Constant): nc_operands.append(operand)
            elif operand.value is True: new_value -= 1

        # too many true constants are present
        if new_value < 0:
            return cls.as_constant(node, False)

        # `new_value` can accomodate all non-constant operands
        if len(nc_operands) <= new_value:
            return cls.as_constant(node, True)

        # shrink the node
        else:
            return cls.as_other(AtMost, operands=nc_operands, value=new_value)


def node_is_true(node: Union[Node, BoolConstant]) -> bool:
    return isinstance(node, BoolConstant) and node.value is True


def node_is_false(node: Union[Node, BoolConstant]) -> bool:
    return isinstance(node, BoolConstant) and node.value is False


def node_from_node(cls: Type[T_type], node: Node, fields: Mapping[str, Any]) -> T_type:
    # get common fields
    kwargs = {'name': node.name}
    if issubclass(cls, Extras) and isinstance(node, Extras):
        kwargs['weight'] = node.weight
        kwargs['in_subgraph'] = node.in_subgraph
    if issubclass(cls, Operation) and isinstance(node, Operation):
        kwargs['operands'] = node.operands
    if issubclass(cls, Valued) and isinstance(node, Valued):
        kwargs['value'] = node.value

    kwargs.update(fields)
    return cls(**kwargs)
