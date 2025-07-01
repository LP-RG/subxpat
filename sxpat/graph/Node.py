from __future__ import annotations
from typing import Tuple, Generic, TypeVar
from typing_extensions import Self

import dataclasses as dc


__all__ = [
    # > abstracts
    'Node',
    # variable
    'Variable',
    # valued
    'Valued',
    # constant
    'Constant',
    # operation
    'Operation', 'Limited1Operation', 'Limited2Operation', 'Limited3Operation',
    # resulting type
    'BoolResType', 'IntResType', 'DynamicResType',
    # > variables
    'BoolVariable', 'IntVariable',
    # > constants
    'BoolConstant', 'IntConstant',
    # > placeholder
    'PlaceHolder',
    # > expressions
    'ExpressionNode',
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
    'Target', 'Constraint',
    # global nodes
    'GlobalNode', 'Min', 'Max', 'ForAll',

    # > aliases
    'OperationNode', 'ValuedNode', 'ConstantNode', 'VariableNode',

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
    weight: int = None
    in_subgraph: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, 'in_subgraph', bool(self.in_subgraph))
        # assert re.match(r'^\w+$', self.name), f'The name `{self.name}` is invalid, it must match regex `\w+`.'

    def copy(self, name: str = None, weight: int = None, in_subgraph: bool = None, **update) -> Self:
        if name is not None: update['name'] = name
        if weight is not None: update['weight'] = weight
        if in_subgraph is not None: update['in_subgraph'] = in_subgraph
        return type(self)(**{**vars(self), **update})


# variable


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Variable(__Base):
    """
        An object representing a variable.

        *abstract*
    """


# valued


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Valued(Generic[T], __Base):
    """
        An object with a `value` attribute.

        *abstract*
    """

    value: T = None

# constant


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Constant(Valued[T]):
    """
        An object representing a constant.

        *abstract*
    """


# operation


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class Operation(__Base):
    """
        An object with operands.

        *abstract*
    """

    operands: Tuple[str, ...] = tuple()

    def __post_init__(self, required_operands_count: int = None):
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
                f'in node {self.name} of class {type(self).__qualname__}.'
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

    @classmethod
    def of(cls, operand: Node) -> Self:
        """Helper constructor with automatic naming."""
        return cls(
            f'{cls.__name__.lower()}_{operand.name}',
            weight=operand.weight, in_subgraph=operand.in_subgraph,
            operands=(operand,)
        )


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


# > variables


@dc.dataclass(frozen=True)
class BoolVariable(Variable, BoolResType, Node):
    """
        Boolean variable.
    """


@dc.dataclass(frozen=True)
class IntVariable(Variable, IntResType, Node):
    """
        Integer variable.
    """


# > constants


@dc.dataclass(frozen=True)
class BoolConstant(Constant[bool], BoolResType, Node):
    """
        Boolean constant.
    """


@dc.dataclass(frozen=True)
class IntConstant(Constant[int], IntResType, Node):
    """
        Integer constant.
    """


# > placeholder


@dc.dataclass(frozen=True)
class PlaceHolder(Node):
    """
        Special node: placeholder for any other node (by name).  

        @note: Used to remove the requirement for the repetition of logic.
    """


# > expressions


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class ExpressionNode(Node):
    """
        A node representing an expression.

        *abtract*
    """


# bool to bool


@dc.dataclass(frozen=True)
class Not(Limited1Operation, BoolResType, ExpressionNode):
    """
        Boolean negation ( `not a` ) expression.  
        This node must have only one operand.
    """


@dc.dataclass(frozen=True)
class And(Operation, BoolResType, ExpressionNode):
    """
        Boolean conjunction ( `a and b and ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class Or(Operation, BoolResType, ExpressionNode):
    """
        Boolean disjunction ( `a or b or ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class Implies(Limited2Operation, BoolResType, ExpressionNode):
    """
        Boolean implication ( `a => b` ) expression.  
        This node must have two ordered operands: left, right.
    """


# int to int


@dc.dataclass(frozen=True)
class Sum(Operation, IntResType, ExpressionNode):
    """
        Integer addition ( `a + b + ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class AbsDiff(Limited2Operation, IntResType, ExpressionNode):
    """
        Integer absolute difference ( `| a - b |` ) expression.  
        This node must have two operands.
    """


# bool to int


@dc.dataclass(frozen=True)
class ToInt(Operation, IntResType, ExpressionNode):
    """
        Special integer node: represents the creation of an integer given a sequence of booleans (the bits).  
        This node can have any amount of ordered operands, where the first represents the least significant bit.
    """


# int to bool


@dc.dataclass(frozen=True)
class Equals(Limited2Operation, BoolResType, ExpressionNode):
    """
        Equality ( `a == b` ) expression.  
        This node must have two operands.
    """


@dc.dataclass(frozen=True)
class NotEquals(Limited2Operation, BoolResType, ExpressionNode):
    """
        Inequality ( `a != b` ) expression.  
        This node must have two operands.
    """


@dc.dataclass(frozen=True)
class LessThan(Limited2Operation, BoolResType, ExpressionNode):
    """
        Less than ( `a < b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True)
class LessEqualThan(Limited2Operation, BoolResType, ExpressionNode):
    """
        Less or equal than ( `a <= b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True)
class GreaterThan(Limited2Operation, BoolResType, ExpressionNode):
    """
        Greater than ( `a > b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True)
class GreaterEqualThan(Limited2Operation, BoolResType, ExpressionNode):
    """
        Greater or equal than ( `a >= b` ) expression.  
        This node must have two ordered operands: left, right.
    """


# identity


@dc.dataclass(frozen=True)
class Identity(Limited1Operation, DynamicResType, ExpressionNode):
    """
        The identity expression.
    """


# branch


@dc.dataclass(frozen=True)
class Multiplexer(Limited3Operation, BoolResType, ExpressionNode):
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
class If(Limited3Operation, DynamicResType, ExpressionNode):
    """
        Special node: represents a selection ( `if a then b else c` ) operation.  
        This node must have three ordered operands: condition, if true, if false.
    """

    @property
    def contition(self) -> str:
        return self.operands[0]

    @property
    def if_true(self) -> str:
        return self.operands[1]

    @property
    def if_false(self) -> str:
        return self.operands[2]


# quantify


@dc.dataclass(frozen=True)
class AtLeast(Valued[int], Operation, BoolResType, ExpressionNode):
    """
        Special node: represents a lower limit to the number of operands that must be true.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class AtMost(Valued[int], Operation, BoolResType, ExpressionNode):
    """
        Special node: represents an upper limit to the number of operands that can be true.  
        This node can have any amount of operands.
    """


# > solver nodes


@dc.dataclass(frozen=True)
class Target(Limited1Operation, Node):
    """
        Special solver node: specifies a node which value must be returned when solving.  
        The only operand represents the value to return.
    """


@dc.dataclass(frozen=True)
class Constraint(Limited1Operation, Node):
    """
        Special solver node: specifies a node which value must be asserted when solving.  
        The only operand represents the value to assert.
    """

# global nodes


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class GlobalNode(Node):
    """
        Special nodes representing a global task, it being min/maximization or a ForAll.

        *abstract*
    """


@dc.dataclass(frozen=True)
class Min(Limited1Operation, GlobalNode):
    """
        Special solver global node: specifies a node which value must be minimized.  
        The only operand represents the value to minimize.
    """


@dc.dataclass(frozen=True)
class Max(Limited1Operation, GlobalNode):
    """
        Special solver global node: specifies a node which value must be maximized.  
        The only operand represents the value to maximized.
    """


@dc.dataclass(frozen=True)
class ForAll(Operation, GlobalNode):
    """
        Special solver global node: specifies that all constraints must be asserted for each permutation of the operands.  
    """


# > aliases


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class OperationNode(Operation, Node):
    """
        **JUST A TYPE ALIAS**  
        Never use it for anything other than type annotations.
    """


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class ValuedNode(Valued, Node):
    """
        **JUST A TYPE ALIAS**  
        Never use it for anything other than type annotations.
    """


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class ConstantNode(Constant, Node):
    """
        **JUST A TYPE ALIAS**  
        Never use it for anything other than type annotations.
    """


@dc.dataclass(frozen=True, init=False, repr=False, eq=False)
class VariableNode(Variable, Node):
    """
        **JUST A TYPE ALIAS**  
        Never use it for anything other than type annotations.
    """


# > other groups
#
contact_nodes = (PlaceHolder,)
#
origin_nodes = (BoolVariable, BoolConstant, IntVariable, IntConstant,)
end_nodes = (Identity, Target, Constraint)
#
global_solver_nodes = (Min, Max, ForAll)
