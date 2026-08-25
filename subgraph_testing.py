from concurrent.futures import ThreadPoolExecutor
from subprocess import run
import os


output_dir = 'program_outputs_subgraph'

def worker_process(beta: int, idx:int) -> int:
    """
    Worker to start the subxpat framework for a specific beta.
    """
    benchmark_path = "benchmarks/v/mul_i8_o8.v"
    
    _output_dir = os.path.join(output_dir, f"beta_{beta:02d}")
    os.makedirs(_output_dir, exist_ok=True)

    print(f"Starting run for beta={beta}...")

    with (
        open(os.path.join(_output_dir, "log.out"), "wb") as out,
        open(os.path.join(_output_dir, "log.err"), "wb") as err,
    ):
        cmd = [
            "python3", "main.py", benchmark_path,
            "--subxpat",
            "--max-error", "10",
            "--extraction-mode", "56",
            "--encoding", "z3bvec",
            "--timeout", "7200",
            "--template", "nonshared",
            "--max-lpp", "4",
            "--max-ppo", "4",
            "--metric", "wre",
            "--imax", "4",
            "--omax", "2",
            "--cnn-constraint", "explicit",
            "--threshold-array-idx", str(idx), 
            "--beta", str(beta),
            "--zone-constraint",
            # "--max-labeling"
        ]
    
        run(cmd, stdout=out, stderr=err)
        
    print(f"Finished run for beta={beta}.")
    return beta

if __name__ == "__main__":
    max_threads = 2

    # the list of betas
    tasks = [16, 8, 4, 2, 1]
    
    #the list of indexes
    index=[2,3,4,5,6]
    

    with ThreadPoolExecutor(max_threads) as pool:
        result = list(pool.map(worker_process, tasks, index))

    print(f"\nAll beta runs completed successfully: {result}")