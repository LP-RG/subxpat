import sys
from time import time
from typing import Tuple, List, Callable, Any, Union
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt

import signal
import functools

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

args = '--grid --subxpat -lpp=10 -ppo=20'

benchmarks_type = sys.argv[1]

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
    'adder_i28_o15',   
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
with open(f'./output/report/all_results_{benchmarks_type}.csv','w') as f:
    csvwriter = csv.writer(f)

    header = ('benchmark_name', 'encoding', 'result', 'cell', 'total_time', 'attempts', 'et')
    csvwriter.writerow(header)

# run main for all benchmarks for both encodings
@timeout(seconds=3600)
def run_experiments():
    for benchmark in benchmarks:
        output = int(benchmark.split('_')[-1][1:])
        et = output // 2
        while et >= 1:
            os.system(f'python3 main.py {path}{benchmark}.v -app {path}{benchmark}.v {args} -et={et} -encoding=1')
            os.system(f'python3 main.py {path}{benchmark}.v -app {path}{benchmark}.v {args} -et={et} -encoding=2')
            et = et // 2

run_experiments()

# create dataframe from all results
df = pd.read_csv('./output/report/all_results.csv')
df['benchmark_name'] = df['benchmark_name'].astype('string')

# create dataframe to store the sum of times for each benchmark
total_times_sum_df = pd.DataFrame(columns = ['benchmark_name', 'time_arithm_encoding', 'time_bitvec_encoding'])

# add the time sums to total_times_sum_df
for benchmark in benchmarks:

    output = int(benchmark.split('_')[-1][1:])
    et = output // 2
    while et >= 1:
        time1 = df.loc[(df['benchmark_name'] == benchmark) & (df['encoding'] == 1) & (df['et'] == et), 'total_time'].sum()
        time2 = df.loc[(df['benchmark_name'] == benchmark) & (df['encoding'] == 2) & (df['et'] == et), 'total_time'].sum()

        row = [f'{benchmark}_et{et}', time1, time2]
        total_times_sum_df.loc[len(total_times_sum_df.index)] = row
        et = et // 2

# create and save plot
axis = plt.gca()
axis.figure.set_size_inches(18,10)

total_times_sum_df.plot(kind='line',
        x='benchmark_name',
        y='time_arithm_encoding',
        color='blue', ax=axis)

total_times_sum_df.plot(kind='line',
        x='benchmark_name',
        y='time_bitvec_encoding',
        color='green', ax=axis)

axis.tick_params(axis='x', rotation=45)

plt.savefig(f'./output/encodings_test_times_plot_{benchmarks_type}.png', bbox_inches='tight')
