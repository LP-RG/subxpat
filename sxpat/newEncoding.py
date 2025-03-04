from typing import IO, Any, Callable, Container, Dict, Sequence, Type, Union, TypeVar

import dataclasses as dc
import itertools as it

from sxpat.newConverter import unpack_toint, get_nodes_type
from sxpat.newGraph import *
from sxpat.specifications import EncodingType, Specifications


ValidGraph = TypeVar('ValidGraph', SGraph, TGraph, CGraph)


NODE_TO_Z3INT: Dict[Type[Node], Callable[[Union[Node, OperationNode, Valued], Sequence[str]], str]] = {
    # inputs
    BoolVariable: lambda n, items: f'Bool(\'{n.name}\')',
    IntVariable: lambda n, items:  f'Int(\'{n.name}\')',
    # constants
    BoolConstant: lambda n, items: f'BoolVal({n.value})',
    IntConstant: lambda n, items:  f'IntVal({n.value})',
    # output
    Copy: lambda n, items:   items[0],
    Target: lambda n, items: items[0],
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
    **NODE_TO_Z3INT,
    # inputs
    IntVariable: lambda n, items:  f'Bv(\'{n.name}\')',  # TODO
    # constants
    IntConstant: lambda n, items:  str(n.value),
    #
    # TODO
}

TYPE_TO_INTSORT: Dict[Type[Union[int, bool]], Callable[..., str]] = {
    bool: lambda *args: 'BoolSort()',
    int: lambda *args: 'IntSort()',
}
TYPE_TO_BVSORT: Dict[Type[Union[int, bool]], Callable[..., str]] = {
    bool: lambda *args: 'BoolSort()',
    int: lambda *args: f'BitVecSort({args[0]})',
}


# class Z3InlinePartialEncoder:
#     @classmethod
#     def recursive_conversion(cls, graph: Graph, node: Union[Node, OperationNode, Valued]) -> str:
#         return NODE_TO_Z3INT[type(node)](
#             node,
#             [cls.recursive_conversion(graph, item) for item in graph.predecessors(node)]
#         )
#     @classmethod
#     def encode(cls, graph: Graph) -> Tuple[str]:
#         leaves = [
#             node
#             for node in graph.nodes
#             if len(graph.successors(node)) == 0
#         ]
#         graph = unpack_toint(graph)
#         return tuple(
#             cls.recursive_conversion(graph, leaf)
#             for leaf in leaves
#         )


class Z3FuncEncoder:
    @classmethod
    def graph_as_function_calls(cls, graph: ValidGraph, inputs_string: str, non_gates_names: Container[str]):
        """
            This method takes a graph in input and returns a new graph with all nodes updated
            to have their name being the equivalent z3 uninterpreted function call.
        """

        # function to compute the new name
        update_name: Callable[[str], str] = lambda name: name if name in non_gates_names else f'{name}({inputs_string})'
        # node conversion
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
    def encode(cls, s_graph: SGraph, t_graph: TGraph, c_graph: CGraph, specs: Specifications, destination: IO[str]) -> ...:
        # select encoding type
        node_mapping = {
            EncodingType.Z3_INTEGER: NODE_TO_Z3INT,
            EncodingType.Z3_BITVECTOR: NODE_TO_Z3BV,
        }[specs.encoding]
        type_mapping = {
            EncodingType.Z3_INTEGER: TYPE_TO_INTSORT,
            EncodingType.Z3_BITVECTOR: TYPE_TO_BVSORT,
        }[specs.encoding]
        solver_construct = {
            EncodingType.Z3_INTEGER: 'Solver()',
            EncodingType.Z3_BITVECTOR: 'SolverFor(\'BV\')',
        }[specs.encoding]
        # digest graphs
        s_graph = unpack_toint(s_graph)
        t_graph = unpack_toint(t_graph)
        c_graph = unpack_toint(c_graph)
        # aggregate grapgs
        graphs = (s_graph, t_graph, c_graph)
        # get node types
        node_types = get_nodes_type(graphs)

        # init
        # TODO: maybe returns a string (which would be used outside, either written to file or other)
        destination.write('\n'.join((
            'from z3 import *',
            *('',) * 2,
        )))

        # variables
        variables = {  # ignore duplicates
            node.name: node
            for graph in graphs
            for node in graph.nodes
            if isinstance(node, (BoolVariable, IntVariable))
        }
        destination.write('\n'.join((
            '# variables (inputs, parameters)',
            *(
                f'{name} = {node_mapping[type(node)](node, None)}'
                for (name, node) in variables.items()
            ),
            *('',) * 2,
        )))

        # constants
        constants = {  # ignore duplicates
            node.name: node
            for graph in graphs
            for node in graph.nodes
            if isinstance(node, (BoolConstant, IntConstant))
        }
        destination.write('\n'.join((
            '# constants',
            *(
                f'{name} = {node_mapping[type(node)](node, None)}'
                for (name, node) in constants.items()
            ),
            *('',) * 2,
        )))

        # gates functions
        inputs_count = len(s_graph.inputs)
        output_count = len(s_graph.outputs)
        function_string = f'{{name}} = Function(\'{{name}}\', {", ".join(("BoolSort()",) * inputs_count)}, {{sort}})'
        destination.write('\n'.join((
            '# nodes (circuits and constraints)',
            *(
                function_string.format(name=node.name, sort=type_mapping[node_types[node.name]](output_count))
                for graph in graphs
                for node in graph.operations
            ),
            *('',) * 2,
        )))

        # preparation
        inputs_string = ','.join(s_graph.inputs_names)
        non_gates_names = frozenset(node.name for node in it.chain(s_graph.inputs, t_graph.parameters, (g.constants for g in graphs)))
        call_graphs = tuple(
            cls.graph_as_function_calls(graph, inputs_string, non_gates_names)
            for graph in graphs
        )

        # gates behavior
        destination.write('\n'.join((
            '# behaviour',
            'constraints = And(',
            *(
                f'    {node.name} == {node_mapping[type(node)](node, node.items)},'
                for graph in call_graphs
                for node in graph.operations
            ),
            ')',
            # 'gates_behavior = And(',
            # '    # Current circuit',
            # *(f'    {node.name} == {cls.NODE_TO_Z3[type(node)](node)},' for node in _s_graph.gates),
            # '    # Template circuit',
            # *(f'    {node.name} == {cls.NODE_TO_Z3[type(node)](node)},' for node in _t_graph.gates),
            # ')',
            *('',) * 2,
        )))

        # solver
        destination.write('\n'.join((
            f'# solver',
            f'solver = {solver_construct}',
            f'solver.add(ForAll(',
            f'    [{",".join(s_graph.inputs_names)}],',
            f'    constraints',
            f'))',
            f'status = solver.check()',
            *('',) * 2,
        )))

        # results
        destination.write('\n'.join((
            f'# results',
            f'print(status)',
            f'if status == sat:',
            f'    model = solver.model()',
            *(
                f'    print(\'{target.item}\', model[{target.item}])'
                for graph in call_graphs
                for target in graph.targets
            ),
            *('',) * 2,
        )))
