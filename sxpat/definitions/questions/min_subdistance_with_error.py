from typing import (
    Sequence,
    Tuple,
    Type,
)

from sxpat.graph.graph import (
    CGraph,
    PGraph,
    SGraph,
)
from sxpat.definitions.templates import (
    ConstantTemplate,
    SwitchedTemplate,
)
from sxpat.definitions.distances import (
    DistanceSpecification,
    HammingDistance,
    WeightedHammingDistance,
)
from sxpat.definitions.questions import (
    exists_parameters,
    optimize_subgraph_distance,
)


class min_subdistance_with_error:
    @staticmethod
    def variant_1(current_circuit: SGraph,
                  threshold: int,
                  circuit_distance: Type[DistanceSpecification],
                  subcircuit_distance: Type[DistanceSpecification],
                  ) -> Tuple[PGraph, Sequence[CGraph]]:
        """@authors: Marco Biasion"""

        # create parametric circuit
        parametric_circuit, *_ = ConstantTemplate.define(current_circuit, None)

        # find parameters for error above threshold
        question_exists = exists_parameters.above_threshold(
            current_circuit, parametric_circuit,
            circuit_distance, threshold,
        )

        # minimize distance between subgraphs
        question_minimize = optimize_subgraph_distance.min(
            current_circuit, parametric_circuit,
            subcircuit_distance,
        )

        return (PGraph, (*question_exists, *question_minimize))

    @staticmethod
    def variant_2(current_circuit: SGraph,
                  threshold: int,
                  circuit_distance: Type[DistanceSpecification],
                  subcircuit_distance: Type[DistanceSpecification],
                  ) -> Tuple[PGraph, Sequence[CGraph]]:
        """@authors: Lorenzo Spada, Marco Biasion"""

        # to implement the distances we have:
        # - HammingDistance: given that the parameters represent bit flips
        #                    the distance is simply the sum of true parameters valued at 1 each
        # - WeightedHammingDistance: same as for the hamming distance but each parameter
        #                            is valued with its relative output weight
        # - AbsoluteDifferenceOfIntegers: ???
        # - WeightedHammingDistance: ???

        #
        # _current_circ: SGraph = set_prefix(current_circ, f'{circuit_prefix}_')

        # #
        # variables: List[BoolVariable] = []
        # outs: List[If] = []
        # updated_nodes: Dict[str, AnyOperation] = dict()
        # for (out_i, out_node) in enumerate(_current_circ.subgraph_outputs):
        #     # replace output with free varibale
        #     variables.append(param := BoolVariable(f'{logic_prefix}_p{out_i}', in_subgraph=True))
        #     outs.append(new_out_node := Xor(f'{logic_prefix}_o{out_i}', operands=(out_node, param), in_subgraph=True))

        #     for succ in _current_circ.successors(out_node):
        #         if not succ.in_subgraph:
        #             succ = updated_nodes.get(succ.name, succ)
        #             new_operands = iterable_replace(succ.operands, out_node.name, new_out_node.name)
        #             updated_nodes[succ.name] = succ.copy(operands=new_operands)

        # template_graph = PGraph(
        #     it.chain(
        #         (  # replace updated nodes
        #             updated_nodes.get(n.name, n)
        #             for n in _current_circ.nodes
        #         ),
        #         variables,
        #         outs,
        #     ),
        #     inputs_names=_current_circ.inputs_names,
        #     outputs_names=_current_circ.outputs_names,
        #     parameters_names=(n.name for n in variables),
        # )

        # # create parametric circuit
        # parametric_circuit, _ = SwitchedTemplate.define(current_circuit, None)

        # # create expression for d
        # aaa = {
        #     HammingDistance: HammingDistance
        #     WeightedHammingDistance: None,
        # }

        # ifl = []
        # others = [zeroC := IntConstant(f'zero_const', value=0)]

        # # subgraph distance
        # # sub_distance = AbsoluteDifferenceOfWeightedSum.define()

        # for (out_i, out_node) in enumerate(_current_circ.subgraph_outputs):
        #     others.extend([
        #         weight := IntConstant(f'weight_o{out_i}', value=out_node.weight),
        #     ])
        #     ifl.append(
        #         If(f'if_o{out_i}', operands=(variables[out_i], weight, zeroC))
        #     )

        # #
        # others.extend([
        #     sum := Sum('sum_s_out', operands=ifl),
        #     min := Min('minimize', operands=(sum,)),
        # ])

        # others.extend([
        #     # distance
        #     cur_int := ToInt('cur_int', operands=current_circ.outputs_names),
        #     tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
        #     abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),
        #     # error check
        #     et := IntConstant('et', value=error_threshold),
        #     error_check := GreaterThan('error_check', operands=(abs_diff, et)),
        #     Constraint.of(error_check),
        # ])

        # constraint_graph = CGraph(
        #     it.chain(
        #         # placeholders
        #         (PlaceHolder(name) for name in it.chain(
        #             (p.name for p in variables),
        #             current_circ.outputs_names,
        #             template_graph.outputs_names
        #         )),
        #         ifl,
        #         others,
        #         # (Target.of(param) for param in variables),
        #         (Target.of(sum),)
        #     )
        # )

        # return (template_graph, constraint_graph)
