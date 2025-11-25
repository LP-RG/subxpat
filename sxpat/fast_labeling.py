from typing import Set
from sxpat.graph.Graph import IOGraph
from sxpat.specifications import Specifications
from sxpat.templating.Labeling import Labeling
from sxpat.solving.QbfSolver import QbfSolver
from sxpat.utils.timer import Timer

def calc_label(exact_graph: IOGraph, current_graph: IOGraph, cur_node, specs_obj: Specifications, upper_bound={}):
    define_template = Labeling.define
    p_graph, c_graph = define_template(current_graph, [cur_node],min_labeling=specs_obj.min_labeling)
    solve = QbfSolver.solve
    status, model = solve((exact_graph, p_graph, c_graph), specs_obj, upper_bound=upper_bound[cur_node] if cur_node in upper_bound else None)
    return model['weight']

def fast_labeling(exact_graph: IOGraph, current_graph: IOGraph, et, specs_obj: Specifications, skip_at_output=True, threshold_for_max_imprecision=10, skip_input=True, weights = {}, upper_bound = {}):
    """
if skip_at_output is true then the nodes at the output will have automatically their weights set to the value of the output
threshold_for_max_imprecision set the weight of the node that you must have compared to et to skip the parents that only have the current node
as the child, for example if the current et is 1000 and threshold_for_max_imprecision is 10 then all the nodes that have weight 100 or less will
make their children that have only them as output equivalent to them this is imprecise since their weight could be less, that's why you can decrease
the value, set to 0 to never use 
    """

    # import importlib
    # module = importlib.import_module(f"input.cashed_labeling.{'min' if specs_obj.min_labeling else 'max'}.{specs_obj.exact_benchmark}")
    # allweights = module.weights
    # alltimes = module.times
    
    tot_time = 0
    stack = []
    visited = set()
    weights = dict(weights)
    upper_bound = dict(upper_bound)

    def recursive_cases(start_node, value):
        nonlocal weights

        st = [start_node]
        while len(st):
            cur_node = st.pop()
            if (threshold_for_max_imprecision != 0 and value <= et/threshold_for_max_imprecision) or (len(current_graph.predecessors(cur_node)) == 1 and len(current_graph.successors(current_graph.predecessors(cur_node)[0])) == 1):
                for pred in current_graph.predecessors(cur_node):
                    if len(current_graph.successors(pred.name)) == 1:
                        weights[pred.name] = value
                        st.append(pred.name)


    for node in current_graph.outputs:
        value = 2 ** int(node.name[3:])
        
        for x in current_graph.predecessors(node):
            if(value <= et):
                stack.append(x.name)
                visited.add(x.name)

    while len(stack):
        cur_node = stack.pop()
        if cur_node[:2] == 'in' and skip_input:
            continue
        if cur_node in weights:
            for succ in current_graph.predecessors(cur_node):
                if succ.name not in visited:
                    stack.append(succ.name)
                    visited.add(succ.name)
            continue
        
        if current_graph.successors(cur_node)[0] in current_graph.outputs and skip_at_output:
            value = 2 ** int(current_graph.successors(cur_node)[0].name[3:])
        
        else:
            value = calc_label(exact_graph, current_graph, cur_node, specs_obj, upper_bound)
            # value = allweights[cur_node]
            # tot_time += alltimes[cur_node]
        
        weights[cur_node] = value

        recursive_cases(cur_node, value)

        for succ in current_graph.predecessors(cur_node):
            if succ.name not in visited:
                stack.append(succ.name)
                visited.add(succ.name)
    
    # print(f'cashed_labeling_time = {tot_time}')
    return weights


def upper_bound(current_graph: IOGraph):
    stack = []
    count = {}  #counts the number of nodes that have reached a node when this equal the number of sucessor of the node we can continue the exploration
    weights = {}

    for x in current_graph.nodes:
        weights[x.name] = 0
        count[x.name] = 0

    for node in current_graph.outputs:
        value = 2 ** int(node.name[3:])
        
        for x in current_graph.predecessors(node):
            count[x.name] += 1
            weights[x.name] |= value
            if count[x.name] == len(current_graph.successors(x.name)):
                stack.append(x.name)

    while len(stack):
        cur_node = stack.pop()
        value = weights[cur_node]
        for x in current_graph.predecessors(cur_node):
            count[x.name] += 1
            weights[x.name] |= value
            if count[x.name] == len(current_graph.successors(x.name)):
                stack.append(x.name)
    
    return weights