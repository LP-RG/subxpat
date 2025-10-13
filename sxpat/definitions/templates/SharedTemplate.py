from typing import Dict, List, Tuple

import itertools as it

from .Template import Template, TemplateBundle

from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.graph.node import *
from sxpat.specifications import Specifications
from sxpat.utils.collections import flat, pairwise


__all__ = ['SharedTemplate']


class SharedTemplate(Template):
    """
        Class for defining the shared template in a subgraph annotated graph.

        TODO: When moving to shared, some of the constraints will need to be checked:
            - constant 0 redundancy for outputs
            - constant 0 redundancy for products
            - add usage of ConstantsType for constant rewriting

        @authors: Marco Biasion
    """

    @classmethod
    def define(cls, graph: SGraph, specs: Specifications) -> TemplateBundle:
        # get prefixed graph
        a_graph: SGraph = set_prefix(graph, 'a_')

        # > Template Graph

        # construct products
        products: List[And] = []
        products_p: List[List[Tuple[BoolVariable, BoolVariable]]] = []
        multiplexers: List[Multiplexer] = []
        for prod_i in range(specs.pit):
            # create all multiplexers for the product
            _muxs = []
            products_p.append([])
            for in_i, in_node in enumerate(a_graph.subgraph_inputs):
                products_p[-1].append((
                    (p_usage := BoolVariable(f'p_p{prod_i}_i{in_i}_u', in_subgraph=True)),
                    (p_assert := BoolVariable(f'p_p{prod_i}_i{in_i}_a', in_subgraph=True)),
                ))
                _muxs.append(Multiplexer(f'mux_p{prod_i}_i{in_i}', in_subgraph=True, operands=[in_node, p_usage, p_assert]))

            # create the product (and store multiplexers)
            products.append(And(f'prod{prod_i}', in_subgraph=True, operands=_muxs))
            multiplexers.extend(_muxs)

        # construct sums and constant 0 switch
        consts = {True: BoolConstant('cT', value=True), False: BoolConstant('cF', value=False)}
        sums = []
        sums_p: List[List[BoolVariable]] = []
        switches = []
        outs_p: List[BoolVariable] = []
        outs: List[If] = []
        out_successors: Dict[str, AnyOperation] = dict()
        for out_i, out_node in enumerate(a_graph.subgraph_outputs):
            # create all switches for the output
            _sws = []
            sums_p.append([])
            for prod_i, prod_node in enumerate(products):
                sums_p[-1].append(param := BoolVariable(f'p_o{out_i}_p{prod_i}', in_subgraph=True))
                _sws.append(If(f'sw_o{out_i}_p{prod_i}', in_subgraph=True, operands=(param, prod_node, consts[True])))

            # create the sum and constant 0 switch
            sums.append(_sum := Or(f'sum{out_i}', in_subgraph=True, operands=_sws))
            switches.extend(_sws)
            outs_p.append(p_o := BoolVariable(f'p_o{out_i}', in_subgraph=True))
            outs.append(new_out_node := If(f'sw_{out_node.name}_o{out_i}', in_subgraph=True, operands=(p_o, _sum, consts[False])))

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
            products,
            # sums and relative operands
            flat(sums_p),
            switches,
            sums,
            outs_p,
            outs,
            # updated successors
            out_successors.values(),
        )
        template_graph = PGraph(
            nodes,
            a_graph.inputs_names, a_graph.outputs_names,
            (n.name for n in flat((products_p, sums_p, outs_p)))
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
        # its constraint
        its_nodes = [
            at_most_its := AtMost('at_most_its', operands=flat(sums_p), value=specs.its),
        ]
        # multiplexer redundancy
        mux_red_nodes = [
            Or(f'prevent_constF_{prod_i}', operands=(p_usage.name, p_assert.name))
            for (prod_i, prod_p) in enumerate(products_p)
            for (p_usage, p_assert) in prod_p
        ]
        # constant zero redundancy
        const0_red_nodes = list(flat(
            (
                not_p_o := Not(f'not_{p_o.name}', operands=(p_o.name,)),
                or_ps := Or(f'or_sum_in_{sum_i}', operands=(n.name for n in p_o_ps)),
                not_or := Not(f'not_{or_ps.name}', operands=(or_ps.name,)),
                impl := Implies(f'impl_sum_{sum_i}', operands=(not_p_o.name, not_or.name)),
            )
            for sum_i, (p_o, p_o_ps) in enumerate(zip(outs_p, sums_p))
        ))

        # order of products redundancy
        prod_ids = [
            ToInt(f'prod{prod_i}_id', operands=flat(prod_p))
            for (prod_i, prod_p) in enumerate(products_p)
        ]
        if len(prod_ids) >= 2:
            prod_ids = prod_ids
            prod_ord_nodes = [
                GreaterThan(f'id_order_{idx_a}_{idx_b}', operands=(prod_a, prod_b))
                for (idx_a, prod_a), (idx_b, prod_b) in pairwise(enumerate(prod_ids))
            ]
        else:
            prod_ids = []
            prod_ord_nodes = []

        # target definition
        targets = [
            Target(f't_{param.name}', operands=(param.name,))
            for param in flat((sums_p, products_p, outs_p, sums_p))
        ]

        nodes = it.chain(
            # placeholders
            (PlaceHolder(node.name) for node in flat((sums_p, products_p, outs_p, sums_p))),
            (PlaceHolder(name) for name in graph.outputs_names),
            (PlaceHolder(name) for name in template_graph.outputs_names),
            # constants
            consts.values(),
            # ints and error
            error_nodes,
            # its constraints
            its_nodes,
            # redundancy constraints
            mux_red_nodes,
            const0_red_nodes,
            prod_ids,
            prod_ord_nodes,
            targets,
        )
        constraint_graph = CGraph(nodes)

        return TemplateBundle(template_graph, [constraint_graph])
