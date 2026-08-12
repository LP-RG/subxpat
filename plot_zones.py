import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def save_zone_heatmaps(z_weights, output_dir="zone_plots"):
    """Converts zone dictionaries to matrices and saves them as heatmap images."""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n>>> Generating {len(z_weights)} node heatmaps in '{output_dir}/'...")

    for node_name, zone_dict in z_weights.items():
        row_bounds = sorted(list(set([(z.input_1.l_bound, z.input_1.u_bound) for z in zone_dict.keys()])))
        col_bounds = sorted(list(set([(z.input_2.l_bound, z.input_2.u_bound) for z in zone_dict.keys()])))
        
        matrix = np.zeros((len(row_bounds), len(col_bounds)), dtype=int)
        
        for zone, weight in zone_dict.items():
            r_idx = row_bounds.index((zone.input_1.l_bound, zone.input_1.u_bound))
            c_idx = col_bounds.index((zone.input_2.l_bound, zone.input_2.u_bound))
            matrix[r_idx, c_idx] = weight
            
        plt.figure(figsize=(5, 4))
        x_labels = [f"In 2\n({b[0]}-{b[1]})" for b in col_bounds]
        y_labels = [f"In 1\n({b[0]}-{b[1]})" for b in row_bounds]
        
        sns.heatmap(
            matrix, annot=True, fmt="d", cmap="Blues", 
            cbar=False, xticklabels=x_labels, yticklabels=y_labels,
            vmin=0, vmax=255
        )
        
        plt.title(f"Node: {node_name} Error Weights", pad=15)
        plt.gca().xaxis.tick_top()
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/{node_name}_heatmap.png")
        plt.close()