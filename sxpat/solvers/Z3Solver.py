import re
from typing import IO, Any, Callable, Container, Dict, Iterable, Iterator, Literal, Mapping, Optional, Sequence, Tuple, Type, Union, List, overload
from typing_extensions import override
from abc import abstractmethod

import itertools as it
import subprocess
from os.path import join as path_join

from sxpat.specifications import Specifications
from sxpat.utils.functions import str_to_int_or_bool
from sxpat.utils.decorators import make_utility_class

from .Solver import Solver

from sxpat.converting import get_nodes_bitwidth, unpack_ToInt, get_nodes_type
from sxpat.graph import *
from sxpat.graph.node import *

import sxpat.config.config as sxpat_cfg


__all__ = [
    'Z3FuncIntSolver', 'Z3FuncBitVecSolver',
    'Z3DirectIntSolver', 'Z3DirectBitVecSolver',
    'Z3HybridIntSolver', 'Z3HybridBitVecSolver',
]


@make_utility_class
class Z3Encoder:
    """
        Base class for Z3 encoders, including some common functions.

        @authors: Marco Biasion
    """

    node_mapping: Mapping[Type[Node], Callable[[Union[Node, Operation, Valued], Sequence[str], Sequence[Any]], str]]
    type_mapping: Mapping[Type[Union[int, bool]], Callable[[Sequence[Any]], str]]
    solver_construct: Mapping[Type[Union[ForAll, Min, Max, None]], str]
    node_accessories: Callable[[Sequence[Any]], Callable[[Node], Sequence[Any]]]

    constraints_assertion: Mapping[Type[Union[ForAll, Min, Max, None]], Callable[[str, str, Sequence[str]], Sequence[str]]] = {
        type(None): lambda solver_name, task, assertions: [
            f'{solver_name}.add(',
            *(f'    {a},' for a in assertions),
            f')',
        ],
        ForAll: lambda solver_name, forall, assertions: [
            f'{solver_name}.add(',
            f'    ForAll(',
            f'        [{",".join(forall.operands)}],',
            f'        And(',
            *(f'            {a},' for a in assertions),
            f'        )',
            f'    )',
            f')',
        ],
        Min: lambda solver_name, min, assertions: [
            f'{solver_name}.add(',
            *(f'    {a},' for a in assertions),
            f')',
            f'{solver_name}.minimize({min.operand})',
        ],
        Max: lambda solver_name, max, assertions: [
            f'{solver_name}.add(',
            *(f'    {a},' for a in assertions),
            f')',
            f'{solver_name}.maximize({max.operand})',
        ],
    }

    @classmethod
    @abstractmethod
    def encode(cls, graphs: Solver._Graphs,
               destination: IO[str],
               global_task: Union[ForAll, Min, Max, None] = None,
               ) -> None:
        raise NotImplementedError(f'{cls.__qualname__}.encode(...) is abstract')

    @classmethod
    def simplification_and_accessories(cls, graphs: Solver._Graphs,
                                       ) -> Tuple[Solver._Graphs, Sequence[str], Sequence[str], Mapping[str, type], Callable[[Node], Sequence[Any]]]:

        # compute initial graph accessories
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
    def inject_variables(cls, destination: IO[str], graphs: Solver._Graphs,
                         accessories: Callable[[Node], Sequence[Any]]) -> None:
        variables = {  # ignore duplicates
            node.name: node
            for graph in graphs
            for node in graph.nodes
            if isinstance(node, Variable)
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
    def inject_constants(cls, destination: IO[str], graphs: Solver._Graphs,
                         accessories: Callable[[Node], Sequence[Any]]) -> None:
        constants = {  # ignore duplicates
            node.name: node
            for graph in graphs
            for node in graph.nodes
            if isinstance(node, Constant)
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
    def inject_nodes_usage(cls,
                           constraint_graphs: Sequence[CGraph],
                           destination: IO[str],) -> None:
        destination.write('\n'.join((
            '# usage',
            'usage = And(', *(
                f'    {constraint_node.operand},'
                for constraint_graph in constraint_graphs
                for constraint_node in constraint_graph.constraints
            ), ')',
            *('',) * 2,
        )))

    @classmethod
    def inject_solver(cls, 
                      destination: IO[str],
                      global_task: Union[ForAll, Min, Max, None],
                      solver_construct: Mapping[Type[Union[ForAll, Min, Max, None]], str],
                      constraint_assertion: Mapping[Type[Union[ForAll, Min, Max, None]], Callable[[str, str, Sequence[str]], Sequence[str]]],
                      solver_add_parameters: List[str]) -> None: 
        destination.write('\n'.join((
            f'# define solver',
            f'solver = {solver_construct[type(global_task)]}',
            *constraint_assertion[type(global_task)]('solver', global_task, solver_add_parameters),
            *('',) * 2,
        )))

    @classmethod
    def inject_solve_and_result_writing(cls, destination: IO[str],
                                        name_graphs: Solver._Graphs,
                                        value_graphs: Solver._Graphs,
                                        ) -> None:
        destination.write('\n'.join((
            f'# check',
            f'status = solver.check()',
            f'print(status)',
            f'',
            f'# model',
            f'if status == sat:',
            f'    model = solver.model()',
            *(
                f'    print(\'{n_target.operand}\', model.eval({v_target.operand}, model_completion=True))'
                for (n_graph, v_graph) in zip(name_graphs, value_graphs)
                for (n_target, v_target) in zip(n_graph.targets, v_graph.targets)
            ),
            *('',) * 2,
        )))


class Z3FuncEncoder(Z3Encoder):
    """
        Z3 encoder using the uninterpreted functions approach.

        @authors: Marco Biasion
    """

    @staticmethod
    def _all_names(nodes: Iterable[Node]) -> Iterator[str]:
        seen_names = set()
        for node in nodes:
            if node.name not in seen_names:
                seen_names.add(node.name)
                yield node.name
            if isinstance(node, Operation):
                for name in node.operands:
                    if name not in seen_names:
                        seen_names.add(name)
                        yield name

    @classmethod
    @overload
    def nodes_as_function_calls(cls, nodes: Iterable[Node], inputs_string: str, non_gates_names: Container[str]
                                ) -> Sequence[Node]:
        """
           Given a sequence of nodes in input, returns a new sequence with all nodes updated
           to have their name being the equivalent z3 uninterpreted function call.
       """

    @classmethod
    @overload
    def nodes_as_function_calls(cls, nodes: Iterable[Node], inputs_string: str, non_gates_names: Container[str],
                                *, get_mapping: Literal[True]
                                ) -> Tuple[Sequence[Node], Mapping[str, str]]:
        """
           Given a sequence of nodes in input, returns a new sequence with all nodes updated
           to have their name being the equivalent z3 uninterpreted function call, and the names mapping.
       """

    @classmethod
    def nodes_as_function_calls(cls, nodes: Iterable[Node], inputs_string: str, non_gates_names: Container[str], 
                                functional_nodes_names: set = None, *, get_mapping: bool = False):
        """@authors: Marco Biasion"""

        # copute updated names
        updated_names: Mapping[str, str] = {
            name: name if (name in non_gates_names or (functional_nodes_names and not(name in functional_nodes_names))) else f'{name}({inputs_string})'
            for name in cls._all_names(nodes)
        }

        # node conversion
        nodes = tuple(
            (
                node.copy(name=updated_names[node.name], operands=(updated_names[name] for name in node.operands))
                if isinstance(node, Operation) else
                node.copy(name=updated_names[node.name])
            )
            for node in nodes
        )

        #
        if get_mapping: return (nodes, updated_names)
        else: return nodes

    @classmethod
    def graph_as_function_calls(cls, graph: Union[IOGraph, PGraph, CGraph],
                                inputs_string: str,
                                non_gates_names: Container[str],
                                functional_nodes_names: set = None):
        """
            Given a graph in input, returns a new graph with all nodes updated
            to have their name being the equivalent z3 uninterpreted function call.

            @authors: Marco Biasion
        """

        nodes, updated_names = cls.nodes_as_function_calls(
            graph.nodes, inputs_string, non_gates_names,
            functional_nodes_names, get_mapping=True
        )

        # update extras (if needed)
        extra = dict()
        if isinstance(graph, IOGraph): extra['outputs_names'] = (updated_names[name] for name in graph.outputs_names)

        return graph.copy(nodes, **extra)
    
    @classmethod
    def inject_gates_functions(cls, 
                               graphs: Solver._Graphs,
                               destination: IO[str], 
                               inputs_names: Sequence[str],
                               type_mapping: Mapping[Type[Union[int, bool]], Callable[[Sequence[Any]], str]], 
                               nodes_types: Mapping[str, type],
                               accessories: Callable[[Node], Sequence[Any]],
                               functional_nodes_names: set = None) -> None:
        function_string = f'{{name}} = Function(\'{{name}}\', {", ".join(("BoolSort()",) * len(inputs_names))}, {{sort}})'
        destination.write('\n'.join((
            '# nodes (circuits and constraints)',
            *(
                function_string.format(name=node.name, sort=type_mapping[nodes_types[node.name]](accessories(node)))
                for graph in graphs
                for node in graph.expressions
                if (not functional_nodes_names) or (node.name in functional_nodes_names)
            ),
            *('',) * 2,
        )))

    @classmethod
    def inject_nodes_behavior(cls,
                              nodes: Sequence[AnyExpression],
                              destination: IO[str],
                              node_mapping: Mapping[Type[Node], Callable[[Union[Node, Operation, Valued], Sequence[str], Sequence[Any]], str]],
                              accessories: Callable[[Node], Sequence[Any]]) -> None:
        destination.write('\n'.join((
            '# behaviour',
            'behaviour = And(',
            *(
                f'    {node.name} == {node_mapping[type(node)](node, node.operands, accessories(node))},'
                for node in nodes
            ),
            ')',
            *('',) * 2,
        )))

    @classmethod
    def encode(cls, graphs: Solver._Graphs,
               destination: IO[str],
               global_task: Union[ForAll, Min, Max, None] = None,
               **_,
               ) -> None:

        # initial computations
        node_mapping = cls.node_mapping
        type_mapping = cls.type_mapping
        solver_construct = cls.solver_construct
        constraint_assertion = cls.constraints_assertion
        (graphs, inputs_names, parameters_names, nodes_types, accessories) = cls.simplification_and_accessories(graphs)

        # create call graphs (graphs where each node name has been replaced with the relative function call)
        inputs_string = ','.join(inputs_names)
        non_gates_names = frozenset(it.chain(
            (n.name for g in graphs for n in g.variables),
            (n.name for g in graphs for n in g.constants),
            (t.name for g in graphs if isinstance(g, CGraph) for t in g.targets),
        ))
        call_graphs = tuple(
            cls.graph_as_function_calls(graph, inputs_string, non_gates_names)
            for graph in graphs
        )
        # update global_task if present (mainly useful for operands)
        if global_task:
            global_task = cls.nodes_as_function_calls([global_task], inputs_string, non_gates_names)[0]

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
        cls.inject_gates_functions(graphs, destination, inputs_names, type_mapping, nodes_types, accessories)

        # nodes behavior
        nodes = tuple(
            node
            for graph in call_graphs
            for node in graph.expressions
        )
        cls.inject_nodes_behavior(nodes, destination, node_mapping, accessories)

        # nodes usage
        cls.inject_nodes_usage(call_c_graphs, destination)

        # solver
        cls.inject_solver(destination, global_task, solver_construct, constraint_assertion, ['behaviour', 'usage'])

        # results
        cls.inject_solve_and_result_writing(destination, graphs, call_graphs)


class Z3DirectEncoder(Z3Encoder):
    """
        Z3 encoder using the direct definition approach.

        @authors: Marco Biasion
    """

    @classmethod
    def inject_nodes_behavior(cls,
                              nodes: Sequence[AnyExpression],
                              destination: IO[str],
                              node_mapping: Mapping[Type[Node], Callable[[Union[Node, Operation, Valued], Sequence[str], Sequence[Any]], str]],
                              accessories: Callable[[Node], Sequence[Any]]) -> None:
        destination.write('\n'.join((
            '# behaviour',
            *(
                f'{node.name} = {node_mapping[type(node)](node, node.operands, accessories(node))}'
                for node in nodes
            ),
            *('',) * 2,
        )))

    @classmethod
    def encode(cls, graphs: Solver._Graphs,
               destination: IO[str],
               global_task: Union[ForAll, Min, Max, None] = None,
               **_,
               ) -> None:

        # initial computations
        node_mapping = cls.node_mapping
        type_mapping = cls.type_mapping
        solver_construct = cls.solver_construct
        constraint_assertion = cls.constraints_assertion
        (graphs, inputs_names, parameters_name, nodes_types, accessories) = cls.simplification_and_accessories(graphs)

        # initialization
        cls.inject_initialization(destination)

        # variables
        cls.inject_variables(destination, graphs, accessories)

        # constants
        cls.inject_constants(destination, graphs, accessories)

        # nodes behavior
        nodes = tuple(
            node
            for graph in graphs
            for node in graph.expressions
        )
        cls.inject_nodes_behavior(nodes, destination, node_mapping, accessories)

        # nodes usage
        c_graphs = tuple(graph for graph in graphs if isinstance(graph, CGraph))
        cls.inject_nodes_usage(c_graphs, destination)

        # solver
        cls.inject_solver(destination, global_task, solver_construct, constraint_assertion, ['usage'])

        # results
        cls.inject_solve_and_result_writing(destination, graphs, graphs)

class Z3HybridEncoder(Z3Encoder):
    """
        Z3 encoder using the hybrid approach between the direct and the functional ones.

        @authors: Ilia Zeller
    """
    
    @classmethod
    def node_name(cls, node: AnyExpression) -> str:
        return (re.split("\(", node.name))[0]

    @classmethod
    def inject_nodes_behavior(cls,
                              graphs: Solver._Graphs, 
                              destination: IO[str], 
                              node_mapping: Mapping[Type[Node], Callable[[Union[Node, Operation, Valued], Sequence[str], Sequence[Any]], str]], 
                              accessories: Callable[[Node], Sequence[Any]], 
                              functional_nodes_names: set) -> None:
        """
            Wrapper that splits up (in order) the nodes needing the method coming from Z3DirectEncoder
            and the nodes needing the method coming from Z3FuncEncoder.
        """
        nodes = []
        for graph in graphs:
            for node in graph.expressions:
                if cls.node_name(node) in functional_nodes_names and (len(nodes) == 0 or cls.node_name(nodes[-1]) in functional_nodes_names):
                    nodes.append(node)
                elif not(cls.node_name(node) in functional_nodes_names) and (len(nodes) == 0 or not(cls.node_name(nodes[-1]) in functional_nodes_names)):
                    nodes.append(node)
                elif cls.node_name(nodes[-1]) in functional_nodes_names:
                    Z3FuncEncoder.inject_nodes_behavior(nodes, destination, node_mapping, accessories)
                    nodes = [node]
                else:
                    Z3DirectEncoder.inject_nodes_behavior(nodes, destination, node_mapping, accessories)
                    nodes = [node]
        if len(nodes) > 0:
            if cls.node_name(nodes[-1]) in functional_nodes_names:
                Z3FuncEncoder.inject_nodes_behavior(nodes, destination, node_mapping, accessories)
            else:
                Z3DirectEncoder.inject_nodes_behavior(nodes, destination, node_mapping, accessories)

    @classmethod
    def encode(cls, graphs: Solver._Graphs,
               destination: IO[str],
               global_task: Union[ForAll, Min, Max, None] = None,
               *, 
               functional_nodes_names: set,
               **_,
               ) -> None:

        # initial computations
        node_mapping = cls.node_mapping
        type_mapping = cls.type_mapping
        solver_construct = cls.solver_construct
        constraint_assertion = cls.constraints_assertion
        (graphs, inputs_names, parameters_name, nodes_types, accessories) = cls.simplification_and_accessories(graphs)

        # create call graphs (graphs where each node name has been replaced with the relative function call)
        inputs_string = ','.join(inputs_names)
        non_gates_names = frozenset(it.chain(
            (n.name for g in graphs for n in g.variables),
            (n.name for g in graphs for n in g.constants),
            (t.name for g in graphs if isinstance(g, CGraph) for t in g.targets),
        ))
        call_graphs = tuple(
            Z3FuncEncoder.graph_as_function_calls(graph, inputs_string, non_gates_names)
            for graph in graphs
        )
        hybrid_graphs = tuple(
            Z3FuncEncoder.graph_as_function_calls(graph, inputs_string, non_gates_names, functional_nodes_names)
            for graph in graphs
        )
        # update global_task if present (mainly useful for operands)
        if global_task:
            global_task = Z3FuncEncoder.nodes_as_function_calls([global_task], inputs_string, non_gates_names, functional_nodes_names)[0]

        # gather constraints graphs
        call_c_graphs = tuple(graph for graph in call_graphs if isinstance(graph, CGraph))

        # initialization
        cls.inject_initialization(destination)

        # variables
        cls.inject_variables(destination, graphs, accessories)

        # constants
        cls.inject_constants(destination, graphs, accessories)

        # gates functions
        Z3FuncEncoder.inject_gates_functions(graphs, destination, inputs_names, type_mapping, nodes_types, accessories, functional_nodes_names)

        # nodes behavior
        cls.inject_nodes_behavior(hybrid_graphs, destination, node_mapping, accessories, functional_nodes_names)

        # nodes usage
        hybrid_c_graphs = tuple(graph for graph in hybrid_graphs if isinstance(graph, CGraph))
        cls.inject_nodes_usage(hybrid_c_graphs, destination)

        # solver
        cls.inject_solver(destination, global_task, solver_construct, constraint_assertion, ['behaviour', 'usage'])

        # results
        cls.inject_solve_and_result_writing(destination, graphs, hybrid_graphs)


# Node to Z3 expression
Z3_INT_NODE_MAPPING = {
    # variables
    BoolVariable: lambda n, operands, accs: f'Bool(\'{n.name}\')',
    IntVariable: lambda n, operands, accs: f'Int(\'{n.name}\')',
    # constants
    BoolConstant: lambda n, operands, accs: f'BoolVal({n.value})',
    IntConstant: lambda n, operands, accs: f'IntVal({n.value})',
    # output
    Identity: lambda n, operands, accs: operands[0],
    Target: lambda n, operands, accs: operands[0],
    # placeholder
    PlaceHolder: lambda n, operands, accs: n.name,
    # boolean operations
    Not: lambda n, operands, accs: f'Not({operands[0]})',
    And: lambda n, operands, accs: f'And({", ".join(operands)})',
    Or: lambda n, operands, accs: f'Or({", ".join(operands)})',
    Xor: lambda n, operands, accs: f'({operands[0]} != {operands[1]})',
    Xnor: lambda n, operands, accs: f'({operands[0]} == {operands[1]})',
    Implies: lambda n, operands, accs: f'Implies({operands[0]}, {operands[1]})',
    # integer operations
    Sum: lambda n, operands, accs: f'Sum({", ".join(operands)})',
    AbsDiff: lambda n, operands, accs: f'If({operands[0]} >= {operands[1]}, {operands[0]} - {operands[1]}, {operands[1]} - {operands[0]})',
    Mul: lambda n, operands, accs: f'{" * ".join(operands)}',
    Div: lambda n, operands, accs: f'({operands[0]} / {operands[1]})',
    # comparison operations
    Equals: lambda n, operands, accs: f'({operands[0]} == {operands[1]})',
    NotEquals: lambda n, operands, accs: f'({operands[0]} != {operands[1]})',
    LessThan: lambda n, operands, accs: f'({operands[0]} < {operands[1]})',
    LessEqualThan: lambda n, operands, accs: f'({operands[0]} <= {operands[1]})',
    GreaterThan: lambda n, operands, accs: f'({operands[0]} > {operands[1]})',
    GreaterEqualThan: lambda n, operands, accs: f'({operands[0]} >= {operands[1]})',
    # quantifier operations
    AtLeast: lambda n, operands, accs: f'AtLeast({", ".join(operands)}, {n.value})',
    AtMost: lambda n, operands, accs: f'AtMost({", ".join(operands)}, {n.value})',
    # branching operations
    Multiplexer: lambda n, operands, accs: f'If({operands[1]}, If({operands[2]}, {operands[0]}, Not({operands[0]})), {operands[2]})',
    If: lambda n, operands, accs: f'If({operands[0]}, {operands[1]}, {operands[2]})',
}
Z3_BITVEC_NODE_MAPPING = {
    **Z3_INT_NODE_MAPPING,
    # variables
    IntVariable: lambda n, operands, accs: f'BitVec(\'{n.name}\', {accs[0]})',
    # constants
    IntConstant: lambda n, operands, accs: f'BitVecVal({n.value}, {accs[0]})',
    # integer operations
    AbsDiff: lambda n, operands, accs: f'If(UGE({operands[0]}, {operands[1]}), {operands[0]} - {operands[1]}, {operands[1]} - {operands[0]})',
    Div: lambda n, operands, accs: f'UDiv({operands[0]}, {operands[1]})',
    # comparison operations
    Equals: lambda n, operands, accs: f'({operands[0]} == {operands[1]})',
    LessThan: lambda n, operands, accs: f'ULT({operands[0]}, {operands[1]})',
    LessEqualThan: lambda n, operands, accs: f'ULE({operands[0]}, {operands[1]})',
    GreaterThan: lambda n, operands, accs: f'UGT({operands[0]}, {operands[1]})',
    GreaterEqualThan: lambda n, operands, accs: f'UGE({operands[0]}, {operands[1]})',
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
Z3_INT_SOLVER_CONSTRUCT = {
    type(None): 'Solver()',  # 'SolverFor(\'LIA\')',
    ForAll: 'Solver()',  # 'SolverFor(\'LIA\')',
    Min: 'Optimize()',
    Max: 'Optimize()',
}
Z3_BITVEC_SOLVER_CONSTRUCT = {
    **Z3_INT_SOLVER_CONSTRUCT,
    #
    type(None): 'SolverFor(\'BV\')',
    ForAll: 'SolverFor(\'BV\')',
}

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

class Z3HybridIntEncoder(Z3HybridEncoder):
    node_mapping = Z3_INT_NODE_MAPPING
    type_mapping = Z3_INT_TYPE_MAPPING
    solver_construct = Z3_INT_SOLVER_CONSTRUCT
    node_accessories = Z3_INT_NODE_ACCESSORIES

class Z3HybridBitVecEncoder(Z3HybridEncoder):
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
    @override
    def solve_exists(cls, graphs: Solver._Graphs,
                     specifications: Specifications,
                     **kwargs,
                     ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        return cls._z3_solve(graphs, specifications, None, **kwargs)

    @classmethod
    @override
    def solve_forall(cls, graphs: Solver._Graphs,
                     specifications: Specifications,
                     forall_task: ForAll,
                     **kwargs,
                     ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        return cls._z3_solve(graphs, specifications, forall_task, **kwargs)

    @classmethod
    @override
    def solve_optimize(cls, graphs: Solver._Graphs,
                       specifications: Specifications,
                       optimize_task: Union[Min, Max],
                       **kwargs,
                       ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        return cls._z3_solve(graphs, specifications, optimize_task, **kwargs)

    @classmethod
    @override
    def solve_optimize_forall(cls, graphs: Solver._Graphs,
                              specifications: Specifications,
                              optimize_target: Union[Min, Max],
                              forall_target: ForAll,
                              **kwargs,
                              ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        # NOTE: the override here is used to remove unnecessary warning,
        #       as the default iterative approach is the correct one for this solver
        return cls._solve_optimize_forall_iterative(graphs, specifications, optimize_target, forall_target, **kwargs)

    @classmethod
    def _z3_solve(cls, graphs: Solver._Graphs,
                  specifications: Specifications,
                  global_task: Union[ForAll, Min, Max, None],
                  **kwargs,
                  ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:

        script_path = path_join(specifications.path.run.solver_scripts, f'iter{specifications.iteration}_{specifications.sub_iteration}.py')

        # encode
        with open(script_path, 'w') as f: cls.encoder.encode(graphs, f, global_task, **kwargs)

        # run
        raw_result = cls._run_script(script_path)

        # decode
        return cls._decode_output(raw_result)

    @classmethod
    def _run_script(cls, script_path: str) -> str:
        """
            Given the file path, run the python script and return the standard output.
        """

        # run
        process = subprocess.run(
            [sxpat_cfg.PYTHON3, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if process.returncode != 0:
            raise RuntimeError(f'Solver execution FAILED. Failed to run file {script_path}')

        # return decoded output
        return process.stdout.decode()

    @classmethod
    def _decode_output(cls, raw_result: str) -> Tuple[str, Optional[Dict[str, Union[bool, int]]]]:
        """
            Given the raw result, returns the contained status and model.
        """

        # documentation: the result is not saved to a json for multiple models and so on.
        #                each Solver.solve call must return at most one model.
        #                the timing must be computed at a higher level, same with the multimodel logic.
        #                the new format is as follows:
        # example sat:
        # sat\n
        # p_somebool True\n
        # p_somemorebool False\n
        # p_someint 1\n
        # p_somemoreint 7\n
        #
        # example unsat (all are the same):
        # unsat\n
        #
        # example unknown (all are the same):
        # unknown\n
        #

        # split status and model
        status, *raw_model = raw_result.splitlines()

        # parse model
        model = None
        if status == 'sat':
            model = {
                (splt := pair.split(' '))[0]: str_to_int_or_bool(splt[1])
                for pair in raw_model
            }

        # return decoded result
        return (status, model)


class Z3FuncIntSolver(Z3Solver):
    encoder = Z3IntFuncEncoder


class Z3FuncBitVecSolver(Z3Solver):
    encoder = Z3BitVecFuncEncoder


class Z3DirectIntSolver(Z3Solver):
    encoder = Z3DirectIntEncoder


class Z3DirectBitVecSolver(Z3Solver):
    encoder = Z3DirectBitVecEncoder

class Z3HybridIntSolver(Z3Solver):
    encoder = Z3HybridIntEncoder

class Z3HybridBitVecSolver(Z3Solver):
    encoder = Z3HybridBitVecEncoder