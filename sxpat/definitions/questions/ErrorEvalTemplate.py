from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

from sxpat.templating.Template import Template

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import flat, iterable_replace, pairwise


__all__ = ['ErrorEvalTemplate']

class ErrorEvalTemplate:

    @classmethod
    def define(cls, s_graph: SGraph, specs: Specifications) -> Tuple[PGraph, CGraph]:

        a_graph: SGraph = set_prefix(s_graph, 'a_')

        others = []

        
        template_graph = PGraph(
            it.chain(
                (
                    n
                    for n in a_graph.nodes
                ),
                others
            ),
            a_graph.inputs_names, a_graph.outputs_names,
            ()
        )
        
        others = []
        
        others.extend([
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),
            maximize := Max('maximize', operands=(abs_diff,))
        ])


        constraint_graph = CGraph(
            it.chain(
                # placeholders
                (PlaceHolder(name) for name in it.chain(
                    s_graph.outputs_names,
                    template_graph.outputs_names
                )),
                others,
            )
        )

        return (template_graph, constraint_graph)
        


