from typing import Any, Sequence
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import sys

def scatter_circuits(circuits: Sequence[Any], color_str: str, label_str: str, alpha_val: float) -> None:
    label = True
    for circuit in circuits:
        ypoints = circuit
        xpoints = [x for x in range(1, len(circuit) + 1)]
        plt.scatter(xpoints, ypoints, color = color_str, label = f'{'' if label else '_'}{label_str}', marker = 'o', alpha=alpha_val)
        label = False

def plot_encoder_circuits(circuits: Sequence[Any], color_str: str, label_str: str) -> None:
    plt.figure(dpi=1500) 
    plt.title(f'{label_str} circuits')
    plt.xlabel('Iterations')
    plt.ylabel("Labelling time")
    
    scatter_circuits(circuits, color_str, label_str, 1.0)

    plt.legend(bbox_to_anchor=(1.1, 1), loc=1)
    plt.grid(linestyle = '--', linewidth = 0.5)
    plt.yscale(value="log")
    plt.savefig(f'all_circuits_plots/{label_str.replace(" ", "_")}_circuits_times_plot.png')
    plt.clf()

def main():

    argv = sys.argv[1:]
    output_dir = "output"
    if len(argv) > 0:
        output_dir = argv[0]

    all_circuits_legacy_times : Sequence[Any] = list()
    all_circuits_Z3_functional_times : Sequence[Any] = list()
    all_circuits_Z3_direct_times : Sequence[Any] = list()
    all_circuits_Z3_hybrid_times : Sequence[Any] = list()
    all_circuits_Qbf_times : Sequence[Any] = list()

    os.makedirs("all_circuits_plots", exist_ok=True)

    circuits = os.listdir(output_dir)
    for circuit in circuits:

        path_details = f'{output_dir}/{circuit}/run_details.csv' #ensure computation for current circuit is done
        if os.path.getsize(path_details) == 0:
            continue
        data = pd.read_csv(path_details)
        exact_circuit_path : str = str(list(data)[1])
        exact_circuit_name : str = (exact_circuit_path.split('/')[2]).split('.')[0]

        path_stats = f'{output_dir}/{circuit}/run_stats.csv'
        data = pd.read_csv(path_stats)

        iterations = np.array(data['iteration'].unique().tolist())

        legacy_time = np.array(data['legacy_labelling_time'].unique().tolist())
        all_circuits_legacy_times.append(legacy_time)

        Z3_functional_time = np.array(data['Z3_functional_labelling_time'].unique().tolist())
        all_circuits_Z3_functional_times.append(Z3_functional_time)

        Z3_direct_time = np.array(data['Z3_direct_labelling_time'].unique().tolist())
        all_circuits_Z3_direct_times.append(Z3_direct_time)

        Z3_hybrid_time = np.array(data['Z3_hybrid_labelling_time'].unique().tolist())
        all_circuits_Z3_hybrid_times.append(Z3_hybrid_time)

        Qbf_time = np.array(data['Qbf_labelling_time'].unique().tolist())
        all_circuits_Qbf_times.append(Qbf_time)

        xpoints = iterations
        plt.title(f'Circuit {exact_circuit_name}')
        plt.xlabel('Iterations')
        plt.ylabel("Labelling time")

        ypoints = legacy_time
        plt.plot(xpoints, ypoints, color = 'b', label = 'Legacy encoder', marker = 'o')
        ypoints = Z3_functional_time
        plt.plot(xpoints, ypoints, color = 'r', label = 'Z3 functional encoder', marker = 'o')
        ypoints = Z3_direct_time
        plt.plot(xpoints, ypoints, color = 'g', label = 'Z3 direct encoder', marker = 'o')
        ypoints = Z3_hybrid_time
        plt.plot(xpoints, ypoints, color = 'c', label = 'Z3 hybrid encoder', marker = 'o')
        ypoints = Qbf_time
        plt.plot(xpoints, ypoints, color = 'm', label = 'Qbf encoder', marker = 'o')

        plt.legend()
        plt.grid(linestyle = '--', linewidth = 0.5)
        plt.savefig(f'{output_dir}/{circuit}/times_plot.png')
        plt.savefig(f'individual_circuits_plots/{exact_circuit_name}.png')
        plt.clf()
    
    plt.figure(dpi=1500) 
    plt.title(f'All circuits')
    plt.xlabel('Iterations')
    plt.ylabel("Labelling time")
    
    scatter_circuits(all_circuits_legacy_times, 'b', 'Legacy encoder', 0.5)
    scatter_circuits(all_circuits_Z3_functional_times, 'r', 'Z3 functional encoder', 0.5)
    scatter_circuits(all_circuits_Z3_direct_times, 'g', 'Z3 direct encoder', 0.5)
    scatter_circuits(all_circuits_Z3_hybrid_times, 'c', 'Z3 hybrid encoder', 0.5)
    scatter_circuits(all_circuits_Qbf_times, 'm', 'Qbf encoder', 0.5)

    plt.legend(bbox_to_anchor=(1.1, 1), loc=1)
    plt.grid(linestyle = '--', linewidth = 0.5)
    plt.yscale(value="log")
    plt.savefig(f'all_circuits_plots/all_circuits_times_plot.png')
    plt.clf()

    plot_encoder_circuits(all_circuits_legacy_times, 'b', 'Legacy encoder')
    plot_encoder_circuits(all_circuits_Z3_functional_times, 'r', 'Z3 functional encoder')
    plot_encoder_circuits(all_circuits_Z3_direct_times, 'g', 'Z3 direct encoder')
    plot_encoder_circuits(all_circuits_Z3_hybrid_times, 'c', 'Z3 hybrid encoder')
    plot_encoder_circuits(all_circuits_Qbf_times, 'm', 'Qbf encoder')

if __name__ == '__main__': main()