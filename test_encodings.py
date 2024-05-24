import sys
from time import time
from typing import Iterable, Iterator, List, Tuple
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import signal
import functools
import datetime

def timeout(seconds=5, default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def handle_timeout(signum, frame):
                raise TimeoutError()
            signal.signal(signal.SIGALRM, handle_timeout)
            signal.alarm(seconds)
            result = func(*args, **kwargs)
            signal.alarm(0)
            return result
        return wrapper
    return decorator

path = 'input/ver/'

imax=4
omax=2

args = f'--grid --subxpat -lpp=10 -ppo=10 --timeout=1800 -mode=5 --min_labeling -imax={imax} -omax={omax}'

benchmarks_type = sys.argv[1]
encoding = sys.argv[2]

# benchmarks to be tested (adder)
benchmarks_adder = [
    'adder_i4_o3',
    'adder_i6_o4',
    'adder_i8_o5',
    'adder_i10_o6', 
    'adder_i12_o7',  
    'adder_i16_o9',  
    'adder_i20_o11',  
    'adder_i24_o13',  
    'adder_i32_o17',   
    'adder_i36_o19',   
    'adder_i40_o21',   
    'adder_i44_o23',   
    'adder_i48_o25',   
    'adder_i52_o27',    
]

# benchmarks to be tested (abs_diff)
benchmarks_abs_diff = [
    'abs_diff_i4_o2',
    'abs_diff_i6_o3',
    'abs_diff_i8_o4',
    'abs_diff_i10_o5',
    'abs_diff_i12_o6',
    'abs_diff_i16_o8',
    'abs_diff_i20_o10',
    'abs_diff_i24_o12',
    'abs_diff_i28_o14',
    'abs_diff_i32_o16',
    'abs_diff_i36_o18',
    'abs_diff_i40_o20',
    'abs_diff_i44_o22',
    'abs_diff_i48_o24',
]

# benchmarks to be tested (mul)
benchmarks_mul = [
    'mul_i4_o4',
    'mul_i6_o6',
    'mul_i8_o8',
    'mul_i10_o10',
    'mul_i12_o12',
    'mul_i14_o14',
    'mul_i16_o16',
    'mul_i20_o20',
]

# benchmarks to be tested (sad)
benchmarks_sad = [
    'sad_i10_o3',
    'sad_i20_o5',    
]

# benchmarks to be tested (madd)
benchmarks_madd = [
    'madd_i6_o4',
    'madd_i9_o6',
    'madd_i12_o8',
    'madd_i15_o10',
    'madd_i18_o12',    
]

if benchmarks_type == 'adder':
    benchmarks = benchmarks_adder
elif benchmarks_type == 'abs_diff':
    benchmarks = benchmarks_abs_diff
elif benchmarks_type == 'mul':
    benchmarks = benchmarks_mul
elif benchmarks_type == 'sad':
    benchmarks = benchmarks_sad
elif benchmarks_type == 'madd':
    benchmarks = benchmarks_madd


# create a csv file to add all results
with open(f'./output/report/all_results.csv','w') as f:
    csvwriter = csv.writer(f)

    header = ('benchmark_name', 'encoding', 'result', 'cell', 'total_time', 'attempts', 'et')
    csvwriter.writerow(header)

# create a csv file to add area, power and delay data for final results of each benchmark
with open(f'./output/report/area_power_delay.csv','w') as f:
    csvwriter = csv.writer(f)

    header = ('benchmark_name', 'Design ID', 'Area', 'Power', 'Delay','et', 'encoding', 'labeling_time', 'subgraph_extraction_time')
    csvwriter.writerow(header)


# def run_command(command: Iterable[str]):

#     print(f'COMMAND {" ".join(command)}')

#     proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

#     for line in proc.stdout:
#         print(line.decode(), end='', sep='', )

#     proc.wait()

@timeout(seconds=1800)
def run_benchmark(benchmark, et, encoding):
    subprocess.run(f'python3 main.py {path}{benchmark}.v -app {path}{benchmark}.v {args} -et={et} -encoding={encoding}', shell=True)

try:

    # run main for all benchmarks for encoding 2
    for benchmark in benchmarks:
        output = int(benchmark.split('_')[-1][1:])
        et = output // 2
        while et >= 1 and et >= output // 8:    
            # command1 = ['python3', 'main.py', f'{path}{benchmark}.v', f'-app', f'{path}{benchmark}.v', '--grid', '--subxpat', '-lpp=10', '-ppo=20', f'-et={et}', '-encoding=1']
            # command2 = ['python3', 'main.py', f'{path}{benchmark}.v', f'-app', f'{path}{benchmark}.v', '--grid', '--subxpat', '-lpp=10', '-ppo=20', f'-et={et}', '-encoding=2']
            # run_command(command1)
            # run_command(command2)

            # subprocess.run(f'python3 main.py {path}{benchmark}.v -app {path}{benchmark}.v --grid --subxpat -lpp=10 -ppo=10 --timeout=900 -et={et} -encoding=1',shell=True)
            # subprocess.run(f'python3 main.py {path}{benchmark}.v -app {path}{benchmark}.v --grid --subxpat -lpp=10 -ppo=10 --timeout=900 -et={et} -encoding=2',shell=True)

            run_benchmark(benchmark, et, encoding)

            et = et // 2


except TimeoutError:
    print("Timeout")
