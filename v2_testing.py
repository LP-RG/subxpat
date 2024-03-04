from typing import Iterable, Iterator, List, Tuple
import dataclasses as dc

import subprocess
import datetime
import itertools as it


def cell_iterator(max_lpp: int, max_ppo: int) -> Iterator[Tuple[int, int]]:
    # special cell
    yield (0, 1)

    # grid cells
    for ppo in range(1, max_ppo + 1):
        for lpp in range(1, max_lpp + 1):
            yield (lpp, ppo)


def is_dominated(coords: Tuple[int, int], sats: List[Tuple[int, int]]) -> bool:
    lpp, ppo = coords
    for d_lpp, d_ppo in sats:
        if lpp >= d_lpp and ppo >= d_ppo:
            return True
    return False


def run_command(command: Iterable[str]):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    with open(logfile, 'ab') as f:
        for line in proc.stdout:
            print(line.decode(), end='', sep='', )
            f.write(line)

    proc.wait()


circuits = [
    # stuff
    # ('input/ver/mul_i8_o8.v', 2**8),
    # ('input/ver/mul_i12_o12.v', 2**12),
    # ('input/ver/madd_i9_o6.v', 2**6),

    # adder
    # ('input/ver/adder_i4_o3.v', 2**3),
    # ('input/ver/adder_i6_o4.v', 2**4),
    ('input/ver/adder_i8_o5.v', 2**5),
    ('input/ver/adder_i10_o6.v', 2**6),
    ('input/ver/adder_i12_o7.v', 2**7),
    ('input/ver/adder_i16_o9.v', 2**9),
    ('input/ver/adder_i20_o11.v', 2**11),
    ('input/ver/adder_i24_o13.v', 2**13),
    ('input/ver/adder_i28_o15.v', 2**15),
    ('input/ver/adder_i32_o17.v', 2**17),

    # abs_diff
    # ('input/ver/abs_diff_i8_o4.v', 2**4),
    # ('input/ver/abs_diff_i10_o5.v', 2**4),
    # ('input/ver/abs_diff_i12_o6.v', 2**6),
    # ('input/ver/abs_diff_i16_o8.v', 2**8),
    # ('input/ver/abs_diff_i20_o10.v', 2**10),
    # ('input/ver/abs_diff_i24_o12.v', 2**12),
    # ('input/ver/abs_diff_i28_o14.v', 2**14),
    # ('input/ver/abs_diff_i32_o16.v', 2**16),
]

ets_portions = [
    lambda x: x * 1 // 16,
    lambda x: x * 2 // 16,
    lambda x: x * 4 // 16,
    lambda x: x * 6 // 16,
]

partitioning_omax = [
    # (1, (10, 20)),
    (2, (10, 20)),
    (3, (10, 20)),
]

extraction_modes = [
    # 1,
    # 2,
    # 3,
    # 4,
    5,
]

full_error_functions = [
    1,
]

sub_error_functions = [
    1,
    # 2,
]

et_partitionings = [
    'asc',
    'desc'
]


logfile = f"{datetime.datetime.now()}.log"
print(f"{logfile = }")

for (
    (omax, (max_lpp, max_ppo)),
    (extr_mode),
    (filename, max_error),
    (et_portion),
    (et_partit),
    (full_func),
    (sub_func),
) in it.product(
    partitioning_omax,
    extraction_modes,
    circuits,
    ets_portions,
    et_partitionings,
    full_error_functions,
    sub_error_functions,
):
    et = et_portion(max_error)

    command = [
        "python3", "main.py",
        filename, f"--app={filename}",
        #
        f"-lpp={max_lpp}", f"-ppo={max_ppo}",
        #
        f"-et={et}", f"--et-partitioning={et_partit}",
        #
        f"--full_error_function={full_func}",
        f"--sub_error_function={sub_func}",

        #
        "--subxpat", "--subxpat-v2", "--grid",

        # partitioning
        "--min_labeling",
        f"-mode={extr_mode}", f"-omax={omax}",
    ]

    print("COMMAND", " ".join(command))
    run_command(command)
