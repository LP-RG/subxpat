import networkx as nx

from sxpat.config.config import WEIGHT
from sxpat.distance_function import HammingDistance, IntegerAbsoluteDifference, WeightedAbsoluteDifference

from sxpat.runner_creator.utils import exctract_subgraph
from sxpat.runner_creator.xpat_creator import XPatRunnerCreator

from sxpat.executor.xpat_executor import XPatExecutor

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

# exports to `output/gv/`
# graph.export_annotated_graph()

# convert AnnotatedGraph to MaGraph(s)
digraph: nx.DiGraph = graph.graph
full_graph = MaGraph(digraph=digraph)

# define distance/error functions
weights = {'out0': 1, 'out1': 2, 'out2': 4}
circuit_distance_function = WeightedAbsoluteDifference(
    [weights[out_name] for out_name in full_graph.outputs]
)

# XPat test
executor = XPatExecutor(
    full_graph,
    specs_obj.exact_benchmark,
    template_obj.literals_per_product, template_obj.products_per_output,
    circuit_distance_function,
    2
)
executor.run()
