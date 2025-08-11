from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

from .Template import Template

from sxpat.converting.utils import set_prefix_new
from sxpat.graph import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import iterable_replace


__all__ = ['Labeling']

class Labeling:

        
    @classmethod
    def define(cls, s_graph: SGraph, specs: Specifications, accs = []) -> Tuple[PGraph, CGraph]:


        assert len(accs) == 1 , "Must pass the node to label"
        assert accs[0] in s_graph , "Node requested to label must be in the graph"

        a_graph: SGraph = set_prefix_new(s_graph, 'a_', it.chain(s_graph.inputs_names))

        labeled_node = accs[0]
        not_node = Not(f'not_{labeled_node}', operands=('a_' + labeled_node,))

        updated_nodes: Dict[str, Node] = dict()

        for succ in a_graph.successors('a_' + labeled_node):
            new_operands = iterable_replace(succ.operands, succ.operands.index('a_' + labeled_node), not_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)
        
        
        template_graph = PGraph(
            it.chain(
                (
                    n
                    for n in a_graph.nodes
                    if n.name not in updated_nodes
                ),
                (not_node,),
                updated_nodes.values(),
            ),
            a_graph.inputs_names,
            a_graph.outputs_names,
            ()
        )
        
        new_nodes = [
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('weight', operands=(cur_int, tem_int,)),
            {
            True: Min('minimize error', operands=(abs_diff,)),
            False: Max('maximize error', operands=(abs_diff,))
            }[specs.min_labeling]
        ]

        if specs.min_labeling:
            new_nodes.extend([
                zero := IntConstant('Zero', value=0),
                gt := GreaterThan('GT_0', operands=(abs_diff, zero)),
                Constraint.of(gt),
            ])
    

        constraint_graph = CGraph(
            it.chain(
                # placeholders
                (PlaceHolder(name) for name in it.chain(
                    s_graph.outputs_names,
                    template_graph.outputs_names
                )),
                new_nodes,
                [Target.of(abs_diff),]
            )
        )

        return (template_graph, constraint_graph)

