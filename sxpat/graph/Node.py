from typing import Tuple, Generic, TypeVar

import dataclasses as dc


__all__ = [
    # nodes
    'AbsDiff', 'And', 'AtLeast', 'AtMost', 'BoolConstant', 'BoolVariable', 'Copy',
    'Equals', 'GreaterEqualThan', 'GreaterThan', 'If', 'Implies', 'IntConstant',
    'IntVariable', 'LessEqualThan', 'LessThan', 'Multiplexer', 'Node', 'Not',
    'OperationNode', 'Or', 'PlaceHolder', 'Sum', 'Target', 'ToInt', 'Valued',
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
    value: T = None


@dc.dataclass(frozen=True)
class OperationNode(Node):
    items: Tuple[str, ...] = tuple()

    def __post_init__(self, required_items_count: int = None):
        object.__setattr__(self, 'items',  tuple(i.name if isinstance(i, Node) else i for i in self.items))
        if required_items_count is not None and len(self.items) != required_items_count:
            raise RuntimeError(f'Wrong items count (expected {required_items_count}) in node {self.name} of class {type(self).__name__}')


@dc.dataclass(frozen=True, repr=False)
class Op1Node(OperationNode):
    def __post_init__(self):
        super().__post_init__(1)

    @property
    def item(self) -> str:
        return self.items[0]


@dc.dataclass(frozen=True, repr=False)
class Op2Node(OperationNode):
    def __post_init__(self):
        super().__post_init__(2)


@dc.dataclass(frozen=True, repr=False)
class Op3Node(OperationNode):
    def __post_init__(self):
        super().__post_init__(3)


@dc.dataclass(frozen=True, repr=False)
class Ord2Node(Op2Node):
    @property
    def left(self) -> str:
        return self.items[0]

    @property
    def right(self) -> str:
        return self.items[1]


# inputs


@dc.dataclass(frozen=True, repr=False)
class BoolVariable(Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class IntVariable(Node):
    pass


# constants


@dc.dataclass(frozen=True)
class BoolConstant(Valued[bool], Node):
    pass


@dc.dataclass(frozen=True)
class IntConstant(Valued[bool], Node):
    pass

# output


@dc.dataclass(frozen=True, repr=False)
class Copy(Op1Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class Target(Copy):  # TODO:MARCO: or result/question/...?
    pass


# placeholder


@dc.dataclass(frozen=True, repr=False)
class PlaceHolder(Node):
    pass


# bool-bool operations


@dc.dataclass(frozen=True, repr=False)
class Not(Op1Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class And(OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class Or(OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class Implies(Ord2Node):
    pass


# int-int operations


@dc.dataclass(frozen=True, repr=False)
class Sum(OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class AbsDiff(Ord2Node):
    pass


# bool-int operations


@dc.dataclass(frozen=True, repr=False)
class ToInt(OperationNode):
    pass


# int-bool operations


@dc.dataclass(frozen=True, repr=False)
class Equals(Op2Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class LessThan(Ord2Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class LessEqualThan(Ord2Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class GreaterThan(Ord2Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class GreaterEqualThan(Ord2Node):
    pass


# quantifier operations


@dc.dataclass(frozen=True, repr=False)
class AtLeast(Valued[int], OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class AtMost(Valued[int], OperationNode):
    pass


# branching operations


@dc.dataclass(frozen=True, repr=False)
class Multiplexer(Op3Node):
    @property
    def origin(self) -> str:
        return self.items[0]

    @property
    def parameter_1(self) -> str:
        return self.items[1]

    @property
    def parameter_2(self) -> str:
        return self.items[2]


@dc.dataclass(frozen=True, repr=False)
class If(Op3Node):
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
boolean_nodes = (BoolVariable, BoolConstant, Not, And, Or, Implies, Equals, AtLeast, AtMost, LessThan, LessEqualThan, GreaterThan, GreaterEqualThan, Multiplexer,)
integer_nodes = (IntVariable, IntConstant, ToInt, Sum, AbsDiff,)
untyped_nodes = (Copy, Target, If,)
#
contact_nodes = (PlaceHolder,)  # TODO:MARCO: what name should we use?
#
origin_nodes = (BoolVariable, BoolConstant, IntVariable, IntConstant,)
end_nodes = (Copy, Target,)
