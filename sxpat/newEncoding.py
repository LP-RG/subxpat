from typing import IO, Any, Callable, Container, Dict, Sequence, Type, Union, TypeVar

import dataclasses as dc
import itertools as it

from sxpat.newConverter import get_nodes_bitwidth, unpack_ToInt, get_nodes_type
from sxpat.newGraph import *
from sxpat.specifications import EncodingType, Specifications


ValidGraph = TypeVar('ValidGraph', SGraph, TGraph, CGraph)


NODE_TO_Z3INT: Dict[Type[Node], Callable[[Union[Node, OperationNode, Valued], Sequence[str], Sequence[Any]], str]] = {
    # variables
    BoolVariable: lambda n, items, accs: f'Bool(\'{n.name}\')',
    IntVariable: lambda n, items, accs:  f'Int(\'{n.name}\')',
    # constants
    BoolConstant: lambda n, items, accs: f'BoolVal({n.value})',
    IntConstant: lambda n, items, accs:  f'IntVal({n.value})',
    # output
    Copy: lambda n, items, accs:   items[0],
    Target: lambda n, items, accs: items[0],
    # placeholder
    PlaceHolder: lambda n, items, accs: n.name,
    # boolean operations
    Not: lambda n, items, accs:     f'Not({items[0]})',
    And: lambda n, items, accs:     f'And({", ".join(items)})',
    Or: lambda n, items, accs:      f'Or({", ".join(items)})',
    Implies: lambda n, items, accs: f'Implies({items[0]}, {items[1]})',
    # integer operations
    Sum: lambda n, items, accs:     f'Sum({", ".join(items)})',
    AbsDiff: lambda n, items, accs: f'If({items[0]} >= {items[1]}, {items[0]} - {items[1]}, {items[1]} - {items[0]})',
    # comparison operations
    Equals: lambda n, items, accs:           f'({items[0]} == {items[1]})',
    LessThan: lambda n, items, accs:         f'({items[0]} < {items[1]})',
    LessEqualThan: lambda n, items, accs:    f'({items[0]} <= {items[1]})',
    GreaterThan: lambda n, items, accs:      f'({items[0]} > {items[1]})',
    GreaterEqualThan: lambda n, items, accs: f'({items[0]} >= {items[1]})',
    # quantifier operations
    AtLeast: lambda n, items, accs:          f'AtLeast({", ".join(items)}, {n.value})',
    AtMost: lambda n, items, accs:           f'AtMost({", ".join(items)}, {n.value})',
    # branching operations
    Multiplexer: lambda n, items, accs: f'If({items[1]}, If({items[2]}, {items[0]}, Not({items[0]})), {items[2]})',
    If: lambda n, items, accs:          f'If({items[0]}, {items[1]}, {items[2]})',
}
NODE_TO_Z3BV: Dict[Type[Node], Callable[[Union[Node, OperationNode, Valued], Sequence[str]], str]] = {
    **NODE_TO_Z3INT,
    # variables
    IntVariable: lambda n, items, accs:  f'BitVec(\'{n.name}\', {accs[0]})',
    # constants
    IntConstant: lambda n, items, accs:  f'BitVecVal({n.value}, {accs[0]})',
    # integer operations
    AbsDiff: lambda n, items, accs: f'If(UGE({items[0]}, {items[1]}), {items[0]} - {items[1]}, {items[1]} - {items[0]})',
    # comparison operations
    Equals: lambda n, items, accs:           f'({items[0]} == {items[1]})',
    # TODO
    LessThan: lambda n, items, accs:         f'ULT({items[0]}, {items[1]})',
    LessEqualThan: lambda n, items, accs:    f'ULE({items[0]}, {items[1]})',
    GreaterThan: lambda n, items, accs:      f'UGT({items[0]}, {items[1]})',
    GreaterEqualThan: lambda n, items, accs: f'UGE({items[0]}, {items[1]})',
}

TYPE_TO_INTSORT: Dict[Type[Union[int, bool]], Callable[[Sequence[Any]], str]] = {
    bool: lambda accs: 'BoolSort()',
    int: lambda accs: 'IntSort()',
}
TYPE_TO_BVSORT: Dict[Type[Union[int, bool]], Callable[[Sequence[Any]], str]] = {
    **TYPE_TO_INTSORT,
    int: lambda accs: f'BitVecSort({accs[0]})',
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
    def encode(cls, s_graph: SGraph, t_graph: TGraph, c_graph: CGraph, specs: Specifications, destination: IO[str]) -> None:
        # select encoding type
        node_mapping = {  # Node to Z3 expression
            EncodingType.Z3_INTEGER: NODE_TO_Z3INT,
            EncodingType.Z3_BITVECTOR: NODE_TO_Z3BV,
        }[specs.encoding]
        type_mapping = {  # bool/int to Z3 sorts
            EncodingType.Z3_INTEGER: TYPE_TO_INTSORT,
            EncodingType.Z3_BITVECTOR: TYPE_TO_BVSORT,
        }[specs.encoding]
        solver_construct = {  # solver object creation
            EncodingType.Z3_INTEGER: 'Solver()',  # 'SolverFor(\'LIA\')',
            EncodingType.Z3_BITVECTOR: 'SolverFor(\'BV\')',
        }[specs.encoding]
        accs = {  # node accessories
            EncodingType.Z3_INTEGER: lambda n: (),
            EncodingType.Z3_BITVECTOR: lambda n: (nodes_bitwidths.get(n.name, None),),
        }[specs.encoding]

        # compute initial accessories
        graphs = (s_graph, t_graph, c_graph)
        nodes_types = get_nodes_type(graphs)
        nodes_bitwidths = get_nodes_bitwidth((s_graph, t_graph, c_graph), nodes_types)
        # digest graphs
        s_graph = unpack_ToInt(s_graph)
        t_graph = unpack_ToInt(t_graph)
        c_graph = unpack_ToInt(c_graph)
        # compute refined acessories
        graphs = (s_graph, t_graph, c_graph)
        nodes_types = get_nodes_type(graphs, nodes_types)
        nodes_bitwidths = get_nodes_bitwidth(graphs, nodes_types, nodes_bitwidths)

        # create call graphs (graphs where each node name has been replaced with the relative function call)
        inputs_string = ','.join(s_graph.inputs_names)
        non_gates_names = frozenset(node.name for node in it.chain(s_graph.inputs,
                                                                   t_graph.parameters,
                                                                   *(g.constants for g in graphs)))
        call_graphs = tuple(
            cls.graph_as_function_calls(graph, inputs_string, non_gates_names)
            for graph in graphs
        )

        # initialization
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
                f'{name} = {node_mapping[type(node)](node, None, accs(node))}'
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
                f'{name} = {node_mapping[type(node)](node, None,accs(node))}'
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
                function_string.format(name=node.name, sort=type_mapping[nodes_types[node.name]](accs(node)))
                for graph in graphs
                for node in graph.operations
            ),
            *('',) * 2,
        )))

        # gates behavior
        destination.write('\n'.join((
            '# behaviour',
            'constraints = And(',
            *(
                f'    {node.name} == {node_mapping[type(node)](node, node.items, accs(node))},'
                for graph in call_graphs
                for node in graph.operations
            ),
            ')',
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
