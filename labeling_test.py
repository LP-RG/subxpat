from __future__ import annotations


from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.solving.Z3Solver import Z3FuncBitVecSolver, Z3FuncIntSolver, Z3DirectIntSolver, Z3DirectBitVecSolver
from sxpat.specifications import Specifications
from sxpat.templating.Labelling import Labeling
from sxpat.converting import iograph_from_legacy, sgraph_from_legacy
from sxpat.labelling_weird import labeling_using_normal, labeling_using_define_improved
import sys
import time
from sxpat.labeling import labeling_explicit
#this is just a test script to benchmark the labeling functions with different solver
#basically : apply labeling with a solver, measure time and compare with labeling explicit
current_filename = sys.argv[1]
used_solver = sys.argv[2]
print("Current file name: {}".format(current_filename))
#read arguments
print("inputed solver {}".format(used_solver))
u_solver = Z3FuncBitVecSolver
print(f"using solver {used_solver}")
if used_solver == "Z3FuncIntSolver":
    solver = Z3FuncIntSolver
elif used_solver == "Z3DirectIntSolver":
    solver = Z3DirectIntSolver
elif used_solver == "Z3DirectBitVecSolver":
    solver = Z3DirectBitVecSolver
elif used_solver == "Z3FuncBitVecSolver":
    solver = Z3FuncBitVecSolver
else:
    print(f"solver not detected, using default one. available solvers are : ")
    print(f"Z3FuncIntSolver | Z3DirectIntSolver | Z3DirectBitVecSolver | Z3FuncBitVecSolver ")
    u_solver = None
all_solvers = {
        "Z3FuncBitVecSolver": Z3FuncBitVecSolver,
        "Z3FuncIntSolver": Z3FuncIntSolver,
        "Z3DirectIntSolver": Z3DirectIntSolver
        #"Z3DirectBitVecSolver": Z3DirectBitVecSolver
    }
#commented last one as it is the buggy one

labeling_with_solvers = []
print(f"Testing labeling_using_explicit...")
start_time = time.perf_counter()
weights_explicit = labeling_explicit(
    current_filename, current_filename,
    min_labeling=False,
    partial_labeling=False, 
    partial_cutoff=None,
    parallel=False
)

explicit_time = time.perf_counter() - start_time
print(f"Explicit method completed in {explicit_time:.4f}s")
print(f"Found {len(weights_explicit)} node weights")

if u_solver is not None:
    #processing wiht a specific solver
    print(f"Benchmarking labeling methods for: {current_filename}, encoder : {used_solver}")
    print(f"=" * 60)
    
    print(f"\nTesting labeling_using_define_improved...")
    start_time = time.perf_counter()

    weights_improved = labeling_using_define_improved(
        current_filename, current_filename,
        min_labeling=False,
        partial_labeling=False, 
        partial_cutoff=None,
        parallel=False,
        MODE_VECTOR=[False, True, False, False],
        solver = u_solver
    )
    improved_time = time.perf_counter() - start_time

    print(f"Improved method completed in {improved_time:.4f}s")
    print(f"Found {len(weights_improved)} node weights")


    print(f"Testing labeling_using_normal...")
    start_time = time.perf_counter()
    weights_normal = labeling_using_normal(
        current_filename, current_filename,
        min_labeling=False,
        partial_labeling=False, 
        partial_cutoff=None,
        parallel=False,
        solver = u_solver
    )
    normal_time = time.perf_counter() - start_time

    print(f"Normal method completed in {normal_time:.4f}s")
    print(f"Found {len(weights_normal)} node weights")

    print(f"\n" + "="*60)
    print(f"COMPARISON RESULTS")
    print(f"="*60)

    print(f"Normal time:   {normal_time:.4f}s")
    print(f"Improved time: {improved_time:.4f}s")
    print(f"Explicit time: {explicit_time:.4f}s")

    if improved_time < normal_time:
        speedup = normal_time / improved_time
        print(f"Improved is {speedup:.2f}x FASTER")
    else:
        slowdown = improved_time / normal_time
        print(f"Improved is {slowdown:.2f}x SLOWER")

    time_diff = abs(normal_time - improved_time)
    print(f"Time difference: {time_diff:.4f}s")

    if weights_normal.keys() == weights_improved.keys():
        identical = sum(1 for k in weights_normal.keys() if weights_normal[k] == weights_improved[k])
        total = len(weights_normal)
        accuracy = (identical / total) * 100 if total > 0 else 0
        print(f"Result accuracy: {accuracy:.1f}% ({identical}/{total} nodes match)")
    else:
        different_counter = 0
        for weight in weights_normal.keys():
            if weights_normal[weight] != weights_improved[weight]:
                print(f"find different weights!")
                print(f"weights for {weight},  normal :  {weights_normal[weight]}; improved : {weights_improved[weight]}")
                different_counter += 1

        print(f"Different number of nodes processed, {different_counter} nodes differ !")
    result = {"improved time": improved_time, "normal time": normal_time, "solver": solver}
    labeling_with_solvers.append(result)
else :
    #processing with all solvers to see difference
    for index , solver in enumerate(all_solvers.keys()):

        print(f"Benchmarking labeling methods for: {current_filename}, encoder : {solver}")
        print(f"=" * 60)
        
        print(f"\nTesting labeling_using_define_improved...")
        start_time = time.perf_counter()

        weights_improved = labeling_using_define_improved(
            current_filename, current_filename,
            min_labeling=False,
            partial_labeling=False, 
            partial_cutoff=None,
            parallel=False,
            MODE_VECTOR=[False, True, False, False],
            solver = all_solvers[solver]
        )
        improved_time = time.perf_counter() - start_time

        print(f"Improved method completed in {improved_time:.4f}s")
        print(f"Found {len(weights_improved)} node weights")


        print(f"Testing labeling_using_normal...")
        start_time = time.perf_counter()
        weights_normal = labeling_using_normal(
            current_filename, current_filename,
            min_labeling=False,
            partial_labeling=False, 
            partial_cutoff=None,
            parallel=False,
            solver = all_solvers[solver]
        )
        normal_time = time.perf_counter() - start_time

        print(f"Normal method completed in {normal_time:.4f}s")
        print(f"Found {len(weights_normal)} node weights")

        print(f"\n" + "="*60)
        print(f"COMPARISON RESULTS")
        print(f"="*60)

        print(f"Normal time:   {normal_time:.4f}s")
        print(f"Improved time: {improved_time:.4f}s")
        print(f"Explicit time: {explicit_time:.4f}s")

        if improved_time < normal_time:
            speedup = normal_time / improved_time
            print(f"Improved is {speedup:.2f}x FASTER")
        else:
            slowdown = improved_time / normal_time
            print(f"Improved is {slowdown:.2f}x SLOWER")

        time_diff = abs(normal_time - improved_time)
        print(f"Time difference: {time_diff:.4f}s")

        if weights_normal.keys() == weights_improved.keys():
            identical = sum(1 for k in weights_normal.keys() if weights_normal[k] == weights_improved[k])
            total = len(weights_normal)
            accuracy = (identical / total) * 100 if total > 0 else 0
            print(f"Result accuracy: {accuracy:.1f}% ({identical}/{total} nodes match)")
        else:
            different_counter = 0
            for weight in weights_normal.keys():
                if weights_normal[weight] != weights_improved[weight]:
                    print(f"find different weights!")
                    print(f"weights for {weight},  normal :  {weights_normal[weight]}; improved : {weights_improved[weight]}")
                    different_counter += 1

            print(f"Different number of nodes processed, {different_counter} nodes differ !")
        result = {"improved time": improved_time, "normal time": normal_time, "solver": solver}
        labeling_with_solvers.append(result)
        
    print(f"showing results...: ")
    best_improved = improved_time
    best_normal = normal_time
    best_index = 0
    for idx, result in enumerate(labeling_with_solvers):
        if result["improved time"] < improved_time:
            improved_time = result["improved time"]
            best_index = idx
        if result["improved time"] < normal_time:
            normal_time_time = result["improved time"]   
        solver = result["solver"] 
        normal_t = result["normal time"]
        improved_t = result["improved time"]
        print(f"times for solver {solver}")
        print(f"normal time : {normal_t}")
        print(f"improved time :{improved_t}")
        print(f"explicit time : {explicit_time}")
    print(f"best improved time : {best_improved}")
    print(f"best normal time : {best_normal}")
    solver =labeling_with_solvers[best_index["solver"]]
    print(f"for solver {solver}")

