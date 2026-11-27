import itertools as it

from sxpat.converting.utils import set_prefix_new
from sxpat.graph.graph import *
from sxpat.graph.node import *
from sxpat.specifications import Specifications
from sxpat.utils.collections import iterable_replace_index
from sxpat.graph.components import IO


__all__ = ['Labelling', 'label_node']


class Labelling:

    @classmethod
    def define(cls, graph: Graph, accs=[], min_labeling=False):
        assert len(accs) == 1, "Must pass the node to label"
        assert accs[0] in graph, f"Node requested to label ({accs[0]}) must be in the graph"
        if accs[0] not in graph: raise ValueError(f"Node '{accs[0]}' not found in graph")

        a_graph: Graph = set_prefix_new(graph, 'a_', it.chain(graph.base_components['IO'].inputs_names))

        template_graph_builder = GraphBuilder()

        labeled_node = accs[0]
        labeled_node_name = labeled_node if labeled_node[:2] == 'in' else 'a_' + labeled_node
        not_node = template_graph_builder.add_node(f'not_{labeled_node}', Not).add_operands([labeled_node_name]).current

        updated_nodes: dict[str, Node] = dict()
        for succ in a_graph.successors(labeled_node_name):
            succ_operands = a_graph.base_components['Topology'].operands(succ.name)
            new_operands = iterable_replace_index(succ_operands, succ_operands.index(labeled_node_name), not_node.name)
            updated_nodes[succ.name] = template_graph_builder.add_node_copy(
                succ,
                a_graph,
                operands=list(new_operands)
            ).current
        constraint_nodes = []
        nodes_to_place_hold = []

        for n in a_graph.nodes:
            if n.name not in updated_nodes:
                template_graph_builder.add_node_from(n, a_graph)

        template_graph_builder.add_base_component(IO({'inputs_names': a_graph.base_components['IO'].inputs_names, 
                                                      'outputs_names': a_graph.base_components['IO'].outputs_names}))
        template_graph = template_graph_builder.create()


        constraint_graph_builder = GraphBuilder()
        constraint_graph_builder.add_autofill_component('Constraints')

        cur_int = constraint_graph_builder.add_node('cur_int', ToInt).add_operands(list(graph.base_components['IO'].outputs_names)).current
        tem_int = constraint_graph_builder.add_node('tem_int', ToInt).add_operands(list(template_graph.base_components['IO'].outputs_names)).current
        abs_diff = constraint_graph_builder.add_node('weight', AbsDiff).add_operands([cur_int.name, tem_int.name]).current
        if min_labeling:
            constraint_graph_builder.add_node('minimize_error', Min).add_operands([abs_diff.name])
        else:
            constraint_graph_builder.add_node('maximize_error', Max).add_operands([abs_diff.name])

        if min_labeling:
            zero = constraint_graph_builder.add_node('Zero', IntConstant).add_extras(value=0).current
            gt = constraint_graph_builder.add_node('GT_0', GreaterThan).add_operands([abs_diff.name, zero.name]).current
            constraint_name, operands = Constraint.of(gt)
            constraint_graph_builder.add_node(constraint_name, Constraint).add_operands(operands)
        
        # placeholders
        for name in it.chain(graph.base_components['IO'].outputs_names,
                             template_graph.base_components['IO'].outputs_names,
                             nodes_to_place_hold):
            constraint_graph_builder.add_node(name, PlaceHolder)

        target_name, operands = Target.of(abs_diff)
        constraint_graph_builder.add_node(target_name, Target).add_operands(operands)
        constraint_graph = constraint_graph_builder.create()

        return (template_graph, constraint_graph)


def label_node(exact_graph: Graph, current_graph: Graph, cur_node, specs_obj: Specifications):
    from sxpat.solvers.QbfSolver import QbfSolver

    define_template = Labelling.define
    p_graph, c_graph = define_template(current_graph, [cur_node], min_labeling=specs_obj.min_labeling)
    solve = QbfSolver.solve
    status, model = solve((exact_graph, p_graph, c_graph), specs_obj)
    return model['weight']  # type: ignore
