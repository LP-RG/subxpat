from __future__ import annotations
from typing import Any, Optional, Tuple, Generic, TypeVar, Union
from typing_extensions import Self

import dataclasses as dc


__all__ = [
    # > abstracts
    'Node',
    'Extras',
    # valued
    'Valued',
    # operation
    'Operation', 'Limited1Operation', 'Limited2Operation', 'Limited3Operation',
    # resulting type
    'ResultingType',
    'BoolResType', 'IntResType', 'DynamicResType',
    # structural type
    'StructuralType',
    'EntryPoint', 'EndPoint',

    # > variables
    'Variable',
    'BoolVariable', 'IntVariable',

    # > constants
    'Constant',
    'BoolConstant', 'IntConstant',

    # > placeholder
    'PlaceHolder',

    # > expressions
    'Expression',
    # bool to bool
    'Not', 'And', 'Or', 'Implies',
    # int to int
    'Sum', 'AbsDiff',
    # bool to int
    'ToInt',
    # int to bool
    'Equals', 'NotEquals', 'LessThan', 'LessEqualThan', 'GreaterThan', 'GreaterEqualThan',
    # identity
    'Identity',
    # branch
    'Multiplexer', 'If',
    # quantify
    'AtLeast', 'AtMost',

    # > solver nodes
    'Objective', 'GlobalTask',
    # objectives
    'Target', 'Constraint',
    # global tasks
    'Min', 'Max', 'ForAll',

    # > aliases
    'VariableNode', 'ValuedNode', 'ConstantNode',
    'OperationNode', 'ExpressionNode',
    'ObjectiveNode', 'GlobalTaskNode',

    'T_AnyNode',

    # > nodes groups
    'contact_nodes', 'origin_nodes', 'end_nodes',
]


T = TypeVar('T', int, bool)


# > abstracts


class __Base:
    def __post_init__(self) -> None: pass


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Node(__Base):
    """
        A node.

        *abstract*
    """

    name: str

    def __post_init__(self) -> None:
        super().__post_init__()
        # assert re.match(r'^\w+$', self.name), f'The name `{self.name}` is invalid, it must match regex `\w+`.'

    def copy(self, **update: Any) -> Self:
        return type(self)(**{**vars(self), **update})


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Extras(__Base):
    """
        An object with extra informations.

        *abstract*
    """

    weight: Optional[int] = None
    in_subgraph: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, 'in_subgraph', bool(self.in_subgraph))


# valued


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Valued(Generic[T], __Base):
    """
        An object with a `value` attribute.

        *abstract*
    """

    value: T


# operation


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Operation(__Base):
    """
        An object with operands.

        *abstract*
    """

    operands: Tuple[str, ...]

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(
            self, 'operands',
            tuple(i.name if isinstance(i, Node) else i for i in self.operands)
        )

    def _check_operands_count(self, required_count: int) -> None:
        if len(self.operands) != required_count:
            raise RuntimeError(
                f'Wrong operands count: '
                f'{len(self.operands)} operands were given (expected {required_count}) '
                f'in {self!r}.'
            )


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Limited1Operation(Operation):
    """
        An object with exactly 1 operand.

        *abstract*
    """

    def __post_init__(self):
        super().__post_init__()
        self._check_operands_count(1)

    @property
    def operand(self) -> str:
        return self.operands[0]


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Limited2Operation(Operation):
    """
        An object with exactly 2 operands.

        *abstract*
    """

    def __post_init__(self):
        super().__post_init__()
        self._check_operands_count(2)

    @property
    def left(self) -> str:
        return self.operands[0]

    @property
    def right(self) -> str:
        return self.operands[1]


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Limited3Operation(Operation):
    """
        An object with exactly 3 operands.

        *abstract*
    """

    def __post_init__(self):
        super().__post_init__()
        self._check_operands_count(3)


# resulting type


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class ResultingType(__Base):
    """
        An object with a resulting type.

        *abstract*
    """


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class BoolResType(ResultingType):
    """
        An object with boolean resulting type.

        *abstract*
    """


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class IntResType(ResultingType):
    """
        An object with integer resulting type.

        *abstract*
    """


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class DynamicResType(ResultingType):
    """
        An object with a dynamic resulting type.

        *abstract*
    """


# structural type


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class StructuralType(__Base):
    """
        An object with a structural type (eg. entry/root, end/leaf, inner, ...).

        *abstract*
    """


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class EntryPoint(StructuralType):
    """
        An object representing an entry-point of a structure (a root).

        *abstract*
    """


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class EndPoint(StructuralType):
    """
        An object representing an end-point of a structure (a leaf).

        *abstract*
    """


# > variables


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Variable(EntryPoint):
    """
        An object representing a variable.

        *abstract*
    """


@dc.dataclass(frozen=True)
class BoolVariable(Extras, Variable, BoolResType, Node):
    """
        Boolean variable.
    """


@dc.dataclass(frozen=True)
class IntVariable(Extras, Variable, IntResType, Node):
    """
        Integer variable.
    """


# > constants


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Constant(Valued[T], EntryPoint):
    """
        An object representing a constant.

        *abstract*
    """


@dc.dataclass(frozen=True)
class BoolConstant(Extras, Constant[bool], BoolResType, Node):
    """
        Boolean constant.
    """


@dc.dataclass(frozen=True)
class IntConstant(Extras, Constant[int], IntResType, Node):
    """
        Integer constant.
    """


# > placeholder


@dc.dataclass(frozen=True)
class PlaceHolder(Node):
    # TODO: should this be an EntryPoint?
    #       structurally in an individual graph yes, but how sould we treat it in multigraph references?
    """
        Special node: placeholder for any other node (by name).  

        @note: Used to remove the requirement for the repetition of logic.
    """


# > expressions


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Expression(__Base):
    """
        An object representing an expression.

        *abtract*
    """


# bool to bool


@dc.dataclass(frozen=True)
class Not(Extras, Limited1Operation, BoolResType, Expression, Node):
    """
        Boolean negation ( `not a` ) expression.  
        This node must have only one operand.
    """


@dc.dataclass(frozen=True)
class And(Extras, Operation, BoolResType, Expression, Node):
    """
        Boolean conjunction ( `a and b and ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class Or(Extras, Operation, BoolResType, Expression, Node):
    """
        Boolean disjunction ( `a or b or ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class Implies(Extras, Limited2Operation, BoolResType, Expression, Node):
    """
        Boolean implication ( `a => b` ) expression.  
        This node must have two ordered operands: left, right.
    """


# int to int


@dc.dataclass(frozen=True)
class Sum(Extras, Operation, IntResType, Expression, Node):
    """
        Integer addition ( `a + b + ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class AbsDiff(Extras, Limited2Operation, IntResType, Expression, Node):
    """
        Integer absolute difference ( `| a - b |` ) expression.  
        This node must have two operands.
    """


# bool to int


@dc.dataclass(frozen=True)
class ToInt(Extras, Operation, IntResType, Expression, Node):
    """
        Special integer node: represents the creation of an integer given a sequence of booleans (the bits).  
        This node can have any amount of ordered operands, where the first represents the least significant bit.
    """


# int to bool


@dc.dataclass(frozen=True)
class Equals(Extras, Limited2Operation, BoolResType, Expression, Node):
    """
        Equality ( `a == b` ) expression.  
        This node must have two operands.
    """


@dc.dataclass(frozen=True)
class NotEquals(Extras, Limited2Operation, BoolResType, Expression, Node):
    """
        Inequality ( `a != b` ) expression.  
        This node must have two operands.
    """


@dc.dataclass(frozen=True)
class LessThan(Extras, Limited2Operation, BoolResType, Expression, Node):
    """
        Less than ( `a < b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True)
class LessEqualThan(Extras, Limited2Operation, BoolResType, Expression, Node):
    """
        Less or equal than ( `a <= b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True)
class GreaterThan(Extras, Limited2Operation, BoolResType, Expression, Node):
    """
        Greater than ( `a > b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True)
class GreaterEqualThan(Extras, Limited2Operation, BoolResType, Expression, Node):
    """
        Greater or equal than ( `a >= b` ) expression.  
        This node must have two ordered operands: left, right.
    """


# identity


@dc.dataclass(frozen=True)
class Identity(Extras, Limited1Operation, DynamicResType, Expression, Node):
    """
        The identity expression.

        **ALMOST DEPRECATED**
    """


# branch


@dc.dataclass(frozen=True)
class Multiplexer(Extras, Limited3Operation, BoolResType, Expression, Node):
    """
        Special boolean node: represents a multiplexer (false, true, not origin, origin) indexed by two parameters.  
        This node must have three ordered operands: origin, usage parameter (origin/constant), assertion parameter (asserted/negated).
    """

    @property
    def origin(self) -> str:
        return self.operands[0]

    @property
    def parameter_usage(self) -> str:
        """If this parameter is true, the origin will be used, otherwise a constant will be produced"""
        return self.operands[1]

    @property
    def parameter_assertion(self) -> str:
        """If this parameter is true, the node will produce the origin or the constant true, otherwise will produce the negated origin or the constant false"""
        return self.operands[2]


@dc.dataclass(frozen=True)
class If(Extras, Limited3Operation, DynamicResType, Expression, Node):
    """
        Special node: represents a selection ( `if a then b else c` ) operation.  
        This node must have three ordered operands: condition, if true, if false.
    """

    @property
    def condition(self) -> str:
        return self.operands[0]

    @property
    def if_true(self) -> str:
        return self.operands[1]

    @property
    def if_false(self) -> str:
        return self.operands[2]


# quantify


@dc.dataclass(frozen=True)
class AtLeast(Extras, Valued[int], Operation, BoolResType, Expression, Node):
    """
        Special node: represents a lower limit to the number of operands that must be true.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class AtMost(Extras, Valued[int], Operation, BoolResType, Expression, Node):
    """
        Special node: represents an upper limit to the number of operands that can be true.  
        This node can have any amount of operands.
    """


# > solver nodes


# objective nodes


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Objective(EndPoint):
    """
        An object representing an objective for the solver.

        *abtract*
    """


@dc.dataclass(frozen=True)
class Target(Limited1Operation, Objective, Node):
    """
        Special solver node: specifies a node which value must be returned when solving.  
        The only operand represents the value to return.
    """

    @classmethod
    def of(cls, operand: Node) -> Self:
        """Helper constructor with automatic naming."""
        return cls(
            f'target_{operand.name}',
            operands=(operand,),
        )


@dc.dataclass(frozen=True)
class Constraint(Limited1Operation, Objective, Node):
    """
        Special solver node: specifies a node which value must be asserted when solving.  
        The only operand represents the value to assert.
    """

    @classmethod
    def of(cls, operand: Node) -> Self:
        """Helper constructor with automatic naming."""
        return cls(
            f'constraint_{operand.name}',
            operands=(operand,),
        )


# global task nodes


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class GlobalTask(Objective):
    """
        An object representing a global solver task (eg. min/maximization, forall quantification).

        *abstract*
    """


@dc.dataclass(frozen=True)
class Min(Limited1Operation, GlobalTask, Node):
    """
        Special solver global node: specifies a node which value must be minimized.  
        The only operand represents the value to minimize.
    """


@dc.dataclass(frozen=True)
class Max(Limited1Operation, GlobalTask, Node):
    """
        Special solver global node: specifies a node which value must be maximized.  
        The only operand represents the value to maximized.
    """


@dc.dataclass(frozen=True)
class ForAll(Operation, GlobalTask, Node):
    """
        Special solver global node: specifies that all constraints must be asserted for each permutation of the operands.  
    """


# > aliases


# @dc.dataclass(frozen=True, init=False, repr=False, eq=False)
# class VariableNode(Extras, Variable, Node):
VariableNode = Union[Extras, Variable, Node]
"""
    **JUST A TYPING ALIAS**  
    Never use it for anything other than type annotations.
"""


# @dc.dataclass(frozen=True, init=False, repr=False, eq=False)
# class ValuedNode(Valued, Node):
ValuedNode = Union[Valued, Node]
"""
    **JUST A TYPING ALIAS**  
    Never use it for anything other than type annotations.
"""


# @dc.dataclass(frozen=True, init=False, repr=False, eq=False)
# class ConstantNode(Extras, Constant, Node):
ConstantNode = Union[Extras, Constant, Node]
"""
    **JUST A TYPING ALIAS**  
    Never use it for anything other than type annotations.
"""


# @dc.dataclass(frozen=True, init=False, repr=False, eq=False)
# class OperationNode(Operation, Node):
OperationNode = Union[Operation, Node]
"""
    **JUST A TYPING ALIAS**  
    Never use it for anything other than type annotations.
"""


# @dc.dataclass(frozen=True, init=False, repr=False, eq=False)
# class ExpressionNode(Extras, Expression, Operation, Node):
ExpressionNode = Union[Extras, Expression, Operation, Node]
"""
    **JUST A TYPING ALIAS**  
    Never use it for anything other than type annotations.
"""


# @dc.dataclass(frozen=True, init=False, repr=False, eq=False)
# class ObjectiveNode(Objective, Operation, Node):
ObjectiveNode = Union[Objective, Operation, Node]
"""
    **JUST A TYPING ALIAS**  
    Never use it for anything other than type annotations.
"""


# @dc.dataclass(frozen=True, init=False, repr=False, eq=False)
# class GlobalTaskNode():
GlobalTaskNode = Union[GlobalTask, Operation, Node]
"""
    **JUST A TYPING ALIAS**  
    Never use it for anything other than type annotations.
"""


# > type variables
T_AnyNode = TypeVar('T_AnyNode', Node, Valued, Operation, Limited1Operation, Limited2Operation, Limited3Operation)


# > other groups
#
contact_nodes = (PlaceHolder,)
"""DEPRECATED: will be removed in a future update"""
#
origin_nodes = (BoolVariable, BoolConstant, IntVariable, IntConstant,)
"""DEPRECATED: will be removed in a future update"""
end_nodes = (Identity, Target, Constraint)
"""DEPRECATED: will be removed in a future update"""
# asdasdas
global_solver_nodes = (Min, Max, ForAll)
"""DEPRECATED: will be removed in a future update"""
