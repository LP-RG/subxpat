from typing import Dict, List, Sequence, Tuple
from typing_extensions import Never

import itertools as it

from .Template import Template

from sxpat.graph import SGraph, PGraph
from sxpat.graph.node import AnyOperation, BoolVariable

from sxpat.utils.collections import iterable_replace
from sxpat.converting.utils import prune_unused, set_prefix_new


__all__ = ['SharedTemplate']


circuit_prefix = 'a_'


class ConstantTemplate(Template):
    """
        This template allows only for constants at the subgraph outputs.

        @authors: Marco Biasion
    """

    @classmethod
    def define(cls, current_circ: SGraph, _unused) -> Tuple[PGraph, Sequence[Never]]:

        # create/update nodes
        parameters: List[BoolVariable] = list()
        updated_nodes: Dict[str, AnyOperation] = dict()
        for (sub_i, out_node) in enumerate(current_circ.subgraph_outputs):
            # create parameter
            parameters.append(param := BoolVariable(f'p{sub_i}', in_subgraph=True))

            # update successors
            for succ in current_circ.successors(out_node):
                if not succ.in_subgraph:
                    succ = updated_nodes.get(succ.name, succ)
                    new_operands = iterable_replace(succ.operands, out_node.name, param.name)
                    updated_nodes[succ.name] = succ.copy(operands=new_operands)

        # create parametric circuit
        param_circ = PGraph.copy(
            current_circ,
            it.chain(
                (  # replace updated nodes
                    updated_nodes.get(n.name, n)
                    for n in current_circ.nodes
                ),
                parameters,
            ),
            parameters_names=(n.name for n in parameters),
        )
        # remove unused nodes
        param_circ = prune_unused(
            param_circ,
            it.chain(
                current_circ.inputs_names,
                current_circ.outputs_names,
                current_circ.parameters_names,
            )
        )
        # prefix all nodes
        param_circ = set_prefix_new(
            param_circ, circuit_prefix,
            current_circ.inputs_names,
        )

        return (param_circ, tuple())
