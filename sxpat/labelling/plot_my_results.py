import json
import os
import matplotlib.pyplot as plt
import numpy as np

BASE_PATH = os.path.join('sxpat', 'labelling')
DATA_DIR = os.path.join(BASE_PATH, 'weight_outputs')
SAVE_DIR = os.path.join(BASE_PATH, 'graph_outputs')

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def get_data(alg, circuit):
    path = os.path.join(DATA_DIR, f"results_{alg}_{circuit}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def plot_top_left(circuit_name):
    """Figure 1: Node Weight Comparison (View all algorithms together) """
    plt.figure(figsize=(10, 6))
    algs = ['sum', 'pp', 'spp']
    
    ref_data = get_data('spp', circuit_name)
    if not ref_data: 
        return
    
    sorted_node_ids = sorted(ref_data['weights'].keys(), key=lambda x: ref_data['weights'][x])
    
    for alg in algs:
        data = get_data(alg, circuit_name)
        if data:
            y_vals = [data['weights'].get(nid, 0) for nid in sorted_node_ids]
            plt.plot(range(len(y_vals)), y_vals, label=alg.upper(), alpha=0.8)

    plt.yscale('log')
    plt.xlabel('Nodes (sorted by SPP weight)')
    plt.ylabel('Computed Weight')
    plt.title(f'Top-Left: Weight Comparison ({circuit_name})')
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.3)
    
    save_path = os.path.join(SAVE_DIR, f'top_left_{circuit_name}.png')
    plt.savefig(save_path)
    plt.close()
    print(f"Saved Accuracy Plot: {save_path}")

def plot_bottom_left_comparison():
    """Figure 2: Extensibility Comparison (Focus on PP vs SPP)"""

    # We draw two subplots: the left side includes SUM, and the right side only includes PP and SPP.

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    families = ['adder_i8_o5', 'adder_i10_o6', 'adder_i12_o7', 'adder_i16_o9', 'adder_i20_o11']
    
    colors = {'sum': '#1f77b4', 'pp': '#ff7f0e', 'spp': '#2ca02c'}


    for alg in ['sum', 'pp', 'spp']:
        x, y = [], []
        for circuit in families:
            data = get_data(alg, circuit)
            if data:
                x.append(data['num_nodes'])
                y.append(data['time_seconds'] / data['num_nodes'])
        if x:
            idx = np.argsort(x)
            ax1.plot(np.array(x)[idx], np.array(y)[idx], marker='o', label=alg.upper(), color=colors[alg])
    
    ax1.set_title("Scalability: ALL Algorithms")
    ax1.set_xlabel("Number of Nodes")
    ax1.set_ylabel("Seconds per Node")
    ax1.legend()
    ax1.grid(True, ls="--", alpha=0.5)

    # --- Right image: Only PP and SPP (see the subtle differences) ---
    for alg in ['pp', 'spp']:
        x, y = [], []
        for circuit in families:
            data = get_data(alg, circuit)
            if data:
                x.append(data['num_nodes'])
                y.append((data['time_seconds'] / data['num_nodes']) * 1e6)
        if x:
            idx = np.argsort(x)
            ax2.plot(np.array(x)[idx], np.array(y)[idx], marker='s', label=alg.upper(), color=colors[alg], linewidth=2)
    
    ax2.set_title("Scalability: PP vs SPP ONLY (Zoomed)")
    ax2.set_xlabel("Number of Nodes")
    ax2.set_ylabel("Microseconds (us) per Node")
    ax2.legend()
    ax2.grid(True, ls="--", alpha=0.5)

    plt.tight_layout()
    save_path = os.path.join(SAVE_DIR, 'bottom_left_combined.png')
    plt.savefig(save_path)
    plt.close()
    print(f"Saved Scalability Plot: {save_path}")

if __name__ == "__main__":
    plot_top_left('adder_i16_o9')
    plot_top_left('abs_diff_i16_o8')
    plot_top_left('mul_i16_o16')
    plot_bottom_left_comparison()