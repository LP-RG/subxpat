from typing import Callable, Dict, Mapping, Optional

from sxpat.graph.graph import IOGraph
from sxpat.graph.node import BoolConstant, BoolVariable
from sxpat.specifications import LabelingRelativeTo, LabelingType, Specifications
from sxpat.definitions.templates.Labeling import Labeling
from sxpat.labelling.labelling import Labelling
from sxpat.solvers.QbfSolver import QbfSolver


def calc_label(exact_graph: IOGraph, current_graph: IOGraph, cur_node: str, specs_obj: Specifications) -> int:
    """Compute the exact weight of a single node, through a QBF query."""
    p_graph, c_graph = Labeling.define(
        current_graph, [cur_node],
        min_labeling=specs_obj.labeling == LabelingType.MIN,
    )
    status, model = QbfSolver.solve((exact_graph, p_graph, c_graph), specs_obj)
    return model['weight']


def calc_label_legacy(labeller: Labelling, cur_node: str) -> int:
    """Compute the weight of a single node using an already prepared `Labelling`."""
    return labeller.label_node(cur_node)


def fast_labeling(
    exact_graph: IOGraph, current_graph: IOGraph, et: int, specs_obj: Specifications,
    skip_at_output: bool = True,
    threshold_for_max_imprecision: int = 10,
    skip_input: bool = True,
    weights: Optional[Mapping[str, int]] = None,
    labeller: Optional[Labelling] = None,
) -> Dict[str, int]:
    """
    Compute the weights of the `current_graph` nodes, in relation to the `exact_graph`.

    Nodes are visited starting from the outputs and moving upwards; a node is only
    labelled when its own weight is needed, which is the case when its weight can
    still influence the error threshold `et`.

    :param skip_at_output: if `True`, nodes driving an output are not labelled, as
        their weight is exactly the output's weight.
    :param threshold_for_max_imprecision: controls the imprecise shortcut used to
        skip labelling. When a node's weight `w` satisfies `w <= et / threshold`,
        its ancestors that have it as their only child are assumed to have the same
        weight. This is an over-approximation, so a lower threshold is more accurate
        but slower; set to `0` to disable the shortcut entirely.
    :param skip_input: if `True`, input nodes are not labelled.
    :param weights: pre-computed weights to seed the labelling with.
    :param labeller: if given, weights are computed through this `Labelling`
        instead of an exact QBF query.
    """
    weights = dict(weights) if weights is not None else {}
    stack: list[str] = []
    visited: set[str] = set()

    def propagate_imprecise_cases(start_node: str, value: int) -> None:
        # propagate `value` up through single-child ancestors, either because the
        # current weight is already negligible w.r.t. `et`, or because the ancestor
        # has no other children to influence it.
        st = [start_node]
        while len(st):
            cur_node = st.pop()
            imprecise = (
                threshold_for_max_imprecision != 0
                and value <= et / threshold_for_max_imprecision
            )
            single_child = (
                len(current_graph.predecessors(cur_node)) == 1
                and len(current_graph.successors(current_graph.predecessors(cur_node)[0])) == 1
            )
            if imprecise or single_child:
                for pred in current_graph.predecessors(cur_node):
                    if len(current_graph.successors(pred.name)) == 1:
                        weights[pred.name] = value
                        st.append(pred.name)

    minimum_found = 2 ** len(current_graph.outputs)

    # seed the exploration with the ancestors of the outputs that can affect `et`
    for node in reversed(current_graph.outputs):
        value = 2 ** int(node.name[3:])

        for x in current_graph.predecessors(node):
            if (value <= et) or specs_obj.labeling_relative_to == LabelingRelativeTo.ORIGIN:
                stack.append(x.name)
                visited.add(x.name)

    while len(stack):
        cur_node = stack.pop()
        if cur_node[:2] == 'in' and skip_input:
            continue
        # a simple-min node driving an output alone cannot improve the minimum
        if (
            specs_obj.labeling == LabelingType.SIMPLE_MIN
            and current_graph.successors(cur_node)[0].name[:3] == 'out'
        ):
            output = current_graph.successors(cur_node)[0].name
            value = 2 ** int(output[3:])
            if value > minimum_found:
                return weights

        if cur_node in weights:
            for succ in current_graph.predecessors(cur_node):
                if succ.name not in visited:
                    stack.append(succ.name)
                    visited.add(succ.name)
            continue

        if (
            len(current_graph.successors(cur_node)) == 1
            and current_graph.successors(cur_node)[0] in current_graph.outputs
            and skip_at_output
        ):
            value = 2 ** int(current_graph.successors(cur_node)[0].name[3:])
        else:
            if labeller is None:
                value = calc_label(exact_graph, current_graph, cur_node, specs_obj)
            else:
                value = calc_label_legacy(labeller, cur_node)

        if not isinstance(current_graph[cur_node], (BoolConstant, BoolVariable)):
            minimum_found = min(minimum_found, value)
        weights[cur_node] = value

        propagate_imprecise_cases(cur_node, value)

        for succ in current_graph.predecessors(cur_node):
            if succ.name not in visited:
                stack.append(succ.name)
                visited.add(succ.name)

    return weights


def compute_bound(current_graph: IOGraph, combine: Callable[[int, int], int], init_value: int) -> Dict[str, int]:
    """
    Propagate a weight from the outputs towards the inputs, combining the values
    of every successor of a node with `combine`.
    """
    stack: list[str] = []
    weights: Dict[str, int] = {}
    # number of successors that have already reached each node; once it equals the
    # node's number of successors, the node itself can be processed
    count: Dict[str, int] = {}

    # initialize
    for x in current_graph.nodes:
        weights[x.name] = init_value
        count[x.name] = 0

    for node in current_graph.outputs:
        value = 2 ** int(node.name[3:])

        for x in current_graph.predecessors(node):
            count[x.name] += 1
            weights[x.name] = combine(value, weights[x.name])
            if count[x.name] == len(current_graph.successors(x.name)):
                stack.append(x.name)

    while stack:
        cur_node = stack.pop()
        value = weights[cur_node]
        for x in current_graph.predecessors(cur_node):
            count[x.name] += 1
            weights[x.name] = combine(value, weights[x.name])
            if count[x.name] == len(current_graph.successors(x.name)):
                stack.append(x.name)

    return weights


def upper_bound(current_graph: IOGraph) -> Dict[str, int]:
    return compute_bound(current_graph, combine=lambda v, w: v | w, init_value=0)


def lower_bound(current_graph: IOGraph) -> Dict[str, int]:
    return compute_bound(current_graph, combine=min, init_value=2 ** len(current_graph.outputs))
