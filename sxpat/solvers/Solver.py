from typing import Mapping, Optional, Sequence, Tuple, Union, TypeVar, NamedTuple
from typing_extensions import final
from abc import abstractmethod, ABCMeta

from sxpat.graph import Graph, GraphBuilder
from sxpat.graph.node import ForAll, Max, Min, PlaceHolder, GlobalTask, GreaterThan, Identity, LessThan, PlaceHolder, Target, Constraint, IntConstant
from sxpat.specifications import Specifications
from sxpat.utils.decorators import make_utility_class

from sxpat.constants import SolverConstants as SC
from sxpat.utils.print import pprint
from sxpat.graph.components import Constraints


__all__ = [
    'Solver',
    'GlobalTasks',
]


class GlobalTasks(NamedTuple):
    optimize: Optional[Union[Min, Max]] = None
    forall: Optional[ForAll] = None


@make_utility_class
class Solver(metaclass=ABCMeta):
    """
    Guide: inheriting from `Solver`.

    The `Solver` super class has the following public methods:
    - `.solve(...)`: entry point to the solver. Will delegate the computation to one of the following methods.  
        This method is already implemented and is **final**.
    - `.solve_exists(...)`: solve non optimization and not forall quantified problems.  
        **Must** be overloaded when inheriting.
    - `solve_forall(...)`: solve forall quantified problems.  
        **Can** be overloaded but a default solver independent implementation is given.
    - `.solve_optimize(...)`: solve optimization problems.  
        **Can** be overloaded but a default solver independent implementation is given.
    - `.solve_optimize_forall(...)`: solve optimizations and forall quantified problems.  
        **Can** be overloaded but a default solver independent implementation is given.

    As stated in the list, the only method strictly required to be overloaded is `.solve_exists(...)`,
    as all others have a default implementation.

    To improve the performance of the solver being implemented,
    the other methods can be overloaded using solver specific features.

    Note that non overloaded methods will print a warning when used,
    to suppress this warning simply overload the method in your subclass
    using the internal call to the `protected` function.

    :authors: Marco Biasion
    """

    _Graphs = TypeVar('_Graphs', bound=Sequence[Union[Graph, Graph]])

    @classmethod
    @final
    def solve(cls, graphs: _Graphs,
              specifications: Specifications,
              *,
              _global_targets_with_mapping: Optional[Tuple[GlobalTasks, dict[str, Graph]]] = None,
              ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
        Solve the required problem defined by the given graphs.

        The supported graphs are:
        - Graph (and subclasses): for input variables (and local behaviour)
        - Graph (and subclasses): for applicable constraints

        Returns the status of the resolution (`sat`, `unsat`, `unknown`) and the model evaluated from the `Target` nodes if `sat`.

        :authors: Marco Biasion
        """

        # compute global targets if not already given
        if _global_targets_with_mapping is None:
            _global_targets, _global_targets_mapping, graphs = cls._pop_global_tasks(graphs)
        else:
            _global_targets = _global_targets_with_mapping[0]
            _global_targets_mapping = _global_targets_with_mapping[1]

        if _global_targets.optimize is not None and _global_targets.forall is not None:
            # solve an optimization and forall quantified problem
            return cls.solve_optimize_forall(
                graphs, specifications,
                _global_targets.optimize, _global_targets.forall,
                _global_targets_mapping,
            )
        elif _global_targets.optimize is not None and _global_targets.forall is None:
            # solve an optimization (not forall quantified) problem
            return cls.solve_optimize(
                graphs, specifications,
                _global_targets.optimize,
                _global_targets_mapping,
            )
        elif _global_targets.optimize is None and _global_targets.forall is not None:
            # solve a forall quantified (and non optimization) problem
            return cls.solve_forall(
                graphs, specifications,
                _global_targets.forall,
                _global_targets_mapping,
            )
        else:
            # solve a non optimization and not forall quantified problem.
            return cls.solve_exists(
                graphs, specifications,
            )

    @classmethod
    @abstractmethod
    def solve_exists(cls, graphs: _Graphs,
                     specifications: Specifications,
                     ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
        Solve a non optimization and not forall quantified problem.
        """
        raise NotImplementedError(f'{cls.__qualname__}.solve_exists(...) is not implemented')

    @classmethod
    def solve_forall(cls, graphs: _Graphs,
                     specifications: Specifications,
                     forall_target: ForAll,
                     global_targets_mapping: dict[str, Graph],
                     ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
        Solve a forall quantified (non optimization) problem.
        """
        pprint.warning(
            '[WARNING] using default (iterative) implementation'
            f' for {cls.__qualname__}.solve_forall(...)'
        )
        return cls._solve_forall(graphs, specifications, forall_target, global_targets_mapping)

    @classmethod
    def solve_optimize(cls, graphs: _Graphs,
                       specifications: Specifications,
                       optimize_target: Union[Min, Max],
                       global_targets_mapping: dict[str, Graph],
                       ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
        Solve an optimization (not forall quantified) problem.
        """
        pprint.warning(
            '[WARNING] using default (iterative) implementation'
            f' for {cls.__qualname__}.solve_optimize(...)'
        )
        return cls._solve_optimize_forall_iterative(graphs, specifications, optimize_target, None, global_targets_mapping)

    @classmethod
    def solve_optimize_forall(cls, graphs: _Graphs,
                              specifications: Specifications,
                              optimize_target: Union[Min, Max],
                              forall_target: ForAll,
                              global_targets_mapping: dict[str, Graph],
                              ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
        Solve an optimization and forall quantified problem.
        """
        pprint.warning(
            '[WARNING] using default (iterative) implementation'
            f' for {cls.__qualname__}.solve_optimize_forall(...)'
        )
        return cls._solve_optimize_forall_iterative(graphs, specifications, optimize_target, forall_target, global_targets_mapping)

    @classmethod
    @abstractmethod
    def _solve_forall(cls, graphs: _Graphs,
                      specifications: Specifications,
                      forall_target: ForAll,
                      global_targets_mapping: dict[str, Graph],
                      ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        # TODO: here we can implement the custom forall approach as for the initial implementations of XPAT (in year ~2021)
        raise NotImplementedError(f'{cls.__qualname__}._solve_forall(...) is work in progress')

    @classmethod
    @final
    def _solve_optimize_forall_iterative(cls, graphs: _Graphs,
                                         specifications: Specifications,
                                         optimize_target: Union[Min, Max],
                                         forall_target: Optional[ForAll],
                                         global_targets_mapping: dict[str, Graph],
                                         ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
        Solve an optimization (optionally forall quantified) problem iteratively without requiring solver specific features.

        :authors: Marco Biasion
        """
        optimize_target_operand = global_targets_mapping[optimize_target.name].base_components['Topology'].operand(optimize_target)
        # for graph in graphs:
        #     if any(optimize_target.name == n.name for n in graph.nodes):
        #         optimize_target_operand = graph.base_components['Topology'].operand(optimize_target)

        graph_builder = GraphBuilder()
        graph_builder.add_autofill_component('Constraints')

        # define common extra nodes
        # extra_nodes = (
        #     PlaceHolder(optimize_target_operand),
        #     Identity(SC.optimization.identity, operands=(optimize_target_operand,)),
        #     Target(SC.optimization.target, operands=(SC.optimization.identity,)),
        # )
        graph_builder.add_node(optimize_target_operand, PlaceHolder)
        graph_builder.add_node(SC.optimization.identity, Identity).add_operands([optimize_target_operand])
        graph_builder.add_node(SC.optimization.target, Target).add_operands([SC.optimization.identity])
        # define node class for the optimization comparison
        comparison_class = {
            Max: GreaterThan,
            Min: LessThan,
        }[type(optimize_target)]

        # iteratively optimize the value
        last_model = None
        previous_value = None
        while True:
            # define custom Constraints Graph with rules for the optimization
            if not previous_value is None:
                graph_builder.add_node(SC.optimization.constant, IntConstant).add_extras(value=previous_value)
                graph_builder.add_node(SC.optimization.rule, comparison_class).add_operands([SC.optimization.identity, SC.optimization.constant])
                graph_builder.add_node(SC.optimization.constraint, Constraint).add_operands([SC.optimization.rule])
            _graphs = (*graphs, graph_builder.create())

            # solve
            _global_targets = GlobalTasks(forall=forall_target)
            status, model = cls.solve(_graphs, specifications, _global_targets_with_mapping=(_global_targets, global_targets_mapping))

            # break if termination condition is reached
            if status == 'unknown': return ('unknown', None)
            if status == 'unsat': break

            # update previous value and model
            previous_value = model.pop(SC.optimization.identity)
            last_model = model

        # return the status and model
        if previous_value is None: return ('unsat', None)
        else: return ('sat', last_model)

    @classmethod
    @final
    def _pop_global_tasks(cls, graphs: _Graphs) -> Tuple[GlobalTasks,  dict[str, Graph], _Graphs]:
        """
        Pops all `GlobalTask` nodes from the graphs.

        Returns
            - `ForAll` and `Min`/`Max` nodes from the given graphs, if present.
            - Sequence of graphs where `Constraints Graphs` are updated/dropped based on their `GlobalTask` content (partial/only).

        :authors: Marco Biasion
        """

        _graphs = []
        _global_tasks = []
        _global_graphs_mapping: dict[str, Graph] = dict()
        for graph in graphs:
            types_component = graph.base_components['Types']
            if (not graph.has_base_component('Constraints')) or (len(graph.base_components['Constraints'].global_tasks) == 0):
                # nothing to extract
                # keep as-is if not a Constraints Graph or not containing any GlobalTask
                pass

            else:
                # extract tasks
                _global_tasks.extend(graph.base_components['Constraints'].global_tasks)
                for n in graph.base_components['Constraints'].global_tasks:
                    _global_graphs_mapping[n.name] = graph

                # drop graph if all nodes are GlobalTask and PlaceHolder
                if all(types_component.instance_of(n, [PlaceHolder, GlobalTask]) for n in graph.nodes):
                    continue

                # update Constraints Graph without GlobalTask (and relative PlaceHolder)
                else:
                    task_names = frozenset(n.name for n in graph.base_components['Constraints'].global_tasks)
                    placeholder_names = frozenset(
                        n.name for n in graph.base_components['Constraints'].placeholders
                        if len(succ := graph.successors(n)) == 1 and succ[0].name in task_names
                    )

                    graph_builder = GraphBuilder()
                    graph_builder.add_autofill_component('Constraints')
                    # graph_builder.add_inherited_nodes([
                    #     n 
                    #     for n in graph.nodes
                    #     if n.name not in task_names and n.name not in placeholder_names
                    # ], graph)
                    for n in graph.nodes:
                        if n.name not in task_names and n.name not in placeholder_names:
                            graph_builder.add_node_from(n, graph)

                    graph = graph_builder.create()

            _graphs.append(graph)

        # categorize tasks
        foralls = tuple(n for n in _global_tasks if isinstance(n, ForAll))
        optimizes = tuple(n for n in _global_tasks if isinstance(n, (Min, Max)))

        # guard for multiple forall quantifiers or multiple optimizations
        # NOTE: the check for the foralls could be removed, as we could treat multiple ForAll as a single ForAll with all the inputs
        if len(foralls) > 1: raise RuntimeError('Too many ForAll nodes in the graphs')
        if len(optimizes) > 1: raise RuntimeError('Too many Min/Max nodes in the graphs')

        return (
            GlobalTasks(
                optimize=(optimizes[0] if optimizes else None),
                forall=(foralls[0] if foralls else None),
            ),
            _global_graphs_mapping,
            tuple(_graphs)
        )
