from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

from .Template import Template

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import flat, iterable_replace, pairwise


__all__ = ['v2Phase1']

class v2Phase1:

    @classmethod
    def define(cls, s_graph: SGraph, specs: Specifications) -> Tuple[PGraph, CGraph]:

        a_graph: SGraph = set_prefix(s_graph, 'a_')

        variables: List[BoolVariable] = []
        outs: List[If] = []
        updated_nodes: Dict[str, OperationNode] = dict()
        others = []

        for (out_i, out_node) in enumerate(a_graph.subgraph_outputs):
            # print(out_i, out_node)
            
            variables.append(p_o := BoolVariable(f'p_o{out_i}', in_subgraph=True))
            others.append(tempN1 := Not(f'tempN1_o{out_i}', in_subgraph=True, operands=(p_o,)))
            others.append(tempN2 := Not(f'tempN2_o{out_i}', in_subgraph=True, operands=(out_node,)))
            others.append(tempA1 := And(f'tempA1_o{out_i}', in_subgraph=True, operands=(tempN1, out_node)))
            others.append(tempA2 := And(f'tempA2_o{out_i}', in_subgraph=True, operands=(tempN2, p_o)))
            outs.append(new_out_node := Or(f'sw_o{out_i}', in_subgraph=True, operands=(tempA1, tempA2)))

            for succ in filter(lambda n: not n.in_subgraph, a_graph.successors(out_node)):
                succ = updated_nodes.get(succ.name, succ)
                new_operands = iterable_replace(succ.operands, succ.operands.index(out_node.name), new_out_node.name)
                updated_nodes[succ.name] = succ.copy(operands=new_operands)
        
        template_graph = PGraph(
            it.chain(
                (
                    n
                    for n in a_graph.nodes
                    if n.name not in updated_nodes
                ),
                updated_nodes.values(),
                variables, outs, others
            ),
            a_graph.inputs_names, a_graph.outputs_names,
            (n.name for n in variables)
        )
        # print()
        # for node in template_graph.nodes:
        #     print(node)
        # exit(0)
        


