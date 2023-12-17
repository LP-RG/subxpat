import networkx as nx

from sxpat.config.config import WEIGHT
from sxpat.distance_function import HammingDistance, WeightedAbsoluteDifference
from sxpat.runner_creator.xpat_creator_direct import XPatRunnerCreator
from sxpat.templateCreator import Template_SOP1
from sxpat.templateSpecs import TemplateSpecs
from sxpat.arguments import Arguments


from sxpat.runner_creator.subxpat_v2_phase1_creator import SubXPatV2Phase1RunnerCreator
from z_marco.ma_graph import MaGraph
from sxpat.executor.subxpat2_executor import SubXPatV2Executor

from sxpat.xplore_ma import explore_cell

# parse arguments and create template object
args = Arguments.parse()
specs_obj = TemplateSpecs(
    name='Sop1',
    exact=args.benchmark_name,
    benchmark_name=args.benchmark_name,


    # XPAT
    literals_per_product=args.lpp,
    products_per_output=args.ppo,

    et=args.et,
    num_of_models=1, subxpat=args.subxpat,
    iterations=args.iterations,
    grid=args.grid,
    timeout=args.timeout,

    # labeling
    min_labeling=args.min_labeling,

    # partitioning
    mode=args.mode,
    imax=args.imax, omax=args.omax,
    sensitivity=args.sensitivity,
    subgraph_size=args.subgraph_size,
    partitioning_percentage=args.partitioning_percentage, 

    population=args.population,
    shared=args.shared,
    products_in_total=args.products_in_total, parallel=args.parallel,

    # error functions
    full_error_function=args.full_error_function,
    sub_error_function=args.sub_error_function
)

# print(specs_obj)
# exit()
explore_cell(specs_obj)

print("ASDASDASDASDASDASDASDASDSDASD")
exit()

template_obj = Template_SOP1(specs_obj)

# load graph
graph = template_obj.import_graph()
template_obj.current_graph = graph

# generate subgraph
template_obj.label_graph(2)
graph.extract_subgraph(specs_obj)

# exports to `output/gv/`
graph.export_annotated_graph()

# convert AnnotatedGraph to MaGraph(s)
full_graph = MaGraph(digraph=graph.subgraph)
sub_graph = MaGraph(digraph=exctract_subgraph(graph))

# define distance/error functions
circuit_distance_function = WeightedAbsoluteDifference(
    [2 ** int(out_name.strip("out")) for out_name in full_graph.outputs]
)
subcircuit_distance_function = WeightedAbsoluteDifference(
    [graph.subgraph.nodes[n[4:]][WEIGHT] for n in sub_graph.outputs]
)
# subcircuit_distance_function = HammingDistance()


executor = SubXPatV2Executor(
    full_graph, sub_graph, specs_obj.exact_benchmark,
    specs_obj.literals_per_product, specs_obj.products_per_output,
    circuit_distance_function,
    subcircuit_distance_function,
    specs_obj.et
)
print("ASDASD")
print(executor.run())

exit()
# generate script phase 1
script_name = f"{args.benchmark_name}_PHASE1.py"
p1_creator = SubXPatV2Phase1RunnerCreator(
    full_graph, sub_graph,
    specs_obj.exact_benchmark,
    circuit_distance_function,
    subcircuit_distance_function
)
p1_creator.generate_script(script_name)
print(f"Phase1 script exported to '{script_name}'")

# # generate script phase 2
# script_name = f"{args.benchmark_name}_PHASE2.py"
# p2_creator = XPatRunnerCreator(
#     sub_graph, f"{specs_obj.exact_benchmark}_phase2",
#     template_obj.literals_per_product, template_obj.products_per_output,
#     subcircuit_distance_function
# )
# p2_creator.generate_script(script_name)
# print(f"Phase2 script exported to '{script_name}'")
