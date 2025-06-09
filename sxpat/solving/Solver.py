from typing import Mapping, Optional, Sequence, Tuple, Union, TypeVar
import dataclasses as dc
from abc import abstractmethod

import itertools as it

from sxpat.graph import IOGraph, PGraph, CGraph, ForAll, Max, Min, GreaterThan, Identity, LessThan, PlaceHolder, Target, Constraint, IntConstant
from sxpat.specifications import Specifications
from sxpat.utils.decorators import make_utility_class

from sxpat.config import SolverConstants as SC


__all__ = [
    'Solver',
    'GlobalGroup',
]


@dc.dataclass(frozen=True)
class GlobalTargets:
    optimize: Optional[Union[Min, Max]] = None
    forall: Optional[ForAll] = None


@make_utility_class
class Solver:
    """
        Guide: inheriting from `Solver`.

        The `Solver` super class has one public method: `.solve(...)`  
        This method internally delegates the computation to one of 4 possible function categories:
        - `_solve_optimize_forall`: used to solve problems with both an optimization target and a forall quantifier
        - `_solve_optimize`: used to solve only optimization problems
        - `_solve_forall`: used to solve only forall quantified problems
        - `_solve`: used to solve non optimization and not forall quantified problems

        Of these categories, the only one strictly required to be implemented in the subclasses is `_solve`,
        in particular the method `._solve(...)`.  
        This is because all other categories have a `multipass` implementation which is not optimized,
        but does not require any solver-specific feature.

        To improve the performance for the solver being implemented you can define a `singlepass` 
        variant for each of the first 3 categories (eg. `._solve_forall_singlepass(...)`).

        @authors: Marco Biasion
    """

    _Graphs = TypeVar('_Graphs', bound=Sequence[Union[IOGraph, PGraph, CGraph]])

    @classmethod
    def solve(cls, graphs: _Graphs,
              specifications: Specifications,
              *,
              _global_targets: GlobalTargets = None,
              ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve the required problem defined by the given graphs.

            The supported graphs are:
            - IOGraph (and subclasses): for input variables (and local behaviour)
            - PGraph (and subclasses): for parameter variables (and local behaviour)
            - CGraph (and subclasses): for applicable constraints

            Returns the status of the resolution (`sat`, `unsat`, `unknown`) and the model evaluated from the `Target` nodes if `sat`.
        """

        # compute global targets if not already given
        if _global_targets is not None:
            _global_targets = cls.get_global_targets(graphs)

        # solve an optimization and forall quantified problem
        if _global_targets.optimize is not None and _global_targets.forall is not None:
            try:  # try solving with solver-specific singlepass approach
                return cls._solve_optimize_forall_singlepass(graphs, specifications, _global_targets)
            except NotImplementedError:  # solve with multipass approach
                return cls._solve_optimize_forall_multipass(graphs, specifications, _global_targets)

        # solve an optimization (not forall quantified) problem
        if _global_targets.optimize is not None and _global_targets.forall is None:
            try:  # try solving with solver-specific singlepass approach
                return cls._solve_optimize_singlepass(graphs, specifications, _global_targets)
            except NotImplementedError:  # solve with multipass approach
                return cls._solve_optimize_multipass(graphs, specifications, _global_targets)

        # solve a forall quantified (and non optimization) problem
        if _global_targets.optimize is None and _global_targets.forall is not None:
            try:  # try solving with solver-specific singlepass approach
                return cls._solve_forall_singlepass(graphs, specifications, _global_targets)
            except NotImplementedError:  # solve with multipass approach
                return cls._solve_forall_multipass(graphs, specifications, _global_targets)

        # solve a non optimization and not forall quantified problem.
        return cls._solve(graphs, specifications, _global_targets)

    @classmethod
    @abstractmethod
    def _solve(cls, graphs: _Graphs,
               specifications: Specifications,
               ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve a non optimization and not forall quantified problem.
        """
        raise NotImplementedError(f'{cls.__qualname__}._solve(...) is abstract')

    @classmethod
    @abstractmethod
    def _solve_forall_singlepass(cls, graphs: _Graphs,
                                 specifications: Specifications,
                                 global_targets: GlobalTargets,
                                 ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve a forall quantified (and non optimization) problem in a single pass using solver-specific features.
        """
        raise NotImplementedError(f'{cls.__qualname__}._solve_forall_singlepass(...) is abstract')

    @classmethod
    @abstractmethod
    def _solve_forall_multipass(cls, graphs: _Graphs,
                                specifications: Specifications,
                                global_targets: GlobalTargets,
                                ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve a forall quantified (and non optimization) problem iteratively without requiring solver-specific features.
        """
        # TODO: here we can implement the custom forall approach as for the initial implementations of XPAT (in year ~2021)
        raise NotImplementedError(f'{cls.__qualname__}._solve_forall_multipass(...) is work in progress')

    @classmethod
    @abstractmethod
    def _solve_optimize_singlepass(cls, graphs: _Graphs,
                                   specifications: Specifications,
                                   global_targets: GlobalTargets,
                                   ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve an optimization (not forall quantified) problem in a single pass using solver-specific features.
        """
        raise NotImplementedError(f'{cls.__qualname__}._solve_optimize_singlepass(...) is abstract')

    @classmethod
    def _solve_optimize_multipass(cls, graphs: _Graphs,
                                  specifications: Specifications,
                                  global_targets: GlobalTargets,
                                  *, _accept_forall: bool = False
                                  ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve an optimization (not forall quantified) problem iteratively without requiring solver-specific features.
        """

        # define common extra nodes
        extra_nodes = (
            PlaceHolder(global_targets.optimize.operand),
            Identity(SC.optimization_identity, operands=(global_targets.optimize.operand,)),
            Target(SC.optimization_target, operands=(SC.optimization_identity,)),
        )
        # define node class for the optimization comparison
        comparison_class = {
            Max: GreaterThan,
            Min: LessThan,
        }[type(global_targets.optimize)]

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
            _global_targets = GlobalTargets(forall=(global_targets.forall if _accept_forall else None))
            status, model = cls.solve(_graphs, specifications, _global_targets=_global_targets)

            # break if termination condition is reached
            if status == 'unknown': return ('unknown', None)
            if status == 'unsat': break

            # update previous value and model
            previouss_value = model.pop(SC.optimization_identity)
            last_model = model

        # return the status and model
        if previous_value is None: return ('unsat', None)
        else: return ('sat', last_model)

    @classmethod
    @abstractmethod
    def _solve_optimize_forall_singlepass(cls, graphs: _Graphs,
                                          specifications: Specifications,
                                          global_targets: GlobalTargets,
                                          ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve an optimization and forall quantified problem in a single pass using solver-specific features.
        """
        raise NotImplementedError(f'{cls.__qualname__}._solve_forall_optimize_singlepass(...) is abstract')

    @classmethod
    def _solve_optimize_forall_multipass(cls, graphs: _Graphs,
                                         specifications: Specifications,
                                         global_targets: GlobalTargets,
                                         ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve an optimization and forall quantified problem iteratively without requiring solver-specific features.
        """
        return cls._solve_optimize_multipass(graphs, specifications, global_targets, _accept_forall=True)

    @classmethod
    def get_global_targets(cls, graphs: _Graphs) -> GlobalTargets:
        """
            Returns the `ForAll` and `Min`/`Max` nodes from the given graphs, if present.
        """

        # extract global nodes
        global_nodes = tuple(it.chain.from_iterable(
            g.global_nodes
            for g in graphs
            if isinstance(g, CGraph)
        ))
        foralls = tuple(n for n in global_nodes if isinstance(n, ForAll))
        optimizes = tuple(n for n in global_nodes if isinstance(n, (Min, Max)))

        # NOTE: the check for the foralls could be removed, as we could treat multiple ForAll as a single ForAll with all the inputs
        if len(foralls) > 1: raise RuntimeError('Too many ForAll nodes in the graphs')
        if len(optimizes) > 1: raise RuntimeError('Too many Min/Max nodes in the graphs')

        return GlobalTargets(
            optimize=(optimizes[0] if optimizes else None),
            forall=(foralls[0] if foralls else None),
        )
