from concurrent.futures import ThreadPoolExecutor
from subprocess import run
import os
from subxpat.verifying_weights import verify_weights

# Destination for external command outputs and errors
output_dir = 'program_outputs'

USE_MAX_LABELING = False

def worker_process(beta: int) -> int:
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
            "--max-lpp", "50",
            "--max-ppo", "50",
            "--metric", "wre",
            "--imax", "2",
            "--omax", "4",
            "--cnn-constraint", "explicit",
            "--threshold-array-idx", "1", 
            "--beta", str(beta),
            "--zone-constraint",
          
        ]

        if USE_MAX_LABELING:
            cmd.append("--max-labeling")
    
        run(cmd, stdout=out, stderr=err)
        
    print(f"Finished run for beta={beta}.")

    if "--max-labeling" in cmd:
        verify_weights(output_dir, False)
    else:
        verify_weights(output_dir, True)

    return beta

if __name__ == "__main__":
    max_threads = 2

    # the list of betas
    tasks = [16, 8, 4, 2, 1]
    

    with ThreadPoolExecutor(max_threads) as pool:
        result = list(pool.map(worker_process, tasks))

    print(f"\nAll beta runs completed successfully: {result}")

    print("\nStarting global weight verification...")
    if USE_MAX_LABELING:
        verify_weights(output_dir, False)
    else:
        verify_weights(output_dir, True)