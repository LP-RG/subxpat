import itertools as it
from typing import Iterable

from sxpat.converting.utils import set_prefix_new
from sxpat.graph.graph import *
from sxpat.graph.node import *
from sxpat.specifications import Specifications
from sxpat.utils.collections import iterable_replace_index


__all__ = ['Labelling', 'label_node']


class Labelling:

    @classmethod
    def define(cls, graph: IOGraph, accs=[], min_labeling=False):
        assert len(accs) == 1, "Must pass the node to label"
        assert accs[0] in graph, f"Node requested to label ({accs[0]}) must be in the graph"
        if accs[0] not in graph: raise ValueError(f"Node '{accs[0]}' not found in graph")

        a_graph: IOGraph = set_prefix_new(graph, 'a_', it.chain(graph.inputs_names))

        labeled_node = accs[0]
        labeled_node_name = labeled_node if labeled_node[:2] == 'in' else 'a_' + labeled_node
        not_node = Not(f'not_{labeled_node}', operands=(labeled_node_name,))

        updated_nodes: dict[str, Node] = dict()
        for succ in a_graph.successors(labeled_node_name):
            new_operands = iterable_replace_index(succ.operands, succ.operands.index(labeled_node_name), not_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)
        constraint_nodes = []
        nodes_to_place_hold = []

        a: Iterable[str] = it.chain(['a', 'b'])

        template_graph = PGraph(
            it.chain(  # type: ignore
                    (
                        n
                        for n in a_graph.nodes
                        if n.name not in updated_nodes
                    ),
                (not_node,),
                updated_nodes.values(),
                constraint_nodes
            ),
            a_graph.inputs_names,
            a_graph.outputs_names,
            ()
        )

        new_nodes = [
            cur_int := ToInt('cur_int', operands=graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('weight', operands=(cur_int.name, tem_int.name)),
            {
                True: Min('minimize_error', operands=(abs_diff.name,)),
                False: Max('maximize_error', operands=(abs_diff.name,))
            }[min_labeling]
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
                    graph.outputs_names,
                    template_graph.outputs_names,
                    nodes_to_place_hold
                )),
                new_nodes,
                [Target.of(abs_diff),]
            )
        )

        return (template_graph, constraint_graph)


def label_node(exact_graph: IOGraph, current_graph: IOGraph, cur_node, specs_obj: Specifications):
    from sxpat.solvers.QbfSolver import QbfSolver

    define_template = Labelling.define
    p_graph, c_graph = define_template(current_graph, [cur_node], min_labeling=specs_obj.min_labeling)
    solve = QbfSolver.solve
    status, model = solve((exact_graph, p_graph, c_graph), specs_obj)
    return model['weight']  # type: ignore
