import csv
import os
import pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import re
import itertools
import matplotlib.cm as cm
import numpy as np
from scipy.stats import pearsonr
from scipy.stats import linregress

from typing import List, Tuple, Dict
from sxpat.config.paths import *
import sxpat.config.config as sxpatconfig
from sxpat.arguments import Arguments
from vpadanalyzer.synthesis import Synthesis


def main():
    args = Arguments.parse()
    print(f'{args.benchmark_name = }')
    folder = f'experiments/mecals/{args.benchmark_name}'
    mecals_area_error = get_mecals_area_error(args, folder)

    # folder = f'experiments/blasys/{args.benchmark_name}'
    # blasys_area_error = get_blasys_area_error(args, folder)
    # folder = f'experiments/blasys/runtimes'
    # blasys_total_runtime = get_blasys_total_runtime(args, folder)


    # muscat_area_error = {}
    # muscat_number_of_models_array = [1, 10, 50, 100]
    # for nm in muscat_number_of_models_array:
    #     folder = f'experiments/muscat/{args.benchmark_name}_{nm}'
    #     muscat_area_error[nm] = get_muscat_area_error(args, folder, False)
    # folder = f'experiments/muscat'
    # create_csv_table_tcad(args, folder, muscat_area_error, sxpatconfig.MUSCAT, total_subxpat_time = None)
    # exit()
    # print(f'{mecals_area_error = }')
    #
    # folder = f'experiments/mecals/{args.benchmark_name}'
    # mecals_exp_specs = ExperimentSpecifications(benchmark_name=args.benchmark_name, tool_name=sxpatconfig.MECALS,
    #                                             folder=folder)
    #



    # print(f'{mecals_exp_specs.get_area_error() = }')

    folder = f'experiments/evoapprox/{args.benchmark_name}'
    evoapprox_area_error = get_evoapprox_area_error(args, folder, False)

    folder = 'experiments/results'
    rel_files = get_relevant_files(args, folder)

    subxpat_exp_specs = ExperimentSpecifications(args.benchmark_name, tool_name='SubXPAT', folder=folder,
                                         imax=6, omax=3, num_models=1, mode=55, et_partitioning='asc',
                                         constants='optimize')
    subxpat_results = Result(subxpat_exp_specs)
    
    # uncomment for grid and cell times
    # constant_dicts = {}
    # for constant_type in ['never', 'optimize', 'always']:
    #     et_runtimes_dict = get_runtimes(rel_files, folder, constant_type)
    #     if et_runtimes_dict:
    #         plot_box_cell_runtimes(args, et_runtimes_dict, constant_type)
    #
    #     constant_dicts[constant_type] = et_runtimes_dict
    # plot_comparison_grid_runtimes(args, constant_dicts, constant_type)

    
    area_error_per_imax_omax_per_num_models_mode = get_subgraph_area_per_mode_num_models_and_imax_omax(rel_files,folder)


    # uncomment for io correlation
    # for nm in area_error_per_imax_omax_per_num_models_mode.keys():
    #     for mode in area_error_per_imax_omax_per_num_models_mode[nm].keys():
    #         for (imax, omax) in area_error_per_imax_omax_per_num_models_mode[nm][mode].keys():
    #             print(f'{nm}, {mode}, {imax}, {omax}')
    #
    # io_21 = area_error_per_imax_omax_per_num_models_mode[55][1][(2, 1)]
    # io_32 = area_error_per_imax_omax_per_num_models_mode[55][1][(3, 2)]
    # io_63 = area_error_per_imax_omax_per_num_models_mode[55][1][(6, 3)]

    # plot_io_correlation(args, (2, 1), (3, 2), (6, 3), io_21, io_32, io_63)
    # exit()

    # uncomment for constant vs no constants available
    area_error_per_constants_always = get_subgraph_area_per_mode_num_models_and_imax_omax_constants(rel_files, folder)
    print(f'Const always has been collected! \n')
    area_error_per_constants_optimize = get_subgraph_area_per_mode_num_models_and_imax_omax_constants_optimize(
        rel_files, folder)
    print(f'Const optimize has been collected! \n')
    plot_area_constants_vs_no_constants(args, area_error_per_imax_omax_per_num_models_mode,
                                        area_error_per_constants_always, None,
                                        mecals_area_error, None, None, None)
    plot_scatter_area_constants_vs_no_constants(args, area_error_per_imax_omax_per_num_models_mode,
                                                area_error_per_constants_always, None,
                                                None, None, None, None)
    exit()


# ======= TCAD CSV table for latex table generation ==========
def create_csv_table_tcad(args: Arguments, folder, pareto_area_et, toolname, total_subxpat_time=None):
    if toolname == sxpatconfig.SUBXPAT:
        print(f'{toolname}')
        print(f'{pareto_area_et = }')
        assert total_subxpat_time is not None
        folder = 'experiments'

        with open(f'{folder}/{toolname}_{args.benchmark_name}.csv', 'w', newline='') as csvfile:
            header = ['wce', 'area (\u03BCm^2)', 'power', 'delay', 'runtime (s)']
            csvwriter = csv.writer(csvfile, delimiter=',')
            csvwriter.writerow(header)

            for area, wce in pareto_area_et:
                row = [wce, area, 'n/a', 'n/a', 'n/a']
                csvwriter.writerow(row)

            row = ['total runtime (s)', f'{total_subxpat_time}']
            csvwriter.writerow(row)

    elif toolname == sxpatconfig.MUSCAT:
        for nm in pareto_area_et.keys():
            print(f'{nm = }')
            tmp_pareto_area_et = pareto_area_et[nm]
            all_files = [f for f in os.listdir(f'{folder}/{args.benchmark_name}_{nm}')]
            print(f'{all_files = }')
            runtime_error_dict = {}
            for f in all_files:
                if f.endswith('.txt') and re.search('time', f):
                    cur_wce = int(re.search('_wc(\d+)_', f).group(1))
                    with open(f'{folder}/{args.benchmark_name}_{nm}/{f}', 'r') as a:
                        cur_runtime = float(a.read())
                    runtime_error_dict[cur_wce] = cur_runtime

            with open(f'{folder}/{toolname}_{args.benchmark_name}_{nm}.csv', 'w', newline='') as csvfile:
                header = ['wce', 'area (\u03BCm^2)', 'power', 'delay', 'runtime (s)']
                csvwriter = csv.writer(csvfile, delimiter=',')
                csvwriter.writerow(header)

                for area, wce in tmp_pareto_area_et:
                    if wce in runtime_error_dict.keys():
                        row = [wce, area, 'n/a', 'n/a', runtime_error_dict[wce]]
                    else:
                        row = [wce, area, 'n/a', 'n/a', 'n/a']
                    csvwriter.writerow(row)

                total_time = sum(runtime_error_dict.values())
                row = ['total runtime (s)', f'{total_time}' if total_time > 0 else 'n/a']
                csvwriter.writerow(row)
    else:
        all_files = [f for f in os.listdir(f'{folder}/{args.benchmark_name}')]
        runtime_error_dict = {}
        for f in all_files:
            if f.endswith('.txt') and re.search('time', f):
                cur_wce = int(re.search('_(\d+).txt', f).group(1))
                with open(f'{folder}/{args.benchmark_name}/{f}', 'r') as a:
                    cur_runtime = float(a.read())
                runtime_error_dict[cur_wce] = cur_runtime

        with open(f'{folder}/{toolname}_{args.benchmark_name}.csv', 'w', newline='') as csvfile:
            header = ['wce', 'area (\u03BCm^2)', 'power', 'delay', 'runtime (s)']
            csvwriter = csv.writer(csvfile, delimiter=',')
            csvwriter.writerow(header)

            for area, wce in pareto_area_et:
                if wce in runtime_error_dict.keys():
                    row = [wce, area, 'n/a', 'n/a', runtime_error_dict[wce]]
                else:
                    row = [wce, area, 'n/a', 'n/a', 'n/a']
                csvwriter.writerow(row)

            total_time = sum(runtime_error_dict.values())
            row = ['total runtime (s)', f'{total_time}' if total_time > 0 else 'n/a']
            csvwriter.writerow(row)


# ======= Area Improvements ===================

def compare_tools_best(subxpat_pareto, other_tool_pareto, tool_name):
    # Convert both lists to dictionaries for quick lookup by the error value
    if not other_tool_pareto:
        return None, None

    subxpat_dict = {error: area for area, error in subxpat_pareto}
    other_tool_dict = {error: area for area, error in other_tool_pareto}

    # Initialize variables to calculate improvements and counts
    total_comparisons = 0
    subxpat_better_count = 0
    max_improvement = 0  # To track maximum improvement (absolute value)
    no_common_points = True

    # Iterate over the errors in subxpat to find matching errors in the other tool
    for error in subxpat_dict:
        if error in other_tool_dict or (error - 1 in other_tool_dict and tool_name == 'MECALS'):
            if error - 1 in other_tool_dict:
                other_error = error - 1
            else:
                other_error = error
            no_common_points = False
            subxpat_area = subxpat_dict[error]
            other_tool_area = other_tool_dict[other_error]
            total_comparisons += 1
            improvement = other_tool_area - subxpat_area

            if improvement < 0:
                subxpat_better_count += 1

            # Update maximum absolute improvement
            max_improvement = max(max_improvement, improvement)

    # If no common points are found, set max_improvement to -500
    if no_common_points and total_comparisons == 0:
        max_improvement = -500

    # Calculate percentage better
    if total_comparisons == 0:
        percentage_better = 0
    else:
        percentage_better = (subxpat_better_count / total_comparisons) * 100

    return percentage_better, round(max_improvement, 2)


def compare_tools_avg(subxpat_pareto, other_tool_pareto, tool_name):
    # Convert both lists to dictionaries for quick lookup by the error value
    if not other_tool_pareto:
        return None, None
    subxpat_dict = {error: area for area, error in subxpat_pareto}
    other_tool_dict = {error: area for area, error in other_tool_pareto}

    # Initialize variables to calculate improvements and counts
    total_comparisons = 0
    subxpat_better_count = 0
    improvements = []

    no_common_points = True
    # Iterate over the errors in subxpat to find matching errors in the other tool
    for error in subxpat_dict:
        if error in other_tool_dict or (error - 1 in other_tool_dict and tool_name == 'MECALS'):
            if error - 1 in other_tool_dict:
                other_error = error - 1
            else:
                other_error = error
            no_common_points = False
            subxpat_area = subxpat_dict[error]
            other_tool_area = other_tool_dict[other_error]
            total_comparisons += 1
            improvement = other_tool_area - subxpat_area

            if improvement < 0:
                subxpat_better_count += 1

            # Record improvement for average calculation
            improvements.append(improvement)

    if total_comparisons == 0:
        percentage_better = 0
        average_improvement = 0
    else:
        percentage_better = (subxpat_better_count / total_comparisons) * 100
        average_improvement = round(sum(improvements) / total_comparisons, 2)

    if no_common_points:
        average_improvement = -500

    return percentage_better, average_improvement


# ======= Runtimes ============================

def get_blasys_total_runtime(args, folder):
    all_files = [f for f in os.listdir(folder)]
    total_time = 0
    for file in all_files:
        if re.search(f'{args.benchmark_name}', file, re.IGNORECASE):
            with open(f'{folder}/{file}', 'r') as f:
                total_time += round(float(f.read()) / 60, 2)
    return total_time


# ======= TABLE (io configurations) ===========

def calculate_total_runtime(args, runtime_error_per_omax_per_mode):
    total_runtime_per_num_model_config = {}
    total_runtime_per_config = {}
    # Iterate over each mode in the dictionary
    for mode, num_model_dict in runtime_error_per_omax_per_mode.items():
        for num_model, config_dict in num_model_dict.items():
            for config, runtime_data in config_dict.items():
                # Calculate the total runtime for this configuration
                total_runtime = sum(runtime for et, runtime in runtime_data)
                total_runtime_per_config[config] = round(total_runtime, 2)
            total_runtime_per_num_model_config[num_model] = total_runtime_per_config
            total_runtime_per_config = {}
    save_to_csv(args, total_runtime_per_num_model_config)
    return total_runtime_per_num_model_config


def save_to_csv(args, total_runtime_per_config):
    # Save the total runtimes to a CSV file
    filename = f'{args.benchmark_name}_io_runtime'
    output_csv = f'output/report/{filename}.csv'
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write the header
        writer.writerow(['config', 'runtime'])
        # Write the data
        for config, runtime in total_runtime_per_config.items():
            writer.writerow([config, runtime])


def analyze_impact_of_configuration_on_area_decrease(args, smallest_pair_data, medium_pair_data, largest_pair_data):
    et_values = set(smallest_pair_data.keys()).union(medium_pair_data.keys()).union(largest_pair_data.keys())

    area_diffs = []
    correlations = []
    weights = []

    for et in et_values:
        areas_small = np.array([pair[0] for pair in smallest_pair_data.get(et, [])])
        areas_medium = np.array([pair[0] for pair in medium_pair_data.get(et, [])])
        areas_large = np.array([pair[0] for pair in largest_pair_data.get(et, [])])

        if len(areas_small) > 0 and len(areas_medium) > 0 and len(areas_large) > 0:
            # Compare areas across configurations
            avg_small = np.mean(areas_small)
            avg_medium = np.mean(areas_medium)
            avg_large = np.mean(areas_large)

            area_diffs.append((avg_small, avg_medium, avg_large))

            # Compute correlation between configuration size and area
            config_sizes = np.array([1, 2, 3])
            areas = np.array([avg_small, avg_medium, avg_large])
            correlation, _ = pearsonr(config_sizes, areas)
            correlations.append(correlation)

            # Store the weight (number of configurations)
            weights.append(len(areas_small) + len(areas_medium) + len(areas_large))

    # Compute the average correlation across all ETs
    avg_correlation = np.mean(correlations)

    # Compute weighted average correlation if desired
    weighted_avg_correlation = np.average(correlations, weights=weights)

    # Compute Pareto percentages
    small_pareto, medium_pareto, large_pareto = compute_pareto_percentage(
        [pair for sublist in smallest_pair_data.values() for pair in sublist],
        [pair for sublist in medium_pair_data.values() for pair in sublist],
        [pair for sublist in largest_pair_data.values() for pair in sublist]
    )
    filename = f'{args.benchmark_name}_io_correlation'
    output_csv = f'output/report/{filename}.csv'
    # Save the results to a CSV file
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['ET', 'Small (2,1) Avg Area', 'Medium (3,2) Avg Area', 'Large (6,3) Avg Area', 'Correlation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for i, et in enumerate(et_values):
            writer.writerow({
                'ET': et,
                'Small (2,1) Avg Area': area_diffs[i][0],
                'Medium (3,2) Avg Area': area_diffs[i][1],
                'Large (6,3) Avg Area': area_diffs[i][2],
                'Correlation': correlations[i]
            })

        # Add a summary row with the average correlation
        writer.writerow({
            'ET': 'Average Correlation',
            'Small (2,1) Avg Area': '',
            'Medium (3,2) Avg Area': '',
            'Large (6,3) Avg Area': '',
            'Correlation': avg_correlation
        })

        # Add a summary row with the Pareto percentages
        writer.writerow({
            'ET': 'Pareto Percentage',
            'Small (2,1) Avg Area': f'{small_pareto:.2f}%',
            'Medium (3,2) Avg Area': f'{medium_pareto:.2f}%',
            'Large (6,3) Avg Area': f'{large_pareto:.2f}%',
            'Correlation': ''
        })

    # Return the average correlation, weighted average correlation, and pareto percentages
    return avg_correlation, weighted_avg_correlation, (small_pareto, medium_pareto, large_pareto)


def compute_pareto_percentage(small_data, medium_data, large_data):
    combined_data = small_data + medium_data + large_data
    pareto_front = []

    for point in combined_data:
        if not any(p[0] <= point[0] and p[1] < point[1] for p in pareto_front):
            pareto_front.append(point)

    pareto_small = len([p for p in pareto_front if p in small_data and p not in medium_data and p not in large_data])
    pareto_medium = len([p for p in pareto_front if p in medium_data and p not in large_data])
    pareto_large = len([p for p in pareto_front if p in large_data])
    print(f'{pareto_small = }')
    print(f'{pareto_medium = }')
    print(f'{pareto_large = }')
    total_pareto_points = pareto_small + pareto_medium + pareto_large

    small_percentage = (pareto_small / total_pareto_points) * 100 if total_pareto_points > 0 else 0
    medium_percentage = (pareto_medium / total_pareto_points) * 100 if total_pareto_points > 0 else 0
    large_percentage = (pareto_large / total_pareto_points) * 100 if total_pareto_points > 0 else 0

    return small_percentage, medium_percentage, large_percentage


# ======= TABLE ===========
def extract_specific_pairs(area_error_per_imax_omax_per_mode):
    # Define the specific pairs we want to extract
    small_pair = (2, 1)
    medium_pair = (3, 2)
    large_pair = (6, 3)

    # Extract data for the specific pairs
    small_pair_data = area_error_per_imax_omax_per_mode[55][small_pair]
    medium_pair_data = area_error_per_imax_omax_per_mode[55][medium_pair]
    large_pair_data = area_error_per_imax_omax_per_mode[55][large_pair]

    return small_pair, medium_pair, large_pair, small_pair_data, medium_pair_data, large_pair_data


# Function to plot the scatter plot for three specific pairs
def plot_io_correlation_null(args, small_pair, medium_pair, large_pair, small_pair_data, medium_pair_data,
                             large_pair_data, global_et: bool = False):
    fig, ax = plt.subplots(figsize=(14, 10))

    plt.scatter([], [], color='blue', alpha=1)
    plt.text(0.5, 0.5, 'ToDo', fontsize=100, color='gray', alpha=0.3, ha='center', va='center', rotation=45,
             transform=plt.gca().transAxes)

    plt.xlabel('ET', fontsize=24)
    plt.ylabel(r'Area ($\mu m^2$)', fontsize=24)
    plt.yticks(fontsize=24)
    plt.xticks(fontsize=22)

    # ax.set_title(f'{args.benchmark_name}', fontsize=26)
    plt.legend(fontsize=24)
    plt.tight_layout()

    plt.grid()
    # plt.xlabel('ET')
    # plt.ylabel('Area')
    # plt.title('Scatter plot of ET vs. Area for Small, Medium, and Large imax, omax Pairs')
    # plt.legend()
    folder, _ = OUTPUT_PATH['figure']

    figname = 'temp.png'
    plt.savefig(figname)


def plot_io_correlation(args, small_pair, medium_pair, large_pair, small_pair_data, medium_pair_data, large_pair_data,
                        global_et: bool = False):
    max_error = 2 ** (int(re.search('_o(\d+)', args.benchmark_name).group(1)) - 1)
    step = max_error // 8
    xticks = list(range(step, max_error + step, step))

    fig, ax = plt.subplots(figsize=(14, 10))
    max_error = 2 ** (int(re.search('_o(\d+)', args.benchmark_name).group(1)) - 1)
    x_threshold = max_error // 8
    # Plot data for the small imax, omax pair
    for et, area_local_et_pairs in small_pair_data.items():
        areas = [pair[0] for pair in area_local_et_pairs if x_threshold <= pair[1] <= max_error]

        if global_et:
            plt.scatter([et] * len(areas), areas, color='blue', alpha=1)
        else:
            ets = [pair[1] for pair in area_local_et_pairs if x_threshold <= pair[1] <= max_error]
            plt.scatter(ets, areas, color='blue', alpha=1)

    # Plot data for the medium imax, omax pair
    for et, area_local_et_pairs in medium_pair_data.items():
        areas = [pair[0] for pair in area_local_et_pairs if x_threshold <= pair[1] <= max_error]

        if global_et:
            plt.scatter([et] * len(areas), areas, color='green', alpha=1)
        else:
            ets = [pair[1] for pair in area_local_et_pairs if x_threshold <= pair[1] <= max_error]
            plt.scatter(ets, areas, color='green', alpha=1)

    # Plot data for the large imax, omax pair
    for et, area_local_et_pairs in large_pair_data.items():
        areas = [pair[0] for pair in area_local_et_pairs if x_threshold <= pair[1] <= max_error]

        if global_et:
            plt.scatter([et] * len(areas), areas, color='red', alpha=1)
        else:
            ets = [pair[1] for pair in area_local_et_pairs if x_threshold <= pair[1] <= max_error]
            plt.scatter(ets, areas, color='red', alpha=1)

    # Add legends for the three pairs
    plt.scatter([], [], color='blue', label=f'imax, omax = {small_pair}')
    plt.scatter([], [], color='green', label=f'imax, omax = {medium_pair}')
    plt.scatter([], [], color='red', label=f'imax, omax = {large_pair}')

    plt.xlabel('ET', fontsize=24)
    plt.ylabel(r'Area ($\mu m^2$)', fontsize=24)
    plt.yticks(fontsize=24)
    plt.xticks(xticks, fontsize=22)
    # ax.set_title(f'{args.benchmark_name}', fontsize=26)
    plt.legend(fontsize=24)
    plt.tight_layout()

    # plt.grid()
    # plt.xlabel('ET')
    # plt.ylabel('Area')
    # plt.title('Scatter plot of ET vs. Area for Small, Medium, and Large imax, omax Pairs')
    # plt.legend()
    folder, _ = OUTPUT_PATH['figure']

    if global_et:
        figname = f'{folder}/{args.benchmark_name}_io_correlation_global_et.png'
    else:
        figname = f'{folder}/{args.benchmark_name}_io_correlation_local_et.png'
    plt.savefig(figname)


def _exists(x_y_tuple: Tuple, x_y_list: List):
    for x, y in x_y_list:
        if y == x_y_tuple[1]:
            return True
    return False


# =================================================
# =================================================
# =================================================
# =================================================

class ExperimentSpecifications:
    def __init__(self,
                 benchmark_name: str = 'adder_i8_o5.v',
                 tool_name: str = sxpatconfig.SUBXPAT,
                 folder: str = 'experiments/results',
                 imax: int = 6, omax: int = 3,
                 num_models: int = 1, constants: str = 'never',
                 mode: int = 55, et_partitioning: str = 'asc'):

        self.tool_name = tool_name
        if self.tool_name == sxpatconfig.SUBXPAT:
            self.benchmark_name = benchmark_name
            self.folder = folder
            self.imax = None
            self.omax = None
            self.num_models = None
            self.constants = None
            self.mode = None
            self.et_partitioning = None
        else:
            self.benchmark_name = benchmark_name
            self.folder = folder



class Result:
    def __init__(self, experiment_specs: ExperimentSpecifications):
        self.specs = experiment_specs
        self.raw_csvs = None

    def read_csv(self, csv_files: str):
        pass


    def _get_subxpat_relevant_files(self):
        pass

    def get_area_error(self):
        if self.specs.tool_name == sxpatconfig.SUBXPAT:
            return f'Not Implemented'
        elif self.specs.tool_name == sxpatconfig.MECALS:
            return get_mecals_area_error(args=None, folder=self.specs.folder, synth=False)
        elif self.specs.tool_name == sxpatconfig.MUSCAT:
            return get_muscat_area_error(args=None, folder=self.specs.folder, synth=False)
        elif self.specs.tool_name == sxpatconfig.EVOAPPROX:
            return get_evoapprox_area_error(args=None, folder=self.specs.folder, synth=False)



# Collect Data ====================================
# =================================================
# =================================================
# =================================================
def get_runtimes(relevant_files, folder, constanttype):
    et_runtime_dict = {}
    for mode in [55]:
        for num_model in [1]:
            for omax in [3]:
                for imax in [6]:
                    for rep in relevant_files:
                        if re.search(f'{constanttype}', rep):
                            if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(
                                    f'imax{imax}_', rep):
                                cur_path = f'{folder}/{rep}'
                                et = int(re.search(f'et(\d+)_', rep).group(1))
                                df = pd.read_csv(
                                    cur_path,
                                    delimiter=',',
                                    header=0,
                                    names=[
                                        'cell', 'iteration', 'model_id', 'status', 'runtime', 'area', 'delay',
                                        'total_power',
                                        'et', 'labeling_time', 'subgraph_extraction', 'subgraph_inputs',
                                        'subgraph_outputs',
                                        'subxpat_phase1', 'subxpat_phase2', 'exploration_time'
                                    ]
                                )
                                df = df.rename(columns={'': 'exploration_time'})
                                df_relevant = df[['labeling_time', 'subgraph_extraction', 'exploration_time']]
                                et_runtime_dict[et] = list(
                                    zip(df_relevant['labeling_time'],
                                        df_relevant['subgraph_extraction'],
                                        df_relevant['exploration_time'])
                                )
    et_runtime_dict = dict(sorted(et_runtime_dict.items()))
    return et_runtime_dict



def plot_box_cell_runtimes(args, et_runtime_dict, factor):
    et_values = sorted(et_runtime_dict.keys())
    exploration_times = [
        [runtime[2] for runtime in et_runtime_dict[et]] for et in et_values
    ]

    # Check for et values with fewer than 5 exploration times
    for et, times in zip(et_values, exploration_times):
        if len(times) < 5:
            print(f"Warning: et={et} has only {len(times)} data points, which may not be enough for a box plot.")

    # Plot box plot with sequential positions
    plt.figure(figsize=(14, 12))

    plt.boxplot(exploration_times, widths=0.2, showfliers=True)

    # Add scatter points for visualization of all individual points
    for i, times in enumerate(exploration_times, start=1):
        plt.scatter([i] * len(times), times, alpha=0.6, color='red', marker='o')

    # Set x-axis with et values as labels
    plt.xlabel("et", fontsize=24)
    plt.ylabel("Cell Exploration Time (seconds)", fontsize=24)
    plt.title(f"{args.benchmark_name} constants={factor}", fontsize=24)
    plt.xticks(ticks=range(1, len(et_values) + 1), labels=et_values, rotation=45, fontsize=22)
    plt.yticks(fontsize=22)
    plt.grid(True)
    plt.tight_layout()
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/cell_times_box_plot_{args.benchmark_name}_runtime_{factor}.png'
    plt.savefig(figname)

def plot_comparison_grid_runtimes(args, et_runtime_dicts, factor):
    # Set up the plot
    plt.figure(figsize=(14, 12))
    plt.xlabel("et", fontsize=24)
    plt.ylabel("Grid Exploration Time (seconds)", fontsize=24)
    plt.title(f"{args.benchmark_name} constants={factor}", fontsize=24)
    plt.xticks(rotation=45, fontsize=22)
    plt.yticks(fontsize=22)

    # Define plot styles for each dictionary
    styles = {
        'optimize': {'marker': '^', 'color': 'teal', 'label': 'Optimize'},
        'never': {'marker': 'o', 'color': 'blue', 'label': 'Never'},
        'always': {'marker': 'x', 'color': 'violet', 'label': 'Always'}
    }

    # Plot each line for 'never', 'optimize', 'always'
    for key, style in styles.items():
        et_values = sorted(et_runtime_dicts[key].keys())
        exploration_time_sums = [
            sum(runtime[2] for runtime in et_runtime_dicts[key][et]) for et in et_values
        ]
        plt.plot(et_values, exploration_time_sums, marker=style['marker'], markersize=14,
                 linestyle='--', color=style['color'], label=style['label'])

    # Add grid, legend, and layout adjustments
    plt.grid(True)
    plt.legend(fontsize=20)
    plt.tight_layout()

    # Save the figure
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/grid_times_{args.benchmark_name}_runtime.png'
    plt.savefig(figname)


def plot_grid_runtimes(args, et_runtime_dict, factor):
    # Extract sorted et values and corresponding sum of exploration times for each et
    et_values = sorted(et_runtime_dict.keys())
    exploration_time_sums = [
        sum(runtime[2] for runtime in et_runtime_dict[et]) for et in et_values
    ]
    plt.figure(figsize=(14, 12))

    plt.xlabel("et", fontsize=24)
    plt.ylabel("Grid Exploration Time (seconds)", fontsize=24)
    plt.plot(et_values, exploration_time_sums, marker='o', markersize=14, linestyle='--', color='blue')
    plt.grid(True)
    plt.title(f"{args.benchmark_name} constants={factor}", fontsize=24)
    plt.xticks(rotation=45, fontsize=22)
    plt.yticks(fontsize=22)
    plt.tight_layout()
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/grid_times_{args.benchmark_name}_runtime_{factor}.png'
    plt.savefig(figname)


def get_subgraph_area_per_mode_num_models_and_imax_omax_constants(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    runtime_error_per_omax_num_models: Dict = {}
    area_error = {}
    cur_area_error = []
    for mode in range(200):
        for num_model in [1]:
            for omax in range(10):
                for imax in range(10):
                    for rep in relevant_files:
                        sorted_cur_area_error = []
                        cur_area_error = []
                        if re.search(f'constalways', rep):
                            if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(
                                    f'imax{imax}_', rep):
                                print(f'{rep = }')
                                et = int(re.search(f'et(\d+)_', rep).group(1))
                                with open(f'{folder}/{rep}', 'r') as f:
                                    csvreader = csv.reader(f)
                                    for line in csvreader:
                                        if line[0].startswith('cell'):  # skip the first line
                                            continue
                                        else:
                                            if line[3].startswith('SAT'):
                                                cur_et = int(line[8])
                                                cur_area = float(line[5])
                                                cur_area_error.append((cur_area, cur_et))

                                sorted_cur_area_error = sorted(cur_area_error, key=lambda x: x[1])
                                if sorted_cur_area_error:
                                    area_error[et] = sorted_cur_area_error

                    if area_error:
                        runtime_error_per_omax[(imax, omax)] = area_error
                        area_error = {}
            if runtime_error_per_omax:
                runtime_error_per_omax_num_models[num_model] = runtime_error_per_omax
                runtime_error_per_omax = {}
        if runtime_error_per_omax_num_models:
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax_num_models
            runtime_error_per_omax_num_models = {}

    return runtime_error_per_omax_per_mode


def get_subgraph_area_per_mode_num_models_and_imax_omax_constants_optimize(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    runtime_error_per_omax_num_models: Dict = {}
    area_error = {}
    cur_area_error = []
    for mode in range(200):
        for num_model in [1]:
            for omax in range(10):
                for imax in range(10):
                    for rep in relevant_files:
                        sorted_cur_area_error = []
                        cur_area_error = []
                        if re.search(f'constoptimize', rep):
                            if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(
                                    f'imax{imax}_', rep):
                                print(f'{rep = }')
                                et = int(re.search(f'et(\d+)_', rep).group(1))
                                with open(f'{folder}/{rep}', 'r') as f:
                                    csvreader = csv.reader(f)
                                    for line in csvreader:
                                        if line[0].startswith('cell'):  # skip the first line
                                            continue
                                        else:
                                            if line[3].startswith('SAT'):
                                                cur_et = int(line[8])
                                                cur_area = float(line[5])
                                                cur_area_error.append((cur_area, cur_et))

                                sorted_cur_area_error = sorted(cur_area_error, key=lambda x: x[1])
                                if sorted_cur_area_error:
                                    area_error[et] = sorted_cur_area_error

                    if area_error:
                        runtime_error_per_omax[(imax, omax)] = area_error
                        area_error = {}
            if runtime_error_per_omax:
                runtime_error_per_omax_num_models[num_model] = runtime_error_per_omax
                runtime_error_per_omax = {}
        if runtime_error_per_omax_num_models:
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax_num_models
            runtime_error_per_omax_num_models = {}

    return runtime_error_per_omax_per_mode


def get_subgraph_area_per_mode_num_models_and_imax_omax(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    runtime_error_per_omax_num_models: Dict = {}
    area_error = {}
    cur_area_error = []
    for mode in range(200):
        for num_model in [1]:
            for omax in range(10):
                for imax in range(10):
                    for rep in relevant_files:
                        sorted_cur_area_error = []
                        cur_area_error = []
                        if re.search('constnever', rep):
                            if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(
                                    f'imax{imax}_', rep):
                                print(f'{rep = }')
                                et = int(re.search(f'et(\d+)_', rep).group(1))
                                with open(f'{folder}/{rep}', 'r') as f:
                                    csvreader = csv.reader(f)
                                    for line in csvreader:
                                        if line[0].startswith('cell'):  # skip the first line
                                            continue
                                        else:
                                            if line[3].startswith('SAT'):
                                                cur_et = int(line[8])
                                                cur_area = float(line[5])
                                                cur_area_error.append((cur_area, cur_et))

                                sorted_cur_area_error = sorted(cur_area_error, key=lambda x: x[1])
                                if sorted_cur_area_error:
                                    area_error[et] = sorted_cur_area_error

                    if area_error:
                        runtime_error_per_omax[(imax, omax)] = area_error
                        area_error = {}
            if runtime_error_per_omax:
                runtime_error_per_omax_num_models[num_model] = runtime_error_per_omax
                runtime_error_per_omax = {}
        if runtime_error_per_omax_num_models:
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax_num_models
            runtime_error_per_omax_num_models = {}

    return runtime_error_per_omax_per_mode


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
    # print(f'{summary}')


# Plotting ===============================

def plot_scatter_area_constants_vs_no_constants(args, area_error_per_imax_omax_per_mode=None,
                                                area_error_constants_always=None,
                                                area_error_per_constants_optimize=None, mecals_area_error=None,
                                                evoapprox_area_error=None,
                                                muscat_area_error=None,
                                                blasys_area_error=None):
    fig, ax = plt.subplots(figsize=(14, 10))

    max_error = 2 ** (int(re.search('_o(\d+)', args.benchmark_name).group(1)) - 1)
    x_threshold = max_error // 8
    all_local_ets = []
    all_global_ets = []
    all_areas = []

    subxpat_never_points = []
    suxpat_always_points = []
    suxpat_optimize_points = []

    for mode, num_models_dict in area_error_per_imax_omax_per_mode.items():
        for num_models, imax_omax_dict in num_models_dict.items():
            for (imax, omax), et_dict in imax_omax_dict.items():
                for global_et, area_local_et_list in et_dict.items():
                    areas, local_ets = zip(*area_local_et_list)
                    all_local_ets.extend(local_ets)
                    all_global_ets.append(global_et)

    if area_error_per_imax_omax_per_mode:
        for mode, num_models_dict in area_error_per_imax_omax_per_mode.items():
            for num_models, imax_omax_dict in num_models_dict.items():
                for (imax, omax), et_dict in imax_omax_dict.items():
                    for global_et, area_local_et_list in et_dict.items():
                        for point in area_local_et_list:
                            subxpat_never_points.append(point)

        subxpat_never_points = [item for item in subxpat_never_points if x_threshold <= item[1] <= max_error]
        # suxpat_optimize_points = [item for item in suxpat_optimize_points if item[1]]
        areas = [item[0] for item in subxpat_never_points]
        errors = [item[1] for item in subxpat_never_points]
        assert len(areas) == len(errors)
        ax.scatter(errors, areas, marker='o', label='SubXPAT (never)', color='blue', alpha=0.4, s=100)

    if area_error_constants_always:
        for mode, num_models_dict in area_error_constants_always.items():
            for num_models, imax_omax_dict in num_models_dict.items():
                for (imax, omax), et_dict in imax_omax_dict.items():
                    for global_et, area_local_et_list in et_dict.items():
                        for point in area_local_et_list:
                            suxpat_always_points.append(point)
        suxpat_always_points = [item for item in suxpat_always_points if x_threshold <= item[1] <= max_error]
        areas = [item[0] for item in suxpat_always_points]
        errors = [item[1] for item in suxpat_always_points]

        ax.scatter(errors, areas, marker='x', label='SubXPAT (always)', color='purple', alpha=0.4, s=200)

    if area_error_per_constants_optimize:
        for mode, num_models_dict in area_error_per_constants_optimize.items():
            for num_models, imax_omax_dict in num_models_dict.items():
                for (imax, omax), et_dict in imax_omax_dict.items():
                    for global_et, area_local_et_list in et_dict.items():
                        for point in area_local_et_list:
                            suxpat_optimize_points.append(point)
        # suxpat_optimize_points = [item for item in suxpat_optimize_points if x_threshold <= item[1] <= max_error]
        suxpat_optimize_points = [item for item in suxpat_optimize_points if item[1]]
        areas = [item[0] for item in suxpat_optimize_points]
        errors = [item[1] for item in suxpat_optimize_points]

        ax.scatter(errors, areas, marker='^', label='SubXPAT (optimize)', color='teal', alpha=0.4, s=200)

    if muscat_area_error:

        muscat_number_of_models_array = list(muscat_area_error.keys())
        muscat_colors = {
            1: 'green',
            10: 'olive',
            50: 'orange',
            100: 'lawngreen'
        }
        muscat_size = {
            1: 16,
            10: 14,
            50: 12,
            100: 10
        }
        for nm in muscat_number_of_models_array:
            muscat_area_error_pareto = _extract_pareto_front_muscat(muscat_area_error[nm])
            muscat_area_error_pareto = [item for item in muscat_area_error_pareto if
                                        x_threshold <= item[1] <= max_error]

            muscat_areas = [item[0] for item in muscat_area_error_pareto]
            muscat_errors = [item[1] for item in muscat_area_error_pareto]
            all_areas.extend(muscat_areas)
            # ax.plot(muscat_errors, muscat_areas, 'd--', label=f'MUSCAT {nm} models', color=muscat_colors[nm],
            #         markersize=muscat_size[nm])
    if mecals_area_error:
        mecals_area_error = [item for item in mecals_area_error if item[1] >= x_threshold]

        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]
        all_areas.extend(mecals_areas)
        ax.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black', markersize=10)
    if blasys_area_error:
        blasys_area_error_pareto = _extract_pareto_front_blasys(blasys_area_error)
        blasys_area_error_pareto = [(area, wae) for area, wae in blasys_area_error_pareto if
                                    x_threshold <= wae <= max_error]

        # blasys_areas = [item[0] for item in blasys_area_error_pareto]
        # blasys_errors = [item[1] for item in blasys_area_error_pareto]
        blasys_areas = []
        blasys_errors = []
        for area, wae in blasys_area_error_pareto:
            if wae < muscat_errors[-1]:
                blasys_errors.append(wae)
                blasys_areas.append(area)

        all_areas.extend(blasys_areas)
        # ax.plot(blasys_errors, blasys_areas, 'x--', label='BLASYS', color='violet', markersize=10)

        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(blasys_errors):
            if blasys_areas[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='violet', markersize=14)

    if evoapprox_area_error:
        evoapprox_area_error = [item for item in evoapprox_area_error if x_threshold <= item[1] <= max_error]

        evoapprox_areas = [item[0] for item in evoapprox_area_error]
        evoapprox_errors = [item[1] for item in evoapprox_area_error]
        all_areas.extend(evoapprox_areas)
        ax.plot(evoapprox_errors, evoapprox_areas, '^--', label='EVOApprox', color='red', markersize=10)

        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(evoapprox_errors):
            if evoapprox_areas[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='red')

    # Set labels and title
    ax.set_xlabel('ET', fontsize=24)
    ax.set_ylabel(r'Area ($\mu m^2$)', fontsize=24)
    plt.yticks(fontsize=24)
    plt.xticks(fontsize=22)
    # ax.set_title(f'{args.benchmark_name}', fontsize=26)
    ax.legend(fontsize=24)
    if all_global_ets[-1] > 1024:
        plt.xticks(rotation=30)
    # Set x-ticks to be the unique Local ET values

    # ax.set_xticks(all_global_ets)
    ax.set_xticks(list(range(max_error // 8, max_error + max_error // 8, max_error // 8)))

    # ax.set_xticklabels(all_global_ets)
    plt.tight_layout()

    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']

    figname = f'{folder}/{args.benchmark_name}_constants_scatter.png'
    plt.savefig(figname)


def plot_area_constants_vs_no_constants(args, area_error_per_imax_omax_per_mode=None,
                                        area_error_per_constants_always=None, area_error_per_constants_optimize=None,
                                        mecals_area_error=None,
                                        evoapprox_area_error=None,
                                        muscat_area_error=None,
                                        blasys_area_error=None):
    fig, ax = plt.subplots(figsize=(14, 10))

    max_error = 2 ** (int(re.search('_o(\d+)', args.benchmark_name).group(1)) - 1)
    x_threshold = max_error // 8
    all_local_ets = []
    all_global_ets = []
    all_areas = []
    # for mode, imax_omax_dict in area_error_per_imax_omax_per_mode.items():
    for mode, num_models_dict in area_error_per_imax_omax_per_mode.items():
        for num_models, imax_omax_dict in num_models_dict.items():

            for (imax, omax), et_dict in imax_omax_dict.items():
                for global_et, area_local_et_list in et_dict.items():
                    areas, local_ets = zip(*area_local_et_list)
                    all_local_ets.extend(local_ets)
                    all_global_ets.append(global_et)
    if area_error_per_imax_omax_per_mode:
        pareto_points = _extract_pareto_front_from_mode_imax_omax_num_models(area_error_per_imax_omax_per_mode)
        # pareto_points = [item for item in pareto_points if x_threshold  <= item[1] <= max_error]
        pareto_points = [item for item in pareto_points if item[1]]
        pareto_area = [item[0] for item in pareto_points]
        pareto_error = [item[1] for item in pareto_points]
        ax.plot(pareto_error, pareto_area, 'o--', label='SubXPAT (never)', color='blue', markersize=10)
        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(pareto_error):
            if pareto_area[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='blue', linewidth=3)

    if area_error_per_constants_always:
        pareto_points = _extract_pareto_front_from_mode_imax_omax_num_models(area_error_per_constants_always)
        # pareto_points = [item for item in pareto_points if x_threshold  <= item[1] <= max_error]
        pareto_points = [item for item in pareto_points if item[1]]
        pareto_area = [item[0] for item in pareto_points]

        pareto_error = [item[1] for item in pareto_points]
        ax.plot(pareto_error, pareto_area, 'X--', label='SubXPAT (always)', color='purple', markersize=14, alpha=0.8)
        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(pareto_error):
            if pareto_area[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='purple', linewidth=3)

    if area_error_per_constants_optimize:
        pareto_points = _extract_pareto_front_from_mode_imax_omax_num_models(area_error_per_constants_optimize)
        # pareto_points = [item for item in pareto_points if x_threshold  <= item[1] <= max_error]
        pareto_points = [item for item in pareto_points if item[1]]
        pareto_area = [item[0] for item in pareto_points]

        pareto_error = [item[1] for item in pareto_points]
        ax.plot(pareto_error, pareto_area, '^--', label='SubXPAT (optimize)', color='teal', markersize=14, alpha=0.8)
        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(pareto_error):
            if pareto_area[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='teal', linewidth=3)

    if muscat_area_error:

        muscat_number_of_models_array = list(muscat_area_error.keys())
        muscat_colors = {
            1: 'green',
            10: 'olive',
            50: 'orange',
            100: 'lawngreen'
        }
        muscat_size = {
            1: 16,
            10: 14,
            50: 12,
            100: 10
        }
        for nm in muscat_number_of_models_array:
            muscat_area_error_pareto = _extract_pareto_front_muscat(muscat_area_error[nm])
            muscat_area_error_pareto = [item for item in muscat_area_error_pareto if
                                        x_threshold <= item[1] <= max_error]

            muscat_areas = [item[0] for item in muscat_area_error_pareto]
            muscat_errors = [item[1] for item in muscat_area_error_pareto]
            all_areas.extend(muscat_areas)
            # ax.plot(muscat_errors, muscat_areas, 'd--', label=f'MUSCAT {nm} models', color=muscat_colors[nm],
            #         markersize=muscat_size[nm])
    if mecals_area_error:
        mecals_area_error = [item for item in mecals_area_error if item[1] >= x_threshold]

        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]
        all_areas.extend(mecals_areas)
        ax.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black', markersize=10)

    if blasys_area_error:
        blasys_area_error_pareto = _extract_pareto_front_blasys(blasys_area_error)
        blasys_area_error_pareto = [(area, wae) for area, wae in blasys_area_error_pareto if
                                    x_threshold <= wae <= max_error]

        # blasys_areas = [item[0] for item in blasys_area_error_pareto]
        # blasys_errors = [item[1] for item in blasys_area_error_pareto]
        blasys_areas = []
        blasys_errors = []
        for area, wae in blasys_area_error_pareto:
            if wae < muscat_errors[-1]:
                blasys_errors.append(wae)
                blasys_areas.append(area)

        all_areas.extend(blasys_areas)
        # ax.plot(blasys_errors, blasys_areas, 'x--', label='BLASYS', color='violet', markersize=10)

        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(blasys_errors):
            if blasys_areas[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        # ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='violet', markersize=14)

    if evoapprox_area_error:
        evoapprox_area_error = [item for item in evoapprox_area_error if x_threshold <= item[1] <= max_error]

        evoapprox_areas = [item[0] for item in evoapprox_area_error]
        evoapprox_errors = [item[1] for item in evoapprox_area_error]
        all_areas.extend(evoapprox_areas)
        ax.plot(evoapprox_errors, evoapprox_areas, '^--', label='EVOApprox', color='red', markersize=10)

        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(evoapprox_errors):
            if evoapprox_areas[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='red')

    # Set labels and title
    ax.set_xlabel('ET', fontsize=24)
    ax.set_ylabel(r'Area ($\mu m^2$)', fontsize=24)
    plt.yticks(fontsize=24)
    plt.xticks(fontsize=22)
    # ax.set_title(f'{args.benchmark_name}', fontsize=26)
    ax.legend(fontsize=24)
    if all_global_ets[-1] > 1024:
        plt.xticks(rotation=30)
    # Set x-ticks to be the unique Local ET values

    # ax.set_xticks(all_global_ets)
    ax.set_xticks(list(range(max_error // 8, max_error + max_error // 8, max_error // 8)))

    # ax.set_xticklabels(all_global_ets)
    plt.tight_layout()

    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']

    figname = f'{folder}/{args.benchmark_name}_constants_pareto.png'
    plt.savefig(figname)


# =======================================

# Pareto Related ========================


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


def _pareto_front(points):
    # Sort the points by the first objective (area)
    points = sorted(points)

    # Initialize the Pareto front with the first point
    pareto = [points[0]]
    for point in points[1:]:

        # If the current point has a better local ET (second objective), add it to the Pareto front
        if point[1] < pareto[-1][1]:
            pareto.append(point)
    return pareto


def _pareto_front_with_et_coverage(points):
    # Sort the points first by ET and then by area
    points = sorted(points, key=lambda x: (x[1], x[0]))

    # Initialize the Pareto front list and a dictionary to track the minimum area for each ET
    pareto = []
    min_area_for_et = {}

    for point in points:
        area, et = point

        # If this is the first point with this ET, add it to the Pareto front
        if et not in min_area_for_et:
            pareto.append(point)
            min_area_for_et[et] = area
        else:
            # If the area is better than the stored one, update the Pareto front for this ET
            if area < min_area_for_et[et]:
                # Remove the old point with this ET from the Pareto front
                pareto = [p for p in pareto if p[1] != et]
                # Add the new point
                pareto.append(point)
                min_area_for_et[et] = area

    # Sort the final Pareto front by area for readability (optional)
    pareto = sorted(pareto, key=lambda x: (x[1], x[0]))

    return pareto


def _extract_pareto_front_from_mode_imax_omax_num_models(data):
    all_points = []
    # Traverse the nested dictionary to extract all (area, local ET) pairs
    for mode in data.values():
        for nm in mode.keys():
            if nm == 1:
                for num_models in mode[nm].values():
                    # print(f'{num_models = }')
                    for imax_omax in num_models.values():

                        for global_et in imax_omax:
                            # print(f'{global_et = }')
                            all_points.append(global_et)
    # Get the Pareto front from all points
    return _pareto_front(all_points)


def _extract_pareto_front_blasys(data):
    return _pareto_front(data)


def _extract_pareto_front_muscat(data):
    return _pareto_front_with_et_coverage(data)


def _identify_pareto(df):
    pareto_points = []
    for i in df.index:
        candidate = df.loc[i]
        if not ((df['Area'] < candidate['Area']) & (df['Local ET'] <= candidate['Local ET'])).any():
            pareto_points.append(candidate)
    return pd.DataFrame(pareto_points)


# =======================================


# MECALS ================================
def get_mecals_area_error(args, folder, synth: bool = False):
    area_error: List[Tuple[float, int]] = []
    relevant_files = _get_mecals_rel_files(args, folder, synth)

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


def _get_mecals_rel_files(args, folder, synth: bool = False):
    _fix_module_names(args, folder)
    # search the folder:
    if os.path.exists(folder):
        all_files = [f for f in os.listdir(folder)]
    else:
        return []
    relevant_files = []
    file_wce_dict = {}

    if not synth:

        for file in all_files:
            area_file = file[:-2] + '.area'
            if not os.path.exists(f'{folder}/{area_file}') and file.endswith('.v') and not re.search('pdk45', file):
                relevant_files.append(file)
                input_file = f'{folder}/{file}'
                temp_dir = f'{folder}'
                report_dir = f'{folder}'
                cur_wce = int(re.search('wce(\d+).', file).group(1))
                file_wce_dict[file] = cur_wce
                with open(f'{folder}/{file}', 'r') as f:
                    content = f.readlines()
                    if not content:
                        continue
                Synthesis.area(input_file, temp_dir, report_dir)

        all_areas = [f for f in os.listdir(folder)]

        for area in all_areas:
            if area.endswith('.area') and not re.search(r'_wce\d+', area):
                base_name = area.replace('.area', '')
                for file in file_wce_dict.keys():
                    if file.startswith(base_name):
                        os.rename(f'{folder}/{area}', f'{folder}/{base_name}_wce{file_wce_dict[file]}.area')
    relevant_files = []
    all_files = [f for f in os.listdir(folder)]
    for file in all_files:
        if file.endswith('.area'):
            relevant_files.append(file)

    return relevant_files


# BLASYS ================================
def get_blasys_area_error(args, folder):
    area_error: List[Tuple[float, int]] = []
    relevant_files = _get_blasys_rel_files(args, folder)

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


def _get_blasys_rel_files(args, folder):
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


# MUSCAT ================================


def _change_module_name_into(filename, new_module_name):
    """
    reads the Verilog file located at "filename", parses the module signature and substitutes the module's name with "new_module_name"
    Example:
    imaging the module signature of a Verilog file is as such:

    the contents of "filename"
    module adder_i4_o3(i0, i1, i2, i3, o0, o1, o2);
    ... the rest of the code
    endmodule;

    "new_module_name" is blahBlah
    and then, the file content will be changed as the following:
    module blahBlah(i0, i1, i2, i3, o0, o1, o2);
    ... the rest of the code
    endmodule;

    :return: None
    """
    old_module_name = None
    with open(filename, 'r') as dp:
        contents = dp.readlines()
        for idx, line in enumerate(contents):
            if re.search(r'module\s+(.*)\(', line):
                old_module_name = re.search(r'module\s+(.*)\(', line).group(1)
                contents[idx] = contents[idx].replace(old_module_name, new_module_name)
                break

    if old_module_name:
        # Write the modified contents back to the file
        with open(filename, 'w') as dp:
            dp.writelines(contents)


def _fix_module_names(args, folder):
    if os.path.exists(folder):
        all_files = [f for f in os.listdir(folder)]
    else:
        return

    for file in all_files:
        if file.endswith('.v') and not re.search('pdk45', file):
            input_file = f'{folder}/{file}'
            _change_module_name_into(input_file, file[:-2])


def _get_muscat_rel_files(args, folder, synth: bool = False):
    _fix_module_names(args, folder)
    # search the folder:

    if os.path.exists(folder):
        all_files = [f for f in os.listdir(folder)]
    else:
        return []

    relevant_files = []
    file_wce_dict = {}
    if not synth:

        for file in all_files:
            area_file = file[:-2] + '.area'
            if not os.path.exists(f'{folder}/{area_file}') and file.endswith('.v') and not re.search('pdk45', file):
                relevant_files.append(file)
                input_file = f'{folder}/{file}'
                temp_dir = f'{folder}'
                report_dir = f'{folder}'
                cur_wce = int(re.search('wc(\d+).', file).group(1))
                file_wce_dict[file] = cur_wce
                with open(f'{folder}/{file}', 'r') as f:
                    content = f.readlines()
                    if not content:
                        continue
                Synthesis.area(input_file, temp_dir, report_dir)

        all_areas = [f for f in os.listdir(folder)]
        for area in all_areas:
            if area.endswith('.area') and not re.search(r'_wc\d+', area):
                base_name = area.replace('.area', '')
                for file in file_wce_dict.keys():
                    if file.startswith(base_name):
                        os.rename(f'{folder}/{area}', f'{folder}/{base_name}_wce{file_wce_dict[file]}.area')
    relevant_files = []
    all_files = [f for f in os.listdir(folder)]
    for file in all_files:
        if file.endswith('.area'):
            relevant_files.append(file)

    return relevant_files


def get_muscat_area_error(args, folder, synth: bool = False):
    area_error: List[Tuple[float, int]] = []
    relevant_files = _get_muscat_rel_files(args, folder, synth)
    if relevant_files:
        for rep in relevant_files:
            with open(f'{folder}/{rep}', 'r') as f:
                cur_area = float(f.readline())
                cur_wce = int(re.search('wc(\d+).', rep).group(1))
                area_error.append((cur_area, cur_wce))
        sorted_area_error = sorted(area_error, key=lambda x: x[1])

        muscat_area_error_pareto = _extract_pareto_front_muscat(sorted_area_error)
        par_folder = f'pareto'
        os.makedirs(f'{folder}/{par_folder}', exist_ok=True)
        for point in muscat_area_error_pareto:
            wce = point[1]
            area = point[0]
            with open(f'{folder}/{par_folder}/axc_{args.benchmark_name}_wc{wce}.area', 'w') as p:
                p.write(f'{float(area)}')
        return sorted_area_error
    else:
        return []


# EVOApprox ================================
def _get_evoapprox_rel_files(args, folder, synth: bool = False):
    # search the folder:
    if os.path.exists(folder):
        all_files = [f for f in os.listdir(folder)]
    else:
        return []
    relevant_files = []
    file_wce_dict = {}
    if not synth:
        for file in all_files:
            if file.endswith('.v') and not re.search('pdk45', file):
                relevant_files.append(file)
                input_file = f'{folder}/{file}'
                temp_dir = f'{folder}'
                report_dir = f'{folder}'
                cur_wce = int(re.search('wce(\d+).', file).group(1))
                file_wce_dict[file] = cur_wce
                Synthesis.area(input_file, temp_dir, report_dir)

        all_areas = [f for f in os.listdir(folder)]
        for area in all_areas:
            if area.endswith('.area') and not re.search(r'_wce\d+', area):
                base_name = area.replace('.area', '')
                for file in file_wce_dict.keys():
                    if file.startswith(base_name):
                        os.rename(f'{folder}/{area}', f'{folder}/{base_name}_wce{file_wce_dict[file]}.area')
    relevant_files = []
    all_files = [f for f in os.listdir(folder)]
    for file in all_files:
        if file.endswith('.area'):
            relevant_files.append(file)

    return relevant_files


def get_evoapprox_area_error(args, folder, synth: bool = False):
    area_error: List[Tuple[float, int]] = []
    relevant_files = _get_evoapprox_rel_files(args, folder, synth)

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


# SubXPAT ==========================
def get_relevant_files(args: Arguments, folder):
    # search the folder:
    all_files = [f for f in os.listdir(folder)]
    relevant_files = []
    for file in all_files:
        if re.search(args.benchmark_name, file) and file.endswith('.csv'):
            relevant_files.append(file)
    return relevant_files


if __name__ == "__main__":
    main()
