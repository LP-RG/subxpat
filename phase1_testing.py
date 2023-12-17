from typing import Iterator, Tuple
import dataclasses as dc

import os
import sys
import subprocess
from multiprocessing.pool import Pool

from z_marco.utils import pprint


@dc.dataclass
class Task:
    verilog_file: str
    error_threshold: int
    max_lpp: int
    max_ppo: int
    full_error_func: int
    sub_error_func: int
    extraction: int
    extraction_param: int


def cell_iterator(max_lpp: int, max_ppo: int) -> Iterator[Tuple[int, int]]:
    # special cell
    yield (0, 1)

    # grid cells
    for ppo in range(1, max_ppo + 1):
        for lpp in range(1, max_lpp + 1):
            yield (lpp, ppo)


circuits = [
    # medium
    # ('input/ver/abs_diff_i8_o5.v', 2**4),
    # ('input/ver/adder_i8_o5.v', 2**5),
    # ('input/ver/mul_i8_o8.v', 2**8),
    # ('input/ver/madd_i9_o6.v', 2**6),
    # large
    # ('input/ver/adder_i12_o7.v', 2**7),
    # ('input/ver/abs_diff_i12_o7.v', 2**6),
    # ('input/ver/mul_i12_o12.v', 2**12),
    ('input/ver/adder_i16_o9.v', 2**9),
    ('input/ver/abs_diff_i16_o9.v', 2**8),

    # extra large
]

ets_portions = [
    lambda x: x * 1 // 16,
    lambda x: x * 2 // 16,
    lambda x: x * 4 // 16,
    lambda x: x * 6 // 16,
]

partitioning_omax = [
    (1, (0, 1)),
    (2, (4, 8)),
]

full_error_functions = [
    1
]

sub_error_functions = [
    1, 2
]

for filename, max_error in circuits:
    for et_portion in ets_portions:
        et = et_portion(max_error)
        for omax, (max_lpp, max_ppo) in partitioning_omax:
            for full_func in full_error_functions:
                for sub_func in sub_error_functions:
                    # grid exploration
                    for lpp, ppo in cell_iterator(max_lpp, max_ppo):
                        command = [
                            "python3", "temp_main6.py",
                            filename,
                            f"-lpp={lpp}", f"-ppo={ppo}",
                            f"-et={et}",
                            f"--full_error_function={full_func}",
                            f"--sub_error_function={sub_func}",

                            # partitioning
                            "--subxpat",
                            "--min_labeling",
                            "-mode=4",
                            f"-omax={omax}",
                        ]
                        print("COMMAND", " ".join(command), flush=True)
                        res = subprocess.run(command)
                        exit()


# # if len(sys.argv) == 2:
# #     tasks = [tasks[int(sys.argv[1])]]

# for circuit, max_lpp, max_ppo, ets in tasks:
#     for et in ets:
#         for lpp, ppo in cell_iterator(max_lpp, max_ppo):
#             command = f"python3 temp_main6.py {circuit} -lpp={lpp} -ppo={ppo} -et={et}"
#             print("COMMAND", command, flush=True)
#             res = subprocess.run(
#                 command.split(" "),
#                 # stdout=subprocess.PIPE
#             )
