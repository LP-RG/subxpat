from typing import Tuple

import itertools as it

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.graph.node import ToInt, AbsDiff, Max, PlaceHolder, Target, AnyNode
from sxpat.graph.components import IO, Constraints


__all__ = ['MaxDistanceEvaluation']

class MaxDistanceEvaluation:

    @classmethod
    def define(cls, circuit: Graph) -> Tuple[Graph, Graph]:

        a_graph: Graph = set_prefix(circuit, 'a_')

        template_graph_builder = GraphBuilder()
        template_graph_builder.add_all_nodes_from(a_graph)
        template_graph_builder.add_base_component(
            IO({'inputs_names': a_graph.base_components['IO'].inputs_names, 
                'outputs_names': a_graph.base_components['IO'].outputs_names
            })
        )
        template_graph = template_graph_builder.create()
        # template_graph = template_graph_builder.create(extra_components=[
        #                                                    IO(a_graph.base_components['IO'].inputs_names, 
        #                                                       a_graph.base_components['IO'].outputs_names)
        #                                                ])

        graph_builder = GraphBuilder()
        graph_builder.add_autofill_component('Constraints')
        # others = [
        #     cur_int := ToInt('cur_int', operands=circuit.base_components['IO'].outputs_names),
        #     tem_int := ToInt('tem_int', operands=template_graph.base_components['IO'].outputs_names),
        #     abs_diff := AbsDiff('error', operands=(cur_int, tem_int,)),
        #     maximize := Max('maximize', operands=(abs_diff,))
        # ]
        cur_int = graph_builder.add_node('cur_int', ToInt).add_operands(list(circuit.base_components['IO'].outputs_names)).current
        tem_int = graph_builder.add_node('tem_int', ToInt).add_operands(list(template_graph.base_components['IO'].outputs_names)).current
        abs_diff = graph_builder.add_node('error', AbsDiff).add_operands([cur_int.name, tem_int.name]).current
        maximize = graph_builder.add_node('maximize', Max).add_operands([abs_diff.name]).current

        # graph_nodes = list(it.chain(
        #     # placeholders
        #     list(PlaceHolder(name) for name in it.chain(
        #         circuit.base_components['IO'].outputs_names,
        #         template_graph.base_components['IO'].outputs_names
        #     )),
        #     others,
        #     [Target.of(abs_diff),]
        # ))
        for name in it.chain(circuit.base_components['IO'].outputs_names,
                             template_graph.base_components['IO'].outputs_names):
            graph_builder.add_node(name, PlaceHolder) 
        
        node_name, operands = Target.of(abs_diff)
        graph_builder.add_node(node_name, Target).add_operands(operands)
        constraint_graph = graph_builder.create()

        # constraint_graph = Graph(
        #     graph_nodes,
        #     [Constraints(graph_nodes)]
        # )

        return (template_graph, constraint_graph)
