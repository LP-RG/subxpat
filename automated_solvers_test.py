import csv
import sys
from typing import Sequence
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import re

output_size = re.compile(r'o(\d+)')

def get_circuits(circuit_type: str, min_output_size: int, max_output_size: int) -> Sequence[str]:
    """
        Get all file names for circuits following the required constraints (circuit type and output size bounds).

        @authors: Ilia Zeller
    """
    path = "benchmarks//v"
    circuits = os.listdir(path)
    return [
            circuit 
            for circuit in circuits
            if circuit.startswith(circuit_type) and int(output_size.search(circuit)[1]) >= min_output_size and int(output_size.search(circuit)[1]) <= max_output_size
           ]

def start_execution(benchmark_circuit: str, record_steps_costs: bool, record_nodes_times: bool) -> None:
    """
        Starting the execution of a single circuit.

        @authors: Ilia Zeller
    """
    if record_steps_costs:
        with open(f'./individual_steps_costs/{benchmark_circuit.split('.')[0]}.csv', 'w', newline='') as csvfile:
            fieldnames = ['iteration', 'threshold_computation_time', 'annotated_graph_loading_time', 'labeling_time', 'subgraph_extraction_time', 'explore_grid_time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    if record_nodes_times:
        with open(f'./individual_nodes_times/{benchmark_circuit.split('.')[0]}.csv', 'w', newline='') as csvfile:
            fieldnames = ['iteration', 'node', 'solver', 'time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    benchmark_path = f"benchmarks/v/{benchmark_circuit}"
    logs_path = f"logs/{benchmark_circuit.split('.')[0]}"
    os.makedirs(logs_path, exist_ok=True)
    with open(f"{logs_path}/out.txt", "w") as out:
        with open(f"{logs_path}/err.txt", "w") as err:
            subprocess.run(["python3", "main.py", benchmark_path, "--subxpat", 
                            "--max-lpp=8", "--max-ppo=10", "--imax=6", "--omax=3", 
                            f"--max-error={2**(int(output_size.search(benchmark_path)[1]) - 2)}", 
                            "--debug"], stdout=out, stderr=err)

def main():
    """
        Automation for solving multiple circuits at the same time.

        @authors: Ilia Zeller
    """
    circuit_type = "adder"
    min_output_size = 0
    max_output_size = 10
    record_steps_costs = False
    record_nodes_times = False
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--circuit-type="):
                circuit_type = (arg.split('='))[1]
            elif arg.startswith("--min-output-size="):
                min_output_size = int((arg.split('='))[1])
            elif arg.startswith("--max-output-size="):
                max_output_size = int((arg.split('='))[1])
            elif arg == "--record-steps-costs":
                record_steps_costs = True
            elif arg == "--record-nodes-times":
                record_nodes_times = True
            else:
                print(
                    "--circuit-type=C     : the type of circuits to target, where C is either 'adder', 'abs_diff', 'madd', 'mul' or 'sad'\n" \
                    "--min-output-size=N  : the minimum output size of the circuits to target, where N is any positive integer\n" \
                    "--max-output-size=N  : the maximum output size of the circuits to target, where N is any positive integer\n" \
                    "--record-steps-costs : flag for recording the individual steps costs of the computation\n" \
                    "--record-nodes-times : flag for recording the individual nodes times")
                return
    os.makedirs("./individual_steps_costs", exist_ok=True)
    os.makedirs("./individual_nodes_times", exist_ok=True)
    benchmark_circuits = get_circuits(circuit_type, min_output_size, max_output_size)
    processes = 10
    with ThreadPoolExecutor(processes) as pool:
        [*var] = pool.map(lambda x: (x, start_execution(x, record_steps_costs, record_nodes_times)), benchmark_circuits)

if __name__ == '__main__': main()