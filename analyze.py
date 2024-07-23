import csv
import os
import pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import re
import itertools
import matplotlib.cm as cm
import numpy as np

from typing import List, Tuple, Dict
from sxpat.config.paths import *
from sxpat.arguments import Arguments

def main():

    args = Arguments.parse()
    print(f'{args.benchmark_name = }')
    folder = f'experiments/mecals/{args.benchmark_name}'
    mecals_area_error = get_mecals_area_error(args, folder)

    folder = 'experiments/results'
    rel_files = get_relevant_files(args, folder)



    # best_per_local_global_et = get_best_area_for_local_global_et(rel_files, folder)
    # plot_report_best_area_for_local_global_et(args, best_per_local_global_et)





    # area_error_mode_et = get_area_error_per_et(rel_files, folder)
    # plot_area_error_per_et(args, area_error_mode_et)



    #
    # area_error_per_omax_dict = get_area_error_per_omax(rel_files, folder)
    # plot_area_error_per_omax(args, area_error_per_omax_dict)
    #
    # runtime_error_per_omax_per_mode = get_runtime_per_mode_and_omax(rel_files, folder)
    runtime_error_per_omax_per_mode = get_subgraph_extraction_runtime_per_mode_and_omax(rel_files, folder)
    plot_runtime_per_mode_and_omax(args, runtime_error_per_omax_per_mode)

    exit()

    # plot_area_error_mode_per_grid_dict(args, area_error_mode_per_grid_dict, area_error_mode_last_points_dict=None,
    #                                    mecals_area_error=mecals_area_error)
    area_error_mode_last_points_dict = get_area_error_per_mode_per_grid_last_points(rel_files, folder)
    # plot_area_error_mode_per_grid_dict(args, area_error_mode_per_grid_dict, area_error_mode_last_points_dict=area_error_mode_last_points_dict, mecals_area_error=mecals_area_error)

    # 
    # 
    # 
    # 
    error_cells_subgraph_inputs_dict_per_mode = get_subgraph_inputs_vs_sat_cells(rel_files, folder)
    report_sat_cells_vs_subgraph_inputs(args, error_cells_subgraph_inputs_dict_per_mode)
    # 
    # 
    # 
    # error_cells_dict_per_mode = get_sat_cells(rel_files, folder)
    # plot_cells_per_mode(args, error_cells_dict_per_mode)
    # 
    # 
    # #
    # get_runtime_per_mode_decomposition(rel_files, folder)
    # sorted_runtime_error_per_mode = get_runtime_per_mode(rel_files, folder)
    # plot_runtime_error_per_mode(args, sorted_runtime_error_per_mode)



    sorted_area_error = get_area_error(rel_files, folder)
    plot_area_error(args, sorted_area_error, area_error_mode_last_points_dict=None, mecals_area_error=mecals_area_error)
    # # plot_area_error(args, sorted_area_error, area_error_mode_last_points_dict=area_error_mode_last_points_dict, mecals_area_error=mecals_area_error)
    # plot_area_error_best(args, sorted_area_error, area_error_mode_last_points_dict=area_error_mode_last_points_dict, mecals_area_error=mecals_area_error)
    # plot_area_error_pareto(args, sorted_area_error, area_error_mode_last_points_dict=area_error_mode_last_points_dict, mecals_area_error=mecals_area_error)
    # area_error_ns_dict = get_area_error_per_num_subgraphs(rel_files, folder)
    # plot_area_error_per_ns(args, area_error_ns_dict)

    area_error_mode_dict = get_area_error_per_mode(rel_files, folder)
    plot_area_error_per_mode(args, area_error_mode_dict)

    # sorted_aggregated_runtime_error = get_runtime_aggregated(rel_files, folder)
    # plot_runtime_aggregated(args, sorted_aggregated_runtime_error)




    # print(f'{sorted_area_error = }')
    # gather the data:




    # draw the figures we want:


def get_relevant_files(args: Arguments, folder):
    # search the folder:
    all_files = [f for f in os.listdir(folder)]
    relevant_files = []
    for file in all_files:
        if re.search(args.benchmark_name, file) and file.endswith('.csv'):
            relevant_files.append(file)
    return relevant_files




def get_sat_cells(relevant_files, folder):
    error_cell_dict_per_mode: Dict = {}
    error_cell_dict: Dict = {}
    for mode in range(200):
        for rep in relevant_files:
            if re.search(f'mode{mode}_', rep):
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'): # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                cell = line[0]
                                cell = cell.replace('(', '').replace(')', '').strip().split(',')

                                lpp = re.search('(\d+)', cell[0]).group()[0]
                                ppo = re.search('(\d+)', cell[1]).group()[0]

                                error = 2 ** (int(line[1]) - 1)

                                if error not in error_cell_dict.keys():
                                    error_cell_dict[error] = []

                                error_cell_dict[error].append((lpp, ppo))
        if error_cell_dict:
            error_cell_dict_per_mode[mode] = error_cell_dict
            error_cell_dict = {}
    return  error_cell_dict_per_mode

def get_subgraph_inputs_vs_sat_cells(relevant_files, folder):
    error_cell_dict_per_mode: Dict = {}
    error_cell_dict: Dict = {}
    for mode in range(200):
        for rep in relevant_files:
            if re.search(f'mode{mode}_', rep):
                global_et = int(re.search(f'et(\d+)_', rep).group(1))
                print(f'{global_et = }')
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'): # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                sub_in = int(line[11])
                                sub_out = int(line[12])
                                cell = line[0]
                                cell = cell.replace('(', '').replace(')', '').strip().split(',')

                                lpp = int(re.search('(\d+)', cell[0]).group()[0])
                                ppo = int(re.search('(\d+)', cell[1]).group()[0])



                                if global_et not in error_cell_dict.keys():
                                    error_cell_dict[global_et] = []

                                error_cell_dict[global_et].append((lpp, ppo, sub_in, sub_out))
        if error_cell_dict:
            error_cell_dict_per_mode[mode] = error_cell_dict
            error_cell_dict = {}
    print(f'{error_cell_dict_per_mode = }')
    return  error_cell_dict_per_mode

def get_area_error(relevant_files, folder):
    area_error: List[Tuple[float, int]] = []
    for rep in relevant_files:
        with open(f'{folder}/{rep}', 'r') as f:
            csvreader = csv.reader(f)
            for line in csvreader:
                if line[0].startswith('cell'): # skip the first line
                    continue
                else:
                    if line[3].startswith('SAT'):
                        area = float(line[5])
                        error = int(line[8])
                        area_error.append((area, error))

    sorted_area_error = sorted(area_error, key=lambda x: x[1])

    return sorted_area_error


def _exists(x_y_tuple: Tuple, x_y_list: List):
    for x, y in x_y_list:
        if y == x_y_tuple[1]:
            return True
    return False


def get_best_area_for_local_global_et(relevant_files, folder):
    best_area_for_local_global_et_per_mode_per_omax: Dict = {} # mode, omax, global_et (local_et, area)
    bests_per_global_et: Dict = {}
    bests_per_omax: Dict = {}
    best_per_local_et: List = []

    for mode in range(200):
        bests_per_omax: Dict = {}
        for omax in range(20):
            bests_per_global_et: Dict = {}
            for rep in relevant_files:
                best_per_local_et = []
                if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep):
                    global_et = int(re.search(f'et(\d+)_', rep).group(1))
                    with open(f'{folder}/{rep}', 'r') as f:
                        csvreader = csv.reader(f)
                        for line in csvreader:
                            if line[0].startswith('cell'):  # skip the first line
                                continue
                            else:
                                if line[3].startswith('SAT'):
                                    local_et = int(line[8])
                                    local_area = float(line[5])

                                    if _exists((local_area, local_et), best_per_local_et):
                                        # if an alternative already exists
                                        for idx, (l_area, l_et) in enumerate(best_per_local_et):
                                            if local_et == l_et:
                                                if local_area < l_area:
                                                    best_per_local_et[idx] = (local_area, local_et)
                                                    break
                                    else:
                                        best_per_local_et.append((local_area, local_et))


                    if best_per_local_et:
                        bests_per_global_et[global_et] = best_per_local_et

            if bests_per_global_et:
                bests_per_omax[omax] = bests_per_global_et
        if bests_per_omax:
            best_area_for_local_global_et_per_mode_per_omax[mode] = bests_per_omax


    # print(F'{best_area_for_local_global_et_per_mode_per_omax = }')
    # for mode in best_area_for_local_global_et_per_mode_per_omax.keys():
    #     print(f'{mode = }')
    #     for omax in best_area_for_local_global_et_per_mode_per_omax[mode].keys():
    #         print(f'{omax = }')
    #         for et in best_area_for_local_global_et_per_mode_per_omax[mode][omax].keys():
    #             print(f'{et}: {best_area_for_local_global_et_per_mode_per_omax[mode][omax][et]}')

    return best_area_for_local_global_et_per_mode_per_omax

def get_area_error_per_et(relevant_files, folder):
    area_error_mode_et_dict: Dict = {}
    area_error_et: Dict = {}
    for mode in range(200):
        for rep in relevant_files:
            area_error: List = []
            if re.search(f'mode{mode}_', rep):
                et = int(re.search('et(\d+)_', rep).group(1))
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'):  # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                area = float(line[5])
                                error = int(line[8])
                                area_error.append((area, error))
                sorted_area_error = sorted(area_error, key=lambda x: x[1])
                area_error_et[et] = sorted_area_error
        if area_error_et:
            area_error_mode_et_dict[mode] = area_error_et
            area_error_et = {}
    return area_error_mode_et_dict




def get_mecals_area_error(args, folder):
    area_error: List[Tuple[float, int]] = []
    relevant_files = _get_mecals_rel_files(args, folder)

    if relevant_files:
        for rep in relevant_files:
            with open(f'{folder}/{rep}', 'r') as f:
                cur_area = float(f.readline())
                cur_wce = int(re.search('wce(\d+).', rep).group(1))

                area_error.append((cur_area, cur_wce))
        sorted_area_error = sorted(area_error, key=lambda x: x[1])
        return sorted_area_error
    else:
        return []
def get_runtime_aggregated(relevant_files, folder):
    runtime_error: List[Tuple[float, int]] = []
    runtime_dict = {}
    for rep in relevant_files:
        with open(f'{folder}/{rep}', 'r') as f:
            csvreader = csv.reader(f)
            for line in csvreader:
                if line[0].startswith('cell'):  # skip the first line
                    continue
                else:
                    error = int(line[8])
                    runtime = float(line[9]) + float(line[10]) + float(line[-1])
                    if error not in runtime_dict:
                        runtime_dict[error] = runtime
                    else:
                        runtime_dict[error] += runtime

    runtime_error = [(runtime, error) for error, runtime in runtime_dict.items()]


    sorted_runtime_error = sorted(runtime_error, key=lambda x: x[1])


    return sorted_runtime_error
def get_area_error_per_num_subgraphs(relevant_files, folder):
    area_error_ns_dict: Dict[int: [float, int]] = {}
    area_error: List[Tuple[float, int]] = []
    for ns in [1, 5, 10, 15]:
        for rep in relevant_files:
            if re.search(f'ns{ns}_', rep):
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'):  # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                area = float(line[5])
                                error = int(line[8])

                                area_error.append((area, error))

        sorted_area_error = sorted(area_error, key=lambda x: x[1])
        area_error_ns_dict[ns] = sorted_area_error
        area_error = []
        sorted_area_error = []
    return area_error_ns_dict

def get_area_error_per_mode(relevant_files, folder):
    area_error_mode_dict: Dict[int: [float, int]] = {}
    area_error: List[Tuple[float, int]] = []
    for mode in range(200):
        for rep in relevant_files:
            if re.search(f'mode{mode}_', rep):
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'):  # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                area = float(line[5])
                                error = int(line[8])

                                area_error.append((area, error))

        sorted_area_error = sorted(area_error, key=lambda x: x[1])
        if sorted_area_error:
            area_error_mode_dict[mode] = sorted_area_error
        area_error = []
        sorted_area_error = []

    return area_error_mode_dict


def get_area_error_per_mode_per_grid_last_points(relevant_files, folder):
    area_error_mode_per_grid_dict: Dict[int: [float, int]] = {}
    area_error_per_grid = {}
    grids = []
    for mode in range(200):
        for rep in relevant_files:
            last_point = False
            last_area = float('inf')
            last_et = 0
            last_iteration = 0
            if re.search(f'mode{mode}_', rep):
                et = int(re.search(f'et(\d+)_', rep).group(1))
                grid = re.search(f'(\d+X\d+)', rep).group()
                if grid not in grids:
                    grids.append(grid)
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'):  # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                area = float(line[5])
                                error = int(line[8])
                                iteration = int(line[1])
                                if iteration > last_iteration:
                                    last_iteration = iteration
                                    last_area = area
                                    last_et = error


                    last_point = (last_area, last_et)
                    if grid not in area_error_per_grid.keys():
                        area_error_per_grid[grid] = []
                    area_error_per_grid[grid].append(last_point)
        if area_error_per_grid:
            area_error_mode_per_grid_dict[mode] = area_error_per_grid
        area_error_per_grid = {}
    return area_error_mode_per_grid_dict

def get_area_error_per_mode_grid(relevant_files, folder):
    area_error_mode_per_grid_dict: Dict[int: [float, int]] = {}
    area_error_per_grid = {}
    grids = []
    # print(f'{relevant_files = }')
    # print(f'{len(relevant_files) = }')

    for mode in range(200):
        for rep in relevant_files:
            if re.search(f'mode{mode}_', rep):
                grid = re.search(f'(\d+X\d+)', rep).group()
                if grid not in grids:
                    grids.append(grid)
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'):  # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                area = float(line[5])
                                error = int(line[8])

                                if grid not in area_error_per_grid.keys():
                                    area_error_per_grid[grid] = []
                                area_error_per_grid[grid].append((area, error))

        if area_error_per_grid:
            area_error_mode_per_grid_dict[mode] = area_error_per_grid
        area_error_per_grid = {}
    return area_error_mode_per_grid_dict

def get_area_error_per_omax(relevant_files, folder):
    area_error_mode_per_grid_dict: Dict[int: [float, int]] = {}
    area_error_per_grid = {}
    grids = []
    for omax in range(20):
        for rep in relevant_files:
            if re.search(f'omax{omax}_', rep):
                grid = re.search(f'(\d+X\d+)', rep).group()
                if grid not in grids:
                    grids.append(grid)
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'):  # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                area = float(line[5])
                                error = int(line[8])

                                if grid not in area_error_per_grid.keys():
                                    area_error_per_grid[grid] = []
                                area_error_per_grid[grid].append((area, error))

        if area_error_per_grid:
            area_error_mode_per_grid_dict[omax] = area_error_per_grid
        area_error_per_grid = {}
    return area_error_mode_per_grid_dict

def get_runtime_per_num_subgraphs(relevant_files, folder):
    pass

def get_runtime_per_mode(relevant_files, folder):

    runtime_error_dict: Dict[Tuple[int, float]] = {}
    runtime_error_per_mode_dict = {}
    for mode in range(200):
        for rep in relevant_files:
            if re.search(f'mode{mode}_', rep):
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'):  # skip the first line
                            continue
                        else:
                            error = int(line[8])
                            runtime = float(line[9]) + float(line[10]) + float(line[-1])

                            if error not in runtime_error_dict:
                                runtime_error_dict[error] = runtime
                            else:
                                runtime_error_dict[error] += runtime

        runtime_error = [(runtime, error) for error, runtime in runtime_error_dict.items()]
        sorted_runtime_error = sorted(runtime_error, key=lambda x: x[1])
        if sorted_runtime_error:
            runtime_error_per_mode_dict[mode] = sorted_runtime_error
        runtime_error_dict ={}
    return runtime_error_per_mode_dict



def get_runtime_per_mode_and_omax(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    runtime_error = []
    for mode in range(200):
        for omax in range(20):
            for rep in relevant_files:
                runtime = 0
                if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep):
                    et = int(re.search(f'et(\d+)_', rep).group(1))
                    with open(f'{folder}/{rep}', 'r') as f:
                        csvreader = csv.reader(f)
                        for line in csvreader:
                            if line[0].startswith('cell'):  # skip the first line
                                continue
                            else:
                                subgraph_extraction = float(line[9])
                                labeling = float(line[10])
                                exploration = float(line[-1])
                                cur_runtime = subgraph_extraction + labeling + exploration
                            runtime += cur_runtime
                    runtime_error.append((et, runtime))
            print(f'{runtime_error = }')
            if runtime_error:
                sorted_runtime_error = sorted(runtime_error, key=lambda x: x[0])
                runtime_error_per_omax[omax] = sorted_runtime_error
                runtime_error = []
        if runtime_error_per_omax:
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax
            runtime_error_per_omax = {}

    return runtime_error_per_omax_per_mode


def get_subgraph_extraction_runtime_per_mode_and_omax(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    runtime_error = []
    for mode in range(200):
        for omax in range(20):
            for rep in relevant_files:
                iterations = []
                runtime = 0
                if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep):
                    et = int(re.search(f'et(\d+)_', rep).group(1))
                    with open(f'{folder}/{rep}', 'r') as f:
                        csvreader = csv.reader(f)
                        for line in csvreader:
                            if line[0].startswith('cell'):  # skip the first line
                                continue
                            else:
                                cur_iter = int(line[1])
                                if cur_iter not in iterations:
                                    iterations.append(cur_iter)
                                    subgraph_extraction = float(line[10])
                                    runtime += subgraph_extraction
                    runtime_error.append((et, runtime))

            if runtime_error:
                sorted_runtime_error = sorted(runtime_error, key=lambda x: x[0])
                runtime_error_per_omax[omax] = sorted_runtime_error
                runtime_error = []
        if runtime_error_per_omax:
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax
            runtime_error_per_omax = {}

    return runtime_error_per_omax_per_mode




def get_runtime_per_mode_decomposition(relevant_files, folder):

    runtime_error_decomposed_dict: Dict[Tuple[int, float]] = {}
    runtime_error_per_mode_dict = {}
    for mode in range(20):
        for rep in relevant_files:
            if re.search(f'mode{mode}_', rep):
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'):  # skip the first line
                            continue
                        else:
                            error = int(line[8])
                            subgraph_extraction = float(line[9])
                            labeling = float(line[10])
                            exploration = float(line[-1])
                            if error not in runtime_error_decomposed_dict:
                                runtime_error_decomposed_dict[error] = []
                            runtime_error_decomposed_dict[error].append((subgraph_extraction, labeling, exploration))
    return runtime_error_per_mode_dict


def report_sat_cells(args, error_cell_dict_per_mode: Dict):
    records = []
    for mode, thresholds in error_cell_dict_per_mode.items():
        for threshold, tuples in thresholds.items():
            for tpl in tuples:
                records.append((mode, threshold, tpl))

    # Create a DataFrame from the records
    df = pd.DataFrame(records, columns=['Mode', 'Error_Threshold', 'Tuple'])

    # Summarize the DataFrame by counting occurrences of each tuple for every mode and error threshold
    summary = df.groupby(['Mode', 'Error_Threshold', 'Tuple']).size().reset_index(name='Count')

    # Calculate the total count for each mode
    total_counts = summary.groupby('Mode')['Count'].transform('sum')

    # Calculate the percentage
    summary['Percentage'] = round((summary['Count'] / total_counts) * 100, 2)

    folder, _ = OUTPUT_PATH['figure']
    # Save the summary DataFrame to a CSV file
    summary.to_csv(f'{folder}/{args.benchmark_name}_error_sat_cells_distribution_per_mode.csv', index=False)
    print(f'{summary}')


def report_sat_cells_vs_subgraph_inputs(args, error_cells_subgraph_inputs_dict_per_mode: Dict):
    records = []
    for mode, thresholds in error_cells_subgraph_inputs_dict_per_mode.items():
        for threshold, tuples in thresholds.items():
            for tpl in tuples:
                lpp, ppo, subgraph_input, subgraph_outputs = tpl
                records.append((mode, threshold, (lpp, ppo)))

    df = pd.DataFrame(records, columns=['Mode', 'Error_Threshold', 'Grid_Cells'])

    # Summarize the DataFrame for Grid Cells
    summary = df.groupby(['Mode', 'Error_Threshold', 'Grid_Cells']).size().reset_index(name='Count')

    # Calculate the total count for each mode
    total_counts = summary.groupby('Mode')['Count'].transform('sum')

    # Calculate the percentage
    summary['Percentage'] = round((summary['Count'] / total_counts) * 100, 2)

    # Rename columns for clarity
    summary.columns = ['Mode', 'Error_Threshold', 'Grid_Cells', 'Count', 'Percentage']

    folder, _ = OUTPUT_PATH['figure']
    # Save the summary DataFrame to a CSV file
    summary.to_csv(f'{folder}/{args.benchmark_name}_error_sat_cells_distribution_per_mode.csv', index=False)
    print(f'{summary}')



def plot_cells_per_mode(args, error_cell_dict_per_mode):
    def tuple_score(tpl):
        return sum(int(x) for x in tpl)

    # Calculate the total score for each mode
    mode_scores = {}
    for mode, thresholds in error_cell_dict_per_mode.items():
        total_score = 0
        for threshold, tuples in thresholds.items():
            for tpl in tuples:
                total_score += tuple_score(tpl)
        mode_scores[mode] = total_score

    # Convert the scores to a DataFrame
    scores_df = pd.DataFrame(list(mode_scores.items()), columns=['Mode', 'Total_Score'])

    # Calculate Spearman rank correlation
    corr, p_value = spearmanr(scores_df['Mode'], scores_df['Total_Score'])

    print(f"Spearman Correlation Coefficient: {corr}")
    print(f"P-value: {p_value}")

    plt.figure(figsize=(8, 5))
    plt.bar(scores_df['Mode'], scores_df['Total_Score'], color=['blue', 'orange'])
    plt.xlabel('Mode')
    plt.ylabel('Total Sum of lpp and ppo for SAT cells')
    plt.title('Total Scores')
    plt.xticks(scores_df['Mode'])

    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_cell_scores_per_mode.png'
    plt.savefig(figname)

def plot_area_error(args, sorted_area_error: List, area_error_mode_last_points_dict: Dict = None, mecals_area_error: List = None):
    color_map = {
        51: 'red',
        53: 'orange',
        12: 'cyan',
        121: 'green'

        # Add more modes and their respective colors as needed
    }
    plt.figure(figsize=(10, 6))

    areas = [item[0] for item in sorted_area_error]
    errors = [item[1] for item in sorted_area_error]
    assert len(errors) == len(areas)
    plt.scatter(errors, areas, marker='D', label='SubXPAT', color='blue', alpha=0.2, s=50)
    # Plot the data


    if mecals_area_error:
        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]
        print(f'{mecals_errors = }')
        plt.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black')
        plt.legend()

    if area_error_mode_last_points_dict:
        for mode in area_error_mode_last_points_dict.keys():
            sorted_area_error_per_mode = area_error_mode_last_points_dict[mode]
            for grid in sorted_area_error_per_mode.keys():
                sorted_area_error = sorted_area_error_per_mode[grid]
                areas = [item[0] for item in sorted_area_error]
                errors = [item[1] for item in sorted_area_error]
                color = color_map.get(mode, 'black')
                plt.scatter(errors, areas, marker='s', label=f'mode{mode} (final-points), grid{grid}', alpha=1,
                            color=color)


    plt.title(f'{args.benchmark_name}, ')
    plt.xlabel('ET')
    plt.ylabel('Area')
    plt.grid(True)
    plt.legend()
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_all.png'
    plt.savefig(figname)


def plot_area_error_per_et(args, area_error_mode_et):

    color_idx = 0
    distinct_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    modes = list(area_error_mode_et.keys())
    mode_markers = ['o', 'x', '^']
    mode_idx = 0
    for mode in area_error_mode_et.keys():
        plt.figure(figsize=(10, 6))
        et_arrays = list(area_error_mode_et[mode].keys())
        et_arrays.sort()

        for et in et_arrays:
            areas = [item[0] for item in area_error_mode_et[mode][et]]
            errors = [item[1] for item in area_error_mode_et[mode][et]]
            plt.scatter(errors, areas, alpha=0.4, label=f'mode{mode}_et{et}', color=distinct_colors[color_idx % 8], marker=mode_markers[mode_idx])
            color_idx += 1
        mode_idx += 1

        plt.title(f'{args.benchmark_name}, ')
        plt.xlabel('ET')
        plt.ylabel('Area')
        plt.grid(True)
        plt.xticks()
        plt.legend()
        folder, _ = OUTPUT_PATH['figure']
        figname = f'{folder}/{args.benchmark_name}_per_et_mode{mode}.png'
        plt.savefig(figname)
        plt.close()



def plot_area_error_best(args, sorted_area_error: List, area_error_mode_last_points_dict: Dict = None, mecals_area_error: List = None):


    min_area_by_error = {}
    for area, error in sorted_area_error:
        if error in min_area_by_error:
            min_area_by_error[error] = min(min_area_by_error[error], area)
        else:
            min_area_by_error[error] = area
    areas = [item[1] for item in min_area_by_error.items()]
    errors = [item[0] for item in min_area_by_error.items()]
    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.scatter(errors, areas, marker='D', label='SubXPAT', color='blue', alpha=0.5, s=50)
    assert len(errors) == len(areas)
    if mecals_area_error:
        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]

        plt.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black')
        plt.legend()




    if area_error_mode_last_points_dict:
        for mode in area_error_mode_last_points_dict.keys():
            sorted_area_error_per_mode = area_error_mode_last_points_dict[mode]
            for grid in sorted_area_error_per_mode.keys():
                sorted_area_error = sorted_area_error_per_mode[grid]
                areas = [item[0] for item in sorted_area_error]
                errors = [item[1] for item in sorted_area_error]
                plt.scatter(errors, areas, marker='D', label=f'mode{mode}, grid{grid}', alpha=1, color='orange')

    plt.title(f'{args.benchmark_name}, ')
    plt.xlabel('ET')
    plt.ylabel('Area')
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_best.png'
    plt.savefig(figname)

def is_dominated(current_point, points):
    """ Check if the current point is dominated by any point in the list """
    for point in points:
        # if point[0] < current_point[0] and point[1] < current_point[1] and point != current_point:
        if point != current_point:
            if point[0] <= current_point[0] and point[1] <= current_point[1]:
                return True



    return False

def find_pareto_points(points):
    """ Find and return the list of Pareto optimal points """
    pareto_points = []
    for point in points:
        if not is_dominated(point, points):
            pareto_points.append(point)
    return pareto_points

def plot_area_error_pareto(args, sorted_area_error: List, area_error_mode_last_points_dict: Dict = None, mecals_area_error: List = None):
    color_map = {
        51: 'red',
        53: 'orange',
        12: 'cyan',
        121: 'green'

        # Add more modes and their respective colors as needed
    }

    # min_area_by_error = {}
    # for area, error in sorted_area_error:
    #     if error in min_area_by_error:
    #         min_area_by_error[error] = min(min_area_by_error[error], area)
    #     else:
    #         min_area_by_error[error] = area
    # areas = [item[1] for item in min_area_by_error.items()]
    # errors = [item[0] for item in min_area_by_error.items()]
    # print(f'{sorted_area_error= }')
    pareto_points = find_pareto_points(sorted_area_error)
    # print(f'{pareto_points= }')
    areas = [item[0] for item in pareto_points]
    errors = [item[1] for item in pareto_points]
    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.scatter(errors, areas, marker='D', label='SubXPAT', color='blue', alpha=1, s=50)
    assert len(errors) == len(areas)
    if mecals_area_error:
        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]

        plt.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black')



    if area_error_mode_last_points_dict:
        for mode in area_error_mode_last_points_dict.keys():
            sorted_area_error_per_mode = area_error_mode_last_points_dict[mode]
            for grid in sorted_area_error_per_mode.keys():
                sorted_area_error = sorted_area_error_per_mode[grid]
                areas = [item[0] for item in sorted_area_error]
                errors = [item[1] for item in sorted_area_error]
                color = color_map.get(mode, 'black')
                plt.scatter(errors, areas, marker='s', label=f'mode{mode} (final-points), grid{grid}', alpha=1, color=color)

    plt.title(f'{args.benchmark_name}, ')
    plt.xlabel('ET')
    plt.ylabel('Area')
    plt.grid(True)
    plt.legend()
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_pareto.png'
    plt.savefig(figname)

def plot_area_error_per_ns(args, area_error_ns_dict: Dict):
    plt.figure(figsize=(10, 6))
    plt.title(f'{args.benchmark_name} per number of subgraphs')
    marker = itertools.cycle(('D', 'o', 'X', 's'))
    for ns in area_error_ns_dict.keys():
        # print(f'{ns = }')

        sorted_area_error = area_error_ns_dict[ns]
        # print(f'{sorted_area_error = }')
        areas = [item[0] for item in sorted_area_error]
        errors = [item[1] for item in sorted_area_error]


        plt.scatter(errors, areas, marker=next(marker), label=ns, alpha=0.5)
    plt.legend()
    plt.xlabel('ET')
    plt.ylabel('Area')
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_per_num_subgraphs.png'
    plt.savefig(figname)

def plot_runtime_error_per_mode(args, runtime_error_per_mode_dict: Dict):
    plt.figure(figsize=(10, 6))
    plt.title(f'{args.benchmark_name} per mode')
    marker = itertools.cycle(('D', 'o', 'X', 's'))
    for mode in runtime_error_per_mode_dict.keys():
        # print(f'{mode = }')

        sorted_area_error = runtime_error_per_mode_dict[mode]

        runtimes = [item[0] for item in sorted_area_error]
        errors = [item[1] for item in sorted_area_error]

        # print(f'{round(sum(runtimes)/60, 2) =  }')
        cur_time = round(sum(runtimes)/60, 2)
        plt.plot(errors, runtimes, marker=next(marker), label=f'{mode}, {cur_time}', alpha=0.5, linestyle='--')

    plt.legend()
    plt.xlabel('ET')
    plt.ylabel('Runtime')
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_runtime_per_mode.png'
    plt.savefig(figname)



def plot_area_error_per_mode(args, area_error_mode_dict: Dict):
    plt.figure(figsize=(10, 6))
    plt.title(f'{args.benchmark_name} per mode')
    marker = itertools.cycle(('D', 'o', 'X', 's'))
    for mode in area_error_mode_dict.keys():
        # print(f'{mode = }')


        sorted_area_error = area_error_mode_dict[mode]
        # print(f'{sorted_area_error = }')
        areas = [item[0] for item in sorted_area_error]
        errors = [item[1] for item in sorted_area_error]


        plt.scatter(errors, areas, marker=next(marker), label=mode, alpha=0.5)
    plt.legend()
    plt.xlabel('ET')
    plt.ylabel('Runtime')
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_area_per_mode.png'
    plt.savefig(figname)


def plot_area_error_mode_per_grid_dict(args, area_error_mode_per_grid_dict: Dict, area_error_mode_last_points_dict: Dict = None, mecals_area_error = None):
    plt.figure(figsize=(10, 6))
    plt.title(f'{args.benchmark_name} per mode and grid')
    marker = itertools.cycle(('D', 'o', 'X', 's'))
    for mode in area_error_mode_per_grid_dict.keys():


        sorted_area_error_per_mode = area_error_mode_per_grid_dict[mode]
        for grid in sorted_area_error_per_mode.keys():
            sorted_area_error = sorted_area_error_per_mode[grid]
            areas = [item[0] for item in sorted_area_error]
            errors = [item[1] for item in sorted_area_error]
            plt.scatter(errors, areas, marker=next(marker), label=f'mode{mode}, grid{grid}' , alpha=0.5)

    if mecals_area_error:
        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]
        plt.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black')
        plt.legend()

    if area_error_mode_last_points_dict:
        for mode in area_error_mode_last_points_dict.keys():
            sorted_area_error_per_mode = area_error_mode_last_points_dict[mode]
            for grid in sorted_area_error_per_mode.keys():
                sorted_area_error = sorted_area_error_per_mode[grid]
                areas = [item[0] for item in sorted_area_error]
                errors = [item[1] for item in sorted_area_error]
                plt.scatter(errors, areas, marker='D', label=f'mode{mode}, grid{grid}', alpha=1)

    plt.legend()
    plt.xlabel('ET')
    plt.ylabel('Area')
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']
    if area_error_mode_last_points_dict:
        figname = f'{folder}/{args.benchmark_name}_area_per_mode_and_grid_last.png'
    else:
        figname = f'{folder}/{args.benchmark_name}_area_per_mode_and_grid.png'
    plt.savefig(figname)



def plot_area_error_per_omax(args, area_error_mode_per_grid_dict: Dict, mecals_area_error = None):
    plt.figure(figsize=(10, 6))
    plt.title(f'{args.benchmark_name} per mode and grid')
    marker = itertools.cycle(('D', 'o', 'X', 's'))
    for omax in area_error_mode_per_grid_dict.keys():


        sorted_area_error_per_mode = area_error_mode_per_grid_dict[omax]
        for grid in sorted_area_error_per_mode.keys():
            sorted_area_error = sorted_area_error_per_mode[grid]
            areas = [item[0] for item in sorted_area_error]
            errors = [item[1] for item in sorted_area_error]
            plt.scatter(errors, areas, marker=next(marker), label=f'omax{omax}, grid{grid}' , alpha=0.5)

    if mecals_area_error:
        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]
        plt.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black')
        plt.legend()

    # if area_error_mode_last_points_dict:
    #     for mode in area_error_mode_last_points_dict.keys():
    #         sorted_area_error_per_mode = area_error_mode_last_points_dict[omax]
    #         for grid in sorted_area_error_per_mode.keys():
    #             sorted_area_error = sorted_area_error_per_mode[grid]
    #             areas = [item[0] for item in sorted_area_error]
    #             errors = [item[1] for item in sorted_area_error]
    #             plt.scatter(errors, areas, marker='D', label=f'mode{mode}, grid{grid}', alpha=1)

    plt.legend()
    plt.xlabel('ET')
    plt.ylabel('Area')
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']

    figname = f'{folder}/{args.benchmark_name}_omax.png'
    plt.savefig(figname)


def plot_runtime_per_mode_and_omax(args, runtime_error_per_omax_per_mode):
    plt.figure(figsize=(10, 6))
    plt.title(f'{args.benchmark_name} runtime')
    marker = itertools.cycle(('D', 'o', 'X', 's'))

    for mode in runtime_error_per_omax_per_mode.keys():
        for omax in runtime_error_per_omax_per_mode[mode].keys():
            errors = [item[0] for item in runtime_error_per_omax_per_mode[mode][omax]]
            runtimes = [item[1] for item in runtime_error_per_omax_per_mode[mode][omax]]
            plt.plot(errors, runtimes, marker=next(marker), label=f'mode{mode}, omax{omax}', alpha=1)

    plt.legend()
    plt.xlabel('ET')
    plt.ylabel('Runtime')

    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']

    figname = f'{folder}/{args.benchmark_name}_omax_runtime.png'
    plt.savefig(figname)


def _identify_pareto(df):
    pareto_points = []
    for i in df.index:
        candidate = df.loc[i]
        if not ((df['Area'] < candidate['Area']) & (df['Local ET'] <= candidate['Local ET'])).any():
            pareto_points.append(candidate)
    return pd.DataFrame(pareto_points)
def plot_report_best_area_for_local_global_et(args, best_per_local_global_et):
    result = []

    # Iterate through the dictionary to find the best area for each local et
    for mode, omax_dict in best_per_local_global_et.items():
        for omax, global_et_dict in omax_dict.items():
            for global_et, areas in global_et_dict.items():
                for area, local_et in areas:
                    result.append([mode, omax, local_et, area, global_et])

    # Create a DataFrame
    df = pd.DataFrame(result, columns=['Mode', 'Omax', 'Local ET', 'Area', 'Global ET'])

    # Find the best (minimum) area for each local et
    best_area_df = df.loc[df.groupby(['Mode', 'Omax', 'Local ET'])['Area'].idxmin()]

    # Sort the DataFrame for better readability
    best_area_df = best_area_df.sort_values(by=['Mode', 'Omax', 'Local ET'])

    # Save to a CSV file
    folder, _ = OUTPUT_PATH['figure']
    best_area_df.to_csv(f'{folder}/{args.benchmark_name}_best_local_et_per_global_et.csv', index=False)

    plt.figure(figsize=(10, 6))

    # Scatter plot
    plt.scatter(best_area_df['Local ET'], best_area_df['Area'], color='blue')

    # Annotate each point with the global ET
    for i in range(len(best_area_df)):
        plt.annotate(best_area_df['Global ET'].iloc[i],
                     (best_area_df['Local ET'].iloc[i], best_area_df['Area'].iloc[i]),
                     textcoords="offset points",
                     xytext=(0, 10),
                     ha='center')

    # Labels and title
    plt.xlabel('Local ET')
    plt.ylabel('Area')
    plt.title('Best Area for Each Local ET')

    # Show the plot
    plt.grid(True)
    figname = f'{folder}/{args.benchmark_name}_best_local_et_per_global_et.png'
    plt.savefig(figname)
    plt.close()

    # Identify Pareto points
    pareto_df = _identify_pareto(best_area_df)


    pareto_df.to_csv(f'{folder}/{args.benchmark_name}_pareto_local_et_per_global_et.csv', index=False)

    # Calculate k for Pareto points
    pareto_df['k'] = pareto_df['Global ET'] / pareto_df['Local ET']

    # Calculate average k
    average_k = pareto_df['k'].mean()

    # Plot Pareto points
    plt.figure(figsize=(10, 6))
    plt.scatter(pareto_df['Local ET'], pareto_df['Area'], color='red')

    # Annotate each point with the global ET
    for i in range(len(pareto_df)):
        plt.annotate(pareto_df['Global ET'].iloc[i],
                     (pareto_df['Local ET'].iloc[i], pareto_df['Area'].iloc[i]),
                     textcoords="offset points",
                     xytext=(0, 10),
                     ha='center')

    # Labels and title
    plt.xlabel('Local ET')
    plt.ylabel('Area')
    plt.title(f'Pareto Points for Each Local ET (Average k = {average_k:.2f})')

    # Show the plot
    plt.grid(True)
    figname = f'{folder}/{args.benchmark_name}_pareto_local_et_per_global_et.png'
    plt.savefig(figname)


def plot_runtime_aggregated(args, sorted_runtime_error):
    areas = [item[0] for item in sorted_runtime_error]
    errors = [item[1] for item in sorted_runtime_error]

    # Plot the data
    plt.figure(figsize=(10, 6))
    assert len(errors) == len(areas)

    plt.plot(errors, areas, 'o-')
    plt.title(f'{args.benchmark_name}, ')
    plt.xlabel('ET')
    plt.ylabel('Runtime')
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_aggregated_runtime.png'
    plt.savefig(figname)




def _get_mecals_rel_files(args, folder):
    # search the folder:
    if os.path.exists(folder):
        all_files = [f for f in os.listdir(folder)]
    else:
        return []
    relevant_files = []
    for file in all_files:
        if re.search(args.benchmark_name, file) and file.endswith('.area'):
            relevant_files.append(file)
    return relevant_files


def get_muscat_area_error():
    pass

if __name__ == "__main__":
    main()