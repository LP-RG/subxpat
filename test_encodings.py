import sys
from time import time
from typing import Tuple, List, Callable, Any, Union
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt

path = 'input/ver/'

args = '--grid --subxpat -imax=2 -omax=2 -et=1'

# benchmarks to be tested
benchmarks = [
    'abs_diff_i4_o2',
    'abs_diff_i6_o3',
    'adder_i4_o3',
    'adder_i8_o5',
    'adder_i10_o6',
    'mul_i6_o6',
    'sad_i10_o3',
    'madd_i9_o6',
]

# create a csv file to add all results
with open(f'./output/report/all_results.csv','w') as f:
    csvwriter = csv.writer(f)

    header = ('benchmark_name', 'encoding', 'result', 'cell', 'total_time', 'attempts')
    csvwriter.writerow(header)

# run main for all benchmarks for both encodings
for benchmark in benchmarks:
    os.system(f'python3 main.py {path}{benchmark}.v -app {path}{benchmark}.v {args} -encoding=1')
    os.system(f'python3 main.py {path}{benchmark}.v -app {path}{benchmark}.v {args} -encoding=2')

# create dataframe from all results
df = pd.read_csv('./output/report/all_results.csv')
df['benchmark_name'] = df['benchmark_name'].astype('string')

# create dataframe to store the sum of times for each benchmark
total_times_sum_df = pd.DataFrame(columns = ['benchmark_name', 'time_encoding1', 'time_encoding2'])

# add the time sums to total_times_sum_df
for benchmark in benchmarks:

    time1 = df.loc[(df['benchmark_name'] == benchmark) & (df['encoding'] == 1), 'total_time'].sum()
    time2 = df.loc[(df['benchmark_name'] == benchmark) & (df['encoding'] == 2), 'total_time'].sum()

    row = [benchmark, time1, time2]
    total_times_sum_df.loc[len(total_times_sum_df.index)] = row

# create and save plot
axis = plt.gca()

total_times_sum_df.plot(kind='line',
        x='benchmark_name',
        y='time_encoding1',
        color='blue', ax=axis)

total_times_sum_df.plot(kind='line',
        x='benchmark_name',
        y='time_encoding2',
        color='green', ax=axis)

axis.tick_params(axis='x', rotation=45)

plt.savefig('./output/encodings_test_times_plot.png', bbox_inches='tight')
