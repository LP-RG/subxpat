import random
from typing import Callable, Dict, Mapping, Optional, Sequence

from sxpat.graph.graph import IOGraph
from sxpat.graph.node import (
    And, BoolConstant, BoolVariable, Identity, Implies, Not, Or, Xnor, Xor,
)
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


def evaluate_samples(graph: IOGraph, input_masks: Mapping[str, int], n_samples: int,
                     flip_name: Optional[str] = None) -> Dict[str, int]:
    """
    Evaluate `graph` once per sample, all in parallel.

    Every node value is returned as a bitmask, where bit `s` is the value of the
    node under sample `s`; boolean operations then map to bitwise operations.
    If `flip_name` is given, that node's value is negated before being stored, so
    its whole downstream cone sees the flipped value (a broken node).
    """
    all_ones = (1 << n_samples) - 1

    values: Dict[str, int] = {}
    for node in graph.nodes:  # topological order
        if isinstance(node, BoolVariable):
            value = input_masks.get(node.name, 0)
        elif isinstance(node, BoolConstant):
            value = all_ones if node.value else 0
        elif isinstance(node, Not):
            value = ~values[node.operands[0]]
        elif isinstance(node, And):
            value = all_ones
            for operand in node.operands: value &= values[operand]
        elif isinstance(node, Or):
            value = 0
            for operand in node.operands: value |= values[operand]
        elif isinstance(node, Xor):
            value = 0
            for operand in node.operands: value ^= values[operand]
        elif isinstance(node, Xnor):
            value = all_ones
            for operand in node.operands: value ^= values[operand]
        elif isinstance(node, Implies):
            (antecedent, consequent) = node.operands
            value = ~(values[antecedent] & ~values[consequent])
        elif isinstance(node, Identity):
            value = values[node.operands[0]]
        else:
            raise ValueError(f'Cannot evaluate node of unsupported type: {type(node).__name__} ({node.name!r})')

        values[node.name] = (~value if node.name == flip_name else value) & all_ones

    return values


def sample_outputs(values: Mapping[str, int], outputs_names: Sequence[str], n_samples: int) -> list[int]:
    """Decode per-node values into the integer output value of each sample (as `ToInt` would)."""
    outputs = [0] * n_samples
    for name in outputs_names:
        bit_weight = 1 << int(name[3:])
        mask = values[name]
        for sample in range(n_samples):
            if (mask >> sample) & 1:
                outputs[sample] += bit_weight
    return outputs


class SamplingLabeler:
    """
    Label nodes by sampling.

    The weight of a node is the maximum (or minimum) absolute difference between
    the integer outputs of the reference circuit and of the current circuit with
    the node broken, over a set of input assignments.

    Mirroring the exact labelling, the minimising variant ignores the assignments
    under which the break has no effect (a zero weight carries no information),
    so it returns the smallest non-zero difference.

    The two corners (all-zero and all-one) are always evaluated; `n_samples`
    further assignments are drawn uniformly at random, without replacement. The
    sampling is deterministic for a given seed (`None` draws a non-deterministic
    seed), and exact whenever `n_samples` covers every assignment.
    """

    def __init__(self, reference_graph: IOGraph, current_graph: IOGraph,
                 n_samples: int, seed: Optional[int], minimise: bool = False) -> None:
        self.reference_graph = reference_graph
        self.current_graph = current_graph
        self.n_samples = max(1, n_samples)
        self.minimise = minimise
        self._random = random.Random(seed)
        self._weights: Dict[str, int] = {}
        # lazily computed (they only depend on the graphs, not on the node)
        self._reference_outputs: Optional[list[int]] = None
        self._input_masks: Mapping[str, int] = {}

    def label_node(self, cur_node: str) -> int:
        if cur_node not in self._weights:
            self._weights[cur_node] = self._label(cur_node)
        return self._weights[cur_node]

    def _assignments(self, n_inputs: int) -> list[int]:
        # assignments of the inputs, encoded as integers (bit `i` -> `inputs[i]`)
        total = 1 << n_inputs
        if total <= 2:
            # the corners already cover every assignment
            return list(range(total))
        if self.n_samples >= total - 2:
            # the sample budget covers every assignment: enumerate exactly
            return list(range(total))
        return [0, total - 1, *self._random.sample(range(1, total - 1), self.n_samples)]

    def _prepare(self) -> int:
        if self._reference_outputs is not None:
            return len(self._reference_outputs)

        inputs_names = self.current_graph.inputs_names
        assignments = self._assignments(len(inputs_names))
        n_samples = len(assignments)

        # transpose the assignments into a per-input bitmask (bit `s` -> sample `s`)
        input_masks = {name: 0 for name in inputs_names}
        for (sample, assignment) in enumerate(assignments):
            for (i, name) in enumerate(inputs_names):
                if (assignment >> i) & 1:
                    input_masks[name] |= 1 << sample

        self._input_masks = input_masks
        self._reference_outputs = sample_outputs(
            evaluate_samples(self.reference_graph, input_masks, n_samples),
            self.reference_graph.outputs_names, n_samples,
        )
        return n_samples

    def _label(self, cur_node: str) -> int:
        n_samples = self._prepare()

        broken = sample_outputs(
            evaluate_samples(self.current_graph, self._input_masks, n_samples, flip_name=cur_node),
            self.current_graph.outputs_names, n_samples,
        )

        errors = [abs(r - b) for (r, b) in zip(self._reference_outputs, broken)]
        if not self.minimise:
            return max(errors)
        # the minimising variant mirrors the exact labelling: the smallest non-zero error
        non_zero = [error for error in errors if error > 0]
        return min(non_zero) if non_zero else 0


def fast_labeling(
    exact_graph: IOGraph, current_graph: IOGraph, et: int, specs_obj: Specifications,
    skip_at_output: bool = True,
    threshold_for_max_imprecision: int = 10,
    skip_input: bool = True,
    weights: Optional[Mapping[str, int]] = None,
    labeller: Optional[Labelling] = None,
    sampler: Optional['SamplingLabeler'] = None,
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
    :param sampler: if given, weights are computed by sampling instead of an exact
        QBF query (takes precedence over `labeller`).
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
            if sampler is not None:
                value = sampler.label_node(cur_node)
            elif labeller is None:
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
