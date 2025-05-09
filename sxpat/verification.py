import csv
import os
import re

from Z3Log.config import path as z3logpath
from Z3Log.config import config as z3logcfg
from Z3Log.utils import convert_verilog_to_gv
from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.z3solver import Z3solver
from sxpat.specifications import MetricType


def erroreval_verification_wce(exact_benchmark_name: str, approximate_benchmark: str, metric: str, zone_constraint: int) -> int:

    verilog_obj_exact = Verilog(exact_benchmark_name)
    verilog_obj_exact.export_circuit()

    verilog_obj_approx = Verilog(approximate_benchmark)
    verilog_obj_approx.export_circuit()

    convert_verilog_to_gv(exact_benchmark_name)
    convert_verilog_to_gv(approximate_benchmark)

    graph_obj_exact = Graph(exact_benchmark_name)
    graph_obj_approx = Graph(approximate_benchmark)

    graph_obj_exact.export_graph()
    graph_obj_approx.export_graph()

    z3py_obj_qor = Z3solver(exact_benchmark_name, approximate_benchmark, metric= metric)
    z3py_obj_qor.convert_gv_to_z3pyscript_maxerror_qor(zone_constraint = zone_constraint)

    z3py_obj_qor.export_z3pyscript()
    z3py_obj_qor.run_z3pyscript_qor()

    # Compare the obtained WCE
    folder, extension = z3logpath.OUTPUT_PATH['report']
    for csvfile in os.listdir(folder):
        if csvfile.endswith(extension) and re.search(approximate_benchmark, csvfile):
            report_file = f'{folder}/{csvfile}'
            with open(report_file, 'r') as rf:
                csvreader = csv.reader(rf)
                for row in csvreader:
                    if row[0] == z3logcfg.WCE:
                        if metric == MetricType.ABSOLUTE:
                            obtained_wce = int(row[1])
                        elif metric == MetricType.RELAVITVE:
                            obtained_wce = int(float(row[1]) * 100) 
                        os.remove(report_file)
                        break

    return obtained_wce
