from abc import (
    ABCMeta,
    abstractmethod,
)
from typing import (
    Iterable,
    List,
    Sequence,
    Tuple,
    Union,
    cast,
    override,
)
from typing_extensions import (
    TypeAlias,
)

import itertools as it
from sxpat.utils.collections import (
    formatted_int_range,
)
from sxpat.utils.decorators import (
    make_utility_class,
)

from sxpat.graph.graph import (
    CGraph,
)
from sxpat.graph.node import (
    AnyBoolResType,
    AnyDynamicResType,
    AnyNode,
    If,
    IntConstant,
    PlaceHolder,
    Sum,
)


__all__ = ['']


AnyBoolOperand: TypeAlias = Union[
    AnyBoolResType,
    AnyDynamicResType
]


@make_utility_class
class SimpleExpression(metaclass=ABCMeta):
    """@authors: Marco Biasion"""

    @classmethod
    def define(
        cls,
        operands: Sequence[AnyBoolOperand],
        expression_id: str = 'x',
    ) -> Tuple[CGraph, str]:
        """Define the expression, returns the CGraph of the expression and the name of the root."""

        # define nodes
        expr_nodes, root_name = cls.define_raw(operands, expression_id)

        # return graph
        return (CGraph(expr_nodes), root_name)

    @classmethod
    @abstractmethod
    def define_raw(
        cls,
        operands: Sequence[AnyBoolOperand],
        expression_id: str = 'x',
    ) -> Tuple[Sequence[AnyNode], str]:
        """Define the expression, returns the Sequence of nodes of the expression and the name of the root."""


class CountTrue(SimpleExpression):
    """
        Defines an expression that evaluates to the number of True operands.

        @authors: Marco Biasion
    """

    @classmethod
    @override
    def define_raw(
        cls,
        operands: Sequence[AnyBoolOperand],
        expression_id: str = 'x',
    ) -> Tuple[Sequence[AnyNode], str]:

        operands = tuple(op.name for op in operands)

        # create constants and integer value for each operand
        consts: List[IntConstant] = list()
        int_node: List[If] = list()
        for (op_i, op) in zip(formatted_int_range(len(operands)), operands):
            consts.extend((
                const_0 := IntConstant(f'{expression_id}_{op_i}_const0', value=0),
                const_1 := IntConstant(f'{expression_id}_{op_i}_const1', value=1),
            ))
            int_node.append(If(f'{expression_id}_{op_i}', operands=[op, const_1, const_0]))

        # distance
        expr_root = Sum(f'{expression_id}_expr', operands=int_node)

        return (
            tuple(it.chain(
                (PlaceHolder(name) for name in operands),
                consts,
                int_node,
                [expr_root],
            )),
            expr_root.name
        )


class CountTrueWeights(SimpleExpression):
    """
        Defines an expression that evaluates to the sum of the weights of True operands.

        @authors: Marco Biasion
    """

    @classmethod
    @override
    def define_raw(
        cls,
        operands: Sequence[AnyBoolOperand],
        expression_id: str = 'x',
    ) -> Tuple[Sequence[AnyNode], str]:

        operands = tuple(op.name for op in operands)

        # create constants and integer value for each operand
        consts: List[IntConstant] = list()
        int_node: List[If] = list()
        for (op_i, op) in zip(formatted_int_range(len(operands)), operands):
            val: int = cast(int, op.weight)
            consts.extend((
                const_0 := IntConstant(f'{expression_id}_{op_i}_const0', value=0),
                const_n := IntConstant(f'{expression_id}_{op_i}_const{val}', value=val),
            ))
            int_node.append(If(f'{expression_id}_{op_i}', operands=[op, const_n, const_0]))

        # distance
        expr_root = Sum(f'{expression_id}_expr', operands=int_node)

        return (
            tuple(it.chain(
                (PlaceHolder(name) for name in operands),
                consts,
                int_node,
                [expr_root],
            )),
            expr_root.name
        )
