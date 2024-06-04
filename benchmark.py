import csv
import re
import os
import sys

from typing import Dict, List, Union

import main
import subprocess
from Z3Log.config import path as z3logpath
import matplotlib.pyplot as plt

import numpy as np


def run_benchmark(benchmarks=["abs_diff_i4_o2"], metric_cols=[5], scatter_plots=False):




    num_et_points = 8
    num_iterations = 10
    num_models = 100
    mode_num = 3

    ET_points = [1, 2, 3, 4]


    y_label_name = "metric"
    x_label_name = "ET"

    if len(metric_cols) == 1:
        if metric_cols[0] == 5:
            y_label_name = "area"
        elif metric_cols[0] == 6:
            y_label_name = "delay"
    elif len(metric_cols) == 2:
        if metric_cols[0] == 9 and metric_cols[1] == 10:
            y_label_name = "run_time"

    for benchmark in benchmarks:
        num_outputs = int((benchmark.split("_")[-1].split("o")[-1]))
        num_inputs = int(benchmark.split("_")[-2].split("i")[-1])
        if num_outputs <= 3:
            ET_points = [1,2,3,4]
        else:
            total = 2 ** (num_outputs - 1)
            interval = total // num_et_points
            ET_points = [(i + 1) * interval for i in range(num_et_points)]

        spo = num_inputs
        ppo = num_inputs * 2
        lpp = num_inputs

        # for et in ET_points:
        #     subprocess.run(
        #         ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
        #          f"-et={et}", "--lut",
        #          f"-spo={spo}", f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}"
        #         ])
        #
        #     subprocess.run(
        #         ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
        #           f"-et={et}", "--lut_MP",
        #          f"-spo={spo}", f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}"
        #          ])
        #
        #
        #     subprocess.run(
        #         ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
        #          f"-et={et}", f"--ppo={ppo}", f"--lpp={lpp}",
        #          f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}"])

    for benchmark in benchmarks:
        # best_models_area_lut = []
        # best_models_area_sop = []
        best_area_per_et_lut = {}
        best_area_per_et_sop = {}
        best_area_per_et_lut_MP = {}


        num_outputs = int((benchmark.split("_")[-1].split("o")[-1]))

        if num_outputs <= 3:
            ET_points = [1, 2,3,4]
        else:
            total = 2 ** (num_outputs - 1)
            interval = total // num_et_points
            ET_points = [(i + 1) * interval for i in range(num_et_points)]


        for et in ET_points:
            files = get_files_matching_regex(f"spo_array.*{benchmark}.*et{et}.*LUT")
            best_area_for_et_lut = get_best_metric_for_et(files, metric_cols, scatter_plot=scatter_plots, sum_all=True)
            if best_area_for_et_lut is not None:
                best_area_per_et_lut[et] = best_area_for_et_lut

            files = get_files_matching_regex(f"grid.*{benchmark}.*et{et}.*SOP1")
            best_area_for_et_sop = get_best_metric_for_et(files, metric_cols,scatter_plot=scatter_plots, sum_all=True)
            if best_area_for_et_sop is not None:
                best_area_per_et_sop[et] = best_area_for_et_sop

            files = get_files_matching_regex(f"spo_array.*{benchmark}.*et{et}.*LUTMP")
            best_area_for_et_lut_MP = get_best_metric_for_et(files, metric_cols, scatter_plot=scatter_plots, sum_all=True)
            if best_area_for_et_lut_MP is not None:
                best_area_per_et_lut_MP[et] = best_area_for_et_lut_MP

        plot_results([best_area_per_et_lut, best_area_per_et_lut_MP, best_area_per_et_sop], ("LUT","LUT MP","SOP"),
                     benchmark, [x_label_name,y_label_name],scatter_plot=scatter_plots)



def get_files_matching_regex(regex: str) -> List[str]:
    lut_regx = re.compile(regex)
    files = [f for f in os.listdir(f"{z3logpath.OUTPUT_PATH['report'][0]}") if
             f.endswith(".csv") and re.match(lut_regx, f)]
    return files

def rand_jitter(arr):
    if not arr:
        return []
    stdev = .01 * (max(arr) - min(arr))
    return arr + np.random.randn(len(arr)) * stdev



def get_best_metric_for_et(files: List[str], metric_cols: List[int], scatter_plot: bool, sum_all: bool) -> Union[List[str],float,None]:
    metric_for_et = []
    sum_rows = 0
    include_result = False
    for file in files:
        file = f"{z3logpath.OUTPUT_PATH['report'][0]}" + "/" + file
        with open(file, newline='') as f:
            reader = csv.reader(f)

            for row in reader:
                if reader.line_num == 1:
                    continue

                if sum_all and len(metric_cols) > 1:
                    sum_rows += sum([float(row[i]) for i in metric_cols])

                if row[3] == "SAT":
                    if len(metric_cols) > 1:
                        include_result = True
                        sum_rows += sum([float(row[i]) for i in metric_cols])
                    else:
                        metric_for_et.append(row[metric_cols[0]])
    if metric_for_et and len(metric_cols) == 1:
        if scatter_plot:
            return metric_for_et
        else:
            return min(metric_for_et)
    elif len(metric_cols) > 1 and include_result:
        return sum_rows
    else:
        return None


def plot_results(results, legend, benchmark_name, labels, scatter_plot = False):

    if scatter_plot:

        for result in results:
            final_x = []
            final_y = []
            x = list(result.keys())
            x = [float(i) for i in x]
            for et in x:
                y = list(result[et])
                y = [float(i) for i in y]
                final_y += y
                final_x += [et] * len(y)
            plt.scatter(rand_jitter(final_x),rand_jitter(final_y), alpha=0.1)
        plt.title(benchmark_name)

    else:
        fig,axs = plt.subplots()
        # axs_idx = 0
        for result in results:
            x = list(result.keys())
            y = list(result.values())

            y = [float(i) for i in y]
            x = [float(i) for i in x]

            axs.plot(x, y, alpha =0.7, linestyle='dashed', marker='o')
        fig.suptitle(benchmark_name)

    plt.xlabel(labels[0])
    plt.ylabel(labels[1])
    plt.gca().legend(legend)

    plt.show()
    if scatter_plot:
        figure_name = f"{benchmark_name}_{labels[1]}_scatter"
    else:
        figure_name = f"{benchmark_name}_{labels[1]}"

    plt.savefig(figure_name + ".png")
    plt.clf()
    plt.cla()

run_benchmark(benchmarks=["abs_diff_i4_o2","abs_diff_i6_o3","adder_i4_o3","adder_i6_o4","mul_i4_o4","mul_i6_o6"],metric_cols=[9,10], scatter_plots=False)


# ["abs_diff_i4_o2","abs_diff_i6_o3","adder_i4_o3","adder_i6_o4","mul_i4_o4","mul_i6_o6"]]
