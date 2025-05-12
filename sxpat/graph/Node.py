from __future__ import annotations
from typing import Iterable, Tuple, Generic, TypeVar
from typing_extensions import Self

import dataclasses as dc


__all__ = [
    # > abstracts
    'Node', 'Valued', 'OperationNode',
    # > variables
    'BoolVariable', 'IntVariable',
    # > constants
    'BoolConstant', 'IntConstant',
    # > placeholder
    'PlaceHolder',
    # > expressions
    'ExpressionNode',
    # bool-bool expressions
    'Not', 'And', 'Or', 'Implies',
    # int-int expressions
    'Sum', 'AbsDiff',
    # bool-int expressions
    'ToInt',
    # int-bool expressions
    'Equals', 'NotEquals', 'LessThan', 'LessEqualThan', 'GreaterThan', 'GreaterEqualThan',
    # branching expressions
    'Multiplexer', 'If',
    # > copy
    'Copy',
    # > solver nodes
    'SolverNode',
    # quantifier operations
    'AtLeast', 'AtMost',
    # targets
    'Target', 'Constraint',
    # global nodes
    'GlobalNode', 'Min', 'Max', 'ForAll',
    # > nodes groups
    'boolean_nodes', 'integer_nodes', 'untyped_nodes', 'contact_nodes', 'origin_nodes', 'end_nodes',
]


T = TypeVar('T', int, bool)


# > abstracts


@dc.dataclass(frozen=True)
class Node:
    """
        A node.

        *abstract*
    """

    name: str
    weight: int = None
    in_subgraph: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, 'in_subgraph', bool(self.in_subgraph))
        # assert re.match(r'^\w+$', self.name), f'The name `{self.name}` is invalid, it must match regex `\w+`.'

    def copy(self, name: str = None, weight: int = None, in_subgraph: bool = None, **update) -> Self:
        if name is not None: update['name'] = name
        if weight is not None: update['weight'] = weight
        if in_subgraph is not None: update['in_subgraph'] = in_subgraph
        return type(self)(**{**vars(self), **update})


@dc.dataclass(frozen=True)
class Valued(Generic[T]):
    """
        An object with a `value` attribute.
    """

    value: T = None


@dc.dataclass(frozen=True)
class OperationNode(Node):
    """
        A node representing an operation given some operands.

        *abstract*
    """

    operands: Tuple[str, ...] = tuple()

    def __post_init__(self, required_operands_count: int = None):
        object.__setattr__(self, 'operands', tuple(i.name if isinstance(i, Node) else i for i in self.operands))
        if required_operands_count is not None and len(self.operands) != required_operands_count:
            raise RuntimeError(f'Wrong operands count: {len(self.operands)} were given (expected {required_operands_count}) in node {self.name} of class {type(self).__name__}.')

    def copy(self, name: str = None, weight: int = None, in_subgraph: bool = None, operands: Iterable[Node] = None, **update) -> Self:
        if operands is not None: update['operands'] = operands
        return super().copy(name, weight, in_subgraph, **update)


@dc.dataclass(init=False, repr=False, eq=False)
class Limited1:
    def __post_init__(self):
        if len(self.operands) != 1:
            raise RuntimeError(f'Wrong operands count: {len(self.operands)} were given (expected 1) in node {self.name} of class {type(self).__name__}.')

    @property
    def operand(self) -> str:
        return self.operands[0]


@dc.dataclass(init=False, repr=False, eq=False)
class Limited2:
    def __post_init__(self):
        if len(self.operands) != 2:
            raise RuntimeError(f'Wrong operands count: {len(self.operands)} were given (expected 2) in node {self.name} of class {type(self).__name__}.')

    @property
    def left(self) -> str:
        return self.operands[0]

    @property
    def right(self) -> str:
        return self.operands[1]


@dc.dataclass(init=False, repr=False, eq=False)
class Limited3:
    def __post_init__(self):
        if len(self.operands) != 3:
            raise RuntimeError(f'Wrong operands count: {len(self.operands)} were given (expected 3) in node {self.name} of class {type(self).__name__}.')


# > variables


@dc.dataclass(frozen=True, repr=False)
class BoolVariable(Node):
    """
        Boolean variable.
    """


@dc.dataclass(frozen=True, repr=False)
class IntVariable(Node):
    """
        Integer variable.
    """


# > constants


@dc.dataclass(frozen=True)
class BoolConstant(Valued[bool], Node):
    """
        Boolean constant.
    """


@dc.dataclass(frozen=True)
class IntConstant(Valued[int], Node):
    """
        Integer constant.
    """


# > placeholder


@dc.dataclass(frozen=True, repr=False)
class PlaceHolder(Node):
    """
        Special node: placeholder for any other node (by name).  

        @note: Used to remove the requirement for the repetition of logic.
    """


# > expressions


@dc.dataclass(frozen=True)
class ExpressionNode(OperationNode):
    """
        A node representing an expression.
    """


# bool-bool expressions


@dc.dataclass(frozen=True, repr=False)
class Not(ExpressionNode, Limited1):
    """
        Boolean negation ( `not a` ) expression.  
        This node must have only one operand.
    """


@dc.dataclass(frozen=True, repr=False)
class And(ExpressionNode):
    """
        Boolean conjunction ( `a and b and ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True, repr=False)
class Or(ExpressionNode):
    """
        Boolean disjunction ( `a or b or ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True, repr=False)
class Implies(ExpressionNode, Limited2):
    """
        Boolean implication ( `a => b` ) expression.  
        This node must have two ordered operands: left, right.
    """


# int-int expressions


@dc.dataclass(frozen=True, repr=False)
class Sum(ExpressionNode):
    """
        Integer addition ( `a + b + ...` ) expression.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True, repr=False)
class AbsDiff(ExpressionNode, Limited2):
    """
        Integer absolute difference ( `| a - b |` ) expression.  
        This node must have two operands.
    """


# bool-int expressions


@dc.dataclass(frozen=True, repr=False)
class ToInt(ExpressionNode):
    """
        Special integer node: represents the creation of an integer given a sequence of booleans (the bits).  
        This node can have any amount of ordered operands, where the first represents the least significant bit.
    """


# int-bool expressions


@dc.dataclass(frozen=True, repr=False)
class Equals(ExpressionNode, Limited2):
    """
        Equality ( `a == b` ) expression.  
        This node must have two operands.
    """


@dc.dataclass(frozen=True, repr=False)
class NotEquals(ExpressionNode, Limited2):
    """
        Inequality ( `a != b` ) expression.  
        This node must have two operands.
    """


@dc.dataclass(frozen=True, repr=False)
class LessThan(ExpressionNode, Limited2):
    """
        Less than ( `a < b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True, repr=False)
class LessEqualThan(ExpressionNode, Limited2):
    """
        Less or equal than ( `a <= b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True, repr=False)
class GreaterThan(ExpressionNode, Limited2):
    """
        Greater than ( `a > b` ) expression.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True, repr=False)
class GreaterEqualThan(ExpressionNode, Limited2):
    """
        Greater or equal than ( `a >= b` ) expression.  
        This node must have two ordered operands: left, right.
    """


# branching expressions


@dc.dataclass(frozen=True, repr=False)
class Multiplexer(ExpressionNode, Limited3):
    """
        Special boolean node: represents a multiplexer (not origin, origin, false, true) indexed by two parameters.  
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


@dc.dataclass(frozen=True, repr=False)
class If(ExpressionNode, Limited3):
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


# > copy


@dc.dataclass(frozen=True, repr=False)
class Copy(OperationNode, Limited1):
    """
        Special node: the copy of another node.  
        The only operand represents the node to copy.  
    """

    @classmethod
    def of(cls, operand: Node) -> Self:
        """Helper constructor with automatic naming."""
        return cls(
            f'{cls.__name__.lower()}_{operand.name}',
            weight=operand.weight, in_subgraph=operand.in_subgraph,
            operands=(operand,)
        )


# solver nodes


@dc.dataclass(init=False, frozen=True, repr=False, eq=False)
class SolverNode(OperationNode):
    """
        A node representing some Solver construct.

        *abstract*
    """


# quantifier operations


@dc.dataclass(frozen=True)
class AtLeast(Valued[int], SolverNode):
    """
        Special solver node: represents a lower limit to the number of operands that must be true.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True)
class AtMost(Valued[int], SolverNode):
    """
        Special solver node: represents an upper limit to the number of operands that can be true.  
        This node can have any amount of operands.
    """

# targets


@dc.dataclass(frozen=True, repr=False)
class Target(SolverNode, Copy):
    """
        Special solver node: specifies a node which value must be returned when solving.  
        The only operand represents the wanted value.
    """


@dc.dataclass(frozen=True, repr=False)
class Constraint(SolverNode, Copy):
    """
        Special solver node: specifies a node which value must be asserted when solving.  
        The only operand represents the value to assert.
    """

# global nodes


@dc.dataclass(frozen=True, repr=False)
class GlobalNode(SolverNode):
    """
        Special nodes representing a global task, it being min/maximization or a ForAll quantifier.

        *abstract*
    """


@dc.dataclass(frozen=True, repr=False)
class Min(GlobalNode, Limited1):
    """
        Special solver global node: specifies a node which value must be minimized.  
        The only operand represents the value to minimize.
    """


@dc.dataclass(frozen=True, repr=False)
class Max(GlobalNode, Limited1):
    """
        Special solver global node: specifies a node which value must be maximized.  
        The only operand represents the value to maximized.
    """


@dc.dataclass(frozen=True, repr=False)
class ForAll(GlobalNode):
    """
        Special solver global node: specifies that all constraints must be asserted for each permutation of the operands.  
    """


#
boolean_nodes = (BoolVariable, BoolConstant, Not, And, Or, Implies, Equals, NotEquals, AtLeast, AtMost, LessThan, LessEqualThan, GreaterThan, GreaterEqualThan, Multiplexer,)
integer_nodes = (IntVariable, IntConstant, ToInt, Sum, AbsDiff, Min, Max)
untyped_nodes = (Copy, Target, If,)
#
contact_nodes = (PlaceHolder,)
#
origin_nodes = (BoolVariable, BoolConstant, IntVariable, IntConstant,)
end_nodes = (Copy, Target, Constraint)
#
global_solver_nodes = (Min, Max, ForAll)
