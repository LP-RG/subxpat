import networkx as nx

from sxpat.config.config import WEIGHT
from sxpat.distance_function import HammingDistance, IntegerAbsoluteDifference, WeightedAbsoluteDifference
from sxpat.runner_creator.utils import exctract_subgraph
from sxpat.runner_creator.xpat_creator import XPatRunnerCreator
from sxpat.templateCreator import Template_SOP1
from sxpat.templateSpecs import TemplateSpecs
from sxpat.arguments import Arguments


from sxpat.runner_creator.subxpat_v2_phase1_creator import SubXPatV2Phase1RunnerCreator
from z_marco.ma_graph import MaGraph


# parse arguments and create template object
args = Arguments.parse()
specs_obj = TemplateSpecs(name='Sop1', exact=args.benchmark_name, literals_per_product=args.lpp,
                          products_per_output=args.ppo,
                          benchmark_name=args.approximate_benchmark, num_of_models=1, subxpat=args.subxpat,
                          et=args.et,
                          partitioning_percentage=args.partitioning_percentage, iterations=args.iterations,
                          grid=args.grid, imax=args.imax, omax=args.omax, sensitivity=args.sensitivity,
                          timeout=args.timeout, subgraph_size=args.subgraph_size)
template_obj = Template_SOP1(specs_obj)

# load graph
graph = template_obj.import_graph()
template_obj.current_graph = graph

# generate subgraph
template_obj.label_graph(2)
graph.extract_subgraph(specs_obj)

# exports to `output/gv/`
graph.export_annotated_graph()

# define distance/error functions
circuit_distance_function = IntegerAbsoluteDifference()
subweights = [graph.subgraph.nodes[n][WEIGHT] for n in graph.subgraph_output_dict.values()]
subcircuit_distance_function = WeightedAbsoluteDifference(subweights)
# subcircuit_distance_function = HammingDistance()

# convert AnnotatedGraph to MaGraph(s)
full_graph = MaGraph(digraph=graph.subgraph)
sub_graph = MaGraph(digraph=exctract_subgraph(graph))

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

# generate script phase 2
script_name = f"{args.benchmark_name}_PHASE2.py"
p2_creator = XPatRunnerCreator(
    sub_graph, f"{specs_obj.exact_benchmark}_phase2",
    template_obj.literals_per_product, template_obj.products_per_output,
    subcircuit_distance_function
)
p2_creator.generate_script(script_name)
print(f"Phase2 script exported to '{script_name}'")
