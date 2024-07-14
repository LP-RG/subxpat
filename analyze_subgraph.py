import os
import csv
import pandas as pd
import re
import matplotlib.pyplot as plt

def main():
    directory = 'new_subgraph_extraction/reports/'

    # List to hold DataFrames
    dataframes = []
    dataframes_dict = {}
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):

            df = pd.read_csv(os.path.join(directory, filename), sep=',')
            dataframes_dict[filename]  =  df

    benchmarks = []
    modes = []
    ets = []

    all_dict = {}
    for el in dataframes_dict.keys():

        benchmark = re.search('(.*)_mode5.*', el).group(1)
        mode = int(re.search('mode(\d+)_', el).group(1))
        et = int(re.search('et(\d+)_', el).group(1))
        solver_time = dataframes_dict[el]['solver time'][0]
        total = dataframes_dict[el]['total'][0]
        if benchmark not in all_dict.keys():
            all_dict[benchmark] = {}
        if mode not in all_dict[benchmark].keys():
            all_dict[benchmark][mode] = {}
        if et not in all_dict[benchmark][mode].keys():
            all_dict[benchmark][mode][et] = {}
        all_dict[benchmark][mode][et] = (solver_time, total)

    plot_dict(all_dict)



def plot_dict(all_dict):
    color_map = {
        51: 'blue',
        53: 'red',
        54: 'green',
        55: 'orange'

        # Add more modes and their respective colors as needed
    }
    for benchmark, modes in all_dict.items():
        plt.figure(figsize=(10, 6))
        for mode, ets_dict in modes.items():
            ets_sorted = sorted(ets_dict.keys())
            solver_times = [ets_dict[et][0] for et in ets_sorted]
            total_times = [ets_dict[et][1] for et in ets_sorted]
            color = color_map.get(mode, 'black')
            plt.plot(ets_sorted, solver_times, label=f'Mode {mode}', marker='o', color=color)
            plt.plot(ets_sorted, total_times, linestyle='--', label=f'Total Time (Mode {mode})', color=color)

        if 51 in modes and 53 in modes:
            for ets in ets_sorted:
                if ets in modes[51] and ets in modes[53]:
                    solver_time_51 = modes[51][ets][0]
                    solver_time_53 = modes[53][ets][0]
                    percentage_faster = ((solver_time_51 - solver_time_53) / solver_time_51) * 100
                    plt.annotate(f'{percentage_faster:.1f}%', (ets, (solver_time_51 + solver_time_53) / 2),
                                 textcoords="offset points", xytext=(0, 10), ha='center', color='green', fontsize=9)

        plt.xlabel('ET')
        plt.ylabel('Solver Time')
        plt.title(f'Solver Time vs ET for {benchmark}')
        plt.legend()
        plt.xscale('log')
        plt.grid(True)
        figname = f'{benchmark}.png'
        plt.savefig(figname)

if __name__ == "__main__":
    main()
