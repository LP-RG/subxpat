from typing import Tuple

import itertools as it

from sxpat.converting import set_prefix
from sxpat.graph import *


__all__ = ['MaxDistanceEvaluation']


class MaxDistanceEvaluation:

    @classmethod
    def define(cls, s_graph: SGraph) -> Tuple[IOGraph, CGraph]:

        a_graph: SGraph = set_prefix(s_graph, 'a_')

        template_graph = IOGraph(
            (n for n in a_graph.nodes),
            a_graph.inputs_names, a_graph.outputs_names,
        )

        others = [
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('error', operands=(cur_int, tem_int,)),
            maximize := Max('maximize', operands=(abs_diff,))
        ]

        constraint_graph = CGraph(
            it.chain(
                # placeholders
                (PlaceHolder(name) for name in it.chain(
                    s_graph.outputs_names,
                    template_graph.outputs_names
                )),
                others,
                [Target.of(abs_diff),]
            )
        )

        return (template_graph, constraint_graph)
