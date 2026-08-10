import matplotlib.pyplot as plt
from matplotlib.lines import Line2D # For custom legend
import os

all_modes_data = {
    "Mode 1": {
            'Error Space 4': {'x_post': [37.544], 'y_pre': [37.544], 'color': 'blue'},
            'Error Space 8': {'x_post': [39.8905], 'y_pre': [31.9124], 'color': 'green'},
            'Error Space 16': {'x_post': [14.079], 'y_pre': [0], 'color': 'yellow'},
            'Error Space 32': {'x_post': [0], 'y_pre': [0], 'color': 'orange'},
            'Error Space 64': {'x_post': [0], 'y_pre': [0], 'color': 'red'}
        },
        "Mode 2": {
            'Error Space 4': {'x_post': [37.544], 'y_pre': [43.1756], 'color': 'blue'},
            'Error Space 8': {'x_post': [10.3246], 'y_pre': [17.3641], 'color': 'green'},
            'Error Space 16': {'x_post': [0], 'y_pre': [2.8158], 'color': 'yellow'},
            'Error Space 32': {'x_post': [0], 'y_pre': [0], 'color': 'orange'},
            'Error Space 64': {'x_post': [0], 'y_pre': [0], 'color': 'red'}
        },
        "Mode 3": {
            'Error Space 4': {'x_post': [47.8686], 'y_pre': [47.8686], 'color': 'blue'},
            'Error Space 8': {'x_post': [17.8334], 'y_pre': [17.8334], 'color': 'green'},
            'Error Space 16': {'x_post': [0], 'y_pre': [6.5702], 'color': 'yellow'},
            'Error Space 32': {'x_post': [0], 'y_pre': [0], 'color': 'orange'},
            'Error Space 64': {'x_post': [0], 'y_pre': [0], 'color': 'red'}
        },
        "Mode 4": {
            'Error Space 4': {'x_post': [31.4431], 'y_pre': [21.5878], 'color': 'blue'},
            'Error Space 8': {'x_post': [31.4431], 'y_pre': [16.4255], 'color': 'green'},
            'Error Space 16': {'x_post': [1.4079], 'y_pre': [0], 'color': 'yellow'},
            'Error Space 32': {'x_post': [0], 'y_pre': [0], 'color': 'orange'},
            'Error Space 64': {'x_post': [0], 'y_pre': [14.079], 'color': 'red'}
        },
        "Mode 5": {
            'Error Space 4': {'x_post': [36.1361], 'y_pre': [36.1361], 'color': 'blue'},
            'Error Space 8': {'x_post': [22.5264], 'y_pre': [10.7939], 'color': 'green'},
            'Error Space 16': {'x_post': [1.4079], 'y_pre': [1.4079], 'color': 'yellow'},
            'Error Space 32': {'x_post': [7.5088], 'y_pre': [7.5088], 'color': 'orange'},
            'Error Space 64': {'x_post': [0], 'y_pre': [0], 'color': 'red'}
        },
        "Mode 55": {
            'Error Space 4': {'x_post': [163.786], 'y_pre': [137.505], 'color': 'blue'},
            'Error Space 8': {'x_post': [126.242], 'y_pre': [129.527], 'color': 'green'},
            'Error Space 16': {'x_post': [94.7986], 'y_pre': [101.369], 'color': 'yellow'},
            'Error Space 32': {'x_post': [53.9695], 'y_pre': [107.939], 'color': 'orange'},
            'Error Space 64': {'x_post': [9.386], 'y_pre': [9.386], 'color': 'red'}
        },
        "Mode 6": {
            'Error Space 4': {'x_post': [164.724], 'y_pre': [140.79], 'color': 'blue'},
            'Error Space 8': {'x_post': [162.847], 'y_pre': [132.343], 'color': 'green'},
            'Error Space 16': {'x_post': [148.768], 'y_pre': [159.093], 'color': 'yellow'},
            'Error Space 32': {'x_post': [142.198], 'y_pre': [129.527], 'color': 'orange'},
            'Error Space 64': {'x_post': [86.3512], 'y_pre': [86.3512], 'color': 'red'}
        },
        "Mode 11": {
            'Error Space 4': {'x_post': [135.628], 'y_pre': [135.628], 'color': 'blue'},
            'Error Space 8': {'x_post': [118.264], 'y_pre': [117.794], 'color': 'green'},
            'Error Space 16': {'x_post': [107.47], 'y_pre': [100.43], 'color': 'yellow'},
            'Error Space 32': {'x_post': [82.5968], 'y_pre': [102.777], 'color': 'orange'},
            'Error Space 64': {'x_post': [11.7325], 'y_pre': [13.6097], 'color': 'red'}
        },
        "Mode 12": {
            'Error Space 4': {'x_post': [158.623], 'y_pre': [158.623], 'color': 'blue'},
            'Error Space 8': {'x_post': [146.422], 'y_pre': [146.422], 'color': 'green'},
            'Error Space 16': {'x_post': [106.062], 'y_pre': [124.365], 'color': 'yellow'},
            'Error Space 32': {'x_post': [78.8424], 'y_pre': [114.04], 'color': 'orange'},
            'Error Space 64': {'x_post': [83.5354], 'y_pre': [19.7106], 'color': 'red'}
        }
}

# Define unique markers for each of the 9 modes
mode_markers = ['o', 's', '^', 'v', '<', '>', 'D', 'p', '*']
error_space_colors = ['blue', 'green', 'yellow', 'orange', 'red']
error_space_labels = ['Error Space 4', 'Error Space 8', 'Error Space 16', 'Error Space 32', 'Error Space 64']

fig, ax = plt.subplots(figsize=(14, 12))
fig.suptitle('Final Circuit Area: Original vs Refactored Across All 45 Points', fontsize=20, fontweight='bold', y=0.92)

all_points_x = []
all_points_y = []
all_points_colors = []
all_points_markers = []
all_points_labels = []

# Generate proxy artists for the comprehensive legend box
custom_legend_handles = []
custom_legend_labels = []

# Section 1 for Error Spaces (colors)
for i, (color, label) in enumerate(zip(error_space_colors, error_space_labels)):
    custom_legend_handles.append(Line2D([0], [0], marker='o', color='white', 
                                         label=label, markerfacecolor=color, 
                                         markeredgecolor='black', markersize=10, 
                                         linestyle='None'))
    custom_legend_labels.append(label)

# Add a spacer
custom_legend_handles.append(Line2D([0], [0], color='white', label='', linestyle='None'))
custom_legend_labels.append('')

# Section 2 for Modes (markers)
for i, (mode_name, marker) in enumerate(zip(all_modes_data.keys(), mode_markers)):
    custom_legend_handles.append(Line2D([0], [0], marker=marker, color='black', 
                                         label=mode_name, markerfacecolor='black', 
                                         markeredgecolor='black', markersize=10, 
                                         linestyle='None'))
    custom_legend_labels.append(mode_name)

# Collect all 45 data points and plot
for mode_idx, (mode_name, mode_data) in enumerate(all_modes_data.items()):
    mode_marker = mode_markers[mode_idx]
    
    for label, metrics in mode_data.items():
        # Plot each mode-error space combo with its custom marker/color
        ax.scatter(
            metrics['x_post'], 
            metrics['y_pre'], 
            c=metrics['color'], 
            marker=mode_marker,
            label=None, 
            edgecolors='black',
            s=120,
            alpha=0.8
        )

# Add the y = x break-even line 
ax.plot([-10, 210], [-10, 210], 'k--', alpha=0.5, label='y = x (No Area Change)')

# Formatting
ax.set_xlabel('Area POST R (Refactored)', fontsize=14, fontweight='bold')
ax.set_ylabel('Area PRE (Original)', fontsize=14, fontweight='bold')
ax.grid(True, linestyle=':', alpha=0.7)

ax.set_xlim(-10, 210)
ax.set_ylim(-10, 210)

# Apply a readable, combined legend in two columns using proxy artists
ax.legend(handles=custom_legend_handles, labels=custom_legend_labels, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=10, framealpha=1.0, ncols=1)

plt.tight_layout()

script_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(script_dir, "all_modes_combined_plot.png")
plt.savefig(filename, dpi=300)
plt.show()

print(f"Combined plot for all 45 points saved successfully as {filename}!")
