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


# argv[1] = benchmarks
# argv[2] = metric_cols

def run_benchmark(benchmarks=["abs_diff_i4_o2"], metric_cols=[5]):




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

        for et in ET_points:
            subprocess.run(
                ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
                 f"-et={et}", "--lut",
                 f"-spo={spo}", f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}"
                ])

            subprocess.run(
                ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
                  f"-et={et}", "--lut_MP",
                 f"-spo={spo}", f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}"
                 ])


            subprocess.run(
                ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
                 f"-et={et}", f"--ppo={ppo}", f"--lpp={lpp}",
                 f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}"])

    for benchmark in benchmarks:
        # best_models_area_lut = []
        # best_models_area_sop = []
        best_area_per_et_lut = {}
        best_area_per_et_sop = {}
        best_area_per_et_lut_MP = {}


        num_outputs = int((benchmark.split("_")[-1].split("o")[-1]))

        if num_outputs <= 3:
            ET_points = [1, 2, 3, 4]
        else:
            total = 2 ** (num_outputs - 1)
            interval = total // num_et_points
            ET_points = [(i + 1) * interval for i in range(num_et_points)]


        for et in ET_points:
            files = get_files_matching_regex(f"spo_array.*{benchmark}.*et{et}.*LUT")
            best_area_for_et_lut = get_best_metric_for_et(files, metric_cols, et)
            if best_area_for_et_lut is not None:
                best_area_per_et_lut[et] = best_area_for_et_lut

            files = get_files_matching_regex(f"grid.*{benchmark}.*et{et}.*SOP1")
            best_area_for_et_sop = get_best_metric_for_et(files, metric_cols, et)
            if best_area_for_et_sop is not None:
                best_area_per_et_sop[et] = best_area_for_et_sop

            files = get_files_matching_regex(f"spo_array.*{benchmark}.*et{et}.*LUTMP")
            best_area_for_et_lut_MP = get_best_metric_for_et(files, metric_cols, et)
            if best_area_for_et_lut_MP is not None:
                best_area_per_et_lut_MP[et] = best_area_for_et_lut_MP

        plot_results([best_area_per_et_lut, best_area_per_et_lut_MP, best_area_per_et_sop], ("LUT", "SOP"),
                     benchmark, [x_label_name,y_label_name])


def get_files_matching_regex(regex: str) -> List[str]:
    lut_regx = re.compile(regex)
    files = [f for f in os.listdir(f"{z3logpath.OUTPUT_PATH['report'][0]}") if
             f.endswith(".csv") and re.match(lut_regx, f)]
    return files


def get_best_metric_for_et(files: List[str], metric_cols: List[int], et:int) -> Union[List[str],None]:
    metric_for_et = {}
    for file in files:
        file = f"{z3logpath.OUTPUT_PATH['report'][0]}" + "/" + file
        with open(file, newline='') as f:
            reader = csv.reader(f)
            # et_file = re.findall("et\d", file)[0].split("et")[1]
            for row in reader:
                if reader.line_num == 1:
                    continue

                if row[3] == "SAT":
                    metric_for_et[file] = (sum([float(row[i]) for i in metric_cols]))
    if metric_for_et:
        print(min(metric_for_et, key = metric_for_et.get))
        return min(list(metric_for_et.values()))
    else:
        return None


def plot_results(results, legend, benchmark_name, labels):

    fig,axs = plt.subplots()
    # axs_idx = 0
    for result in results:
        x = list(result.keys())
        y = list(result.values())

        y = [float(i) for i in y]
        x = [float(i) for i in x]

        axs.plot(x, y, alpha =0.7, linestyle='dashed', marker='o')

    plt.xlabel(labels[0])
    plt.ylabel(labels[1])
    plt.gca().legend(legend)
    fig.suptitle(benchmark_name)
    #
    # plt.set_xticks(np.arange(1,num_et_points,1))
    # plt.set_yticks(np.arange(0,20,1))
    # ax.set(xlim=(0, 8), xticks=np.arange(1, 8),
    #        ylim=(0, 8), yticks=np.arange(1, 8))

    plt.show()
    # figure_name = f"{benchmark_name}"
    # plt.savefig(figure_name + ".png")




    #
    # header = list(range(len(cur_model_results)))
    # all = list(cur_model_results.values())
    # content = [f for (f, _, _, _) in all]
    # print(f'{content = }')
    #
    # csvwriter.writerow(header)
    # csvwriter.writerow(content)
run_benchmark(metric_cols=[5])