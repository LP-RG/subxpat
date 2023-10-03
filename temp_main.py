import dataclasses as dc
import z3
import sys

from sxpat.templateCreator import Template_SOP1, Template_V2
from sxpat.templateSpecs import _TemplateSpecs, TemplateSpecs
from sxpat.arguments import Arguments

from z_marco.circuit import load_verilog, load_annotated
from z_marco.z3_utils import weighted_sum
from z_marco.v2_phase1 import find_smallest_invalid_distance
from z_marco.utils import augment

# c = load_verilog(file_path=sys.argv[1])
# print(c)
# exit()

# print(find_smallest_invalid_distance(1, 2))

args = Arguments.parse()
specs_obj = TemplateSpecs(name='Sop1', exact=args.benchmark_name, literals_per_product=args.lpp,
                          products_per_output=args.ppo,
                          benchmark_name=args.approximate_benchmark, num_of_models=1, subxpat=args.subxpat,
                          et=args.et,
                          partitioning_percentage=args.partitioning_percentage, iterations=args.iterations,
                          grid=args.grid, imax=args.imax, omax=args.omax, sensitivity=args.sensitivity,
                          timeout=args.timeout, subgraph_size=args.subgraph_size)
# template_obj = Template_SOP1(specs_obj)
template_obj = Template_V2(specs_obj)

template_obj.current_graph = template_obj.import_graph()
template_obj.label_graph(2)
subgraph_is_available = template_obj.current_graph.extract_subgraph(specs_obj)
template_obj.setup_distance_functions()
# print(subgraph_is_available)

# graph: nx.DiGraph = self.current_graph.subgraph_input_dict
# print("ASDASD", *template_obj.current_graph.subgraph_input_dict.items(), sep="\n")
template_obj.current_graph.export_annotated_graph()
# exit()

# template_obj.z3_generate_v2_phase1_circuit(1)

# load_annotated(template_obj.current_graph)

template_obj.generate_z3py_script_v2_phase1()
# print(template_obj.z3_generate_exact_circuit_integer_output_constraints("banana", "MAA"))


# AA = 'a'
# ns = list(range(10000))
# d = {
#     n: [{AA: 1}, {AA: 0}, {}][i % 3]
#     for i, n in enumerate(ns)
# }


# def a(n):
#     return d[n].get(AA, 0) == 1


# def b(n):
#     if AA in d[n]:
#         if d[n][AA] == 1:
#             return True
#         else:
#             return False
#     else:
#         return False


# @augment(["timed"])
# def tot(ns):
#     z = list(map(a, ns))


# print(tot(ns))
