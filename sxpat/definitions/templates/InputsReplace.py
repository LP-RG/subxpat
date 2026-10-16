from __future__ import annotations
from typing import Dict, Optional, Sequence, Tuple, Union

import itertools as it

from sxpat.converting.utils import set_prefix_new
from sxpat.graph.graph import CGraph, IOGraph, PGraph, SGraph
from sxpat.graph.node import (
    AbsDiff, BoolConstant, BoolVariable, Constraint, ForAll, IntConstant,
    LessEqualThan, Node, PlaceHolder, Target, ToInt,
)
from sxpat.specifications import Specifications
from sxpat.utils.collections import iterable_replace_index


__all__ = ['InputsReplace']


class InputsReplace:
    """
        Helper defining the "slash of inputs" question.

        Given a circuit and a set of inputs to remove, defines a parametric circuit
        (a `PGraph`) in which every removed input is replaced by a single shared
        boolean value, together with the `CGraph` asserting that the resulting
        circuit stays within `specs_obj.error_for_slash` of the original one for
        every assignment of the remaining inputs.

        The replacement value is shared between all the removed inputs, so a single
        boolean value replaces the whole set (this is what makes the circuit smaller
        than the original).

        @authors: Marco Biasion, Lorenzo Spada
    """

    @classmethod
    def build(cls,
              current: IOGraph,
              selected_nodes: Sequence[str],
              replace_output: bool = True,
              replace_with_constant: Optional[bool] = None,
              ) -> PGraph:
        """
            Builds the parametric circuit obtained by replacing the selected inputs
            with a single shared boolean value.

            All the nodes of the original circuit are prefixed with `a_` (so that the
            parametric circuit can coexist with the original one in the same question),
            except the inputs (and the outputs, when `replace_output` is `False`).

            :param current: the circuit whose inputs are to be removed.
            :param selected_nodes: the names of the inputs to remove.
            :param replace_output: if the outputs should be prefixed too (they are not
                preserved). Set to `False` to keep the original output names.
            :param replace_with_constant: if not `None`, the removed inputs are replaced
                by a fixed boolean constant instead of a shared parameter, and the
                resulting circuit is fully determined.
        """

        # guard: only existing inputs can be removed
        for selected_node in selected_nodes:
            if selected_node not in current:
                raise ValueError(f'Node {selected_node!r} to slash is not in the circuit')
            if not isinstance(current[selected_node], BoolVariable):
                raise ValueError(f'Node {selected_node!r} to slash is not an input')

        # the inputs must be shared with the original circuit; the outputs are prefixed
        # (i.e. replaced) unless explicitly preserved
        preserved = current.inputs_names if replace_output else it.chain(current.inputs_names, current.outputs_names)
        a_graph: SGraph = set_prefix_new(current, 'a_', preserved)

        # the value each removed input is replaced with
        if replace_with_constant is not None:
            identity_node: Union[BoolVariable, BoolConstant] = BoolConstant('constant_ID', value=replace_with_constant)
        else:
            identity_node = BoolVariable('constant_ID')

        # rewire every successor of a removed input to use the replacement value
        updated_nodes: Dict[str, Node] = dict()
        for selected_node in selected_nodes:
            for succ in a_graph.successors(selected_node):
                # if the successor was already updated, use the updated version
                succ = updated_nodes.get(succ.name, succ)
                new_operands = iterable_replace_index(
                    succ.operands, succ.operands.index(selected_node), identity_node.name,
                )
                updated_nodes[succ.name] = succ.copy(operands=new_operands)

        # the parametric circuit: the original (prefixed) nodes that were not rewired,
        # the replacement value and the rewired nodes
        return PGraph(
            it.chain(
                (n for n in a_graph.nodes if n.name not in updated_nodes),
                (identity_node,),
                updated_nodes.values(),
            ),
            a_graph.inputs_names,
            a_graph.outputs_names,
            [identity_node.name] if replace_with_constant is None else [],
        )

    @classmethod
    def define(cls,
               current: IOGraph,
               specs_obj: Specifications,
               selected_nodes: Sequence[str],
               replace_output: bool = True,
               ) -> Tuple[PGraph, CGraph]:
        """
            Builds the parametric circuit and the constraint asserting that, for every
            assignment of the remaining inputs, the distance between the outputs of the
            original circuit and of the parametric one is at most `error_for_slash`.

            The replacement value is returned as a target, so that a model with
            `constant_ID = False` (resp. `True`) corresponds to tying the removed
            inputs to `0` (resp. `1`).
        """

        template_graph = cls.build(current, selected_nodes, replace_output=replace_output)

        # the constraint: | current.outputs - template.outputs | <= error_for_slash, forall inputs
        new_nodes = [
            cur_int := ToInt('cur_int', operands=current.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', operands=(cur_int.name, tem_int.name)),
            et := IntConstant('et_const', value=specs_obj.error_for_slash),
            less_than := LessEqualThan('less_than', operands=(abs_diff.name, et.name)),
            Constraint.of(less_than),
        ]

        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    current.outputs_names,
                    current.inputs_names,
                    template_graph.outputs_names,
                    ('constant_ID',),
                )),
                new_nodes,
                (Target.of('constant_ID'),),
                (ForAll('forall_inputs', operands=current.inputs_names),),
            )
        )

        return (template_graph, constraint_graph)
