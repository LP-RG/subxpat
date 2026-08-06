import matplotlib.pyplot as plt
import os

def plot_extraction_results(mode_name, data):
    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    axes = axes.flatten()

    for i, (err_name, runs) in enumerate(data.items()):
        ax = axes[i]
        for version, nodes in runs.items():
            iterations = range(1, len(nodes) + 1)
            ax.plot(iterations, nodes, marker='o', linestyle='-', label=version)
        
        ax.set_title(f"{mode_name} - {err_name}")
        ax.set_xlabel("Iteration")
        ax.set_ylabel("# of Nodes")
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()

    if len(data) < len(axes):
        fig.delaxes(axes[-1])

    plt.tight_layout()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, f"extraction_comparison_{mode_name.lower().replace(' ', '_')}.png")
    plt.savefig(filename, dpi=300)
    plt.show()
    print(f"Plot saved successfully as {filename}!")

# benchmarks -> adder_i8_o5.v
mode_1_data = {
    "Error Space 4": {
        "Original": [8, 8, 8, 8],
        "Refactored": [8, 8, 8, 8]
    },
    "Error Space 8": {
        "Original": [8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        "Refactored": [8, 8, 8, 8, 8, 8, 8, 8, 8] 
    },
    "Error Space 16": {
        "Original": [8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        "Refactored": [8, 8, 8, 8, 8, 8, 8, 8, 8, 8]
    },
    "Error Space 32": {
        "Original": [8, 8, 8, 8, 8, 7, 1],
        "Refactored": [8, 8, 14, 8, 7]
    },
    "Error Space 64": {
        "Original": [8, 8, 8, 7, 7],
        "Refactored": [8, 8, 8, 8, 8, 7]
    }
}

# benchmarks -> adder_i8_o5.v
mode_2_data = {
    "Error Space 4": {
        "Original": [4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "Refactored": [4, 1, 1, 1, 1, 1, 1, 1]
    },
    "Error Space 8": {
        "Original": [4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 4, 4],
        "Refactored": [4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 1, 3] 
    },
    "Error Space 16": {
        "Original": [4, 2, 1, 1, 1, 1, 1, 1, 4, 4, 4, 8, 4, 4, 4, 1, 1, 1],
        "Refactored": [4, 2, 1, 1, 1, 3, 4, 4, 4, 4, 3, 3, 3, 2, 4, 2]
    },
    "Error Space 32": {
        "Original": [4, 1, 1, 4, 2, 4, 3, 4, 3, 1],
        "Refactored": [4, 1, 1, 4, 2, 4, 3, 3, 1, 4, 2, 4]
    },
    "Error Space 64": {
        "Original": [4, 1, 3, 4, 4, 4, 1, 1],
        "Refactored": [4, 1, 3, 4, 4, 4, 4, 1]
    }
}

# benchmarks -> adder_i8_o5.v
mode_3_data = {
    "Error Space 4": {
        "Original": [5, 1, 1, 1, 1, 1],
        "Refactored": [5, 1, 1, 1, 1]
    },
    "Error Space 8": {
        "Original": [5, 1, 1, 1, 1, 1, 1, 1, 1, 5, 11, 4],
        "Refactored": [5, 1, 1, 1, 1, 1, 1, 1, 5, 11, 5] 
    },
    "Error Space 16": {
        "Original": [5, 1, 1, 1, 5, 2, 5, 2, 8, 8, 8, 8, 8],
        "Refactored": [5, 1, 1, 1, 5, 11, 5, 5, 6, 6, 6, 6, 11]
    },
    "Error Space 32": {
        "Original": [5, 2, 2, 5, 2, 5, 1, 1, 1, 5, 2, 1],
        "Refactored": [5, 2, 2, 5, 11, 4, 5, 4, 1, 1]
    },
    "Error Space 64": {
        "Original": [5, 5, 11, 4, 5, 3, 1],
        "Refactored": [5, 5, 11, 4, 5, 3, 1]
    }
}

# benchmarks -> adder_i8_o5.v
mode_4_data = {
    "Error Space 4": {
        "Original": [7, 2, 7, 3, 3, 3, 7],
        "Refactored": [7, 2, 7, 3, 3, 8]
    },
    "Error Space 8": {
        "Original": [7, 2, 7, 3, 3, 3, 7, 8, 7, 8, 5, 5, 5, 8, 8],
        "Refactored": [7, 2, 7, 3, 3, 8, 8, 8, 8, 8] 
    },
    "Error Space 16": {
        "Original": [8, 7, 8, 8, 8, 8, 8, 8, 8, 8],
        "Refactored": [8, 7, 8, 8, 8, 8, 8, 8, 7, 7, 1, 1, 1]
    },
    "Error Space 32": {
        "Original": [8, 8, 8, 8, 8, 8, 8, 7, 7],
        "Refactored": [8, 8, 8, 8, 8, 8, 7]
    },
    "Error Space 64": {
        "Original": [8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        "Refactored": [8, 8, 8, 8, 7]
    }
}

# benchmarks -> adder_i8_o5.v
mode_5_data = {
    "Error Space 4": {
        "Original": [4, 2, 4, 3, 3, 4],
        "Refactored": [4, 2, 4, 3, 3, 4]
    },
    "Error Space 8": {
        "Original": [4, 2, 4, 3, 3, 4, 4, 4, 4, 8],
        "Refactored": [4, 2, 4, 3, 3, 4, 4, 4, 4, 4, 4, 5] 
    },
    "Error Space 16": {
        "Original": [7, 4, 4, 4, 3, 3, 8, 4, 4, 4, 4, 4, 4, 4, 5, 3],
        "Refactored": [7, 4, 4, 4, 3, 3, 8, 4, 4, 4, 4, 4, 4, 4, 5, 3]
    },
    "Error Space 32": {
        "Original": [8, 7, 8, 5, 4, 4, 4, 4, 4, 4, 4],
        "Refactored": [8, 7, 8, 5, 4, 4, 4, 4, 4, 4, 4]
    },
    "Error Space 64": {
        "Original": [8, 8, 7, 4, 1],
        "Refactored": [8, 8, 7, 4, 1]
    }
}

# benchmarks -> mul_i8_o8.v
mode_55_data = {
    "Error Space 4": {
        "Original": [0, 4, 2, 2, 4],
        "Refactored": [0, 4, 2, 2, 4]
    },
    "Error Space 8": {
        "Original": [0, 4, 2, 2, 4, 3, 3, 4, 3, 3, 4],
        "Refactored": [0, 4, 2, 2, 4, 3, 3, 4, 4, 3, 3, 4, 7] 
    },
    "Error Space 16": {
        "Original": [2, 4, 4, 4, 4, 4, 6, 5, 6, 5, 6, 6, 6, 8],
        "Refactored": [2, 4, 4, 4, 4, 6, 4, 4, 4, 8, 4, 4, 6, 3, 6, 7]
    },
    "Error Space 32": {
        "Original": [4, 4, 8, 8, 8, 8, 6, 6, 6, 8, 7],
        "Refactored": [4, 4, 7, 4, 4, 4, 6, 8, 8, 8, 8, 8, 8, 8, 8, 5]
    },
    "Error Space 64": {
        "Original": [8, 7, 8, 14, 8, 8, 8, 8, 8, 8, 8, 8, 5],
        "Refactored": [8, 7, 8, 14, 8, 8, 13, 14, 14, 7, 14, 7, 7, 7, 4, 8]
    }
}

# benchmarks -> mul_i8_o8.v
mode_6_data = {
    "Error Space 4": {
        "Original": [1, 3, 1, 1, 1, 2],
        "Refactored": [1, 3, 2, 2, 2]
    },
    "Error Space 8": {
        "Original": [1, 3, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1],
        "Refactored": [1, 3, 2, 2, 2, 2, 2, 2, 1]
    },
    "Error Space 16": {
        "Original": [2, 3, 2, 2, 1, 2, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1],
        "Refactored": [2, 3, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 2]
    },
    "Error Space 32": {
        "Original": [2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 1, 8],
        "Refactored": [2, 3, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 6]
    },
    "Error Space 64": {
        "Original": [3, 7, 1, 1, 4, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 4, 4],
        "Refactored": [3, 7, 1, 1, 4, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 4, 4]
    }
}

# benchmarks -> adder_i8_o5.v
plot_extraction_results("Mode 1", mode_1_data)
plot_extraction_results("Mode 2", mode_2_data)
plot_extraction_results("Mode 3", mode_3_data)
plot_extraction_results("Mode 4", mode_4_data)
plot_extraction_results("Mode 5", mode_5_data)
# benchmarks -> mul_i8_o8.v
plot_extraction_results("Mode 55", mode_55_data)
plot_extraction_results("Mode 6", mode_6_data)

