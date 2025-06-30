from typing import Mapping, Optional, Sequence, Tuple, Union, TypeVar, NamedTuple
from typing_extensions import final
from abc import abstractmethod, ABCMeta

from sxpat.graph import IOGraph, PGraph, CGraph, ForAll, Max, Min, GreaterThan, Identity, LessThan, PlaceHolder, Target, Constraint, IntConstant, GlobalTask
from sxpat.specifications import Specifications
from sxpat.utils.decorators import make_utility_class

from sxpat.config import SolverConstants as SC
from sxpat.utils.print import pprint


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

        @authors: Marco Biasion
    """

    _Graphs = TypeVar('_Graphs', bound=Sequence[Union[IOGraph, PGraph, CGraph]])

    @classmethod
    @final
    def solve(cls, graphs: _Graphs,
              specifications: Specifications,
              *,
              __global_targets: GlobalTasks = None,
              ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve the required problem defined by the given graphs.

            The supported graphs are:
            - IOGraph (and subclasses): for input variables (and local behaviour)
            - PGraph (and subclasses): for parameter variables (and local behaviour)
            - CGraph (and subclasses): for applicable constraints

            Returns the status of the resolution (`sat`, `unsat`, `unknown`) and the model evaluated from the `Target` nodes if `sat`.

            @authors: Marco Biasion
        """

        # compute global targets if not already given
        if __global_targets is None:
            __global_targets, graphs = cls._pop_global_tasks(graphs)

        if __global_targets.optimize is not None and __global_targets.forall is not None:
            # solve an optimization and forall quantified problem
            return cls.solve_optimize_forall(
                graphs, specifications,
                __global_targets.optimize, __global_targets.forall,
            )
        elif __global_targets.optimize is not None and __global_targets.forall is None:
            # solve an optimization (not forall quantified) problem
            return cls.solve_optimize(
                graphs, specifications,
                __global_targets.optimize,
            )
        elif __global_targets.optimize is None and __global_targets.forall is not None:
            # solve a forall quantified (and non optimization) problem
            return cls.solve_forall(
                graphs, specifications,
                __global_targets.forall,
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
                     ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve a forall quantified (non optimization) problem.
        """
        pprint.warning(
            '[WARNING] using default (iterative) implementation'
            f' for {cls.__qualname__}.solve_forall(...)'
        )
        cls._solve_forall(graphs, specifications, forall_target)

    @classmethod
    def solve_optimize(cls, graphs: _Graphs,
                       specifications: Specifications,
                       optimize_target: Union[Min, Max],
                       ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve an optimization (not forall quantified) problem.
        """
        pprint.warning(
            '[WARNING] using default (iterative) implementation'
            f' for {cls.__qualname__}.solve_optimize(...)'
        )
        return cls._solve_optimize_forall_iterative(graphs, specifications, optimize_target, None)

    @classmethod
    def solve_optimize_forall(cls, graphs: _Graphs,
                              specifications: Specifications,
                              optimize_target: Union[Min, Max],
                              forall_target: ForAll,
                              ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve an optimization and forall quantified problem.
        """
        pprint.warning(
            '[WARNING] using default (iterative) implementation'
            f' for {cls.__qualname__}.solve_optimize_forall(...)'
        )
        return cls._solve_optimize_forall_iterative(graphs, specifications, optimize_target, forall_target)

    @classmethod
    @abstractmethod
    def _solve_forall(cls, graphs: _Graphs,
                      specifications: Specifications,
                      forall_target: ForAll,
                      ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        # TODO: here we can implement the custom forall approach as for the initial implementations of XPAT (in year ~2021)
        raise NotImplementedError(f'{cls.__qualname__}._solve_forall(...) is work in progress')

    @classmethod
    @final
    def _solve_optimize_forall_iterative(cls, graphs: _Graphs,
                                         specifications: Specifications,
                                         optimize_target: Union[Min, Max],
                                         forall_target: Optional[ForAll],
                                         ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve an optimization (optionally forall quantified) problem iteratively without requiring solver specific features.

            @authors: Marco Biasion
        """

        # define common extra nodes
        extra_nodes = (
            PlaceHolder(optimize_target.operand),
            Identity(SC.optimization_identity, operands=(optimize_target.operand,)),
            Target(SC.optimization_target, operands=(SC.optimization_identity,)),
        )
        # define node class for the optimization comparison
        comparison_class = {
            Max: GreaterThan,
            Min: LessThan,
        }[type(optimize_target)]

        # iteratively optimize the value
        last_model = None
        previous_value = None
        while True:
            # define custom CGraph with rules for the optimization
            if previous_value is None:
                _extra_nodes = extra_nodes
            else:
                _extra_nodes = (
                    *extra_nodes,
                    IntConstant(SC.optimization_constant, value=previous_value),
                    comparison_class(SC.optimization_rule, operands=(SC.optimization_identity, SC.optimization_constant)),
                    Constraint(SC.optimization_constraint, operands=(SC.optimization_rule,)),
                )
            _graphs = tuple(*graphs, CGraph(_extra_nodes))

            # solve
            _global_targets = GlobalTasks(forall=forall_target)
            status, model = cls.solve(_graphs, specifications, __global_targets=_global_targets)

            # break if termination condition is reached
            if status == 'unknown': return ('unknown', None)
            if status == 'unsat': break

            # update previous value and model
            previous_value = model.pop(SC.optimization_identity)
            last_model = model

        # return the status and model
        if previous_value is None: return ('unsat', None)
        else: return ('sat', last_model)

    @classmethod
    @final
    def _pop_global_tasks(cls, graphs: _Graphs) -> Tuple[GlobalTasks, _Graphs]:
        """
            Pops all `GlobalTask` nodes from the graphs.

            Returns
             - `ForAll` and `Min`/`Max` nodes from the given graphs, if present.
             - Sequence of graphs where `CGraphs` are updated/dropped based on their `GlobalTask` content (partial/only).

            @authors: Marco Biasion
        """

        _graphs = []
        _global_tasks = []
        for graph in graphs:
            if (not isinstance(graph, CGraph)) or (len(graph.global_tasks) == 0):
                # nothing to extract
                # keep as-is if not a CGraph or not containing any GlobalTask
                pass

            else:
                # extract tasks
                _global_tasks.extend(graph.global_tasks)

                # drop graph if all nodes are GlobalTask and PlaceHolder
                if all(isinstance(n, (PlaceHolder, GlobalTask)) for n in graph.nodes):
                    continue

                # update CGraph without GlobalTask (and relative PlaceHolder)
                else:
                    task_names = frozenset(n.name for n in graph.global_tasks)
                    placeholder_names = frozenset(
                        n.name for n in graph.placeholders
                        if len(succ := graph.successors(n)) == 1 and succ[0].name in task_names
                    )

                    graph = CGraph(
                        n for n in graph.nodes
                        if n.name not in task_names and n.name not in placeholder_names
                    )

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
            tuple(_graphs)
        )
