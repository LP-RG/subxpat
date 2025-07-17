import sys
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.colors import LogNorm

output_plots_path = "./outputs_plot/"
def mult_output_plotting(mult_name, matrix, output_plots_path):
    plt.title('Multiplier output', fontsize=16)
    plt.rcParams.update({'font.size': 20})
    plt.imshow(matrix, cmap='Blues', origin='upper')# Modifica per avere i ticks da -128 a 128
    plt.xticks(np.arange(matrix.shape[1], step=np.round(matrix.shape[1] / 5)))
    plt.yticks(np.arange(matrix.shape[0], step=np.round(matrix.shape[1] / 5)))
    plt.xlabel("Weights")
    plt.ylabel("Inputs") 
    plt.colorbar()  
    full_save_path = os.path.join(output_plots_path, mult_name + ".png")
    plt.savefig(full_save_path, bbox_inches='tight')
    plt.close()

def mult_AE_plotting(mult_name, matrix, output_plots_path):
    plt.title('Multiplier Absolute Error', fontsize=16)
    n_inputs = matrix.shape[0]
    exact_outputs = np.outer(np.arange(n_inputs), np.arange(n_inputs))
    differences = np.abs(matrix - exact_outputs)
    plt.rcParams.update({'font.size': 20})
    plt.imshow(differences, cmap='Reds', origin='upper', vmax=(np.max(differences)))
    plt.xticks(np.arange(differences.shape[1], step=np.round(matrix.shape[1] / 5)))
    plt.yticks(np.arange(differences.shape[0], step=np.round(matrix.shape[1] / 5)))
    plt.xlabel("Weights")
    plt.ylabel("Inputs") 
    plt.colorbar() 
    full_save_path = os.path.join(output_plots_path, mult_name + "_AE.png")
    plt.savefig(full_save_path, bbox_inches='tight')
    plt.close()


def mult_binary_AE_plotting(mult_name, matrix, output_plots_path):
    plt.title('Multiplier Absolute Error', fontsize=16)
    n_inputs = matrix.shape[0]
    exact_outputs = np.outer(np.arange(n_inputs), np.arange(n_inputs))
    differences = (np.abs(matrix - exact_outputs) >  3).astype(int)
    plt.rcParams.update({'font.size': 20})
    plt.imshow(differences, cmap='Reds', origin='upper', vmax=(np.max(differences)))
    plt.xticks(np.arange(differences.shape[1], step=np.round(matrix.shape[1] / 5)))
    plt.yticks(np.arange(differences.shape[0], step=np.round(matrix.shape[1] / 5)))
    plt.xlabel("Weights")
    plt.ylabel("Inputs") 
    plt.colorbar() 
    full_save_path = os.path.join(output_plots_path, mult_name + "_RE.png")
    plt.savefig(output_plots_path + mult_name + "_AE_binary.png", bbox_inches='tight')
    plt.close()

def mult_RE_plotting(mult_name: str, matrix: np.ndarray, output_plots_path: str):
    plt.rcParams.update({'font.size': 20})

    fig, ax = plt.subplots(figsize=(10, 8))

    n_inputs = matrix.shape[0]
    exact_outputs = np.outer(np.arange(n_inputs), np.arange(n_inputs))

    zero_exact_mask = (exact_outputs == 0)
    
    relative_errors = np.abs(matrix - exact_outputs) * 100 / np.where(zero_exact_mask, 1, exact_outputs)

    finite_positive_errors = relative_errors[np.isfinite(relative_errors) & (relative_errors > 0)]

    if finite_positive_errors.size == 0:
        min_val = 1e-10
        max_val = 1e-9
        print(f"Warning for {mult_name}: No finite, positive relative errors found. Using default LogNorm range ({min_val}, {max_val}).")
    else:
        min_val = np.min(finite_positive_errors)
        max_val = np.max(finite_positive_errors)

        if min_val == max_val:
            if min_val > 0:
                min_val_safe = min_val * 0.99 if min_val * 0.99 < min_val else min_val - 1e-10
                max_val_safe = max_val * 1.01 if max_val * 1.01 > max_val else max_val + 1e-10
                min_val = max(1e-10, min_val_safe)
                max_val = max(min_val + 1e-10, max_val_safe)
            else:
                min_val = 1e-10
                max_val = 1e-9
            print(f"Warning for {mult_name}: All finite positive relative errors are identical. Adjusted LogNorm range to ({min_val}, {max_val}).")
        else:
            min_val = max(1e-10, min_val)

    my_norm = LogNorm(vmin=min_val, vmax=max_val)

    im = ax.imshow(relative_errors, cmap='Greens', origin='upper', norm=my_norm)
    
    ax.set_title('Multiplier Relative Error', fontsize=16)
    ax.set_xticks(np.arange(relative_errors.shape[1], step=max(1, int(np.round(relative_errors.shape[1] / 5)))))
    ax.set_yticks(np.arange(relative_errors.shape[0], step=max(1, int(np.round(relative_errors.shape[0] / 5)))))
    
    ax.set_xlabel("Weights")
    ax.set_ylabel("Inputs") 
    
    cbar = fig.colorbar(im, ax=ax, label='Relative Error (%) (Log Scale)') 

    if matrix.shape[0] <= 16 and matrix.shape[1] <= 16:
        for i in range(relative_errors.shape[0]):
            for j in range(relative_errors.shape[1]):
                val = relative_errors[i, j]
                if np.isfinite(val):
                    ax.text(j, i, f'{val:.0f}', 
                            ha='center', va='center', color='black', fontsize=8)
                else:
                    ax.text(j, i, 'N/A',
                            ha='center', va='center', color='gray', fontsize=8)

    os.makedirs(output_plots_path, exist_ok=True)
    full_save_path = os.path.join(output_plots_path, mult_name + "_RE.png")
    plt.savefig(full_save_path, bbox_inches='tight')
    plt.close(fig)

def plots(mult_name,file_path, output_plots_path = output_plots_path):
    if(not os.path.exists(output_plots_path)):
        os.makedirs(output_plots_path)
    outputs = np.load(file_path)
    mult_output_plotting(mult_name=mult_name, matrix=outputs, output_plots_path=output_plots_path)
    mult_AE_plotting(mult_name=mult_name, matrix=outputs, output_plots_path=output_plots_path)
    mult_RE_plotting(mult_name=mult_name, matrix=outputs, output_plots_path=output_plots_path)

if __name__ == "__main__":
    if(len(sys.argv) != 2):
        raise NotImplementedError
    if(os.path.isfile(sys.argv[1])):
        plots(sys.argv[1].split("/")[-1].split(".")[0],sys.argv[1])
    if(os.path.isdir(sys.argv[1])):
        for filename in os.listdir(sys.argv[1]):
            if filename.endswith('.npy'):
                input_full_path = os.path.join(sys.argv[1], filename)
                plots(filename.split(".")[0],input_full_path)
