import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse


def copy_project_to_exp(base: str, destination: str):
    """
    Create an experiment folder by copying only necessary parts:
        - directories: config, sxpat
        - file: main.py
        - input/ver.bak --> input/ver in destination
    """
    if os.path.exists(destination):
        shutil.rmtree(destination)
    os.makedirs(destination, exist_ok=True)

    # Copy config and sxpat directories
    for d in ['config', 'sxpat']:
        src = os.path.join(base, d)
        dst = os.path.join(destination, d)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            print(f"Warning: {src} not found, skipping.")

    # Copy main.py
    main_src = os.path.join(base, 'main.py')
    main_dst = os.path.join(destination, 'main.py')
    shutil.copy2(main_src, main_dst)

    # Copy input/ver.bak to input/ver
    ver_bak = os.path.join(base, 'input', 'ver.bak')
    ver_dst_dir = os.path.join(destination, 'input', 'ver')
    shutil.copytree(ver_bak, ver_dst_dir)

def dict_to_args(kwargs_dict):
    """
    Convert a dict of keyword arguments into a list of command-line args.
    Booleans: include flag if True; skip if False.
    Others: add --key and str(value).
    """
    args = []
    for key, value in sorted(kwargs_dict.items()):
        flag = f"--{key}"
        if isinstance(value, bool):
            if value:
                args.append(flag)
        else:
            args.extend([flag, str(value)])
    return args


def run_experiment(name, circuit, args, base_dir, destination_root):
    """
    Copy the current directory to a new one for this experiment and run main.py with the given args.

    Args:
        name (str): Name of the experiment (used as output directory name).
        circuit (str): Name of the circuit on which you perform the experiments
        args (list): List of command-line arguments for main.py.
        base_dir (str): Path to the directory to copy from (defaults to cwd).
        output_base_dir (str): Path to the directory to place experiment copies.

    Returns:
        tuple: (experiment name, subprocess.CompletedProcess)
    """
    dest_dir = os.path.join(destination_root, name)
    copy_project_to_exp(base_dir, dest_dir)

    # Use the same Python interpreter
    python_executable = os.getenv("PYTHON", "python")
    cmd = [python_executable, "main.py", circuit] + dict_to_args(args)
    print(f"[{name}] Running", ' '.join(cmd))

    result = subprocess.run(
        cmd,
        cwd=dest_dir,
        capture_output=True,
        text=True
    )
    print(f"[{name}] Done")

    # Write logs
    out_log = os.path.join(dest_dir, 'terminal.out.log')
    err_log = os.path.join(dest_dir, 'terminal.err.log')
    with open(out_log, 'w') as f_out:
        f_out.write(result.stdout or '')
    with open(err_log, 'w') as f_err:
        f_err.write(result.stderr or '')
    return name, result


def run_experiments(circuit, tasks, max_workers, base_dir=None, output_base_dir=None):
    """
    Run multiple experiments in parallel.

    Args:
        circuit (str): Name of the circuit on which you perform the experiments
        tasks (dict): Mapping from experiment names to argument lists.
        max_workers (int): Number of parallel experiments.
        base_dir (str): Directory to copy for each experiment (defaults to cwd).
        output_base_dir (str): Parent directory for experiment folders.

    Returns:
        dict: Mapping experiment names to result dicts containing returncode, stdout, stderr.
    """
    print("Running experiments...")
    base_dir = base_dir or os.getcwd()
    output_base_dir = output_base_dir or base_dir

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        print("Creating futures...")
        future_to_name = {
            executor.submit(run_experiment, name, circuit, args, base_dir, output_base_dir): name
            for name, args in tasks.items()
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                _, completed = future.result()
                results[name] = {
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr
                }
            except Exception as e:
                results[name] = {"error": str(e)}
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run experiments in parallel by copying the current directory and executing main.py.")
    parser.add_argument(
        "-m",
        "--max-parallel",
        type=int,
        default=10,
        help="Maximum number of parallel experiments."
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default=None,
        help="Parent directory to place experiment copies. Defaults to current directory."
    )
    parser.add_argument(
        "circuit",
        type=str,
        help="The circuit you want to perform the experiments on"
    )
    args = parser.parse_args()
    common_args = {
        "subxpat": True,
        "imax": 4,
        "omax": 2,
        "min-labeling": True,
        "extraction-mode": 0,
        "max-lpp": 4,
        "max-ppo": 4,
        "encoding": "z3bvec",
        "metric": "wre",
        "max-error": 35,
    }

    # Define your tasks here: mapping experiment name to a list of args for main.py
    tasks = {
        # example:
        # "persistance_0_divisor_8": { **common_args, "perstistance": 0 #, "pardiv": 8 }
        # "persistance_1_divisor_8": { **common_args, "perstistance": 0 #, "pardiv": 8 }
        # ...
        **{
            f"base_et_{base_et}_step_size_{step_size}_step_factor_{step_factor}": {
                **common_args,
                "baseet": base_et,
                "stepsize": step_size,
                "stepfactor": step_factor
            }
            for base_et in [450,550]
            for step_size in [40]
            for step_factor in [1]
        }
    }

    results = run_experiments(
        args.circuit,
        tasks,
        max_workers=args.max_parallel,
        output_base_dir=args.output_dir
    )

    # Print summary
    for name, info in results.items():
        if "error" in info:
            print(f"{name} failed with error: {info['error']}")
        else:
            print(f"{name}: return code={info['returncode']}")
            if info['stdout']:
                print(f"stdout:\n{info['stdout']}")
            if info['stderr']:
                print(f"stderr:\n{info['stderr']}")

                
