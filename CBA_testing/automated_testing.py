import sys
from typing import Sequence
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
            if int(output_size.search(circuit)[1]) >= min_output_size and int(output_size.search(circuit)[1]) <= max_output_size
           ]

def start_execution(benchmark_circuit: str) -> None:
    """
        Starting the execution of a single circuit.

        @authors: Ilia Zeller
    """
    print(f"Current circuit: {benchmark_circuit}")
    benchmark_path = f"benchmarks/v/{benchmark_circuit}"
    subprocess.run(["python3", "main.py", benchmark_path, "--subxpat", 
                    "--max-lpp=8", "--max-ppo=10", "--imax=6", "--omax=3", 
                    f"--max-error={2**(int(output_size.search(benchmark_path)[1]) - 2)}", 
                    "--debug"])

def main():
    """
        Automation for solving multiple circuits at the same time.

        @authors: Ilia Zeller
    """
    circuit_type = "adder"
    min_output_size = 0
    max_output_size = 5
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--circuit-type="):
                circuit_type = (arg.split('='))[1]
            elif arg.startswith("--min-output-size="):
                min_output_size = int((arg.split('='))[1])
            elif arg.startswith("--max-output-size="):
                max_output_size = int((arg.split('='))[1])
            else:
                print(
                    "--circuit-type=C     : the type of circuits to target, where C is either 'adder', 'abs_diff', 'madd', 'mul' or 'sad'\n" \
                    "--min-output-size=N  : the minimum output size of the circuits to target, where N is any positive integer\n" \
                    "--max-output-size=N  : the maximum output size of the circuits to target, where N is any positive integer")
                return
    # benchmark_circuits = get_circuits(circuit_type, min_output_size, max_output_size)
    benchmark_circuits = ['abs_diff_i4_o2.v', 'adder_i2_o2.v', 
                          'adder_i6_o4.v', 'abs_diff_i10_o5.v', 'adder_i8_o5.v', 
                          'sad_i10_o4.v', 'madd_i3_o2.v', 'mul_i4_o4.v', 
                          'madd_i6_o4.v', 'abs_diff_i8_o4.v', 'mul_i2_o2.v', 'adder_i4_o3.v', 
                          'abs_diff_i6_o3.v', 'sad_i5_o3.v']
    for circuit in benchmark_circuits:
        start_execution(circuit)

if __name__ == '__main__': main()

# # Add following code to end of xplore::print_results for testing
# 
# import sys
# import re
# with open("./data.txt", "a") as f:
#     title = f"{re.split(r'\.', (re.split('/', sys.argv[1]))[-1])[0]}\n"
#     f.write(title)
#     data = f"area->power->delay: {re.split('/', sel.apd.path, 2)[2]}, {sel.apd.area}, {sel.apd.power}, {sel.apd.delay}, {sel.apd.error_to_origin}\n" \
#     f"area->delay->power: {re.split('/', sel.adp.path, 2)[2]}, {sel.adp.area}, {sel.adp.power}, {sel.adp.delay}, {sel.adp.error_to_origin}\n" \
#     f"power->area->delay: {re.split('/', sel.pad.path, 2)[2]}, {sel.pad.area}, {sel.pad.power}, {sel.pad.delay}, {sel.pad.error_to_origin}\n" \
#     f"power->delay->area: {re.split('/', sel.pda.path, 2)[2]}, {sel.pda.area}, {sel.pda.power}, {sel.pda.delay}, {sel.pda.error_to_origin}\n" \
#     f"delay->area->power: {re.split('/', sel.dap.path, 2)[2]}, {sel.dap.area}, {sel.dap.power}, {sel.dap.delay}, {sel.dap.error_to_origin}\n" \
#     f"delay->power->area: {re.split('/', sel.dpa.path, 2)[2]}, {sel.dpa.area}, {sel.dpa.power}, {sel.dpa.delay}, {sel.dpa.error_to_origin}\n"
#     f.write(data)