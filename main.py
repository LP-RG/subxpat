import shutil
import csv
import Z3Log
from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath
# from Z3Log.argument import Arguments
from sxpat.templateCreator import TemplateCreator
from sxpat.templateCreator import Template_SOP1ShareLogic
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *
from sxpat.synthesis import Synthesis
from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.synthesis import Synthesis
from sxpat.arguments import Arguments


def main():
    setup_folder_structure()
    for key in OUTPUT_PATH.keys():
        directory = OUTPUT_PATH[key][0]
        if ~os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    args = Arguments.parse()
    print(f'{args = }')

    specs_obj = TemplateSpecs(name='Sop1', literals_per_product=args.lpp, products_per_output=args.ppo,
                              benchmark_name=args.benchmark_name, num_of_models=1, subxpat=False, et=args.et, products_in_total=args.pit)
    print(f'{specs_obj = }')


    template_obj = Template_SOP1ShareLogic(specs_obj)
    print(f'{template_obj = }')
    template_obj.z3_generate_z3pyscript()

    template_obj.run_z3pyscript(args.et)
    template_obj.import_json_model()
    # print(f'{template_obj.json_model = }')

    # synth_obj = Synthesis(specs_obj, template_obj.graph, template_obj.json_model)
    # synth_obj.export_verilog()

    # # Verify the output verilog
    # # 0) copy the output approximate Verilgo file into the input/ver folder
    # src_ver = synth_obj.ver_out_path

    # approximate_benchmark = f'{synth_obj.ver_out_name[:-2]}'
    # des_ver = f"{z3logpath.INPUT_PATH['ver'][0]}/{synth_obj.ver_out_name}"
    # shutil.copyfile(src_ver, des_ver)
    # # exit()
    # # 1) create a clean verilog out of exact and approximate circuits

    # #
    # verilog_obj_exact = Verilog(args.benchmark_name)
    # verilog_obj_exact.export_circuit()
    # #

    # verilog_obj_approx = Verilog(approximate_benchmark)
    # verilog_obj_approx.export_circuit()
    # #
    # convert_verilog_to_gv(args.benchmark_name)
    # convert_verilog_to_gv(approximate_benchmark)
    # #
    # graph_obj_exact = Graph(args.benchmark_name)
    # graph_obj_approx = Graph(approximate_benchmark)
    # #
    # graph_obj_exact.export_graph()
    # graph_obj_approx.export_graph()

    # z3py_obj_qor = Z3solver(args.benchmark_name, approximate_benchmark)
    # z3py_obj_qor.convert_gv_to_z3pyscript_maxerror_qor()

    # print(f'evaluating the metric with {args.strategy}...')
    # z3py_obj_qor.export_z3pyscript()
    # z3py_obj_qor.run_z3pyscript_qor()
    # print(f'metric is evaluated!')

    # # Compare the obtained WCE
    # folder, extension = z3logpath.OUTPUT_PATH['report']
    # for csvfile in os.listdir(folder):
    #     if csvfile.endswith(extension) and re.search(approximate_benchmark, csvfile):
    #         report_file = f'{folder}/{csvfile}'
    # with open(report_file, 'r') as rf:
    #     csvreader = csv.reader(rf)
    #     for row in csvreader:
    #         if row[0] == WCE:
    #             obtained_wce = int(row[1])

    #             if obtained_wce <= args.et:
    #                 print(f'{obtained_wce = } <= ET = {args.et}')
    #                 print(f'TEST -> PASS')
    #                 break
    #             else:
    #                 print(f'ERROR!!! The obtained WCE does not match the given error threshold!')
    #                 print(f'{obtained_wce = } > ET = {args.et}')
    #                 exit()


if __name__ == "__main__":
    main()
