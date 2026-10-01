from sxpat.utils.formats.aiger import iograph_from_digraph, gen_circuit_digraph
from sxpat.newag import load_circuit_from_verilog_testing
from sxpat.specifications import Paths
from time import perf_counter
from typing import Sequence
from sxpat.utils.names import extract_name
import sys
import os
import re
import csv

output_size = re.compile(r'o(\d+)')
inputs_paths = ["./benchmarks/v", "./input/ver"]
inputs_path = inputs_paths[0]

def get_circuits(circuit_type, min_output_size: int, max_output_size: int) -> Sequence[str]:
    """
        Get all file names for circuits following the required constraints (circuit type and output size bounds).

        @authors: Ilia Zeller
    """
    path = inputs_path
    circuits = os.listdir(path)
    return [
            (re.split(r"\.", circuit))[0]
            for circuit in circuits
            if circuit.startswith(circuit_type) and int(output_size.search(circuit)[1]) >= min_output_size and int(output_size.search(circuit)[1]) <= max_output_size
           ]

def new_execution(benchmark_circuits: list) -> None:
    """
        Generating IOGraph for a single circuit, both in the new way (using aigverse).

        @authors: Ilia Zeller
    """

    fieldnames = ['name', 'generation_time', 'inputs_amount', 'outputs_amount', 'AND_gates_amount', 'NOT_gates_amount', 'const_amount']

    with open(f'./new_iograph_generation.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
  
    # new way (using aigverse)
    for benchmark_circuit in benchmark_circuits:
        info = list()
        start = perf_counter()
        iograph_from_digraph(benchmark_circuit, gen_circuit_digraph(benchmark_circuit, inputs_path), info)
        end = perf_counter()
        time = end - start
        with open(f'./new_iograph_generation.csv', 'a', newline='') as csvfile:
            data = [ {'name': benchmark_circuit, 
                    'generation_time': time, 
                    'inputs_amount': info[0], 
                    'outputs_amount': info[1],
                    'AND_gates_amount': info[2],
                    'NOT_gates_amount': info[3],
                    'const_amount': info[4],} ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)

def legacy_execution(benchmark_circuits: list) -> None:
    """
        Generating IOGraph for a single circuit, in the legacy way.

        @authors: Ilia Zeller
    """

    fieldnames = ['name', 'generation_time', 'inputs_amount', 'outputs_amount', 'gates_amount', 'const_amount']

    with open(f'./legacy_iograph_generation.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    # legacy way
    for benchmark_circuit in benchmark_circuits:
        specs = Paths(f"legacy/{extract_name(benchmark_circuit)}", "", "", "", True)
        os.makedirs(f"legacy/{extract_name(benchmark_circuit)}/tmp", exist_ok=True)
        info = list()
        start = perf_counter()
        load_circuit_from_verilog_testing(f"{inputs_path}/{benchmark_circuit}.v", specs.run, info)
        end = perf_counter()
        time = end - start
        with open(f'./legacy_iograph_generation.csv', 'a', newline='') as csvfile:
            data = [ {'name': benchmark_circuit, 
                    'generation_time': time, 
                    'inputs_amount': info[0], 
                    'outputs_amount': info[1],
                    'gates_amount': info[2],
                    'const_amount': info[3],} ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)


def main():
    """
        @authors: Ilia Zeller
    """
    benchmark_names = []
    if sys.argv[1] == "--all":
        path = inputs_path
        for f in os.listdir(path):
            benchmark_names.append((re.split(r"\.", f))[0])
    elif not sys.argv[1].startswith("--"):
        benchmark_names.append(sys.argv[1])
    else:
        circuit_type = ("abs_diff", "adder", "madd", "mul", "sad")
        min_output_size = 0
        max_output_size = sys.maxsize
        for arg in sys.argv[1:]:
            if arg.startswith("--circuit-type="):
                circuit_type = (arg.split('='))[1]
            elif arg.startswith("--min-output-size="):
                min_output_size = int((arg.split('='))[1])
            elif arg.startswith("--max-output-size="):
                max_output_size = int((arg.split('='))[1])
        benchmark_names = get_circuits(circuit_type, min_output_size, max_output_size)
    print(f"Targeting {len(benchmark_names)} benchmarks while testing")
    start = perf_counter()
    new_execution(list(benchmark_names))
    end = perf_counter()
    time = end - start
    print(f"Testing new execution on all benchmarks took {time} seconds")
    start = perf_counter()
    legacy_execution(list(benchmark_names))
    end = perf_counter()
    time = end - start
    print(f"Testing legacy execution on all benchmarks took {time} seconds")

if __name__ == '__main__':
    main()