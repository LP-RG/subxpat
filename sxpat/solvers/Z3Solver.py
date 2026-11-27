from typing import IO, Any, Callable, Container, Dict, Iterable, Iterator, Mapping, Optional, Sequence, Tuple, Type, Union, overload, override
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
from sxpat.graph.components import IO, Parameter


__all__ = [
    'Z3FuncIntSolver', 'Z3FuncBitVecSolver',
    'Z3DirectIntSolver', 'Z3DirectBitVecSolver',
]


@make_utility_class
class Z3Encoder:
    """
    Base class for Z3 encoders, including some common functions.

    :authors: Marco Biasion, Ilia Zeller
    """

    node_mapping: Mapping[Type[Node], Callable[[Union[Node, Operation, Valued], Graph, Sequence[str], Sequence[Any]], str]]
    type_mapping: Mapping[Type[Union[int, bool]], Callable[[Sequence[Any]], str]]
    solver_construct: Mapping[Type[Union[ForAll, Min, Max, None]], str]
    node_accessories: Callable[[Sequence[Any]], Callable[[Node], Sequence[Any]]]

    constraints_assertion: Mapping[Type[Union[ForAll, Min, Max, None]], Callable[[str, Union[list[str], str, None], Sequence[str]], Sequence[str]]] = {
        type(None): lambda solver_name, global_task_operands, assertions: [
            f'{solver_name}.add(',
            *(f'    {a},' for a in assertions),
            f')',
        ],
        ForAll: lambda solver_name, global_task_operands, assertions: [
            f'{solver_name}.add(',
            f'    ForAll(',
            f'        [{",".join(global_task_operands)}],',
            f'        And(',
            *(f'            {a},' for a in assertions),
            f'        )',
            f'    )',
            f')',
        ],
        Min: lambda solver_name, global_task_operands, assertions: [
            f'{solver_name}.add(',
            *(f'    {a},' for a in assertions),
            f')',
            f'{solver_name}.minimize({global_task_operands})',
        ],
        Max: lambda solver_name, global_task_operands, assertions: [
            f'{solver_name}.add(',
            *(f'    {a},' for a in assertions),
            f')',
            f'{solver_name}.maximize({global_task_operands})',
        ],
    }

    @classmethod
    @abstractmethod
    def encode(cls, graphs: Solver._Graphs,
               destination: IO[str],
               global_task: Union[ForAll, Min, Max, None] = None,
               global_targets_mapping: dict[str, Graph] | None = None,
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

        # extract graph inputs (each Graph should have the same inputs_names)
        found_inputs_names = set(graph.base_components['IO'].inputs_names for graph in graphs if graph.has_base_component('IO'))
        if len(found_inputs_names) == 0: raise ValueError('No Graph was given to the Solver module.')
        elif len(found_inputs_names) >= 2: raise ValueError('The inputs of the Graphs given to the Solver module did not match.')

        parameters_names = tuple(it.chain.from_iterable(
            graph.base_components['Parameter'].parameters_names
            for graph in graphs if graph.has_base_component('Parameter')
        ))

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
            node.name: graph
            for graph in graphs
            for node in graph.nodes
            if graph.base_components['Types'].instance_of(node, [Variable])
        }
        destination.write('\n'.join((
            '# variables (inputs, parameters)',
            *(
                f'{name} = {cls.node_mapping[type(graph[name])](graph[name], graph, None, accessories(graph[name]))}'
                for (name, graph) in variables.items()
            ),
            *('',) * 2,
        )))

    @classmethod
    def inject_constants(cls, destination: IO[str], graphs: Solver._Graphs,
                         accessories: Callable[[Node], Sequence[Any]]) -> None:
        constants = {  # ignore duplicates
            node.name: graph
            for graph in graphs
            for node in graph.nodes
            if graph.base_components['Types'].instance_of(node, [Constant])
        }
        destination.write('\n'.join((
            '# constants',
            *(
                f'{name} = {cls.node_mapping[type(graph[name])](graph[name], graph, None, accessories(graph[name]))}'
                for (name, graph) in constants.items()
            ),
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
                f'    print(\'{n_graph.base_components['Topology'].operand(n_target)}\', model.eval({v_graph.base_components['Topology'].operand(v_target)}, model_completion=True))'
                for (n_graph, v_graph) in zip(name_graphs, value_graphs)
                for (n_target, v_target) in zip(n_graph.targets, v_graph.targets)
            ),
            *('',) * 2,
        )))


class Z3FuncEncoder(Z3Encoder):
    """
    Z3 encoder using the uninterpreted functions approach.

    :authors: Marco Biasion, Ilia Zeller
    """

    @staticmethod
    def _all_names(nodes: Iterable[Node], graph: Graph) -> Iterator[str]:
        topology_component = graph.base_components['Topology']
        seen_names = set()
        for node in nodes:
            if node.name not in seen_names:
                seen_names.add(node.name)
                yield node.name
            if isinstance(node, Operation):
                for name in topology_component.operands(node):
                    if name not in seen_names:
                        seen_names.add(name)
                        yield name

    # @classmethod
    # @overload
    # def nodes_as_function_calls(cls, nodes: Iterable[Node], inputs_string: str, non_gates_names: Container[str]
    #                             ) -> Sequence[Node]:
    #     """
    #     Given a sequence of nodes in input, returns a new sequence with all nodes updated
    #     to have their name being the equivalent z3 uninterpreted function call.
    #     """

    # @classmethod
    # @overload
    # def nodes_as_function_calls(cls, nodes: Iterable[Node], inputs_string: str, non_gates_names: Container[str],
    #                             *, get_mapping: Literal[True]
    #                             ) -> Tuple[Sequence[Node], Mapping[str, str]]:
    #     """
    #     Given a sequence of nodes in input, returns a new sequence with all nodes updated
    #     to have their name being the equivalent z3 uninterpreted function call, and the names mapping.
    #     """

    @classmethod
    def nodes_names_as_function_calls(cls, 
                                      nodes: Iterable[Node], 
                                      graph: Graph,
                                      inputs_string: str, 
                                      non_gates_names: Container[str]) -> Mapping[str, str]:
        """
        Given a sequence of nodes in input, returns a mapping between their old names their updated
        names, to have the updated names being the equivalent z3 uninterpreted function calls.

        :authors: Marco Biasion, Ilia Zeller
        """

        # compute updated names
        updated_names: Mapping[str, str] = {
            name: name if name in non_gates_names else f'{name}({inputs_string})'
            for name in cls._all_names(nodes, graph)
        }

        return updated_names

    @classmethod
    def graph_as_function_calls(cls, graph: Graph,
                                inputs_string: str,
                                non_gates_names: Container[str]):
        """
        Given a graph in input, returns a new graph with all nodes updated
        to have their name being the equivalent z3 uninterpreted function call.

        :authors: Marco Biasion
        """

        updated_names = cls.nodes_names_as_function_calls(
            graph.nodes, graph, inputs_string, non_gates_names
        )

        graph_copier = GraphCopier(graph)
        types_component = graph.base_components['Types']
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

        topology_component = graph.base_components['Topology']
        for node in graph.nodes:
            if types_component.instance_of(node.name, [Operation]):
                operands=[updated_names[name] for name in topology_component.operands(node.name)]
                graph_copier.add_node_copy(
                    node,
                    name=updated_names[node.name],
                    operands=operands
                )
            else:
                graph_copier.add_node_copy(
                    node,
                    name=updated_names[node.name]
                )
        
        return graph_copier.copy()

    @classmethod
    def encode(cls, graphs: Solver._Graphs,
               destination: IO[str],
               global_task: Union[ForAll, Min, Max, None] = None,
               global_tasks_mapping: dict[str, Graph] | None = None,
               ) -> None:

        # initial computations
        assert((global_task is None) == (global_tasks_mapping is None)) # global_task has to be passed together with the global tasks graphs mapping
        global_task_graph: Graph | None = None
        global_task_operands: list[str] | str | None = None
        if global_task:
            global_task_graph = global_tasks_mapping[global_task.name]
            if type(global_task) == ForAll:
                global_task_operands = global_task_graph.base_components['Topology'].operands(global_task)
            else:
                global_task_operands = global_task_graph.base_components['Topology'].operand(global_task)
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
            (t.name for g in graphs if g.has_base_component('Constraints') for t in g.targets),
        ))
        call_graphs = tuple(
            cls.graph_as_function_calls(graph, inputs_string, non_gates_names)
            for graph in graphs
        )
        # update global_task if present (mainly useful for operands)
        if global_task:
            updated_names = cls.nodes_names_as_function_calls([global_task], global_task_graph, inputs_string, non_gates_names)
            global_task = type(global_task)(name=updated_names[global_task.name])
            new_operands = [
                updated_names[old_name]
                for old_name in list(global_task_operands)
            ]
            global_task_operands = new_operands if len(new_operands) > 1 else new_operands[0]

        # gather constraints graphs
        c_graphs = tuple(graph for graph in graphs if graph.has_base_component('Constraints'))
        call_c_graphs = tuple(graph for graph in call_graphs if graph.has_base_component('Constraints'))

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
                for node in graph.expressions
            ),
            *('',) * 2,
        )))

        # nodes behavior
        destination.write('\n'.join((
            '# behaviour',
            'behaviour = And(',
            *(
                f'    {node.name} == {node_mapping[type(node)](node, call_graph, call_graph.base_components['Topology'].operands(node), accessories(node))},'
                for call_graph in call_graphs
                for node in call_graph.expressions
            ),
            ')',
            *('',) * 2,
        )))

        # nodes usage
        destination.write('\n'.join((
            '# usage',
            'usage = And(', *(
                f'    {call_graph.base_components['Topology'].operand(constraint_node)},'
                for call_graph in call_c_graphs
                for constraint_node in call_graph.base_components['Constraints'].constraints
            ), ')',
            *('',) * 2,
        )))

        # solver
        destination.write('\n'.join((
            f'# define solver',
            f'solver = {solver_construct[type(global_task)]}',
            *constraint_assertion[type(global_task)]('solver', global_task_operands, ['behaviour', 'usage']),
            *('',) * 2,
        )))

        # results
        cls.inject_solve_and_result_writing(destination, graphs, call_graphs)


class Z3DirectEncoder(Z3Encoder):
    """
    Z3 encoder using the direct definition approach.

    :authors: Marco Biasion, Ilia Zeller
    """

    @classmethod
    def encode(cls, graphs: Solver._Graphs,
               destination: IO[str],
               global_task: Union[ForAll, Min, Max, None] = None,
               global_tasks_mapping: dict[str, Graph] | None = None,
               ) -> None:

        # initial computations
        assert((global_task is None) == (global_tasks_mapping is None)) # global_task has to be passed together with the global tasks graphs mapping
        global_task_graph: Graph | None = None
        global_task_operands: list[str] | str | None = None
        if global_task:
            global_task_graph = global_tasks_mapping[global_task.name]
            if type(global_task) == ForAll:
                global_task_operands = global_task_graph.base_components['Topology'].operands(global_task)
            else:
                global_task_operands = global_task_graph.base_components['Topology'].operand(global_task)
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
        destination.write('\n'.join((
            '# behaviour',
            *(
                f'{node.name} = {node_mapping[type(node)](node, graph, graph.base_components['Topology'].operands(node), accessories(node))}'
                for graph in graphs
                for node in graph.expressions
            ),
            *('',) * 2,
        )))

        # nodes usage
        destination.write('\n'.join((
            '# usage',
            'usage = And(', *(
                f'    {graph.base_components['Topology'].operand(constraint_node)},'
                for graph in graphs
                if graph.has_base_component('Constraints')
                for constraint_node in graph.base_components['Constraints'].constraints
            ), ')',
            *('',) * 2,
        )))

        # solver
        destination.write('\n'.join((
            f'# define solver',
            f'solver = {solver_construct[type(global_task)]}',
            *constraint_assertion[type(global_task)]('solver', global_task_operands, ['usage']),
            *('',) * 2,
        )))

        # results
        cls.inject_solve_and_result_writing(destination, graphs, graphs)


# Node to Z3 expression
Z3_INT_NODE_MAPPING = {
    # variables
    BoolVariable: lambda n, g, operands, accs: f'Bool(\'{n.name}\')',
    IntVariable: lambda n, g, operands, accs: f'Int(\'{n.name}\')',
    # constants
    BoolConstant: lambda n, g, operands, accs: f'BoolVal({g.base_components['Values'].get(n)})',
    IntConstant: lambda n, g, operands, accs: f'IntVal({g.base_components['Values'].get(n)})',
    # output
    Identity: lambda n, g, operands, accs: operands[0],
    Target: lambda n, g, operands, accs: operands[0],
    # placeholder
    PlaceHolder: lambda n, g, operands, accs: n.name,
    # boolean operations
    Not: lambda n, g, operands, accs: f'Not({operands[0]})',
    And: lambda n, g, operands, accs: f'And({", ".join(operands)})',
    Or: lambda n, g, operands, accs: f'Or({", ".join(operands)})',
    Xor: lambda n, g, operands, accs: f'({operands[0]} != {operands[1]})',
    Xnor: lambda n, g, operands, accs: f'({operands[0]} == {operands[1]})',
    Implies: lambda n, g, operands, accs: f'Implies({operands[0]}, {operands[1]})',
    # integer operations
    Sum: lambda n, g, operands, accs: f'Sum({", ".join(operands)})',
    AbsDiff: lambda n, g, operands, accs: f'If({operands[0]} >= {operands[1]}, {operands[0]} - {operands[1]}, {operands[1]} - {operands[0]})',
    Mul: lambda n, g, operands, accs: f'{" * ".join(operands)}',
    Div: lambda n, g, operands, accs: f'({operands[0]} / {operands[1]})',
    # comparison operations
    Equals: lambda n, g, operands, accs: f'({operands[0]} == {operands[1]})',
    NotEquals: lambda n, g, operands, accs: f'({operands[0]} != {operands[1]})',
    LessThan: lambda n, g, operands, accs: f'({operands[0]} < {operands[1]})',
    LessEqualThan: lambda n, g, operands, accs: f'({operands[0]} <= {operands[1]})',
    GreaterThan: lambda n, g, operands, accs: f'({operands[0]} > {operands[1]})',
    GreaterEqualThan: lambda n, g, operands, accs: f'({operands[0]} >= {operands[1]})',
    # quantifier operations
    AtLeast: lambda n, g, operands, accs: f'AtLeast({", ".join(operands)}, {g.base_components['Values'].get(n)})',
    AtMost: lambda n, g, operands, accs: f'AtMost({", ".join(operands)}, {g.base_components['Values'].get(n)})',
    # branching operations
    Multiplexer: lambda n, g, operands, accs: f'If({operands[1]}, If({operands[2]}, {operands[0]}, Not({operands[0]})), {operands[2]})',
    If: lambda n, g, operands, accs: f'If({operands[0]}, {operands[1]}, {operands[2]})',
}
Z3_BITVEC_NODE_MAPPING = {
    **Z3_INT_NODE_MAPPING,
    # variables
    IntVariable: lambda n, g, operands, accs: f'BitVec(\'{n.name}\', {accs[0]})',
    # constants
    IntConstant: lambda n, g, operands, accs: f'BitVecVal({g.base_components['Values'].get(n)}, {accs[0]})',
    # integer operations
    AbsDiff: lambda n, g, operands, accs: f'If(UGE({operands[0]}, {operands[1]}), {operands[0]} - {operands[1]}, {operands[1]} - {operands[0]})',
    Div: lambda n, g, operands, accs: f'UDiv({operands[0]}, {operands[1]})',
    # comparison operations
    Equals: lambda n, g, operands, accs: f'({operands[0]} == {operands[1]})',
    LessThan: lambda n, g, operands, accs: f'ULT({operands[0]}, {operands[1]})',
    LessEqualThan: lambda n, g, operands, accs: f'ULE({operands[0]}, {operands[1]})',
    GreaterThan: lambda n, g, operands, accs: f'UGT({operands[0]}, {operands[1]})',
    GreaterEqualThan: lambda n, g, operands, accs: f'UGE({operands[0]}, {operands[1]})',
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


class Z3Solver(Solver):
    """
    Base class for solving using z3, implements all logic but the encoding.

    :authors: Marco Biasion
    """

    encoder: Type[Z3Encoder]

    @classmethod
    @override
    def solve_exists(cls, graphs: Solver._Graphs,
                     specifications: Specifications,
                     ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        return cls._z3_solve(graphs, specifications, None, None)

    @classmethod
    @override
    def solve_forall(cls, graphs: Solver._Graphs,
                     specifications: Specifications,
                     forall_target: ForAll,
                     global_targets_mapping: dict[str, Graph],
                     ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        return cls._z3_solve(graphs, specifications, forall_target, global_targets_mapping)

    @classmethod
    @override
    def solve_optimize(cls, graphs: Solver._Graphs,
                       specifications: Specifications,
                       optimize_target: Union[Min, Max],
                       global_targets_mapping: dict[str, Graph],
                       ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        return cls._z3_solve(graphs, specifications, optimize_target, global_targets_mapping)

    @classmethod
    @override
    def solve_optimize_forall(cls, graphs: Solver._Graphs,
                              specifications: Specifications,
                              optimize_target: Union[Min, Max],
                              forall_target: ForAll,
                              global_targets_mapping: dict[str, Graph],
                              ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        # NOTE: the override here is used to remove unnecessary warning,
        #       as the default iterative approach is the correct one for this solver
        return cls._solve_optimize_forall_iterative(graphs, specifications, optimize_target, forall_target, global_targets_mapping)

    @classmethod
    def _z3_solve(cls, graphs: Solver._Graphs,
                  specifications: Specifications,
                  global_task: Union[ForAll, Min, Max, None],
                  global_targets_mapping: dict[str, Graph] | None,
                  ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:

        script_path = path_join(specifications.path.run.solver_scripts,
                                f'iter{specifications.iteration}_{specifications.sub_iteration}.py')

        # encode
        with open(script_path, 'w') as f:
            cls.encoder.encode(graphs, f, global_task, global_targets_mapping)

        # run
        raw_result = cls._run_script(script_path)

        # decode
        return cls._decode_output(raw_result)

    @classmethod
    def _run_script(cls, script_path: str) -> str:
        """
        Run the given python script and return its standard output.
        """

        # run
        process = subprocess.run(
            ['python3', script_path],
            capture_output=True, text=True,
            check=True,
        )

        # return decoded output
        return process.stdout

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
