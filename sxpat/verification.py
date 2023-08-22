import csv
from colorama import Style, Fore

from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath


def erroreval_verification(exact_benchmark_name: str, approximate_benchmark: str, et: int) -> bool:
    verilog_obj_exact = Verilog(exact_benchmark_name)
    verilog_obj_exact.export_circuit()
    #

    verilog_obj_approx = Verilog(approximate_benchmark)
    verilog_obj_approx.export_circuit()
    #
    convert_verilog_to_gv(exact_benchmark_name)
    convert_verilog_to_gv(approximate_benchmark)
    #
    graph_obj_exact = Graph(exact_benchmark_name)
    graph_obj_approx = Graph(approximate_benchmark)
    #
    graph_obj_exact.export_graph()
    graph_obj_approx.export_graph()

    z3py_obj_qor = Z3solver(exact_benchmark_name, approximate_benchmark)
    z3py_obj_qor.convert_gv_to_z3pyscript_maxerror_qor()

    # print(f'evaluating the metric with monotonic...')
    z3py_obj_qor.export_z3pyscript()
    z3py_obj_qor.run_z3pyscript_qor()
    # print(f'metric is evaluated!')

    # Compare the obtained WCE
    folder, extension = z3logpath.OUTPUT_PATH['report']
    for csvfile in os.listdir(folder):
        if csvfile.endswith(extension) and re.search(approximate_benchmark, csvfile):
            report_file = f'{folder}/{csvfile}'
            with open(report_file, 'r') as rf:
                csvreader = csv.reader(rf)
                for row in csvreader:
                    if row[0] == WCE:
                        obtained_wce = int(row[1])

                        if obtained_wce <= et:
                            # print(Fore.GREEN + f'{obtained_wce = } <= ET = {et} (ErrorEval PASS)' + Style.RESET_ALL)
                            # # print(f'ErrorEval Error Verification -> PASS' + Style.RESET_ALL)
                            # with open(
                            #         f'output/report/PASS_{approximate_benchmark}.txt',
                            #         'w') as f:
                            #     pass
                            return True

                        else:
                            print(Fore.RED + f'ERROR!!! The obtained WCE does not match the given error threshold!')
                            print(f'{obtained_wce = } > ET = {et}' + Style.RESET_ALL)
                            with open(
                                    f'output/report/FAILED_{approximate_benchmark}.txt',
                                    'w') as f:
                                pass
                            return False
