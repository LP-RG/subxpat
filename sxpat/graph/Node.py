from typing import Tuple, Generic, TypeVar

import dataclasses as dc


__all__ = [
    # nodes
    'AbsDiff', 'And', 'AtLeast', 'AtMost', 'BoolConstant', 'BoolVariable', 'Copy',
    'Equals', 'GreaterEqualThan', 'GreaterThan', 'If', 'Implies', 'IntConstant',
    'IntVariable', 'LessEqualThan', 'LessThan', 'Multiplexer', 'Node', 'NotEquals',
    'Not', 'OperationNode', 'Or', 'PlaceHolder', 'Sum', 'Target', 'ToInt', 'Valued',
    # nodes groups
    'boolean_nodes', 'integer_nodes', 'untyped_nodes', 'contact_nodes', 'origin_nodes', 'end_nodes',
]


T = TypeVar('T', int, bool)


# abstracts


@dc.dataclass(frozen=True)
class Node:
    name: str
    weight: int = None
    in_subgraph: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, 'in_subgraph', bool(self.in_subgraph))
        # assert re.match(r'^\w+$', self.name), f'The name `{self.name}` is invalid, it must match regex `\w+`.'

    def copy(self, **update):
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
    """

    items: Tuple[str, ...] = tuple()

    def __post_init__(self, required_items_count: int = None):
        object.__setattr__(self, 'items', tuple(i.name if isinstance(i, Node) else i for i in self.items))
        if required_items_count is not None and len(self.items) != required_items_count:
            raise RuntimeError(f'Wrong items count (expected {required_items_count}) in node {self.name} of class {type(self).__name__}')


@dc.dataclass(frozen=True, repr=False)
class Op1Node(OperationNode):
    """
        A node that must have only one operand.  
        With getter for it.
    """

    def __post_init__(self):
        super().__post_init__(1)

    @property
    def item(self) -> str:
        return self.items[0]


@dc.dataclass(frozen=True, repr=False)
class Op2Node(OperationNode):
    """
        A node that must have two operands.  
        With getters for left and right.
    """

    def __post_init__(self):
        super().__post_init__(2)

    @property
    def left(self) -> str:
        return self.items[0]

    @property
    def right(self) -> str:
        return self.items[1]


@dc.dataclass(frozen=True, repr=False)
class Op3Node(OperationNode):
    """
        A node that must have three operands.
    """

    def __post_init__(self):
        super().__post_init__(3)


# variables


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


# constants


@dc.dataclass(frozen=True)
class BoolConstant(Valued[bool], Node):
    """
        Boolean constant.
    """


@dc.dataclass(frozen=True)
class IntConstant(Valued[bool], Node):
    """
        Integer constant.
    """


# output


@dc.dataclass(frozen=True, repr=False)
class Copy(Op1Node):
    """
        Special node: the copy of another node.  
        The only operand represents the node to copy.
    """


@dc.dataclass(frozen=True, repr=False)
class Target(Copy):  # TODO:MARCO: or result/question/...?
    """
        Special solver node: specifies a node which value must be returned when solving.  
        The only operand represents the wanted value.
    """


# placeholder


@dc.dataclass(frozen=True, repr=False)
class PlaceHolder(Node):
    """
        Special node: placeholder for any other node (by name).  

        @note: Used to remove the requirement for the repetition of logic.
    """


# bool-bool operations


@dc.dataclass(frozen=True, repr=False)
class Not(Op1Node):
    """
        Boolean not ( `not a` ) operation.  
        This node must have only one operand.
    """


@dc.dataclass(frozen=True, repr=False)
class And(OperationNode):
    """
        Boolean and ( `a and b and ...` ) operation.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True, repr=False)
class Or(OperationNode):
    """
        Boolean or ( `a or b or ...` ) operation.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True, repr=False)
class Implies(Op2Node):
    """
        Boolean implies ( `a => b` ) operation.  
        This node must have two ordered operands: left, right.
    """


# int-int operations


@dc.dataclass(frozen=True, repr=False)
class Sum(OperationNode):
    """
        Integer sum ( `a + b + ...` ) operation.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True, repr=False)
class AbsDiff(Op2Node):
    """
        Integer absolute difference ( `| a - b |` ) operation.  
        This node must have two operands.
    """


# bool-int operations


@dc.dataclass(frozen=True, repr=False)
class ToInt(OperationNode):
    """
        Special integer node: represents the convertion to an integer from a sequence of booleans (the bits).  
        This node can have any amount of ordered operands, where the first represents the least significant bit.
    """


# int-bool operations


@dc.dataclass(frozen=True, repr=False)
class Equals(Op2Node):
    """
        Equality ( `a == b` ) operation.  
        This node must have two operands.
    """


@dc.dataclass(frozen=True, repr=False)
class NotEquals(Op2Node):
    """
        Inequality ( `a != b` ) operation.  
        This node must have two operands.
    """


@dc.dataclass(frozen=True, repr=False)
class LessThan(Op2Node):
    """
        Less than ( `a < b` ) operation.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True, repr=False)
class LessEqualThan(Op2Node):
    """
        Less or equal than ( `a <= b` ) operation.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True, repr=False)
class GreaterThan(Op2Node):
    """
        Greater than ( `a > b` ) operation.  
        This node must have two ordered operands: left, right.
    """


@dc.dataclass(frozen=True, repr=False)
class GreaterEqualThan(Op2Node):
    """
        Greater or equal than ( `a >= b` ) operation.  
        This node must have two ordered operands: left, right.
    """


# quantifier operations


@dc.dataclass(frozen=True, repr=False)
class AtLeast(Valued[int], OperationNode):
    """
        Special solver node: represents a lower limit to the number of operands that must be true.  
        This node can have any amount of operands.
    """


@dc.dataclass(frozen=True, repr=False)
class AtMost(Valued[int], OperationNode):
    """
        Special solver node: represents an upper limit to the number of operands that can be true.  
        This node can have any amount of operands.
    """


# branching operations


@dc.dataclass(frozen=True, repr=False)
class Multiplexer(Op3Node):
    """
        Special boolean node: represents a multiplexer (not origin, origin, false, true) indexed by two parameters.  
        This node must have three ordered operands: origin, usage parameter (origin/constant), assertion parameter (asserted/negated).
    """

    @property
    def origin(self) -> str:
        return self.items[0]

    @property
    def parameter_usage(self) -> str:
        """If this parameter is true, the origin will be used, otherwise a constant will be produced"""
        return self.items[1]

    @property
    def parameter_assertion(self) -> str:
        """If this parameter is true, the node will produce the origin or the constant true, otherwise will produce the negated origin or the constant false"""
        return self.items[2]


@dc.dataclass(frozen=True, repr=False)
class If(Op3Node):
    """
        Special node: represents a selection ( `if a then b else c` ) operation.  
        This node must have three ordered operands: condition, if true, if false.
    """

    @property
    def contition(self) -> str:
        return self.items[0]

    @property
    def if_true(self) -> str:
        return self.items[1]

    @property
    def if_false(self) -> str:
        return self.items[2]


# TODO:WIP: global operations
# @dc.dataclass(frozen=True, repr=False)
# class Min(Op1Node):
#     pass
# @dc.dataclass(frozen=True, repr=False)
# class Max(Op1Node):
#     pass
# @dc.dataclass(frozen=True, repr=False)
# class ForAll(OperationNode):
#     pass


#
boolean_nodes = (BoolVariable, BoolConstant, Not, And, Or, Implies, Equals, NotEquals, AtLeast, AtMost, LessThan, LessEqualThan, GreaterThan, GreaterEqualThan, Multiplexer,)
integer_nodes = (IntVariable, IntConstant, ToInt, Sum, AbsDiff,)
untyped_nodes = (Copy, Target, If,)
#
contact_nodes = (PlaceHolder,)  # TODO:MARCO: what name should we use?
#
origin_nodes = (BoolVariable, BoolConstant, IntVariable, IntConstant,)
end_nodes = (Copy, Target,)
