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


def labeling(exact_benchmark_name: str,
             approximate_benchmark: str,
             min_labeling: bool = False,
             parallel: bool = True
             ) -> Dict:
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
        print(Fore.LIGHTBLUE_EX + f'min labeling...' + Style.RESET_ALL)
        z3py_obj = Z3solver(exact_benchmark_name, approximate_benchmark, experiment=SINGLE, optimization=MAXIMIZE, style='min', parallel=parallel)
    else:
        print(Fore.LIGHTBLUE_EX + f'max labeling...' + Style.RESET_ALL)
        z3py_obj = Z3solver(exact_benchmark_name, approximate_benchmark, experiment=SINGLE, optimization=MAXIMIZE, parallel=parallel)

    z3py_obj.run_implicit_labeling()

    labels = {}
    for key in z3py_obj.labels.keys():
        weight = z3py_obj.labels[key]
        if key.startswith('app_'):
            key = key.replace('app_', "")
        labels[key] = weight

    return labels


def labeling_explicit(exact_benchmark_name: str, approximate_benchmark: str, constant_value: 0, min_labeling: bool,
                      partial: bool = False, et: int = -1, parallel: bool = False) -> Dict:
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
        z3py_obj = Z3solver(exact_benchmark_name, approximate_benchmark, experiment=SINGLE, optimization=MAXIMIZE, style='min', parallel=parallel)
    else:
        z3py_obj = Z3solver(exact_benchmark_name, approximate_benchmark, experiment=SINGLE, optimization=MAXIMIZE, parallel=parallel)

    if constant_value == 0:
        labels_false = z3py_obj.label_circuit(False, partial=partial, et=et)

        # cleanup (folder report/)
        report_folder, _ = OUTPUT_PATH['report']
        all_files = [f for f in os.listdir(report_folder)]
        # print(f'{all_files= }')
        for dir in all_files:
            if re.search('labeling', dir) and os.path.isdir(f'{report_folder}/{dir}'):
                shutil.rmtree(f'{report_folder}/{dir}')

        # cleanup (folder z3/)
        z3_folder, _ = OUTPUT_PATH['z3']
        all_files = [f for f in os.listdir(z3_folder)]
        # print(f'{all_files= }')
        for dir in all_files:
            if re.search('labeling', dir) and os.path.isdir(f'{z3_folder}/{dir}'):
                shutil.rmtree(f'{z3_folder}/{dir}')

        return labels_false, labels_false

    elif constant_value == 1:
        labels_true = z3py_obj.label_circuit(True, partial=partial, et=et)
        folder, _ = OUTPUT_PATH['z3']
        all_files = [f for f in os.listdir(folder)]
        for dir in all_files:
            if os.path.isdir(f'{folder}/{dir}') and re.search('labeling', dir):
                shutil.rmtree(f'{folder}/{dir}')

        return labels_true, labels_true

    else:
        labels_false = z3py_obj.label_circuit(False, partial=partial, et=et)
        labels_true = z3py_obj.label_circuit(True, partial=partial, et=et)
        folder, _ = OUTPUT_PATH['z3']
        all_files = [f for f in os.listdir(folder)]
        for dir in all_files:
            if os.path.isdir(f'{folder}/{dir}') and re.search('labeling', dir):
                shutil.rmtree(f'{folder}/{dir}')

        return labels_true, labels_false
