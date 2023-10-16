from sxpat.templateCreator import Template_V2
from sxpat.templateSpecs import TemplateSpecs
from sxpat.arguments import Arguments


# parse arguments and create template object
args = Arguments.parse()
specs_obj = TemplateSpecs(name='Sop1', exact=args.benchmark_name, literals_per_product=args.lpp,
                          products_per_output=args.ppo,
                          benchmark_name=args.approximate_benchmark, num_of_models=1, subxpat=args.subxpat,
                          et=args.et,
                          partitioning_percentage=args.partitioning_percentage, iterations=args.iterations,
                          grid=args.grid, imax=args.imax, omax=args.omax, sensitivity=args.sensitivity,
                          timeout=args.timeout, subgraph_size=args.subgraph_size)
template_obj = Template_V2(specs_obj)

# load and label graph
template_obj.current_graph = template_obj.import_graph()
template_obj.label_graph(2)
# generate subgraph
subgraph_is_available = template_obj.current_graph.extract_subgraph(specs_obj)

# exports to `output/gv/`
template_obj.current_graph.export_annotated_graph()

# generate script
script_name = f"{args.benchmark_name}_PHASE1.py"
template_obj.setup_distance_functions()
template_obj.generate_z3py_script_v2_phase1(script_name)
print(f"Script exported to '{script_name}'")
