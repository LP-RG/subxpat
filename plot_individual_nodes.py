from typing import Any, Sequence, Dict
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import sys
import csv

solvers_dict =	{
  "legacy": ('Legacy encoder', 'b'),
  "func": ('Z3 functional encoder', 'r'),
  "dire": ('Z3 direct encoder', 'g'),
  "hybr": ('Z3 hybrid encoder', 'c'),
  "qbf": ('Qbf encoder', 'm')
}

def parse_data() -> Dict[int, Dict[str, Dict[int, float]]]:

    data : Dict[int, Dict[str, Dict[int, float]]] = {}
    with open('./individual_nodes_times.csv') as f:
        reader_obj = list(csv.reader(f))
        for row in reader_obj[1:]:
            iteration = int(row[0])
            node = int(row[1])
            solver = str(row[2])
            time = float(row[3])
            solvers = data.get(iteration) if data.get(iteration) else {}
            nodes = {}
            new_time = time
            if solvers.get(solver):
                nodes = solvers.get(solver)
                if nodes.get(node):
                    new_time += nodes.get(node)
            nodes[node] = new_time
            solvers[solver] = nodes
            data[iteration] = solvers
    
    return data

def main():
    os.makedirs("individual_nodes_plots", exist_ok=True)
    data = parse_data()

    argv = sys.argv[1:]
    iterations = []
    if len(argv) > 0:
        iterations = [int(argv[0])]
    else:
        iterations = list(dict.fromkeys(data.keys()))

    for iteration in iterations:
        plt.title(f'Iteration {iteration}')
        plt.xlabel('Nodes')
        plt.ylabel("Time (s)")

        for solver in data[iteration]:
            nodes = np.array(list(((data[iteration])[solver]).keys()))
            times = np.array(list(((data[iteration])[solver]).values()))

            xpoints = nodes
            ypoints = times
            plt.scatter(xpoints, ypoints, color = (solvers_dict[solver])[1], label = (solvers_dict[solver])[0], marker = 'o')

        plt.legend(bbox_to_anchor=(1.1, 0.45), loc=1)
        plt.grid(linestyle = '--', linewidth = 0.5)
        plt.savefig(f'individual_nodes_plots/iter{iteration}.png')
        plt.clf()

if __name__ == '__main__': main()