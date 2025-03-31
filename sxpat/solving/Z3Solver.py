from abc import abstractmethod
from typing import IO, Any, Callable, Container, Mapping, NoReturn, Optional, Sequence, Tuple, Type, TypeVar, Union

import itertools as it
import subprocess

from sxpat.specifications import Specifications
from sxpat.utils.functions import str_to_int_or_bool

from .Solver import Solver

from sxpat.converting import get_nodes_bitwidth, unpack_ToInt, get_nodes_type
from sxpat.graph import *

import sxpat.config.config as sxpat_cfg


__all__ = [
    'Z3FuncIntSolver', 'Z3FuncBitVecSolver',
    'Z3DirectIntSolver', 'Z3DirectBitVecSolver',
]


_Graphs = TypeVar('_Graphs', bound=Sequence[Union[IOGraph, PGraph, SGraph]])


class Z3Encoder:
    """
        Base class for Z3 encoders, including some common functions.

        @authors: Marco Biasion
    """

    def __new__(cls) -> NoReturn: raise NotImplementedError(f'{cls.__qualname__} is a utility class and as such cannot be instantiated')

    node_mapping: Mapping[Type[Node], Callable[[Union[Node, OperationNode, Valued], Sequence[str], Sequence[Any]], str]]
    type_mapping: Mapping[Type[Union[int, bool]], Callable[[Sequence[Any]], str]]
    solver_construct: str
    node_accessories: Callable[[Sequence[Any]], Callable[[Node], Sequence[Any]]]

    @classmethod
    @abstractmethod
    def encode(cls,
               graphs: _Graphs,
               #   reference_graph: IOGraph, parametric_graph: PGraph, constraints_graph: CGraph,
               destination: IO[str]) -> None:

        raise NotImplementedError(f'{cls.__qualname__}.encode(...) is abstract')

    @classmethod
    def simplification_and_accessories(cls,
                                       graphs: _Graphs,
                                       #   reference_graph: IOGraph, parametric_graph: PGraph, constraints_graph: CGraph,
                                       ) -> Tuple[_Graphs, Sequence[str], Sequence[str], Mapping[str, type], Callable[[Node], Sequence[Any]]]:

        # compute initial graph accessories
        # graphs = (reference_graph, parametric_graph, constraints_graph)
        nodes_types = get_nodes_type(graphs)
        nodes_bitwidths = get_nodes_bitwidth(graphs, nodes_types)

        # simplify graphs
        graphs = tuple(unpack_ToInt(graph) for graph in graphs)

        # compute refined graph accessories
        nodes_types = get_nodes_type(graphs, nodes_types)
        nodes_bitwidths = get_nodes_bitwidth(graphs, nodes_types, nodes_bitwidths)

        # finalize node accessories
        accessories = cls.node_accessories((nodes_bitwidths,))

        # extract graph inputs (each IOGraph should have the same inputs_names)
        found_inputs_names = set(graph.inputs_names for graph in graphs if isinstance(graph, IOGraph))
        if len(found_inputs_names) == 0: raise ValueError('No IOGraph was given to the Solver module.')
        elif len(found_inputs_names) >= 2: raise ValueError('The inputs of the IOGraphs given to the Solver module did not match.')

        # extract graphs parameters (multiple PGraphs can define their own parameters)
        parameters_names = tuple(it.chain.from_iterable(graph.parameters_names for graph in graphs if isinstance(graph, PGraph)))

        return (graphs, found_inputs_names.pop(), parameters_names, nodes_types, accessories,)

    @classmethod
    def inject_initialization(cls, destination: IO[str]) -> None:
        destination.write('\n'.join((
            'from z3 import *',
            *('',) * 2,
        )))

    @classmethod
    def inject_variables(cls, destination: IO[str],
                         graphs: _Graphs,
                         accessories: Callable[[Node], Sequence[Any]]) -> None:
        variables = {  # ignore duplicates
            node.name: node
            for graph in graphs
            for node in graph.nodes
            if isinstance(node, (BoolVariable, IntVariable))
        }
        destination.write('\n'.join((
            '# variables (inputs, parameters)',
            *(
                f'{name} = {cls.node_mapping[type(node)](node, None, accessories(node))}'
                for (name, node) in variables.items()
            ),
            *('',) * 2,
        )))

    @classmethod
    def inject_constants(cls, destination: IO[str],
                         graphs: _Graphs,
                         accessories: Callable[[Node], Sequence[Any]]) -> None:
        constants = {  # ignore duplicates
            node.name: node
            for graph in graphs
            for node in graph.nodes
            if isinstance(node, (BoolConstant, IntConstant))
        }
        destination.write('\n'.join((
            '# constants',
            *(
                f'{name} = {cls.node_mapping[type(node)](node, None, accessories(node))}'
                for (name, node) in constants.items()
            ),
            *('',) * 2,
        )))

    @classmethod
    def inject_result_writing(cls, destination: IO[str],
                              graphs: Tuple[IOGraph, PGraph, CGraph]) -> None:
        destination.write('\n'.join((
            f'# results',
            f'print(status)',
            f'if status == sat:',
            f'    model = solver.model()',
            *(
                f'    print(\'{target.item}\', model.eval({target.item}))'
                for graph in graphs
                for target in graph.targets
            ),
            *('',) * 2,
        )))


class Z3FuncEncoder(Z3Encoder):
    """
        Z3 encoder using the uninterpreted functions approach.

        @authors: Marco Biasion
    """

    @classmethod
    def graph_as_function_calls(cls, graph: Union[IOGraph, PGraph, CGraph],
                                inputs_string: str,
                                non_gates_names: Container[str]):
        """
            This method takes a graph in input and returns a new graph with all nodes updated
            to have their name being the equivalent z3 uninterpreted function call.

            @authors: Marco Biasion
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

        # update extras (if needed)
        extra = dict()
        if isinstance(graph, IOGraph): extra['outputs_names'] = (update_name(name) for name in graph.outputs_names)

        return graph.copy(nodes, **extra)

    @classmethod
    def encode(cls,
               graphs: _Graphs,
               #   reference_graph: IOGraph, parametric_graph: PGraph, constraints_graph: CGraph,
               destination: IO[str]) -> None:

        # initial computations
        node_mapping = cls.node_mapping
        type_mapping = cls.type_mapping
        solver_construct = cls.solver_construct
        (graphs, inputs_names, parameters_names, nodes_types, accessories) = cls.simplification_and_accessories(graphs)

        # create call graphs (graphs where each node name has been replaced with the relative function call)
        inputs_string = ','.join(inputs_names)
        non_gates_names = frozenset(it.chain(inputs_names,
                                             parameters_names,
                                             (n.name for g in graphs for n in g.constants)))
        call_graphs = tuple(
            cls.graph_as_function_calls(graph, inputs_string, non_gates_names)
            for graph in graphs
        )

        # gather constraints graphs
        c_graphs = tuple(graph for graph in graphs if isinstance(graph, CGraph))
        call_c_graphs = tuple(graph for graph in call_graphs if isinstance(graph, CGraph))

        # initialization
        cls.inject_initialization(destination)

        # variables
        cls.inject_variables(destination, graphs, accessories)

        # constants
        cls.inject_constants(destination, graphs, accessories)

        # gates functions
        function_string = f'{{name}} = Function(\'{{name}}\', {", ".join(("BoolSort()",) * len(inputs_names))}, {{sort}})'
        destination.write('\n'.join((
            '# nodes (circuits and constraints)',
            *(
                function_string.format(name=node.name, sort=type_mapping[nodes_types[node.name]](accessories(node)))
                for graph in graphs
                for node in graph.operations
            ),
            *('',) * 2,
        )))

        # nodes behavior
        destination.write('\n'.join((
            '# behaviour',
            'behaviour = And(',
            *(
                f'    {node.name} == {node_mapping[type(node)](node, node.items, accessories(node))},'
                for graph in call_graphs
                for node in graph.operations
            ),
            ')',
            *('',) * 2,
        )))

        # nodes usage
        destination.write('\n'.join((
            '# usage',
            'usage = And(', *(
                f'    {call_node.name},'
                for (graph, call_graph) in zip(c_graphs, call_c_graphs)
                for (node, call_node) in zip(graph.operations, call_graph.operations)
                if not graph.successors(node) and nodes_types[node.name] is bool
            ), ')',
            *('',) * 2,
        )))

        # solver
        destination.write('\n'.join((
            f'# solver',
            f'solver = {solver_construct}',
            f'solver.add(ForAll(',
            f'    [{",".join(inputs_names)}],',
            f'    And(behaviour, usage)',
            f'))',
            f'status = solver.check()',
            *('',) * 2,
        )))

        # results
        cls.inject_result_writing(destination, call_graphs)


class Z3DirectEncoder(Z3Encoder):
    """
        Z3 encoder using the direct definition approach.

        @authors: Marco Biasion
    """

    @classmethod
    def encode(cls,
               graphs: _Graphs,
               #   reference_graph: IOGraph, parametric_graph: PGraph, constraints_graph: CGraph,
               destination: IO[str]) -> None:

        # initial computations
        node_mapping = cls.node_mapping
        type_mapping = cls.type_mapping
        solver_construct = cls.solver_construct
        (graphs, inputs_names, parameters_name, nodes_types, accessories) = cls.simplification_and_accessories(graphs)

        # initialization
        cls.inject_initialization(destination)

        # variables
        cls.inject_variables(destination, graphs, accessories)

        # constants
        cls.inject_constants(destination, graphs, accessories)

        # nodes behavior
        destination.write('\n'.join((
            '# behaviour',
            *(
                f'{node.name} = {node_mapping[type(node)](node, node.items, accessories(node))}'
                for graph in graphs
                for node in graph.operations
            ),
            *('',) * 2,
        )))

        # nodes usage
        destination.write('\n'.join((
            '# usage',
            'usage = And(', *(
                f'    {node.name},'
                for graph in graphs if isinstance(graph, CGraph)
                for node in graph.operations if not graph.successors(node) and nodes_types[node.name] is bool
            ), ')',
            *('',) * 2,
        )))

        # solver
        destination.write('\n'.join((
            f'# solver',
            f'solver = {solver_construct}',
            f'solver.add(ForAll(',
            f'    [{",".join(inputs_names)}],',
            f'    usage',
            f'))',
            f'status = solver.check()',
            *('',) * 2,
        )))

        # results
        cls.inject_result_writing(destination, graphs)


# Node to Z3 expression
Z3_INT_NODE_MAPPING = {
    # variables
    BoolVariable: lambda n, items, accs: f'Bool(\'{n.name}\')',
    IntVariable: lambda n, items, accs: f'Int(\'{n.name}\')',
    # constants
    BoolConstant: lambda n, items, accs: f'BoolVal({n.value})',
    IntConstant: lambda n, items, accs: f'IntVal({n.value})',
    # output
    Copy: lambda n, items, accs: items[0],
    Target: lambda n, items, accs: items[0],
    # placeholder
    PlaceHolder: lambda n, items, accs: n.name,
    # boolean operations
    Not: lambda n, items, accs: f'Not({items[0]})',
    And: lambda n, items, accs: f'And({", ".join(items)})',
    Or: lambda n, items, accs: f'Or({", ".join(items)})',
    Implies: lambda n, items, accs: f'Implies({items[0]}, {items[1]})',
    # integer operations
    Sum: lambda n, items, accs: f'Sum({", ".join(items)})',
    AbsDiff: lambda n, items, accs: f'If({items[0]} >= {items[1]}, {items[0]} - {items[1]}, {items[1]} - {items[0]})',
    # comparison operations
    Equals: lambda n, items, accs: f'({items[0]} == {items[1]})',
    NotEquals: lambda n, items, accs: f'({items[0]} != {items[1]})',
    LessThan: lambda n, items, accs: f'({items[0]} < {items[1]})',
    LessEqualThan: lambda n, items, accs: f'({items[0]} <= {items[1]})',
    GreaterThan: lambda n, items, accs: f'({items[0]} > {items[1]})',
    GreaterEqualThan: lambda n, items, accs: f'({items[0]} >= {items[1]})',
    # quantifier operations
    AtLeast: lambda n, items, accs: f'AtLeast({", ".join(items)}, {n.value})',
    AtMost: lambda n, items, accs: f'AtMost({", ".join(items)}, {n.value})',
    # branching operations
    Multiplexer: lambda n, items, accs: f'If({items[1]}, If({items[2]}, {items[0]}, Not({items[0]})), {items[2]})',
    If: lambda n, items, accs: f'If({items[0]}, {items[1]}, {items[2]})',
}
Z3_BITVEC_NODE_MAPPING = {
    **Z3_INT_NODE_MAPPING,
    # variables
    IntVariable: lambda n, items, accs: f'BitVec(\'{n.name}\', {accs[0]})',
    # constants
    IntConstant: lambda n, items, accs: f'BitVecVal({n.value}, {accs[0]})',
    # integer operations
    AbsDiff: lambda n, items, accs: f'If(UGE({items[0]}, {items[1]}), {items[0]} - {items[1]}, {items[1]} - {items[0]})',
    # comparison operations
    Equals: lambda n, items, accs: f'({items[0]} == {items[1]})',
    LessThan: lambda n, items, accs: f'ULT({items[0]}, {items[1]})',
    LessEqualThan: lambda n, items, accs: f'ULE({items[0]}, {items[1]})',
    GreaterThan: lambda n, items, accs: f'UGT({items[0]}, {items[1]})',
    GreaterEqualThan: lambda n, items, accs: f'UGE({items[0]}, {items[1]})',
}

# bool/int to Z3 sorts
Z3_INT_TYPE_MAPPING = {
    bool: lambda accs: 'BoolSort()',
    int: lambda accs: 'IntSort()',
}
Z3_BITVEC_TYPE_MAPPING = {
    **Z3_INT_TYPE_MAPPING,
    int: lambda accs: f'BitVecSort({accs[0]})',
}

# solver object creation
Z3_INT_SOLVER_CONSTRUCT = 'Solver()'  # 'SolverFor(\'LIA\')'
Z3_BITVEC_SOLVER_CONSTRUCT = 'SolverFor(\'BV\')'

# node accessories
Z3_INT_NODE_ACCESSORIES = lambda d: lambda n: ()
Z3_BITVEC_NODE_ACCESSORIES = lambda d: lambda n: (d[0].get(n.name, None),)


class Z3IntFuncEncoder(Z3FuncEncoder):
    node_mapping = Z3_INT_NODE_MAPPING
    type_mapping = Z3_INT_TYPE_MAPPING
    solver_construct = Z3_INT_SOLVER_CONSTRUCT
    node_accessories = Z3_INT_NODE_ACCESSORIES


class Z3BitVecFuncEncoder(Z3FuncEncoder):
    node_mapping = Z3_BITVEC_NODE_MAPPING
    type_mapping = Z3_BITVEC_TYPE_MAPPING
    solver_construct = Z3_BITVEC_SOLVER_CONSTRUCT
    node_accessories = Z3_BITVEC_NODE_ACCESSORIES


class Z3DirectIntEncoder(Z3DirectEncoder):
    node_mapping = Z3_INT_NODE_MAPPING
    type_mapping = Z3_INT_TYPE_MAPPING
    solver_construct = Z3_INT_SOLVER_CONSTRUCT
    node_accessories = Z3_INT_NODE_ACCESSORIES


class Z3DirectBitVecEncoder(Z3DirectEncoder):
    node_mapping = Z3_BITVEC_NODE_MAPPING
    type_mapping = Z3_BITVEC_TYPE_MAPPING
    solver_construct = Z3_BITVEC_SOLVER_CONSTRUCT
    node_accessories = Z3_BITVEC_NODE_ACCESSORIES


class Z3Solver(Solver):
    """
        Base class for solving using z3, implements all logic but the encoding.

        @authors: Marco Biasion
    """

    encoder: Z3Encoder

    @classmethod
    def solve(cls,
              graphs: _Graphs,
              #   reference_graph: IOGraph, parametric_graph: PGraph, constraints_graph: CGraph,
              specifications: Specifications) -> Tuple[str, Optional[Mapping[str, Any]]]:

        # encode
        # TODO:#15: how do we generate a name here
        script_path = f'output/z3/{specifications.exact_benchmark}_iter{specifications.iteration}.py'
        with open(script_path, 'w') as f:
            cls.encoder.encode(graphs, f)

        # run
        process = subprocess.run(
            [sxpat_cfg.PYTHON3, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if process.returncode != 0:
            raise RuntimeError(f'Solver execution FAILED. Failed to run file {script_path}')

        # decode
        # documentation: the result is not saved to a json for multiple models and so on
        #                each Solver.solve call can returns at most one model
        #                the timing must be computed at a higher level, same with the multimodel logic
        #                the new format is as follows
        # example sat:
        # sat\n
        # p_somebool True\n
        # p_somemorebool False\n
        # p_someint 1\n
        # p_somemoreint 7\n
        #
        # example unsat (unknowns are similar):
        # unsat\n
        #

        status, *raw_model = process.stdout.decode().splitlines()
        if status in ('unsat', 'unknown'):
            return (status, None)
        else:
            return (status, {
                (splt := pair.split(' '))[0]: str_to_int_or_bool(splt[1])
                for pair in raw_model
            })


class Z3FuncIntSolver(Z3Solver):
    encoder = Z3IntFuncEncoder


class Z3FuncBitVecSolver(Z3Solver):
    encoder = Z3BitVecFuncEncoder


class Z3DirectIntSolver(Z3Solver):
    encoder = Z3DirectIntEncoder


class Z3DirectBitVecSolver(Z3Solver):
    encoder = Z3DirectBitVecEncoder
