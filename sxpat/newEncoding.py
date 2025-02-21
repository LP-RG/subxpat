from typing import Callable, Tuple, Container, Dict, Sequence, Type, Union, TypeVar

import itertools as it

from sxpat.newGraph import *
from sxpat.specifications import Specifications


ValidGraph = TypeVar('ValidGraph', SGraph, TGraph, CGraph)

NODE_TO_Z3INT: Dict[Type[Node], Callable[[Union[Node, OperationNode, Valued], Sequence[str]], str]] = {
    # inputs
    BoolVariable: lambda n, items: n.name,
    IntVariable: lambda n, items:  n.name,
    # constants
    BoolConstant: lambda n, items: str(n.value),
    IntConstant: lambda n, items:  str(n.value),
    # output
    Copy: lambda n, items: items[0],
    # placeholder
    PlaceHolder: lambda n, items: n.name,
    # bool operations
    Not: lambda n, items:     f'Not({items[0]})',
    And: lambda n, items:     f'And({", ".join(items)})',
    Or: lambda n, items:      f'Or({", ".join(items)})',
    Implies: lambda n, items: f'Implies({items[0]}, {items[1]})',
    # int operations
    ToInt: lambda n, items:   f'If({items[0]}, {items[1]}, {items[2]})',
    Sum: lambda n, items:     f'Sum({", ".join(items)})',
    AbsDiff: lambda n, items: f'If({items[0]} >= {items[1]}, {items[0]} - {items[1]}, {items[1]} - {items[0]})',
    # comparison operations
    Equals: lambda n, items:           f'({items[0]} == {items[1]})',
    AtLeast: lambda n, items:          f'AtLeast({", ".join(items)}, {n.value})',
    AtMost: lambda n, items:           f'AtMost({", ".join(items)}, {n.value})',
    LessThan: lambda n, items:         f'({items[0]} < {items[1]})',
    LessEqualThan: lambda n, items:    f'({items[0]} <= {items[1]})',
    GreaterThan: lambda n, items:      f'({items[0]} > {items[1]})',
    GreaterEqualThan: lambda n, items: f'({items[0]} >= {items[1]})',
    # branching operations
    Multiplexer: lambda n, items: f'If({items[1]}, If({items[2]}, {items[0]}, Not({items[0]})), {items[2]})',
    Switch: lambda n, items:      f'If({items[1]}, {items[0]}, {n.off_value})',
    If: lambda n, items:          f'If({items[0]}, {items[1]}, {items[2]})',
}
NODE_TO_Z3BV: Dict[Type[Node], Callable[[Union[Node, OperationNode, Valued], Sequence[str]], str]] = {
    # TODO
}


# class Z3InlinePartialEncoder(Z3PartialEncoder):
class Z3InlinePartialEncoder:
    @classmethod
    def recursive_conversion(cls, graph: Graph, node: Union[Node, OperationNode, Valued]) -> str:
        return cls.NODE_TO_Z3INT[type(node)](
            node,
            [cls.recursive_conversion(graph, item) for item in graph.predecessors(node)]
        )

    @classmethod
    def encode(cls, graph: TGraph) -> Tuple[str]:
        leaves = [
            node
            for node in graph.nodes
            if len(graph.successors(node)) == 0
        ]

        a = cls.unpack_toint(graph)

        return tuple(
            cls.recursive_conversion(graph, leaf)
            for leaf in leaves
        )


class Z3IntFuncEncoder:
    NODE_TO_Z3: Dict[Type[Node], Callable[[Union[Node, OperationNode]], str]] = {
        # inputs
        BoolVariable: lambda n: n.name,
        IntVariable: lambda n:  n.name,
        # constants
        BoolConstant: lambda n: n.value,
        IntConstant: lambda n:  n.value,
        # output
        Copy: lambda n: n.item,
        # placeholder
        PlaceHolder: lambda n: n.name,
        # bool operations
        Not: lambda n:     f'Not({n.item})',
        And: lambda n:     f'And({", ".join(n.items)})',
        Or: lambda n:      f'Or({", ".join(n.items)})',
        Implies: lambda n: f'Implies({n.left}, {n.right})',
        # int operations
        ToInt: lambda n:   'Sum(' + ', '.join(f'IntVal({2 ** i}) * {_n}' for i, _n in enumerate(n.items)) + ')',
        Sum: lambda n:     f'Sum({", ".join(n.items)})',
        AbsDiff: lambda n: f'If({n.left} >= {n.right}, {n.left} - {n.right}, {n.right} - {n.left})',
        # comparison operations
        Equals: lambda n:           f'({n.items[0]} == {n.items[1]})',
        AtLeast: lambda n:          f'AtLeast({", ".join(n.items)}, {n.value})',
        AtMost: lambda n:           f'AtMost({", ".join(n.items)}, {n.value})',
        LessThan: lambda n:         f'({n.left} < {n.right})',
        LessEqualThan: lambda n:    f'({n.left} <= {n.right})',
        GreaterThan: lambda n:      f'({n.left} > {n.right})',
        GreaterEqualThan: lambda n: f'({n.left} >= {n.right})',
        # branching operations
        Multiplexer: lambda n: f'If({n.parameter_1}, If({n.parameter_2}, {n.origin}, Not({n.origin})), {n.parameter_2})',
        Switch: lambda n:      f'If({n.parameter}, {n.origin}, {n.off_value})',
        If: lambda n:          f'If({n.condition}, {n.if_true}, {n.if_false})',
    }

    @classmethod
    def graph_as_function_calls(cls, graph: ValidGraph, inputs_string: str, non_gates_names: Container[str]):
        update_name: Callable[[str], str] = lambda name: name if name in non_gates_names else f'{name}({inputs_string})'
        nodes = [
            (
                node.copy(name=update_name(node.name), items=(update_name(name) for name in node.items))
                if isinstance(node, OperationNode) else
                node.copy(name=update_name(node.name))
            )
            for node in graph.nodes
        ]

        extra = dict()
        if isinstance(graph, SGraph):
            extra['inputs_names'] = graph.inputs_names
            extra['outputs_names'] = (update_name(name) for name in graph.outputs_names)
        if isinstance(graph, TGraph):
            extra['parameters_names'] = graph.parameters_names

        return type(graph)(nodes, **extra)

    @classmethod
    def encode(cls, s_graph: SGraph, t_graph: TGraph, c_graph: CGraph, specs: Specifications) -> ...:
        f = open('testing.py', 'w')

        # init
        f.write('\n'.join((
            'from z3 import *',
            *('',) * 2,
        )))

        # bools
        f.write('\n'.join((
            '# Inputs',
            *(f'{name} = Bool(\'{name}\')' for name in s_graph.inputs_names),
            '# Parameters',
            *(f'{name} = Bool(\'{name}\')' for name in t_graph.parameters_names),
            *('',) * 2,
        )))

        # gates functions
        inputs_count = len(s_graph.inputs)
        f.write('\n'.join((
            '# Current circuit',
            *(f'{node.name} = Function(\'{node.name}\', {", ".join(("BoolSort()",) * inputs_count)}, BoolSort())' for node in s_graph.gates),
            '# Template circuit',
            *(f'{node.name} = Function(\'{node.name}\', {", ".join(("BoolSort()",) * inputs_count)}, BoolSort())' for node in t_graph.gates),
            *('',) * 2,
        )))

        # preparation
        inputs_string = ','.join(s_graph.inputs_names)
        non_gates = frozenset(it.chain(s_graph.inputs, t_graph.parameters))
        non_gates_names = frozenset(node.name for node in non_gates)
        _s_graph = cls.graph_as_function_calls(s_graph, inputs_string, non_gates_names)
        _t_graph = cls.graph_as_function_calls(t_graph, inputs_string, non_gates_names)

        # gates behavior
        f.write('\n'.join((
            'gates_behavior = And(',
            '    # Current circuit',
            *(f'    {node.name} == {cls.NODE_TO_Z3[type(node)](node)},' for node in _s_graph.gates),
            '    # Template circuit',
            *(f'    {node.name} == {cls.NODE_TO_Z3[type(node)](node)},' for node in _t_graph.gates),
            ')',
            *('',) * 2,
        )))

        # constraints
        f.write('\n'.join((
            'constraints = And(',
            *(f'    {cls.NODE_TO_Z3[type(node)](node)},' for node in c_graph.gates),
            ')',
            *('',) * 2,
        )))
