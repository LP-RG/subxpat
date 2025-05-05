from typing import Dict, Tuple

import glob
import os
from sxpat.utils.filesystem import FS

from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import convert_verilog_to_gv
from Z3Log.config.config import SINGLE, MAXIMIZE
import Z3Log.config.path as paths
from Z3Log.z3solver import Z3solver


def labeling_explicit(exact_benchmark_name: str, approximate_benchmark: str,
                      min_labeling: bool,
                      partial_labeling: bool, partial_cutoff: int,
                      constant_value: int = 0,
                      parallel: bool = False,
                      ) -> Tuple[Dict[str, int], Dict[str, int]]:

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
    style = 'min' if min_labeling else 'max'
    z3py_obj = Z3solver(
        exact_benchmark_name, approximate_benchmark,
        experiment=SINGLE, optimization=MAXIMIZE, style=style,
        partial=partial_labeling, parallel=parallel
    )

    if constant_value == 0:
        labels_false = z3py_obj.label_circuit(False, partial=partial_labeling, et=partial_cutoff)
        labels_pair = (labels_false, labels_false)
    elif constant_value == 1:
        labels_true = z3py_obj.label_circuit(True, partial=partial_labeling, et=partial_cutoff)
        labels_pair = (labels_true, labels_true)
    else:
        labels_false = z3py_obj.label_circuit(False, partial=partial_labeling, et=partial_cutoff)
        labels_true = z3py_obj.label_circuit(True, partial=partial_labeling, et=partial_cutoff)
        labels_pair = (labels_true, labels_false)

    # cleanup (folder report/ and z3/)
    for folder in [paths.OUTPUT_PATH['report'][0], paths.OUTPUT_PATH['z3'][0]]:
        for dir in glob.glob(f'{folder}/*labeling*'):
            if os.path.isdir(dir):
                FS.rmdir(dir, True)

    return labels_pair
