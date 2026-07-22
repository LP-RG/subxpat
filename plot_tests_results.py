import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

def main():

    circuits = os.listdir("output")
    for circuit in circuits:

        path = f'output/{circuit}/run_stats.csv'
        if os.path.getsize(path) == 0:
            continue
        data = pd.read_csv(path)
        iterations = data['iteration'].tolist()
        legacy_time = data['legacy_labelling_time'].tolist()
        Z3_functional_time = data['Z3_functional_labelling_time'].tolist()
        Z3_direct_time = data['Z3_direct_labelling_time'].tolist()
        Z3_hybrid_time = data['Z3_hybrid_labelling_time'].tolist()
        Qbf_time = data['Qbf_labelling_time'].tolist()

        xpoints = iterations
        plt.title(f'Circuit {circuit}')
        plt.xlabel('Iterations')
        plt.ylabel("Labelling time")

        ypoints = np.array(legacy_time)
        plt.plot(xpoints, ypoints, color = 'b', label = 'Legacy encoder')
        ypoints = np.array(Z3_functional_time)
        plt.plot(xpoints, ypoints, color = 'r', label = 'Z3 functional encoder')
        ypoints = np.array(Z3_direct_time)
        plt.plot(xpoints, ypoints, color = 'g', label = 'Z3 direct encoder')
        ypoints = np.array(Z3_hybrid_time)
        plt.plot(xpoints, ypoints, color = 'c', label = 'Z3 hybrid encoder')
        ypoints = np.array(Qbf_time)
        plt.plot(xpoints, ypoints, color = 'm', label = 'Qbf encoder')

        plt.legend()
        plt.savefig(f'output/{circuit}/encoders_times_plot.png')
        plt.clf()

if __name__ == '__main__': main()