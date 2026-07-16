from typing import Sequence
from multiprocessing.pool import ThreadPool
import subprocess
import os


def get_paths() -> Sequence[str]:
    path = "benchmarks//v"
    circuits = os.listdir(path)
    return [
            "benchmarks/v/" + circuit 
            for circuit in circuits
           ]

def start_execution(benchmark_path: str) -> None:
    subprocess.run(["python3", "main.py", benchmark_path, "--subxpat", 
                    "--max-lpp=8", "--max-ppo=10", "--imax=6", "--omax=3", 
                    "--max-error=8", "--no-partial-labeling", "--debug"])

def main():
    benchmark_paths = get_paths()
    processes = 3
    with ThreadPool(processes) as pool:
        pool.map(lambda x: (x, start_execution(x)), benchmark_paths)



if __name__ == '__main__': main()