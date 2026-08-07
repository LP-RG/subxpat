import csv
from typing import Sequence
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import re

output_size = re.compile(r'o(\d+)')

def get_circuits() -> Sequence[str]:
    path = "benchmarks//v"
    circuits = os.listdir(path)
    return [
            circuit 
            for circuit in circuits
            if circuit.startswith("adder") and int(output_size.search(circuit)[1]) > 9 and int(output_size.search(circuit)[1]) < 20
           ]

def start_execution(benchmark_circuit: str) -> None:
    with open('./costs.txt', 'a') as file:
        file.write(f'------------------------------------------\n')
        file.write(f'Circuit: {benchmark_circuit.split('.')[0]}\n')
        file.write(f'------------------------------------------\n')
    benchmark_path = f"benchmarks/v/{benchmark_circuit}"
    logs_path = f"logs/{benchmark_circuit.split('.')[0]}"
    os.makedirs(logs_path, exist_ok=True)
    with open(f"{logs_path}/out.txt", "w") as out:
        with open(f"{logs_path}/err.txt", "w") as err:
            subprocess.run(["python3", "main.py", benchmark_path, "--subxpat", 
                            "--max-lpp=8", "--max-ppo=10", "--imax=6", "--omax=3", 
                            f"--max-error={2**(int(output_size.search(benchmark_path)[1]) - 2)}", 
                            "--no-partial-labeling", "--debug"], stdout=out, stderr=err)

def main():
    with open('./individual_nodes_times.csv', 'w', newline='') as csvfile:
        fieldnames = ['iteration', 'node', 'solver', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    benchmark_circuits = get_circuits()
    benchmark_circuits = ["adder_i8_o5.v"]
    processes = 8
    with ThreadPoolExecutor(processes) as pool:
        [*var] = pool.map(lambda x: (x, start_execution(x)), benchmark_circuits)

if __name__ == '__main__': main()