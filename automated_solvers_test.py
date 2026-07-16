from typing import Sequence
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import re

output_size = re.compile(r'o(\d+)')

def get_paths() -> Sequence[str]:
    path = "benchmarks//v"
    circuits = os.listdir(path)
    return [
            "benchmarks/v/" + circuit 
            for circuit in circuits
            if circuit.startswith("adder") and int(output_size.search(circuit)[1]) <= 49 
           ]

def start_execution(benchmark_path: str) -> None:
    subprocess.run(["python3", "main.py", benchmark_path, "--subxpat", 
                    "--max-lpp=8", "--max-ppo=10", "--imax=6", "--omax=3", 
                    f"--max-error={2**(int(output_size.search(benchmark_path)[1]) - 2)}", 
                    "--no-partial-labeling", "--debug"])

def main():
    benchmark_paths = get_paths()
    processes = 10
    with ThreadPoolExecutor(processes) as pool:
        pool.map(lambda x: (x, start_execution(x)), benchmark_paths)


if __name__ == '__main__': main()