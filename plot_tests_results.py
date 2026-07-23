from typing import Any, Sequence
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

def scatter_circuits(circuits: Sequence[Any], color_str: str, label_str: str) -> None:
    label = True
    for circuit in circuits:
        ypoints = circuit
        xpoints = [x for x in range(1, len(circuit) + 1)]
        plt.scatter(xpoints, ypoints, color = color_str, label = f'{'' if label else '_'}{label_str}', marker = 'o')
        label = False

def plot_encoder_circuits(circuits: Sequence[Any], color_str: str, label_str: str) -> None:
    plt.figure(dpi=1500) 
    plt.title(f'{label_str} circuits')
    plt.xlabel('Iterations')
    plt.ylabel("Labelling time")
    
    scatter_circuits(circuits, color_str, label_str)

    plt.legend(bbox_to_anchor=(1.1, 1), loc=1)
    plt.grid(linestyle = '--', linewidth = 0.5)
    plt.yscale(value="log")
    plt.savefig(f'all_circuits_plots/{label_str.replace(" ", "_")}_circuits_times_plot.png')
    plt.clf()

def main():

    all_circuits_legacy_times : Sequence[Any] = list()
    all_circuits_Z3_functional_times : Sequence[Any] = list()
    all_circuits_Z3_direct_times : Sequence[Any] = list()
    all_circuits_Z3_hybrid_times : Sequence[Any] = list()
    all_circuits_Qbf_times : Sequence[Any] = list()

    os.makedirs("all_circuits_plots", exist_ok=True)

    circuits = os.listdir("output")
    for circuit in circuits:

        path = f'output/{circuit}/run_stats.csv'
        if os.path.getsize(path) == 0:
            continue
        data = pd.read_csv(path)

        iterations = np.unique(np.array(data['iteration'].tolist()))
        legacy_time = np.unique(np.array(data['legacy_labelling_time'].tolist()))
        all_circuits_legacy_times.append(legacy_time)
        Z3_functional_time = np.unique(np.array(data['Z3_functional_labelling_time'].tolist()))
        all_circuits_Z3_functional_times.append(Z3_functional_time)
        Z3_direct_time = np.unique(np.array(data['Z3_direct_labelling_time'].tolist()))
        all_circuits_Z3_direct_times.append(Z3_direct_time)
        Z3_hybrid_time = np.unique(np.array(data['Z3_hybrid_labelling_time'].tolist()))
        all_circuits_Z3_hybrid_times.append(Z3_hybrid_time)
        Qbf_time = np.unique(np.array(data['Qbf_labelling_time'].tolist()))
        all_circuits_Qbf_times.append(Qbf_time)

        xpoints = iterations
        plt.title(f'Circuit {circuit}')
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
        plt.savefig(f'output/{circuit}/times_plot.png')
        plt.clf()
    
    plt.figure(dpi=1500) 
    plt.title(f'All circuits')
    plt.xlabel('Iterations')
    plt.ylabel("Labelling time")
    
    scatter_circuits(all_circuits_legacy_times, 'b', 'Legacy encoder')
    scatter_circuits(all_circuits_Z3_functional_times, 'r', 'Z3 functional encoder')
    scatter_circuits(all_circuits_Z3_direct_times, 'g', 'Z3 direct encoder')
    scatter_circuits(all_circuits_Z3_hybrid_times, 'c', 'Z3 hybrid encoder')
    scatter_circuits(all_circuits_Qbf_times, 'm', 'Qbf encoder')

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