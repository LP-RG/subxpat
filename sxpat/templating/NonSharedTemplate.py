from typing import Dict, List, Tuple

import itertools as it

from .Template import Template

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.specifications import ConstantsType, MetricType, Specifications
from sxpat.utils.collections import flat, iterable_replace, pairwise


__all__ = ['NonSharedTemplate']


class _NonSharedBase:
    """
       Base class for non shared utilities.

       @authors: Marco Biasion
    """

    @classmethod
    def construct_products(cls, a_graph: SGraph, products_per_output: int
                           ) -> Tuple[List[List[And]], List[List[List[Tuple[BoolVariable, BoolVariable]]]], List[Multiplexer]]:
        """
            Generates the products and all relative multiplexers and parameters.
        """

        products: List[List[And]] = []
        out_prod_mux_params: List[List[List[Tuple[BoolVariable, BoolVariable]]]] = []
        multiplexers: List[Multiplexer] = []

        # for all outputs
        for out_i, _ in enumerate(a_graph.subgraph_outputs):

            # for all products
            products.append([])
            out_prod_mux_params.append([])
            for prod_i in range(products_per_output):

                # create all multiplexers and relative parameters for the product
                _muxs, parameters = [], []
                for in_i, in_node in enumerate(a_graph.subgraph_inputs):
                    parameters.append((
                        (p_usage := BoolVariable(f'p_o{out_i}_t{prod_i}_i{in_i}_u', in_subgraph=True)),
                        (p_assert := BoolVariable(f'p_o{out_i}_t{prod_i}_i{in_i}_a', in_subgraph=True)),
                    ))
                    _muxs.append(Multiplexer(f'mux_o{out_i}_t{prod_i}_i{in_i}', in_subgraph=True, operands=[in_node, p_usage, p_assert]))
                out_prod_mux_params[-1].append(parameters)
                multiplexers.extend(_muxs)

                # create the product
                products[-1].append(And(f'o{out_i}_p{prod_i}', in_subgraph=True, operands=_muxs))

        return (
            products,
            out_prod_mux_params,
            multiplexers,
        )

    @classmethod
    def construct_sums(cls, a_graph: SGraph, products: List[List[And]]
                       ) -> List[Or]:
        return [
            Or(f'sum{out_i}', in_subgraph=True, operands=products[out_i])
            for out_i, _ in enumerate(a_graph.subgraph_outputs)
        ]

    @classmethod
    def constants_rewriting(cls, a_graph: SGraph, updated_nodes: Dict[str, OperationNode], specs: Specifications
                            ) -> List[BoolVariable]:
        """
            Generates the nodes for constants rewriting, will update `updated_nodes` inplace with the changed successors (if any).
        """

        # skip if constant rewriting is not needed
        if specs.constants is not ConstantsType.ALWAYS: return []

        constants_rewriting = []

        # for all constants
        for const in a_graph.constants:
            # if the constants is at the graph output
            if len(succs := a_graph.successors(const)) == 1 and (out_i := a_graph.output_index_of(succ := succs[0])) >= 0:
                constants_rewriting.append(const_rew := BoolVariable(f'p_c{out_i}'))
                updated_nodes[succ.name] = succ.copy(operands=(const_rew,))  # by definition, the output node has no other operand

        return constants_rewriting

    @classmethod
    def error_constraint(cls, s_graph: SGraph, t_graph: PGraph, error_threshold: int) -> List[Node]:
        return [
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=t_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),
            et := IntConstant('et', value=error_threshold),
            error_check := LessEqualThan('error_check', operands=(abs_diff, et)),
        ]
    
    @classmethod
    def relative_error_constraint(cls, s_graph: SGraph, t_graph: PGraph, error_threshold: int) -> List[Node]:
        return [
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=t_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),
            et := IntConstant('et', value=error_threshold),
            zero := IntConstant('zero', value = 0),
            one := IntConstant('one', value = 1),
            hundred := IntConstant('hundred', value = 100),
            condition := Equals('condition', operands = (cur_int, zero)),
            divider := If("divider", operands=(condition, one, cur_int)),
            abs_diff_hundred := Mul('abs_diff_hundred', operands=(abs_diff, hundred)),
            rel_diff := UDiv('rel_diff',operands=(abs_diff_hundred, divider)),
            error_check := LessEqualThan('error_check', operands=(rel_diff, et)),
        ]
    """@classmethod
    def relative_error_zone_constraint(cls, s_graph: SGraph, t_graph: PGraph, error_threshold: int, zone_constraint: int) -> List[Node]:
        return [
            *(PlaceHolder(name) for name in s_graph.inputs_names[:len(s_graph.inputs_names)//2]),
            input_one_value := ToInt('input_one', operands=s_graph.inputs_names[:len(s_graph.inputs_names)//2]),
            *(PlaceHolder(name) for name in s_graph.inputs_names[len(s_graph.inputs_names)//2:]),
            input_two_value := ToInt('input_one', operands=s_graph.inputs_names[len(s_graph.inputs_names)//2:]),
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=t_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),
            et := IntConstant('et', value=error_threshold),
            zero := IntConstant('zero', value = 0),
            one := IntConstant('one', value = 1),
            hundred := IntConstant('hundred', value = 100),
            mean_value := IntConstant('mean_value', value = 7),
            a := IntConstant('a', value = 81),
            condition := Equals('condition', operands = (cur_int, zero)),
            divider := If("divider", operands=(condition, one, cur_int)),
            abs_diff_hundred := Mul('abs_diff_hundred', operands=(abs_diff, hundred)),
            rel_diff := UDiv('rel_diff',operands=(abs_diff_hundred, divider)),
            # calculate distance from mean x2
            abs_diff_mean := AbsDiff('abs_diff_mean', operands=(input_two_value, mean_value)),
            distance_sum := Sum('distance_sum', operands=(abs_diff_mean, input_one_value)),
            square_distance_sum := Mul('square_distance_sum', operands=(distance_sum, distance_sum)),
            et_coefficient := Mul('et_coefficient', operands=(square_distance_sum, et)),
            undounded_et := UDiv('undounded_et', operands=(et_coefficient, a)),
            bounding_et_condition := LessEqualThan('bounding_et_condition', operands=(undounded_et, et)),
            final_et := If('final_et', operands=(bounding_et_condition, et, undounded_et)),
            error_check := LessEqualThan('error_check', operands=(rel_diff, final_et)),
        ]"""
    @classmethod
    def relative_error_zone_constraint(cls, s_graph: SGraph, t_graph: PGraph, error_threshold: int, zone_constraint: int) -> List[Node]:
        return [
            *(PlaceHolder(name) for name in s_graph.inputs_names[:len(s_graph.inputs_names)//2]),
            input_one_value := ToInt('input_one', operands=s_graph.inputs_names[:len(s_graph.inputs_names)//2]),
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=t_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),
            et := IntConstant('et', value=error_threshold),
            zero := IntConstant('zero', value = 0),
            one := IntConstant('one', value = 1),
            zone_limit := IntConstant('zone_limit', value = zone_constraint),
            hundred := IntConstant('hundred', value = 100),
            condition := Equals('condition', operands = (cur_int, zero)),
            divider := If("divider", operands=(condition, one, cur_int)),
            zone := LessEqualThan('zone', operands=(input_one_value,zone_limit)),
            abs_diff_hundred := Mul('abs_diff_hundred', operands=(abs_diff, hundred)),
            rel_diff := UDiv('rel_diff',operands=(abs_diff_hundred, divider)),
            error := LessEqualThan('error', operands=(rel_diff, et)),
            error_check := Implies("error_check", operands=(zone,error))
        ]

    @classmethod
    def atmost_lpp_constraints(cls, out_prod_mux_params: List[List[List[Tuple[BoolVariable, BoolVariable]]]], literals_per_product: int
                               ) -> List[AtMost]:
        return [
            AtMost(f'at_most_lpp_o{out_i}_p{prod_i}', operands=(p[0] for p in prod_params), value=literals_per_product)
            for (out_i, out_params) in enumerate(out_prod_mux_params)
            for (prod_i, prod_params) in enumerate(out_params)
        ]

    @classmethod
    def products_order_redundancy(cls, out_prod_mux_params: List[List[List[Tuple[BoolVariable, BoolVariable]]]]
                                  ) -> Tuple[List[ToInt], List[GreaterEqualThan]]:

        # skip if we have only one product
        if len(out_prod_mux_params[0]) < 2: return ([], [])

        prod_ids: List[ToInt] = []
        prod_ord_nodes: List[GreaterEqualThan] = []

        # for all outputs
        for (out_i, out_params) in enumerate(out_prod_mux_params):
            # generate an integer identifier for each product
            prod_ids.extend(_prod_ids := [
                ToInt(f'out{out_i}_prod{prod_i}_id', operands=flat(prod_params))
                for (prod_i, prod_params) in enumerate(out_params)
            ])
            # set the order of the identifiers ( a >= b >= c ... )
            prod_ord_nodes.extend(
                GreaterEqualThan(f'id_order_{idx_a}_{idx_b}', operands=(prod_a, prod_b))
                for (idx_a, prod_a), (idx_b, prod_b) in pairwise(enumerate(_prod_ids))
            )

        return (
            prod_ids,
            prod_ord_nodes,
        )


class NonSharedTemplate(Template, _NonSharedBase):
    """
        Class for defining the non-shared template in a subgraph annotated graph.

        @authors: Marco Biasion, Francesco Costa
    """
    @classmethod
    def define(cls, s_graph: SGraph, specs: Specifications) -> Tuple[PGraph, CGraph]:
        # get prefixed graph
        a_graph: SGraph = set_prefix(s_graph, 'a_')

        # > Template Graph

        # construct products
        (products, out_prod_mux_params, multiplexers) = cls.construct_products(a_graph, specs.ppo)

        # construct sums
        sums = cls.construct_sums(a_graph, products)

        # construct output switches (for constant False output)
        outs_p: List[BoolVariable] = []
        outs: List[If] = []
        updated_nodes: Dict[str, OperationNode] = dict()
        for (out_i, (out_node, sum_node)) in enumerate(zip(a_graph.subgraph_outputs, sums)):
            # create the constant False switch
            outs_p.append(p_o := BoolVariable(f'p_o{out_i}', in_subgraph=True))
            outs.append(new_out_node := And(f'sw_o{out_i}', in_subgraph=True, operands=(p_o, sum_node)))

            # update all output successors to descend from new outputs
            for succ in filter(lambda n: not n.in_subgraph, a_graph.successors(out_node)):
                succ = updated_nodes.get(succ.name, succ)
                new_operands = iterable_replace(succ.operands, succ.operands.index(out_node.name), new_out_node.name)
                updated_nodes[succ.name] = succ.copy(operands=new_operands)

        # constants rewriting
        constants_rewriting = cls.constants_rewriting(a_graph, updated_nodes, specs)

        # create template graph
        template_graph = PGraph(
            it.chain(  # nodes
                (  # unchanged nodes
                    n
                    for n in a_graph.nodes
                    if not n.in_subgraph
                    if n.name not in updated_nodes
                ),
                # changed nodes
                updated_nodes.values(),
                # products and relative operands
                multiplexers, flat(products),
                flat(out_prod_mux_params),
                # sums and relative operands
                sums, outs_p, outs,
                # output constant rewriting
                constants_rewriting,
            ),
            a_graph.inputs_names, a_graph.outputs_names,
            (n.name for n in flat((out_prod_mux_params, outs_p)))
        )

        # > Constraints Graph

        # multiplexer redundancy
        mux_red_nodes = [
            Or(f'prevent_constF_{out_i}_{prod_i}_{in_i}', operands=(p_usage.name, p_assert.name))
            for (out_i, prod_o) in enumerate(out_prod_mux_params)
            for (prod_i, prod_p) in enumerate(prod_o)
            for (in_i, (p_usage, p_assert)) in enumerate(prod_p)
        ]

        # constant zero redundancy
        const0_red_nodes = list(flat(
            (
                not_p_o := Not(f'not_{p_o.name}', operands=(p_o.name,)),
                or_ps := Or(f'or_sum_in_{sum_i}', operands=(p_usage.name for prods_p in p_o_t for (p_usage, p_assert) in prods_p)),
                not_or := Not(f'not_{or_ps.name}', operands=(or_ps.name,)),
                impl := Implies(f'impl_sum_{sum_i}', operands=(not_p_o.name, not_or.name)),
            )
            for sum_i, (p_o, p_o_t) in enumerate(zip(outs_p, out_prod_mux_params))
        ))

        # target definition
        targets = [
            Target(f't_{param.name}', operands=(param.name,))
            for param in flat((out_prod_mux_params, outs_p))
        ]

        # create constraints graph
        constraint_graph = CGraph(
            it.chain(  # nodes
                # placeholders
                (PlaceHolder(node.name) for node in flat((out_prod_mux_params, outs_p))),
                (PlaceHolder(name) for name in s_graph.outputs_names),
                (PlaceHolder(name) for name in template_graph.outputs_names),
                # behavioural constraints
                cls.error_constraint(s_graph, template_graph, specs.et) if(specs.metric is MetricType.ABSOLUTE) else cls.relative_error_constraint(s_graph, template_graph, specs.max_error) if(specs.zone_constraint == None) else cls.relative_error_zone_constraint(s_graph, template_graph, specs.max_error, specs.zone_constraint),
                cls.atmost_lpp_constraints(out_prod_mux_params, specs.lpp),
                # redundancy constraints
                mux_red_nodes,
                const0_red_nodes,
                *cls.products_order_redundancy(out_prod_mux_params),
                # targets
                targets,
            )
        )

        return (template_graph, constraint_graph)

