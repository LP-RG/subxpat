from typing import Dict, Tuple

import os
from os.path import join as path_join
from contextlib import redirect_stdout

from Z3Log_patched.graph import Graph
from Z3Log_patched.z3solver import Z3solver

from Z3Log_patched.config.config import SINGLE, MAXIMIZE
from sxpat.specifications import Paths


def labeling_explicit(reference_graph: Graph, current_graph: Graph,
                      run_paths: Paths.RunFiles,
                      min_labeling: bool,
                      partial_labeling: bool, partial_cutoff: int,
                      constant_value: bool = False,
                      parallel: bool = False,
                      ) -> Tuple[Dict[str, int], Dict[str, int]]:

    tmp_reference_gv = path_join(run_paths.temporary, 'lbl_reference.gv')
    tmp_current_gv = path_join(run_paths.temporary, 'lbl_current.gv')
    Graph('', _copy_of=reference_graph).export_graph(tmp_reference_gv)
    Graph('', _copy_of=current_graph).export_graph(tmp_current_gv)

    # convert gv to z3 expression
    style = 'min' if min_labeling else 'max'
    z3py_obj = Z3solver(
        tmp_reference_gv, tmp_current_gv, run_paths.temporary,
        experiment=SINGLE, optimization=MAXIMIZE, style=style,
        partial=partial_labeling, parallel=parallel
    )

    with open(os.devnull, 'w') as f, redirect_stdout(f):  # suppress prints
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
