# from __future__ import annotations
# from typing import Dict, Iterable, Iterator, List, Tuple

# from tabulate import tabulate
# import functools as ft
# import csv
# import math
# import networkx as nx

# from Z3Log.config import path as z3logpath

# from sxpat.labeling import labeling_explicit
# from sxpat.metrics import MetricsEstimator
from sxpat.specifications import Specifications, SlashExploration
# from sxpat.config import paths as sxpatpaths
# from sxpat.config.config import *
# from sxpat.utils.filesystem import FS
# from sxpat.utils.name import NameData
# from sxpat.stats import Stats, sxpatconfig, Model
from sxpat.annotatedGraph import AnnotatedGraph
# from sxpat.definitions.questions.max_distance_evaluation import MaxDistanceEvaluation
from sxpat.graph.graph import IOGraph

# from sxpat.templating import get_specialized as get_templater
from sxpat.solvers.Z3Solver import Z3DirectBitVecSolver, Z3DirectIntSolver, Z3FuncBitVecSolver, Z3FuncIntSolver
from sxpat.solvers.QbfSolver import QbfSolver

from sxpat.converting import VerilogExporter
from sxpat.converting.legacy import iograph_from_legacy
# from sxpat.converting import set_bool_constants, prevent_combination

# from sxpat.utils.print import pprint
from sxpat.utils.timer import Timer

# from sxpat.templating.LabelingConstants import Labeling
from sxpat.definitions.templates.InputsReplace import InputsReplace
# from sxpat.temp_labelling import labeling
# from sxpat.fast_labeling import fast_labeling, upper_bound, lower_bound, calc_label
# import random

def input_amount(specs_obj: Specifications):
    possibilities = {
        'abs_diff': 2,
        'adder' : 2,
        'madd' : 3,
        'mul' : 2,
        'sad' : 5
    }

    for x in possibilities.keys():
        if specs_obj.exact_benchmark.startswith(x):
            return possibilities[x]
    
    raise(ValueError(f'{specs_obj.exact_benchmark} isn\'t available'))

def calculate(exact: IOGraph, specs_obj: Specifications,inputs: list):
    selected_nodes = []
    for i in range(len(inputs)):
        for j in range(inputs[i]):
            selected_nodes.append(f'in{i*len(exact.inputs)//len(inputs)+j}')
    
    p_graph, c_graph = InputsReplace.define(exact, specs_obj, selected_nodes)
    solve = Z3DirectIntSolver.solve
    status, model = solve((exact, p_graph, c_graph), specs_obj)

    return status == 'sat', model['constant_ID'] if status == 'sat' else None

# def same_predict(exact: IOGraph, specs_obj: Specifications, input_count: int):
#     low = 0, high = len(exact.inputs)//input_count
#     current = high - 1
#     saved = {}

#     def _calc(x: int):
#         if x in saved:
#             return saved[x]
#         saved[x], _ = calculate(exact, specs_obj, [x for _ in range(input_count)])
#         if saved[x] < specs_obj.error_for_slash:
#             low = x
#         else:
#             high = x - 1
#         return saved[x]

#     while low < high:
#         current_error = _calc(current)

#         if current_error < specs_obj.error_for_slash:
#             nex = current + 1
#             nex_error = _calc(nex)
#             predicted_error = nex_error
#             while predicted_error < specs_obj.error_for_slash:
#                 #TODO: continue here
#                 pass
        
#         elif current_error > specs_obj.error_for_slash:
#             nex = current - 1

#         else:
#             return [current for _ in range(input_count)]

def same_iterative(exact: IOGraph, specs_obj: Specifications, input_count: int):
    x = len(exact.inputs)//input_count
    while True:
        x -= 1
        status, constant = calculate(exact, specs_obj, [x for _ in range(input_count)])

        if status:
            break

    res = []
    for i in range(input_count):
        for j in range(x):
            res.append(f'in{i*len(exact.inputs)//input_count+j}')
    return res, constant
        
def exploration(exact: IOGraph, specs_obj: Specifications):
    func = {
        SlashExploration.SAME_ITERATIVE: same_iterative,
        # SlashExploration.SAME_BINARY: same_binary,
        # SlashExploration.SAME_PREDICT: same_predict,
    }[specs_obj.slash_inputs_explore]

    return func(exact, specs_obj, input_amount(specs_obj))


def remove_inputs(specs_obj: Specifications) -> str:

    annotated = AnnotatedGraph.cached_load(specs_obj.exact_benchmark)
    exact = iograph_from_legacy(annotated)

    start = Timer.now()
    selected_nodes, constant = exploration(exact, specs_obj)
    print(f'total_slash_inputs = {Timer.now() - start}')

    p_graph, _ = InputsReplace.define(exact, specs_obj, selected_nodes, replace_with_constant=constant)
    io_graph = IOGraph([n for n in p_graph.nodes], p_graph.inputs_names, p_graph.outputs_names)
    
    base_path = f'input/ver/{specs_obj.exact_benchmark}_{specs_obj.time_id}_i{specs_obj.iteration}_{{model_number}}.v'
    verilog_path = base_path.format(model_number=0)
    VerilogExporter.to_file(
        io_graph, verilog_path,
        VerilogExporter.Info(model_number=0),
    )
    return verilog_path[10:]


    