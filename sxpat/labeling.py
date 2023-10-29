import csv
import os
import shutil

from colorama import Style, Fore
from typing import Dict
from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath

def labeling(exact_benchmark_name: str, approximate_benchmark: str, constant_value: 0, min_labeling: bool) -> Dict:
    # 1) create a clean verilog out of exact and approximate circuits
    verilog_obj_exact = Verilog(exact_benchmark_name)
    verilog_obj_exact.export_circuit()

    verilog_obj_approx = Verilog(approximate_benchmark)
    verilog_obj_approx.export_circuit()

    convert_verilog_to_gv(exact_benchmark_name)
    convert_verilog_to_gv(approximate_benchmark)

    # 2) convert clean exact and approximate circuits into their gv formats
    graph_obj_exact = Graph(exact_benchmark_name)
    graph_obj_approx = Graph(approximate_benchmark)

    graph_obj_exact.export_graph()
    graph_obj_approx.export_graph()

    # convert gv to z3 expression
    if min_labeling:
        z3py_obj = Z3solver(exact_benchmark_name, approximate_benchmark, experiment=SINGLE, optimization=MAXIMIZE, style='min')
    else:
        z3py_obj = Z3solver(exact_benchmark_name, approximate_benchmark, experiment=SINGLE, optimization=MAXIMIZE)

    if constant_value == 0:

        labels_false = z3py_obj.label_circuit(False)
        z3_folder, _ = OUTPUT_PATH['z3']
        report_folder, _ = OUTPUT_PATH['report']
        all_files = [f for f in os.listdir(z3_folder)]
        # print(f'{all_files = }')
        for dir in all_files:
            if os.path.isdir(f'{z3_folder}/{dir}') and re.search('labeling', dir):
                shutil.rmtree(f'{z3_folder}/{dir}')

        all_files = [f for f in os.listdir(report_folder)]
        for dir in all_files:
            if os.path.isdir(f'{report_folder}/{dir}') and re.search('labeling', dir):
                shutil.rmtree(f'{report_folder}/{dir}')


        return labels_false, labels_false
    elif constant_value == 1:
        labels_true = z3py_obj.label_circuit(True)
        folder, _ = OUTPUT_PATH['z3']
        all_files = [f for f in os.listdir(folder)]

        for dir in all_files:
            if os.path.isdir(f'{folder}/{dir}') and re.search('labeling', dir):
                shutil.rmtree(f'{folder}/{dir}')
        return labels_true, labels_true
    else:
        labels_false = z3py_obj.label_circuit(False)
        labels_true = z3py_obj.label_circuit(True)
        folder, _ = OUTPUT_PATH['z3']
        all_files = [f for f in os.listdir(folder)]

        for dir in all_files:
            if os.path.isdir(f'{folder}/{dir}') and re.search('labeling', dir):
                shutil.rmtree(f'{folder}/{dir}')
        return labels_true, labels_false





if __name__ == "__main__":
    pass
else:
    pass
