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

    folder = f'experiments/blasys/{args.benchmark_name}'
    blasys_area_error = get_blasys_area_error(args, folder)
    folder = f'experiments/blasys/runtimes'
    blasys_total_runtime = get_blasys_total_runtime(args, folder)

    muscat_area_error = {}
    muscat_number_of_models_array = [1, 10, 50, 100]
    for nm in muscat_number_of_models_array:
        folder = f'experiments/muscat/{args.benchmark_name}_{nm}'
        muscat_area_error[nm] = get_muscat_area_error(args, folder, False)




    folder = f'experiments/evoapprox/{args.benchmark_name}'
    evoapprox_area_error = get_evoapprox_area_error(args, folder, False)

    folder = 'experiments/results'
    rel_files = get_relevant_files(args, folder)

    area_error_per_imax_omax_per_num_models_mode = get_subgraph_area_per_mode_num_models_and_imax_omax(rel_files,
                                                                                                       folder)


    # uncomment for constant vs no constants available
    area_error_per_constants = get_subgraph_area_per_mode_num_models_and_imax_omax_constants(rel_files,folder)
    print(f'{ area_error_per_constants = }')

    # plot_area_constants_vs_no_constants(args, area_error_per_imax_omax_per_num_models_mode, area_error_per_constants,
    #                                     None, None, None, None)
    print(f'{mecals_area_error = }')
    print(f'{muscat_area_error = }')
    plot_area_constants_vs_no_constants(args, area_error_per_imax_omax_per_num_models_mode, area_error_per_constants, mecals_area_error, evoapprox_area_error, muscat_area_error, blasys_area_error)
    #
    print(f'Blah Blah')
    exit()


    subxpat_pareto = _extract_pareto_front_from_mode_imax_omax_num_models(area_error_per_imax_omax_per_num_models_mode)
    subxpat_pareto.sort(key = lambda x: x[1]) # sort ascending based on wce (i.e., et)

    # uncomment for preparing the inputs for auto table generation
    if muscat_area_error:
        muscat_pareto = {}
        for nm in muscat_number_of_models_array:
            muscat_pareto[nm] = _extract_pareto_front_muscat(muscat_area_error[nm])
            create_csv_table_tcad(args, f'experiments/muscat', muscat_pareto, 'muscat')
    if mecals_area_error:
        mecals_pareto = mecals_area_error
        create_csv_table_tcad(args, f'experiments/mecals', mecals_pareto, 'mecals')

    if evoapprox_area_error:
        evoapprox_pareto = evoapprox_area_error
        create_csv_table_tcad(args, f'experiments/evoapprox', evoapprox_pareto, 'evoapprox')

    create_csv_table_tcad(args, None, subxpat_pareto, 'subxpat', total_subxpat_time = total_subxpat_time)

    # exit()
    # uncomment for multi vs single

    # plot_report_subxpat_area_per_mode_and_imax_omax_all_models(args, area_error_per_imax_omax_per_num_models_mode)
    # plot_report_subxpat_area_per_mode_and_imax_omax_pareto_models(args, area_error_per_imax_omax_per_num_models_mode)



    # uncomment for subxpat vs soa comparison
    # area_error_per_imax_omax_per_mode = get_subgraph_area_per_mode_and_imax_omax(rel_files, folder)
    # plot_area_per_mode_and_imax_omax(args, area_error_per_imax_omax_per_num_models_mode, mecals_area_error, evoapprox_area_error, muscat_area_error, blasys_area_error)
    plot_area_per_mode_and_imax_omax_pareto(args, area_error_per_imax_omax_per_num_models_mode, mecals_area_error, evoapprox_area_error, muscat_area_error, blasys_area_error)

    # print(f'{total_runtime_per_config = }')
    # print(f'{total_runtime_per_config[1][(6, 3)] = }')
    # print(f'ratio = {round(total_runtime_per_config[50][(6, 3)]/ total_runtime_per_config[1][(6, 3)], 2)}')

    # exit()




    muscat_pareto, mecals_pareto, blasys_pareto, evoapprox_pareto = None, None, None, None

    if muscat_area_error:
        muscat_pareto = _extract_pareto_front_muscat(muscat_area_error)
    if mecals_area_error:
        mecals_pareto = mecals_area_error
    if blasys_area_error:
        blasys_pareto = blasys_area_error
    if evoapprox_area_error:
        evoapprox_pareto = evoapprox_area_error


    # percentage_better, average_improvement = compare_tools_avg(subxpat_pareto, muscat_pareto, 'MUSCAT')
    # percentage_better, max_improvement = compare_tools_best(subxpat_pareto, muscat_pareto, 'MUSCAT')
    # print(f'MUSCACT: {max_improvement = }')
    # # print(f'MUSCACT: {average_improvement = }')
    # percentage_better, average_improvement = compare_tools_avg(subxpat_pareto, mecals_pareto, 'MECALS')
    # percentage_better, max_improvement = compare_tools_best(subxpat_pareto, mecals_pareto, 'MECALS')
    # print(f'MECALS: {max_improvement = }')
    # # print(f'MECALS: {average_improvement = }')
    # percentage_better, average_improvement = compare_tools_avg(subxpat_pareto, blasys_pareto, 'BLASYS')
    # percentage_better, max_improvement = compare_tools_best(subxpat_pareto, blasys_pareto, 'BLASYS')
    # print(f'BLASYS: {max_improvement}')
    # percentage_better, average_improvement = compare_tools_avg(subxpat_pareto, evoapprox_pareto, 'EvoApprox')
    # percentage_better, max_improvement = compare_tools_best(subxpat_pareto, evoapprox_pareto, 'EvoApprox')
    # print(f'EvoApprox: {max_improvement}')





    # Extract data

    small_pair, medium_pair, large_pair, small_pair_data, medium_pair_data, large_pair_data = extract_specific_pairs(
        area_error_per_imax_omax_per_mode)
    # Plot the scatter plot
    plot_io_correlation(args, small_pair, medium_pair, large_pair, small_pair_data, medium_pair_data, large_pair_data, global_et= False)
    plot_io_correlation_null(args, small_pair, medium_pair, large_pair, small_pair_data, medium_pair_data, large_pair_data, global_et= False)


    # exit()
    # plot_io_correlation(args, smallest_pair, largest_pair, smallest_pair_data, largest_pair_data, global_et= True)
    #
    avg_correlation, weighted_avg_correlation, pareto_percentages = analyze_impact_of_configuration_on_area_decrease(args, small_pair_data, medium_pair_data, large_pair_data)



# ======= TCAD CSV table for latex table generation ==========
def create_csv_table_tcad(args: Arguments, folder, pareto_area_et, toolname, total_subxpat_time = None):
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

            row = ['total runtime (s)', f'{total_subxpat_time}' ]
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
            row = ['total runtime (s)', f'{total_time}' if total_time > 0 else 'n/a' ]
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
        if error in other_tool_dict or (error-1 in other_tool_dict and tool_name == 'MECALS'):
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
        if error in other_tool_dict or (error-1 in other_tool_dict and tool_name == 'MECALS'):
            if error-1 in other_tool_dict:
                other_error = error-1
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
                total_time += round(float(f.read())/60, 2)
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
def plot_io_correlation_null(args, small_pair, medium_pair, large_pair, small_pair_data, medium_pair_data, large_pair_data, global_et: bool = False):
    fig, ax = plt.subplots(figsize=(14, 10))

    plt.scatter([], [], color='blue', alpha=1)
    plt.text(0.5, 0.5, 'ToDo', fontsize=100, color='gray', alpha=0.3, ha='center', va='center', rotation=45, transform=plt.gca().transAxes)



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
    fig, ax = plt.subplots(figsize=(14, 10))

    # Plot data for the small imax, omax pair
    for et, area_local_et_pairs in small_pair_data.items():
        areas = [pair[0] for pair in area_local_et_pairs]
        if global_et:
            plt.scatter([et] * len(areas), areas, color='blue', alpha=1)
        else:
            ets = [pair[1] for pair in area_local_et_pairs]
            plt.scatter(ets, areas, color='blue', alpha=1)

    # Plot data for the medium imax, omax pair
    for et, area_local_et_pairs in medium_pair_data.items():
        areas = [pair[0] for pair in area_local_et_pairs]
        if global_et:
            plt.scatter([et] * len(areas), areas, color='green', alpha=1)
        else:
            ets = [pair[1] for pair in area_local_et_pairs]
            plt.scatter(ets, areas, color='green', alpha=1)

    # Plot data for the large imax, omax pair
    for et, area_local_et_pairs in large_pair_data.items():
        areas = [pair[0] for pair in area_local_et_pairs]
        if global_et:
            plt.scatter([et] * len(areas), areas, color='red', alpha=1)
        else:
            ets = [pair[1] for pair in area_local_et_pairs]
            plt.scatter(ets, areas, color='red', alpha=1)

    # Add legends for the three pairs
    plt.scatter([], [], color='blue', label=f'imax, omax = {small_pair}')
    plt.scatter([], [], color='green', label=f'imax, omax = {medium_pair}')
    plt.scatter([], [], color='red', label=f'imax, omax = {large_pair}')

    plt.xlabel('ET', fontsize=24)
    plt.ylabel(r'Area ($\mu m^2$)', fontsize=24)
    plt.yticks(fontsize=24)
    plt.xticks(fontsize=22)
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
                # print(f'{global_et = }')
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
    # print(f'{error_cell_dict_per_mode = }')
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


def get_area_error_per_mode_and_omax(relevant_files, folder):
    area_error_per_omax_per_mode: Dict = {}
    area_error_per_omax: Dict = {}
    area_error = []
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
                    area_error.append((et, runtime))

            if area_error:
                sorted_runtime_error = sorted(area_error, key=lambda x: x[0])
                area_error_per_omax[omax] = sorted_runtime_error
                area_error = []
        if area_error_per_omax:
            area_error_per_omax_per_mode[mode] = area_error_per_omax
            area_error_per_omax = {}

    return area_error_per_omax_per_mode


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
        for num_model in [1, 49]:
            for omax in range(10):
                for imax in range(10):
                    for rep in relevant_files:
                        sorted_cur_area_error = []
                        cur_area_error = []
                        if re.search(f'num_models{num_model}_', rep) and not re.search('constalways', rep):
                            if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(f'imax{imax}_', rep) and re.search(f'num_models{num_model}_', rep):

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
                        else:
                            if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(f'imax{imax}_', rep) and not re.search(f'num_models\d+', rep):
                                # print(f'Here')
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
                                    sorted_cur_area_error = []


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

def get_subgraph_area_per_mode_and_imax_omax(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    area_error = {}
    cur_area_error = []
    for mode in range(200):
        for omax in range(10):
            for imax in range(10):
                for rep in relevant_files:
                    sorted_cur_area_error = []
                    cur_area_error = []
                    if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(f'imax{imax}_', rep):
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
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax
            runtime_error_per_omax = {}
    return runtime_error_per_omax_per_mode

def get_subgraph_extraction_runtime_per_mode_and_imax_omax(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    runtime_error = []
    for mode in range(200):
        for omax in range(10):
            for imax in range(10):
                for rep in relevant_files:
                    iterations = []
                    runtime = 0
                    if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(f'imax{imax}_', rep):
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
                    runtime_error_per_omax[(imax, omax)] = sorted_runtime_error
                    runtime_error = []
        if runtime_error_per_omax:
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax
            runtime_error_per_omax = {}

    return runtime_error_per_omax_per_mode


def get_total_runtime_per_mode_num_models_and_imax_omax(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    runtime_error_per_omax_num_models: Dict = {}
    runtime_error = []
    for mode in range(200):
        for num_model in [1, 49]:
            for omax in range(10):
                for imax in range(10):
                    for rep in relevant_files:
                        iterations = []
                        runtime = 0
                        if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(f'imax{imax}_', rep):
                            et = int(re.search(f'et(\d+)_', rep).group(1))
                            with open(f'{folder}/{rep}', 'r') as f:
                                csvreader = csv.reader(f)
                                for line in csvreader:
                                    if line[0].startswith('cell'):  # skip the first line
                                        continue
                                    else:
                                        if line[3].startswith('UNSAT'):
                                            exploration = float(line[15])
                                            runtime += exploration
                                        elif line[3].startswith('SAT'):
                                            cur_iter = int(line[1])
                                            if cur_iter not in iterations:
                                                iterations.append(cur_iter)
                                                labeling = float(line[9])
                                                subgraph_extraction = float(line[10])
                                                exploration = float(line[15])
                                                runtime += subgraph_extraction + labeling + exploration
                            runtime_error.append((et, runtime))

                    if runtime_error:
                        sorted_runtime_error = sorted(runtime_error, key=lambda x: x[0])
                        runtime_error_per_omax[(imax, omax)] = sorted_runtime_error
                        runtime_error = []
            if runtime_error_per_omax:
                runtime_error_per_omax_num_models[num_model] = runtime_error_per_omax
                runtime_error_per_omax = {}
        if runtime_error_per_omax_num_models:
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax_num_models
            runtime_error_per_omax_num_models = {}

    return runtime_error_per_omax_per_mode

def get_total_runtime_per_mode_and_imax_omax(relevant_files, folder):
    runtime_error_per_omax_per_mode: Dict = {}
    runtime_error_per_omax: Dict = {}
    runtime_error = []
    for mode in range(200):
        for omax in range(10):
            for imax in range(10):
                for rep in relevant_files:
                    iterations = []
                    runtime = 0
                    if re.search(f'mode{mode}_', rep) and re.search(f'omax{omax}_', rep) and re.search(f'imax{imax}_', rep):
                        et = int(re.search(f'et(\d+)_', rep).group(1))
                        with open(f'{folder}/{rep}', 'r') as f:
                            csvreader = csv.reader(f)
                            for line in csvreader:
                                if line[0].startswith('cell'):  # skip the first line
                                    continue
                                else:
                                    if line[3].startswith('UNSAT'):
                                        exploration = float(line[15])
                                        runtime += exploration
                                    elif line[3].startswith('SAT'):
                                        cur_iter = int(line[1])
                                        if cur_iter not in iterations:
                                            iterations.append(cur_iter)
                                            labeling = float(line[9])
                                            subgraph_extraction = float(line[10])
                                            exploration = float(line[15])
                                            runtime += subgraph_extraction + labeling + exploration
                        runtime_error.append((et, runtime))

                if runtime_error:
                    sorted_runtime_error = sorted(runtime_error, key=lambda x: x[0])
                    runtime_error_per_omax[(imax, omax)] = sorted_runtime_error
                    runtime_error = []
        if runtime_error_per_omax:
            runtime_error_per_omax_per_mode[mode] = runtime_error_per_omax
            runtime_error_per_omax = {}

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


def plot_area_constants_vs_no_constants(args, area_error_per_imax_omax_per_mode = None, area_error_constants = None, mecals_area_error = None,
                                     evoapprox_area_error = None,
                                     muscat_area_error = None,
                                     blasys_area_error = None):
    fig, ax = plt.subplots(figsize=(14, 10))


    max_error = 2 ** (int(re.search('_o(\d+)', args.benchmark_name).group(1)) - 1)
    x_threshold = max_error // 8
    print(f'{x_threshold = }')
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
        # pareto_points = [item for item in pareto_points if x_threshold - 1 <= item[1] <= max_error]
        pareto_points = [item for item in pareto_points if item[1] ]
        pareto_area = [item[0] for item in pareto_points]
        pareto_error = [item[1] for item in pareto_points]
        ax.plot(pareto_error, pareto_area, 'o--', label='SubXPAT', color='blue', markersize=10)
        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(pareto_error):
            if pareto_area[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='blue', linewidth=3)

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
            ax.plot(muscat_errors, muscat_areas, 'd--', label=f'MUSCAT {nm} models', color=muscat_colors[nm],
                    markersize=muscat_size[nm])
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

    if area_error_constants:
        for mode in area_error_constants.keys():
            print(f'{mode = }')
            for nm in area_error_constants[mode].keys():
                print(f'{nm = }')
                for (imax, omax) in area_error_constants[mode][nm].keys():
                    print(f'{(imax, omax) = }')
        pareto_points = _extract_pareto_front_from_mode_imax_omax_num_models(area_error_constants)
        print(f'{pareto_points = }')
        # pareto_points = [item for item in pareto_points if x_threshold - 1 <= item[1] <= max_error]
        pareto_points = [item for item in pareto_points if item[1]]
        pareto_area = [item[0] for item in pareto_points]


        pareto_error = [item[1] for item in pareto_points]
        print(f'{pareto_error = }')
        ax.plot(pareto_error, pareto_area, 'X--', label='SubXPAT-Constants', color='purple', markersize=14, alpha=0.8)
        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(pareto_error):
            if pareto_area[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='purple', linewidth=3)


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
    print(f'{all_global_ets = }')
    if all_global_ets[-1] > 1024:
        plt.xticks(rotation=30)
    # Set x-ticks to be the unique Local ET values

    # ax.set_xticks(all_global_ets)
    print(f'{max_error = }')
    ax.set_xticks(list(range(max_error // 8, max_error + max_error // 8, max_error // 8)))

    # ax.set_xticklabels(all_global_ets)
    plt.tight_layout()

    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']

    figname = f'{folder}/{args.benchmark_name}_constants_pareto.png'
    plt.savefig(figname)


def plot_area_per_mode_and_imax_omax(args, area_error_per_imax_omax_per_mode, mecals_area_error = None,
                                     evoapprox_area_error = None,
                                     muscat_area_error = None,
                                     blasys_area_error = None):
    fig, ax = plt.subplots(figsize=(14, 10))

    max_error = 2 ** (int(re.search('_o(\d+)', args.benchmark_name).group(1)) - 1)
    x_threshold = max_error // 8
    # Calculate the number of unique labels (mode, (imax, omax) pairs)
    unique_labels = [(mode, (imax, omax)) for mode in area_error_per_imax_omax_per_mode
                                          for num_model in area_error_per_imax_omax_per_mode[mode]
                                          for (imax, omax) in area_error_per_imax_omax_per_mode[mode][num_model]]
    num_unique_labels = len(unique_labels)
    # Generate as many colors as unique labels
    colormap = plt.cm.get_cmap("tab20b")
    colors = [colormap(i % 20) for i in range(num_unique_labels + num_unique_labels)]

    color_idx = 0
    all_local_ets = []
    all_global_ets = []
    for mode, num_model_dict in area_error_per_imax_omax_per_mode.items():

        for num_model, imax_omax_dict in num_model_dict.items():
            for (imax, omax), et_dict in imax_omax_dict.items():
                # print(f'{et_dict = }')
                for global_et, area_local_et_list in et_dict.items():
                    # print(f'{global_et = }')
                    areas, local_ets = zip(*area_local_et_list)
                    all_local_ets.extend(local_ets)
                    all_global_ets.append(global_et)
                    ax.scatter(local_ets, areas, color=colors[color_idx], alpha=0.6, s=70)

                ax.scatter([], [], color=colors[color_idx],
                           label=f'SubXPAT (imax, omax) = ({imax}, {omax})', s=100)  # Empty scatter for legend
                color_idx += 2

    if mecals_area_error:
        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]
        ax.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black', markersize=10)
    if evoapprox_area_error:
        evoapprox_areas = [item[0] for item in evoapprox_area_error]
        evoapprox_errors = [item[1] for item in evoapprox_area_error]
        ax.plot(evoapprox_errors, evoapprox_areas, '^--', label='EVOApprox', color='red', markersize=10)
    if muscat_area_error:
        muscat_area_error_pareto = _extract_pareto_front_muscat(muscat_area_error)
        muscat_area_error_pareto = [item for item in muscat_area_error_pareto if x_threshold <= item[1] <= max_error]
        muscat_areas = [item[0] for item in muscat_area_error_pareto]
        muscat_errors = [item[1] for item in muscat_area_error_pareto]
        ax.plot(muscat_errors, muscat_areas, 'd--', label='MUSCAT', color='green', markersize=10)
    # if blasys_area_error:
    #     blasys_area_error_pareto = _extract_pareto_front_blasys(blasys_area_error)
    #     blasys_areas = [item[0] for item in blasys_area_error_pareto]
    #     blasys_errors = [item[1] for item in blasys_area_error_pareto]
    #     ax.plot(blasys_errors, blasys_areas, 'x--', label='BLASYS', color='violet', markersize=10)

    ax.set_xlabel('ET', fontsize=24)
    ax.set_ylabel(r'Area ($\mu m^2$)', fontsize=24)
    plt.yticks(fontsize=24)
    plt.xticks(fontsize=22)
    # ax.set_title(f'{args.benchmark_name}', fontsize=26)
    ax.legend(fontsize=24)
    print(f'{all_global_ets = }')
    if all_global_ets[-1] > 1024:
        plt.xticks(rotation=30)
    # Set x-ticks to be the unique Local ET values

    all_global_ets = sorted(set(all_global_ets))
    ax.set_xticks(all_global_ets)
    ax.set_xticklabels(all_global_ets)
    plt.tight_layout()

    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']

    figname = f'{folder}/{args.benchmark_name}_imax_omax_area.png'
    plt.savefig(figname)


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




def plot_report_subxpat_area_per_mode_and_imax_omax_all_models(args, area_error_per_imax_omax_per_num_models_mode):
    model_marker = {
        1: 'x',
        50: 'o'
    }
    model_size = {
        1: 44,
        50: 34
    }

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_title(f'{args.benchmark_name} Scatter Plot of Area-ET for different number of models', fontsize=24)
    ax.set_xlabel('ET', fontsize=24)
    ax.set_ylabel(r'Area ($\mu m^2$)', fontsize=24)
    plt.yticks(fontsize=24)
    plt.xticks(fontsize=22)

    area_error_per_num_models_imax_omax = {}

    for mode in area_error_per_imax_omax_per_num_models_mode.keys():
        for num_model in area_error_per_imax_omax_per_num_models_mode[mode].keys():
            for (imax, omax), area_error_dict in area_error_per_imax_omax_per_num_models_mode[mode][num_model].items():
                area_error_per_num_models_imax_omax[(mode, num_model, imax, omax)] = []
                for error in area_error_dict.keys():
                    area_error_per_num_models_imax_omax[(mode, num_model, imax, omax)].extend(area_error_dict[error])


    for curve in area_error_per_num_models_imax_omax.keys():
        cur_area_list = [area for area, _ in area_error_per_num_models_imax_omax[curve]]
        cur_error_list = [error for _, error in area_error_per_num_models_imax_omax[curve]]
        ax.scatter(cur_error_list, cur_area_list, label=f'(mode, #models, imax, omax) = {curve}', s=model_size[curve[1]], marker=model_marker[curve[1]])

    plt.tight_layout()
    ax.legend(fontsize=24)
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']
    figname = f'{folder}/{args.benchmark_name}_multi_vs_single_({imax},{omax})_all_models.png'
    plt.savefig(figname)
    plt.close()





def plot_report_subxpat_area_per_mode_and_imax_omax_pareto_models(args, area_error_per_imax_omax_per_num_models_mode):


    pareto_num_models_dict = {}
    imax_omax_array = []
    num_models_pareto_points = {}
    imax_omax_pareto_points = {}
    if area_error_per_imax_omax_per_num_models_mode:
        for mode in area_error_per_imax_omax_per_num_models_mode.keys():
            for num_models in area_error_per_imax_omax_per_num_models_mode[mode].keys():

                pareto_num_models_dict[num_models] = {}
                for (imax, omax) in area_error_per_imax_omax_per_num_models_mode[mode][num_models].keys():
                    pareto_num_models_dict[num_models][(imax, omax)] = []

        common_keys = set(pareto_num_models_dict[next(iter(pareto_num_models_dict))].keys())
        for sub_dict in pareto_num_models_dict.values():
            common_keys &= set(sub_dict.keys())
        for key in pareto_num_models_dict:
            pareto_num_models_dict[key] = {k: pareto_num_models_dict[key][k] for k in common_keys}


        for mode, num_models_dict in area_error_per_imax_omax_per_num_models_mode.items():
            for num_models, imax_omax_dict in num_models_dict.items():
                for (imax, omax), et_dict in imax_omax_dict.items():
                    cur_list = []
                    for global_et, area_local_et_list in et_dict.items():
                        cur_list = cur_list + area_local_et_list


                    cur_list.sort(key=lambda x: x[1])
                    pareto_num_models_dict[num_models][(imax, omax)] = _pareto_front(cur_list)

        model_marker = {
            1: 'o--',
            50: 'o--'
        }
        model_size= {
            1: 12,
            50: 8
        }
        # print(f'{common_keys = }')

        metrics_data = []

        for (imax, omax) in common_keys:
            fig, ax = plt.subplots(figsize=(14, 10))
            ax.set_title(f'{args.benchmark_name} {(imax, omax)}', fontsize=24)
            ax.set_xlabel('ET', fontsize=24)
            ax.set_ylabel(r'Area ($\mu m^2$)', fontsize=24)
            plt.yticks(fontsize=24)
            plt.xticks(fontsize=22)

            # Extract points for num_models=1 and num_models=50
            areas_1, ets_1 = zip(*pareto_num_models_dict[1][(imax, omax)])
            areas_50, ets_50 = zip(*pareto_num_models_dict[50][(imax, omax)])

            # Find common ET points
            common_ets = set(ets_1).intersection(set(ets_50))
            # Filter areas based on common ETs
            areas_1_filtered = [area for area, et in zip(areas_1, ets_1) if et in common_ets]
            areas_50_filtered = [area for area, et in zip(areas_50, ets_50) if et in common_ets]

            count_1_better = sum(a1 < a50 for a1, a50 in zip(areas_1_filtered, areas_50_filtered))
            count_50_better = len(areas_1_filtered) - count_1_better
            if areas_1_filtered == 0:
                pass
            if areas_50_filtered == 0:
                pass
            efficiency_percentage_1 = (count_1_better / len(areas_1_filtered)) * 100
            efficiency_percentage_50 = (count_50_better / len(areas_1_filtered)) * 100
            # Area reduction and error reduction calculations
            area_reduction_percentages = [
                ((a1 - a50) / a1) * 100 for a1, a50 in zip(areas_1_filtered, areas_50_filtered) if a1 != 0
            ]
            error_reduction_percentages = [
                ((et1 - et50) / et1) * 100 for et1, et50 in zip(ets_1, ets_50) if et1 in common_ets and et1 != 0
            ]

            if len(area_reduction_percentages) == 0:
                average_area_reduction = '-'
            else:
                average_area_reduction = sum(area_reduction_percentages) / len(area_reduction_percentages)
            if len(error_reduction_percentages) == 0:
                average_error_reduction = '-'
            else:
                average_error_reduction = sum(error_reduction_percentages) / len(error_reduction_percentages)

            # Store metrics data
            metrics_data.append({
                'imax_omax': (imax, omax),
                'efficiency_percentage_1': round(efficiency_percentage_1, 2),
                'efficiency_percentage_50': round(efficiency_percentage_50, 2),
                'average_area_reduction_at_same_error (when increasing)': '-' if average_area_reduction == '-' else round(average_area_reduction,2) ,
                'average_error_reduction_at_same_area (when increasing)': '-' if average_error_reduction == '-' else round(average_error_reduction,2)
            })

            for num_models in pareto_num_models_dict:
                # print(f'{pareto_num_models_dict[num_models][(imax, omax)] = }')
                areas = [area for area, _ in pareto_num_models_dict[num_models][(imax, omax)]]
                ets = [error for _, error in pareto_num_models_dict[num_models][(imax, omax)]]

                ax.plot(ets, areas, model_marker[num_models], markersize=model_size[num_models], label=f'#models={num_models}, {imax, omax}')
            plt.tight_layout()
            ax.legend(fontsize=24)
            plt.grid(True)
            folder, _ = OUTPUT_PATH['figure']
            figname = f'{folder}/{args.benchmark_name}_multi_vs_single_({imax},{omax})_pareto.png'
            plt.savefig(figname)
            plt.close()
            print(f'We are here!!!')
            metrics_df = pd.DataFrame(metrics_data)
              # Assuming a similar folder structure for CSV output
            csv_filename = f'output/report/{args.benchmark_name}_single_vs_multi.csv'
            metrics_df.to_csv(csv_filename, index=False)
            print(f"Metrics saved to {csv_filename}")

            # # Print metrics in a tabular format
            # print("Performance Metrics:")
            # print(
            #     "| (imax, omax) | Efficiency (num_models=1) (%) | Efficiency (num_models=50) (%) | Area Reduction (%) | Error Reduction (%) |")
            # print(
            #     "|--------------|--------------------------------|--------------------------------|-------------------|-------------------|")
            # for data in metrics_data:
            #     print(
            #         f"| {data['imax_omax']} | {data['efficiency_percentage_1']:.2f} | {data['efficiency_percentage_50']:.2f} | {data['average_area_reduction_at_same_error (when increasing)']:.2f} | {data['average_error_reduction_at_same_area (when increasing)']:.2f} |")


def plot_area_per_mode_and_imax_omax_pareto(args, area_error_per_imax_omax_per_mode, mecals_area_error = None,
                                     evoapprox_area_error = None,
                                     muscat_area_error = None,
                                     blasys_area_error = None,
                                     stretched: bool = True):
    fig, ax = plt.subplots(figsize=(14, 10))

    max_error = 2 ** (int(re.search('_o(\d+)', args.benchmark_name).group(1)) - 1)
    x_threshold = max_error // 8

    all_local_ets = []
    all_global_ets = []
    all_areas = []
    print(f'{area_error_per_imax_omax_per_mode = }')
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
        pareto_points = [item for item in pareto_points if  x_threshold <= item[1] <= max_error]
        pareto_area = [item[0] for item in pareto_points]
        pareto_error = [item[1] for item in pareto_points]
        ax.plot(pareto_error, pareto_area, 'o--', label='SubXPAT', color='blue', markersize=10)
        # zero expansion of the line
        zero_exapnsion_errors = []
        for idx, error in enumerate(pareto_error):
            if pareto_area[idx] == 0:
                zero_exapnsion_errors.append(error)
        zero_exapnsion_errors.append(max_error)
        ax.plot(zero_exapnsion_errors, [0] * len(zero_exapnsion_errors), '--', color='blue', linewidth=3)


    if muscat_area_error:
        muscat_number_of_models_array = list(muscat_area_error.keys())
        muscat_colors = {
            1: 'green',
            10: 'olive',
            50: 'orange',
            100: 'lawngreen'
        }
        for nm in muscat_number_of_models_array:
            muscat_area_error_pareto = _extract_pareto_front_muscat(muscat_area_error[nm])
            muscat_area_error_pareto = [item for item in muscat_area_error_pareto if x_threshold  <= item[1] <= max_error]

            muscat_areas = [item[0] for item in muscat_area_error_pareto]
            muscat_errors = [item[1] for item in muscat_area_error_pareto]
            all_areas.extend(muscat_areas)
            ax.plot(muscat_errors, muscat_areas, 'd--', label=f'MUSCAT {nm} models', color = muscat_colors[nm], markersize=10)
    if mecals_area_error:
        print(f'{mecals_area_error = }')
        mecals_area_error = [item for item in mecals_area_error if item[1] >= (x_threshold - 1)]

        mecals_areas = [item[0] for item in mecals_area_error]
        mecals_errors = [item[1] for item in mecals_area_error]
        all_areas.extend(mecals_areas)
        ax.plot(mecals_errors, mecals_areas, 's--', label='MECALS', color='black', markersize=10)

    if blasys_area_error:
        blasys_area_error_pareto = _extract_pareto_front_blasys(blasys_area_error)
        blasys_area_error_pareto = [(area, wae) for area, wae in blasys_area_error_pareto if x_threshold <= wae <= max_error]

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
    print(f'{all_global_ets = }')
    if all_global_ets[-1] > 1024:
        plt.xticks(rotation=30)
    # Set x-ticks to be the unique Local ET values





    # ax.set_xticks(all_global_ets)
    print(f'{max_error = }')
    ax.set_xticks(list(range(max_error//8, max_error + max_error//8, max_error//8)))

    # ax.set_xticklabels(all_global_ets)
    plt.tight_layout()






    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']

    figname = f'{folder}/{args.benchmark_name}_area_pareto.png'
    plt.savefig(figname)

def plot_runtime_per_mode_and_imax_omax(args, runtime_error_per_omax_per_mode):
    # print(f'{runtime_error_per_omax_per_mode = }')
    # plt.figure(figsize=(10, 6))
    # plt.title(f'{args.benchmark_name} runtime')
    # marker = itertools.cycle(('D', 'o', 'X', 's'))
    #
    # for mode in runtime_error_per_omax_per_mode.keys():
    #     for omax in runtime_error_per_omax_per_mode[mode].keys():
    #         errors = [item[0] for item in runtime_error_per_omax_per_mode[mode][omax]]
    #         runtimes = [item[1] for item in runtime_error_per_omax_per_mode[mode][omax]]
    #         plt.plot(errors, runtimes, marker=next(marker), label=f'mode{mode}, omax{omax}', alpha=1)

    fig, ax = plt.subplots(figsize=(14, 7))
    bar_width = 0.1  # Width of the bars
    total_bars = sum(len(imax_omax_dict) for imax_omax_dict in runtime_error_per_omax_per_mode.values())
    colors = plt.cm.viridis(np.linspace(0, 1, total_bars))

    # Create a counter for the color and bar positions
    color_idx = 0

    # Determine the number of ET values from the first mode and first (imax, omax) pair
    first_mode = next(iter(runtime_error_per_omax_per_mode.values()))
    first_imax_omax = next(iter(first_mode.values()))
    num_ets = len(first_imax_omax)
    bar_positions = np.arange(num_ets)

    for idx, (mode, imax_omax_dict) in enumerate(runtime_error_per_omax_per_mode.items()):
        for (imax, omax), et_runtime_list in imax_omax_dict.items():
            ets, runtimes = zip(*et_runtime_list)
            positions = bar_positions + color_idx * bar_width  # Offset each group's bars
            ax.bar(positions, runtimes, width=bar_width, label=f'Mode {mode}, (imax, omax) = ({imax}, {omax})',
                   color=colors[color_idx])
            color_idx += 1


    plt.legend()
    plt.xlabel('ET')
    plt.ylabel('Runtime')
    plt.title(f'{args.benchmark_name}', size=20)
    ax.set_xticks(np.arange(len(ets)))
    ax.set_xticklabels(ets)
    plt.grid(True)
    folder, _ = OUTPUT_PATH['figure']

    figname = f'{folder}/{args.benchmark_name}_imax_omax_runtime.png'
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







# Others

# MECALS ================================
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

def get_muscat_area_error(args, folder,  synth: bool = False):
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

def get_evoapprox_area_error(args, folder, synth : bool = False):
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