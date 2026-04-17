import os

from sxpat.specifications import Specifications, SlashType
from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.graph.graph import IOGraph

from sxpat.solvers.Z3Solver import Z3DirectBitVecSolver, Z3DirectIntSolver, Z3FuncBitVecSolver, Z3FuncIntSolver
from sxpat.solvers.QbfSolver import QbfSolver

from sxpat.converting import VerilogExporter
from sxpat.converting.legacy import iograph_from_legacy

from sxpat.utils.timer import Timer

from sxpat.definitions.templates.InputsReplace import InputsReplace

def input_amount(exact_benchmark: str):
    possibilities = {
        'abs_diff': 2,
        'adder' : 2,
        'madd' : 3,
        'mul' : 2,
        'sad' : 5
    }

    for x in possibilities.keys():
        if exact_benchmark.startswith(x):
            return possibilities[x]
    
    raise(ValueError(f'{exact_benchmark} isn\'t available'))

def calculate(exact: IOGraph, specs_obj: Specifications,inputs: list):
    selected_nodes = []
    for i in range(len(inputs)):
        for j in range(inputs[i]):
            selected_nodes.append(f'in{i*len(exact.inputs)//len(inputs)+j}')
    
    p_graph, c_graph = InputsReplace.define(exact, specs_obj, selected_nodes)
    solve = QbfSolver.solve
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
        
def exploration(exact: IOGraph, specs_obj: Specifications, exact_benchmark: str):
    func = {
        SlashType.SLASH_INPUT_ITERATIVE: same_iterative,
    }[specs_obj.slash]

    return func(exact, specs_obj, input_amount(exact_benchmark))


def remove_inputs(specs_obj: Specifications, exact_benchmark: str) -> str:

    annotated = AnnotatedGraph(specs_obj.exact_benchmark, specs_obj.path.run)
    exact = iograph_from_legacy(annotated)

    start = Timer.now()
    selected_nodes, constant = exploration(exact, specs_obj, exact_benchmark)
    print(f'total_slash_inputs = {Timer.now() - start}')

    p_graph, _ = InputsReplace.define(exact, specs_obj, selected_nodes, replace_with_constant=constant)
    io_graph = IOGraph([n for n in p_graph.nodes], p_graph.inputs_names, p_graph.outputs_names)
    
    circuit_id = f'gen_slash'
    verilog_path = os.path.join(specs_obj.path.run.verilog, f'{circuit_id}.v')
    VerilogExporter.to_file(
        io_graph, verilog_path,
        VerilogExporter.Info(model_number=0),
    )
    return verilog_path