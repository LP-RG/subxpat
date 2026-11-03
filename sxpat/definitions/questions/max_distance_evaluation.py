from typing import Tuple

import itertools as it

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.graph.node import ToInt, AbsDiff, Max, PlaceHolder, Target
from sxpat.graph.graphCreators import GraphBuilder
from sxpat.graph.components import IO


__all__ = ['MaxDistanceEvaluation']

# GRAPH CREATION/COPY
class MaxDistanceEvaluation:

    @classmethod
    def define(cls, circuit: IOGraph) -> Tuple[IOGraph, CGraph]:

        a_graph: IOGraph = set_prefix(circuit, 'a_')

        template_graph_builder = GraphBuilder()
        template_graph_builder.add_inherited_nodes([n for n in a_graph.nodes], a_graph)
        template_graph = template_graph_builder.create(IOGraph, 
                                                       extra_components=[
                                                           IO(a_graph.base_components['IO'].inputs_names, 
                                                              a_graph.base_components['IO'].outputs_names)
                                                       ])

        # template_graph = IOGraph(
        #     (n for n in a_graph.nodes),
        #     a_graph.inputs_names, a_graph.outputs_names,
        # )

        others = [
            cur_int := ToInt('cur_int', operands=circuit.base_components['IO'].outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.base_components['IO'].outputs_names),
            abs_diff := AbsDiff('error', operands=(cur_int, tem_int,)),
            maximize := Max('maximize', operands=(abs_diff,))
        ]

        constraint_graph = CGraph(
            it.chain(
                # placeholders
                (PlaceHolder(name) for name in it.chain(
                    circuit.base_components['IO'].outputs_names,
                    template_graph.base_components['IO'].outputs_names
                )),
                others,
                [Target.of(abs_diff),]
            )
        )

        return (template_graph, constraint_graph)
