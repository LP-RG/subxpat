import csv
import os
import pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import re
import itertools

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


    # area_error_mode_per_grid_dict = get_area_error_per_mode_grid(rel_files, folder)
    # plot_area_error_mode_per_grid_dict(args, area_error_mode_per_grid_dict, area_error_mode_last_points_dict=None,
    #                                    mecals_area_error=mecals_area_error)
    area_error_mode_last_points_dict = get_area_error_per_mode_per_grid_last_points(rel_files, folder)
    # plot_area_error_mode_per_grid_dict(args, area_error_mode_per_grid_dict, area_error_mode_last_points_dict=area_error_mode_last_points_dict, mecals_area_error=mecals_area_error)

    # 
    # 
    # 
    # 
    # error_cells_subgraph_inputs_dict_per_mode = get_subgraph_inputs_vs_sat_cells(rel_files, folder)
    # report_sat_cells_vs_subgraph_inputs(args, error_cells_subgraph_inputs_dict_per_mode)
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
    plot_area_error(args, sorted_area_error, area_error_mode_last_points_dict=area_error_mode_last_points_dict, mecals_area_error=mecals_area_error)
    # plot_area_error_best(args, sorted_area_error, area_error_mode_last_points_dict=area_error_mode_last_points_dict, mecals_area_error=mecals_area_error)
    plot_area_error_pareto(args, sorted_area_error, area_error_mode_last_points_dict=area_error_mode_last_points_dict, mecals_area_error=mecals_area_error)
    # area_error_ns_dict = get_area_error_per_num_subgraphs(rel_files, folder)
    # plot_area_error_per_ns(args, area_error_ns_dict)

    # area_error_mode_dict = get_area_error_per_mode(rel_files, folder)
    # plot_area_error_per_mode(args, area_error_mode_dict)

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
                with open(f'{folder}/{rep}', 'r') as f:
                    csvreader = csv.reader(f)
                    for line in csvreader:
                        if line[0].startswith('cell'): # skip the first line
                            continue
                        else:
                            if line[3].startswith('SAT'):
                                sub_in = int(line[11])
                                cell = line[0]
                                cell = cell.replace('(', '').replace(')', '').strip().split(',')

                                lpp = re.search('(\d+)', cell[0]).group()[0]
                                ppo = re.search('(\d+)', cell[1]).group()[0]

                                error = 2 ** (int(line[1]) - 1)

                                if error not in error_cell_dict.keys():
                                    error_cell_dict[error] = []

                                error_cell_dict[error].append((lpp, ppo, sub_in))
        if error_cell_dict:
            error_cell_dict_per_mode[mode] = error_cell_dict
            error_cell_dict = {}
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
    for mode in range(20):
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



        # runtime_error = [(runtime, error) for error, runtime in runtime_error_dict.items()]
        # sorted_runtime_error = sorted(runtime_error, key=lambda x: x[1])
        # if sorted_runtime_error:
        #     runtime_error_per_mode_dict[mode] = sorted_runtime_error
        # runtime_error_dict ={}
    # for el in runtime_error_decomposed_dict:
    #     print(f'{runtime_error_decomposed_dict[el] = }')
    # print(f'{runtime_error_decomposed_dict = }')
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
                lpp, ppo, subgraph_input = tpl
                records.append((mode, threshold, (lpp, ppo), subgraph_input))

    df = pd.DataFrame(records, columns=['Mode', 'Error_Threshold', 'Tuple (lpp, ppo)', 'Subgraph_Input'])

    # Summarize the DataFrame
    summary = df.groupby(['Mode', 'Error_Threshold', 'Tuple (lpp, ppo)'])['Subgraph_Input'].agg(
        ['count', 'mean', 'std']).reset_index()

    # Rename columns for clarity
    summary.columns = ['Mode', 'Error_Threshold', 'Tuple (lpp, ppo)', 'Count', 'Mean of Subgraph Inputs',
                       'Std of Subgraph Inputs']

    # Calculate the total count for each mode
    total_counts = summary.groupby('Mode')['Count'].transform('sum')

    # Calculate the percentage
    summary['Percentage'] = round((summary['Count'] / total_counts) * 100, 2)

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
        print(f'{ns = }')

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
        print(f'{mode = }')

        sorted_area_error = runtime_error_per_mode_dict[mode]

        runtimes = [item[0] for item in sorted_area_error]
        errors = [item[1] for item in sorted_area_error]

        print(f'{round(sum(runtimes)/60, 2) =  }')
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
        print(f'{mode = }')

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