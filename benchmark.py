import csv
import re
import os
import main
import subprocess
from Z3Log.config import path as z3logpath



# benchmarks = ["abs_diff_i4_o2", "mul_i4_o4","adder_i4_o3"]
benchmarks = ["abs_diff_i4_o2"]
num_et_points = 8
num_iterations = 2
num_models = 2
mode_num = 4

ET_points = [1,2,3,4]

# for benchmark in benchmarks:
#     num_outputs = int((benchmark.split("_")[-1].split("o")[-1]))
#     num_inputs = int(benchmark.split("_")[-2].split("i")[-1])
#     if num_outputs <= 3:
#         ET_points = [1,2,3,4]
#     else:
#         total = 2**(num_outputs-1)
#         interval = total // num_et_points
#         ET_points = [(i+1) * interval for i in range(num_et_points)]
#
#     for et in ET_points:
#         for spo in range(num_inputs):
#             subprocess.run(
#                 ["python3", "./main.py", f"./input/ver/{benchmark}.v", "-app", f"./input/ver/{benchmark}.v", "--grid",
#                  "--subxpat", "-imax=2", "-omax=2", f"-et={et}", "--lut",
#                  f"-spo={spo}", f"--iterations={num_iterations}", "--min_labeling", f"-num_models={num_models}", f"-mode={mode_num}"])
#

for benchmark in benchmarks:
    best_models_area_lut = []
    best_models_area_sop = []

    for et in ET_points:
        lut_regx = re.compile(f"area_model_nummodels.*et{et}.*subxpat_lut")
        files = [f for f in os.listdir(f"{z3logpath.OUTPUT_PATH['report'][0]}") if f.endswith(".csv")]
        for file in files:
            file = f"{z3logpath.OUTPUT_PATH['report'][0]}" + "/" + file
            with open(file, newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    print(','.join(row))
    #
    # header = list(range(len(cur_model_results)))
    # all = list(cur_model_results.values())
    # content = [f for (f, _, _, _) in all]
    # print(f'{content = }')
    #
    # csvwriter.writerow(header)
    # csvwriter.writerow(content)
