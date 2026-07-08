from typing import ClassVar, Mapping

import itertools as it

from sxpat.graph import *
from sxpat.graph.node import *

from sxpat.converting.utils import set_prefix_new
from sxpat.solvers.Z3Solver import Z3DirectIntSolver
from sxpat.specifications import Specifications
from sxpat.utils.collections import iterable_replace


__all__ = ['Labelling']


class Labelling:
    """
        :authors: Marco Biasion, Lorenzo Spada
    """

    __slots__ = [
        'reference', 'to_be_labelled',
        '_minimise', '_specs',
    ]

    def __init__(
        self,
        reference: IOGraph, to_be_labelled: IOGraph,
        *,
        specs: Specifications,
    ):
        # store
        self.reference = set_prefix_new(reference, 'ref_', it.chain(reference.inputs_names))
        self.to_be_labelled = to_be_labelled
        #
        self._minimise = specs.min_labeling
        self._specs = specs

    def label_node(self, node_to_label: str) -> int:
        # define question
        question = [
            self.reference,
            *self._define_question(node_to_label)
        ]

        # run solver
        status, model = Z3DirectIntSolver.solve(question, self._specs)
        assert status == 'sat'

        # extract node weight
        return model['weight']

    def label_graph(self) -> Mapping[str, int]:
        raise NotImplementedError('To be done later')

    def _define_question(self, node_to_label: str):
        # > guards
        if node_to_label not in self.to_be_labelled:
            raise ValueError(f'Node {node_to_label} not found in circuit')

        # > define "broken" circuit (the behaviour)
        # define target node
        not_node = Not(f'not_{node_to_label}', operands=[node_to_label])
        # update successors of target node
        updated_nodes: dict[str, Node] = dict()
        for succ in self.to_be_labelled.successors(node_to_label):
            new_operands = iterable_replace(succ.operands, node_to_label, not_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)
        # construct circuit
        broken_circuit = PGraph(
            it.chain(
                (
                    n
                    for n in self.to_be_labelled.nodes
                    if n.name not in updated_nodes
                ),
                (not_node,),
                updated_nodes.values(),
            ),
            self.to_be_labelled.inputs_names,
            self.to_be_labelled.outputs_names,
            ()
        )

        # > define the constraints (error and rules)
        # define error function (and optimisation)
        new_nodes = [
            cur_int := ToInt('cur_int', operands=self.reference.outputs_names),
            tem_int := ToInt('tem_int', operands=broken_circuit.outputs_names),
            abs_diff := AbsDiff('weight', operands=[cur_int.name, tem_int.name]),
            {
                True: Min('minimise_error', operands=[abs_diff.name]),
                False: Max('maximise_error', operands=[abs_diff.name])
            }[self._minimise]
        ]
        if self._minimise:
            new_nodes.extend([
                zero := IntConstant('Zero', value=0),
                gt := GreaterThan('GT_0', operands=[abs_diff.name, zero.name]),
                Constraint.of(gt),
            ])
        # construct structure
        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    self.reference.outputs_names,
                    broken_circuit.outputs_names,
                )),
                new_nodes,
                [Target.of(abs_diff)]
            )
        )

        return (broken_circuit, constraint_graph)
