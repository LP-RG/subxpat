from aiger.circuitDiGraph import gen_circuit_digraph
from aiger.circuitDiGraph import MyAnnotatedGraph
from time import perf_counter
import sys
import os
import re

def main():
    benchmark_names = []
    if sys.argv[1] == "--all":
        path = "./aiger/ver_files"
        for f in os.listdir(path):
            benchmark_names.append((re.split(r"\.", f))[0])
    else:
        benchmark_names.append(sys.argv[1])
    print("Targeting " + str(len(benchmark_names)) + " benchmarks...\n")
    total_time = 0
    for benchmark_name in benchmark_names:
        print("***")
        print("Testing MyAnnotatedGraph performance with benchmark " + benchmark_name)
        start = perf_counter()
        MyAnnotatedGraph(benchmark_name, gen_circuit_digraph(benchmark_name))
        end = perf_counter()
        time = end - start
        total_time += time
        print("Time elapsed during MyAnnotatedGraph call: " + str(time) + " seconds")
        print("***\n")
    print("Total time elapsed to execute " + str(len(benchmark_names)) + " benchmarks: " + str(total_time) + " seconds")

if __name__ == '__main__':
    main()