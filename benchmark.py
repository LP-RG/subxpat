import csv
import re
import os
from typing import Dict, List, Union

import main
import subprocess
from Z3Log.config import path as z3logpath
import matplotlib.pyplot as plt
import numpy as np

def get_files_matching_regex(regex: str) -> List[str]:
    lut_regx = re.compile(regex)
    files = [f for f in os.listdir(f"{z3logpath.OUTPUT_PATH['report'][0]}") if
             f.endswith(".csv") and re.match(lut_regx, f)]
    return files


def get_best_metric_for_et(files: List[str], metric_cols: List[int], et:int) -> Union[List[str],None]:
    area_for_et = []
    for file in files:
        file = f"{z3logpath.OUTPUT_PATH['report'][0]}" + "/" + file
        with open(file, newline='') as f:
            reader = csv.reader(f)
            # et_file = re.findall("et\d", file)[0].split("et")[1]
            for row in reader:
                if reader.line_num == 1:
                    continue

                if row[3] == "SAT":
                    area_for_et.append(sum([float(row[i]) for i in metric_cols]))
    if area_for_et:
        return min(area_for_et)
    else:
        return None

# benchmarks = ["abs_diff_i4_o2", "mul_i4_o4","adder_i4_o3"]
benchmarks = ["abs_diff_i4_o2"]
num_et_points = 8
num_iterations = 10
num_models = 100
mode_num = 4

ET_points = [1,2,3,4]

for benchmark in benchmarks:
    num_outputs = int((benchmark.split("_")[-1].split("o")[-1]))
    num_inputs = int(benchmark.split("_")[-2].split("i")[-1])
    if num_outputs <= 3:
        ET_points = [1,2,3,4]
    else:
        total = 2**(num_outputs-1)
        interval = total // num_et_points
        ET_points = [(i+1) * interval for i in range(num_et_points)]

    spo = num_inputs
    ppo = num_inputs * 2
    lpp = num_inputs

    for et in ET_points:
        # subprocess.run(
        #     ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
        #      "--subxpat", f"-et={et}", "--lut",
        #      f"-spo={spo}", f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}", f"-mode={mode_num}"])
        #
        # subprocess.run(
        #     ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
        #      "--subxpat", f"-et={et}", "--lut_MP",
        #      f"-spo={spo}", f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}", f"-mode={mode_num}"])
        #
        #
        subprocess.run(
            ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
             "--subxpat", f"-et={et}", f"--ppo={ppo}", f"--lpp={lpp}",
             f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}", f"-mode={mode_num}"])

for benchmark in benchmarks:
    # best_models_area_lut = []
    # best_models_area_sop = []
    best_area_per_et_lut = {}
    best_area_per_et_sop = {}
    best_area_per_et_lut_MP = {}


    for et in ET_points:
        # files = get_files_matching_regex(f"spo_array.*{benchmark}.*et{et}.*LUT")
        # best_area_for_et_lut = get_best_metric_for_et(files, [5], et)
        # if best_area_for_et_lut is not None:
        #     best_area_per_et_lut[et] = best_area_for_et_lut

        #
        files = get_files_matching_regex(f"grid.*{benchmark}.*et{et}.*SOP1")
        best_area_for_et_sop = get_best_metric_for_et(files, [5], et)
        if best_area_for_et_sop is not None:
            best_area_per_et_sop[et] = best_area_for_et_sop

        # files = get_files_matching_regex(f"spo_array.*{benchmark}.*et{et}.*LUTMP")
        # best_area_for_et_lut_MP = get_best_metric_for_et(files, [5], et)
        # if best_area_for_et_lut_MP is not None:
        #     best_area_per_et_lut_MP[et] = best_area_for_et_lut_MP
    #
    # x_lut = list(best_area_per_et_lut.keys())
    # y_lut = list(best_area_per_et_lut.values())
    #
    # y_lut = [float(i) for i in y_lut ]
    # x_lut = [float(i) for i in x_lut ]

    x_sop = list(best_area_per_et_sop.keys())
    y_sop = list(best_area_per_et_sop.values())

    y_sop = [float(i) for i in y_sop ]
    x_sop = [float(i) for i in x_sop ]
    #
    # x_lut_MP = list(best_area_per_et_lut_MP.keys())
    # y_lut_MP = list(best_area_per_et_lut_MP.values())
    #
    # y_lut_MP = [float(i) for i in y_lut_MP ]
    # x_lut_MP = [float(i) for i in x_lut_MP ]

    # print(best_area_per_et_lut_MP)
    # fig,ax = plt.subplots()

    # plt.plot(x_lut, y_lut, alpha =0.7, linestyle='dashed', marker='o')
    plt.plot(x_sop, y_sop, alpha = 0.7, linestyle='dashed', marker='o')
    # plt.plot(x_lut_MP, y_lut_MP, alpha =0.7, linestyle='dashed', marker='o')
    plt.gca().legend(("lut","sop","lut_MP"))
    plt.title(benchmark)
    #
    # plt.set_xticks(np.arange(1,num_et_points,1))
    # plt.set_yticks(np.arange(0,20,1))
    # ax.set(xlim=(0, 8), xticks=np.arange(1, 8),
    #        ylim=(0, 8), yticks=np.arange(1, 8))

    plt.show()


    #
    # header = list(range(len(cur_model_results)))
    # all = list(cur_model_results.values())
    # content = [f for (f, _, _, _) in all]
    # print(f'{content = }')
    #
    # csvwriter.writerow(header)
    # csvwriter.writerow(content)
