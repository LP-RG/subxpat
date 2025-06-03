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
        
        ifl = []
        others = [zeroC := IntConstant(f'zero_const', value=0)]
        

        for (out_i, out_node) in enumerate(a_graph.subgraph_outputs):
            others.extend([
                weight := IntConstant(f'weight_o{out_i}', value=out_node.weight)
            ])
            ifl.append(If(f'if_o{out_i}', operands=(variables[out_i], weight, zeroC)))
        
        others.extend([
            sum := Sum('sum_s_out', operands=ifl),
            min := Min('minimize', operands=(sum,)),
            Constraint.of(min)
        ])
        
        others.extend([
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),
            et := IntConstant('et', value=specs.et),
            error_check := GreaterThan('error_check', operands=(abs_diff, et)),
            Constraint.of(error_check),
        ])


        constraint_graph = CGraph(
            it.chain(
                # placeholders
                (PlaceHolder(name) for name in it.chain(
                    (p.name for p in variables),
                    s_graph.outputs_names,
                    template_graph.outputs_names
                )),
                ifl,
                others,
                (Target.of(param) for param in variables),
            )
        )

        exit(0)
        #  python3 -u main.py adder_i4_o3 --subxpat -e=2 --mode=55 --imax=4 --omax=2 --max-lpp=5 --max-ppo=5 --template=temp --clean
        


