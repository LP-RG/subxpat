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
            if circuit.startswith("adder") and int(output_size.search(circuit)[1]) <= 9
           ]

def start_execution(benchmark_circuit: str) -> None:
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
    benchmark_circuits = get_circuits()
    processes = 8
    with ThreadPoolExecutor(processes) as pool:
        [*var] = pool.map(lambda x: (x, start_execution(x)), benchmark_circuits)

if __name__ == '__main__': main()