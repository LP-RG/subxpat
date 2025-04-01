from typing import Dict, List, Tuple

import itertools as it

from .Template import Template

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.specifications import Specifications
from sxpat.utils.collections import flat, pairwise


__all__ = ['NonSharedTemplate']


class NonSharedTemplate(Template):
    """
        Base class for defining the non-shared template in a subgraph annotated graph.

        @authors: Marco Biasion, Francesco Costa
    """

    @classmethod
    def define(cls, graph: SGraph, specs: Specifications) -> Tuple[PGraph, CGraph]:
        # get prefixed graph
        a_graph: SGraph = set_prefix(graph, 'a_')

        # > Template Graph

        # construct products
        products: List[List[And]] = []
        products_p: List[List[List[Tuple[BoolVariable, BoolVariable]]]] = []
        multiplexers: List[Multiplexer] = []
        for out_i, out in enumerate(a_graph.subgraph_outputs):
            products.append([])
            products_p.append([])
            for prod_i in range(specs.ppo):
                # create all multiplexers for the product
                _muxs = []
                products_p[-1].append([])
                for in_i, in_node in enumerate(a_graph.subgraph_inputs):
                    products_p[-1][-1].append((
                        (p_usage := BoolVariable(f'p_o{out_i}_t{prod_i}_i{in_i}_u', in_subgraph=True)),
                        (p_assert := BoolVariable(f'p_o{out_i}_t{prod_i}_i{in_i}_a', in_subgraph=True)),
                    ))
                    _muxs.append(Multiplexer(f'mux_o{out_i}_t{prod_i}_i{in_i}', in_subgraph=True, operands=[in_node, p_usage, p_assert]))

                # create the product (and store multiplexers)
                products[-1].append(And(f'o{out_i}_p{prod_i}', in_subgraph=True, operands=_muxs))
                multiplexers.extend(_muxs)

        # construct sums and constant 0 switch
        consts = {True: BoolConstant('cT', value=True), False: BoolConstant('cF', value=False)}
        sums = []
        outs_p: List[BoolVariable] = []
        outs: List[If] = []
        out_successors: Dict[str, OperationNode] = dict()
        for out_i, out_node in enumerate(a_graph.subgraph_outputs):
            # create the sum and constant 0 switch
            sums.append(_sum := Or(f'sum{out_i}', in_subgraph=True, operands=products[out_i]))
            outs_p.append(p_o := BoolVariable(f'p_o{out_i}', in_subgraph=True))
            outs.append(new_out_node := If(f'sw_o{out_i}', in_subgraph=True, operands=(p_o, _sum, consts[False])))

            # update all output successors to descend from new outputs
            for succ in a_graph.successors(out_node):
                if not succ.in_subgraph:
                    succ = out_successors.get(succ.name, succ)
                    new_out_index = succ.operands.index(out_node.name)
                    new_operands = succ.operands[:new_out_index] + (new_out_node.name,) + succ.operands[new_out_index + 1:]
                    out_successors[succ.name] = succ.copy(operands=new_operands)

        # create template graph
        nodes = it.chain(
            (  # unchanged nodes
                n
                for n in a_graph.nodes
                if not n.in_subgraph
                if n.name not in out_successors
            ),
            # constants
            consts.values(),
            # products and relative operands
            flat(products_p),
            multiplexers,
            flat(products),
            # sums and relative operands
            sums,
            outs_p,
            outs,
            # updated successors
            out_successors.values(),
        )
        template_graph = PGraph(
            nodes,
            a_graph.inputs_names, a_graph.outputs_names,
            (n.name for n in flat((products_p, outs_p)))
        )

        # > Constraints Graph

        # error constraint
        error_nodes = [
            cur_int := ToInt('cur_int', operands=graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),
            et := IntConstant('et', value=specs.et),
            error_check := LessEqualThan('error_check', operands=(abs_diff, et)),
        ]

        # lpp constraint
        lpp_nodes = [
            AtMost(f'at_most_lpp_o{out_i}_p{prod_i}', operands=(p[0] for p in prod_t), value=specs.lpp)
            for (out_i, prod_o) in enumerate(products_p)
            for (prod_i, prod_t) in enumerate(prod_o)
        ]

        # multiplexer redundancy
        mux_red_nodes = [
            Or(f'prevent_constF_{out_i}_{prod_i}_{in_i}', operands=(p_usage.name, p_assert.name))
            for (out_i, prod_o) in enumerate(products_p)
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
            for sum_i, (p_o, p_o_t) in enumerate(zip(outs_p, products_p))
        ))

        # order of products redundancy
        prod_ids = []
        prod_ord_nodes = []
        if len(products_p[0]) >= 2:
            for (out_i, prod_o) in enumerate(products_p):
                prod_ids.extend(_prod_ids := [
                    ToInt(f'out{out_i}_prod{prod_i}_id', operands=flat(prod_p))
                    for (prod_i, prod_p) in enumerate(prod_o)
                ])
                prod_ord_nodes.extend(
                    GreaterEqualThan(f'id_order_{idx_a}_{idx_b}', operands=(prod_a, prod_b))
                    for (idx_a, prod_a), (idx_b, prod_b) in pairwise(enumerate(_prod_ids))
                )

        # target definition
        targets = [
            Target(f't_{param.name}', operands=(param.name,))
            for param in flat((products_p, outs_p))
        ]

        nodes = it.chain(
            # placeholders
            (PlaceHolder(node.name) for node in flat((products_p, outs_p))),
            (PlaceHolder(name) for name in graph.outputs_names),
            (PlaceHolder(name) for name in template_graph.outputs_names),
            # constants
            consts.values(),
            # ints and error
            error_nodes,
            # its constraints
            lpp_nodes,
            # redundancy constraints
            mux_red_nodes,
            const0_red_nodes,
            prod_ids,
            prod_ord_nodes,
            targets,
        )
        constraint_graph = CGraph(nodes)

        return (template_graph, constraint_graph)
