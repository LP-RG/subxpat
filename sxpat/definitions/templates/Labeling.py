import itertools as it

from sxpat.converting.utils import set_prefix_new
from sxpat.graph.graph import CGraph, PGraph, SGraph
from sxpat.graph.node import (
    AbsDiff, Constraint, GreaterThan, IntConstant, Max, Min, Node, Not, PlaceHolder,
    Target, ToInt,
)
from sxpat.utils.collections import iterable_replace_index


__all__ = ['Labeling']


class Labeling:
    """
    Template used to compute the weight of a single node.

    A copy of the circuit is built in which the value of the node to label is
    flipped (its successors are rewired to read its negation); the absolute
    difference between the integer outputs of the original and the flipped copy
    is then minimised or maximised to obtain the node's weight.
    """

    @classmethod
    def define(cls, s_graph: SGraph, accs=[], min_labeling: bool = False):
        assert len(accs) == 1, "Must pass the node to label"
        assert accs[0] in s_graph, "Node requested to label must be in the graph"

        a_graph: SGraph = set_prefix_new(s_graph, 'a_', it.chain(s_graph.inputs_names))

        labeled_node = accs[0]
        labeled_node_name = labeled_node if labeled_node[:2] == 'in' else 'a_' + labeled_node
        not_node = Not(f'not_{labeled_node}', operands=(labeled_node_name,))

        # every successor of the labelled node now reads its negated value
        updated_nodes: dict[str, Node] = dict()
        for succ in a_graph.successors(labeled_node_name):
            new_operands = iterable_replace_index(
                succ.operands, succ.operands.index(labeled_node_name), not_node.name,
            )
            updated_nodes[succ.name] = succ.copy(operands=new_operands)

        template_graph = PGraph(
            it.chain(
                (n for n in a_graph.nodes if n.name not in updated_nodes),
                (not_node,),
                updated_nodes.values(),
            ),
            a_graph.inputs_names,
            a_graph.outputs_names,
            (),
        )

        new_nodes = [
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('weight', operands=(cur_int.name, tem_int.name)),
            {
                True: Min('minimize_error', operands=(abs_diff.name,)),
                False: Max('maximize_error', operands=(abs_diff.name,)),
            }[min_labeling],
        ]

        if min_labeling:
            new_nodes.extend([
                zero := IntConstant('Zero', value=0),
                gt := GreaterThan('GT_0', operands=(abs_diff.name, zero.name)),
                Constraint.of(gt),
            ])

        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    s_graph.outputs_names,
                    template_graph.outputs_names,
                )),
                new_nodes,
                (Target.of(abs_diff),),
            )
        )

        return (template_graph, constraint_graph)
