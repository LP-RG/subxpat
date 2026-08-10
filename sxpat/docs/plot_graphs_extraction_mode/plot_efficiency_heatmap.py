import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
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

# 1. Process data into a format Seaborn loves (Tidy DataFrame)
rows = []
for mode, error_spaces in all_modes_data.items():
    for es, metrics in error_spaces.items():
        pre = metrics['y_pre'][0]
        post = metrics['x_post'][0]
        
        # Calculate % Reduction (Handling the 0->0 case)
        pct_red = ((pre - post) / pre * 100) if pre > 0 else 0
        
        rows.append({'Mode': mode, 'Error Space': es, '% Reduction': pct_red})

df = pd.DataFrame(rows)

# 2. Create the Heatmap
error_space_order = ['Error Space 4', 'Error Space 8', 'Error Space 16', 'Error Space 32', 'Error Space 64']
mode_order = ['Mode 1', 'Mode 2', 'Mode 3', 'Mode 4', 'Mode 5', 'Mode 6', 'Mode 11', 'Mode 12', 'Mode 55']

# Pivot data into a 2D matrix
pivot = df.pivot(index='Mode', columns='Error Space', values='% Reduction')
pivot = pivot.reindex(index=mode_order, columns=error_space_order)

# Set up the matplotlib figure size
plt.figure(figsize=(10, 8))

# Draw the heatmap
# center=0 ensures that 0% is yellow, positive reductions are green, negative reductions (bloat) are red
heatmap = sns.heatmap(pivot, cmap='RdYlGn', center=0, annot=True, fmt=".1f", 
                      linewidths=.5, cbar_kws={'label': '% Area Reduction'})

# Formatting
plt.title('Refactoring Efficiency: % Area Reduction by Mode', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Error Space Tolerance', fontsize=12, fontweight='bold')
plt.ylabel('Extraction Mode', fontsize=12, fontweight='bold')
plt.tight_layout()

# 3. Robust save logic for SSH execution
script_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(script_dir, "efficiency_heatmap.png")
plt.savefig(filename, dpi=300)
plt.show()

print(f"Heatmap successfully generated and saved to: {filename}")