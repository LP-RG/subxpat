from typing import Dict, Tuple

from Z3Log_patched.verilog import Verilog
from Z3Log_patched.graph import Graph
from Z3Log_patched.utils import convert_verilog_to_gv
from Z3Log_patched.config.config import SINGLE, MAXIMIZE

from Z3Log_patched.z3solver import Z3solver

from sxpat.specifications import Paths


def labeling_explicit(exact_in_verilog_path: str, current_in_verilog_path: str,
                      run_paths: Paths.RunFiles,
                      min_labeling: bool,
                      partial_labeling: bool, partial_cutoff: int,
                      constant_value: bool = False,
                      parallel: bool = False,
                      ) -> Tuple[Dict[str, int], Dict[str, int]]:

    # 1) create a clean verilog out of exact and approximate circuits
    verilog_obj_exact = Verilog(exact_in_verilog_path, tmp_exact_v := f'{run_paths.temporary}/lbl_exact.v', run_paths.temporary)
    verilog_obj_exact.export_circuit()
    verilog_obj_approx = Verilog(current_in_verilog_path, tmp_current_v := f'{run_paths.temporary}/lbl_current.v', run_paths.temporary)
    verilog_obj_approx.export_circuit()

    convert_verilog_to_gv(tmp_exact_v, tmp_exact_gv := f'{run_paths.temporary}/lbl_exact.gv', run_paths.temporary)
    convert_verilog_to_gv(tmp_current_v, tmp_current_gv := f'{run_paths.temporary}/lbl_current.gv', run_paths.temporary)

    # 2) convert clean exact and approximate circuits into their clean gv formats
    graph_obj_exact = Graph(tmp_exact_gv)
    graph_obj_current = Graph(tmp_current_gv)
    graph_obj_exact.export_graph()
    graph_obj_current.export_graph()

    # convert gv to z3 expression
    style = 'min' if min_labeling else 'max'
    z3py_obj = Z3solver(
        tmp_exact_gv, tmp_current_gv, run_paths.temporary,
        experiment=SINGLE, optimization=MAXIMIZE, style=style,
        partial=partial_labeling, parallel=parallel
    )

    if constant_value is False:
        labels_pair = (
            z3py_obj.label_circuit(False, partial=partial_labeling, et=partial_cutoff),
        ) * 2
    elif constant_value is True:
        labels_pair = (
            z3py_obj.label_circuit(True, partial=partial_labeling, et=partial_cutoff),
        ) * 2
    else:
        labels_pair = (
            z3py_obj.label_circuit(False, partial=partial_labeling, et=partial_cutoff),
            z3py_obj.label_circuit(True, partial=partial_labeling, et=partial_cutoff),
        )

    return labels_pair
