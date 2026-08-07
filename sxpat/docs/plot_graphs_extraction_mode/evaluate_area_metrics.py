import matplotlib.pyplot as plt

# metrics: area->power->delay
all_modes_data = {
    "Mode 1": {
        'Error Space 4': {'x_post': [], 'y_pre': [], 'color': 'blue'},
        'Error Space 8': {'x_post': [], 'y_pre': [], 'color': 'green'},
        'Error Space 16': {'x_post': [], 'y_pre': [], 'color': 'yellow'},
        'Error Space 32': {'x_post': [], 'y_pre': [], 'color': 'orange'},
        'Error Space 64': {'x_post': [], 'y_pre': [], 'color': 'red'}
    },
    "Mode 2": {
        'Error Space 4': {'x_post': [], 'y_pre': [], 'color': 'blue'},
        'Error Space 8': {'x_post': [], 'y_pre': [], 'color': 'green'},
        'Error Space 16': {'x_post': [], 'y_pre': [], 'color': 'yellow'},
        'Error Space 32': {'x_post': [], 'y_pre': [], 'color': 'orange'},
        'Error Space 64': {'x_post': [], 'y_pre': [], 'color': 'red'}
    },
    "Mode 3": {
        'Error Space 4': {'x_post': [], 'y_pre': [], 'color': 'blue'},
        'Error Space 8': {'x_post': [], 'y_pre': [], 'color': 'green'},
        'Error Space 16': {'x_post': [], 'y_pre': [], 'color': 'yellow'},
        'Error Space 32': {'x_post': [], 'y_pre': [], 'color': 'orange'},
        'Error Space 64': {'x_post': [], 'y_pre': [], 'color': 'red'}
    },
    "Mode 4": {
        'Error Space 4': {'x_post': [], 'y_pre': [], 'color': 'blue'},
        'Error Space 8': {'x_post': [], 'y_pre': [], 'color': 'green'},
        'Error Space 16': {'x_post': [], 'y_pre': [], 'color': 'yellow'},
        'Error Space 32': {'x_post': [], 'y_pre': [], 'color': 'orange'},
        'Error Space 64': {'x_post': [], 'y_pre': [], 'color': 'red'}
    },
    "Mode 5": {
        'Error Space 4': {'x_post': [], 'y_pre': [], 'color': 'blue'},
        'Error Space 8': {'x_post': [], 'y_pre': [], 'color': 'green'},
        'Error Space 16': {'x_post': [], 'y_pre': [], 'color': 'yellow'},
        'Error Space 32': {'x_post': [], 'y_pre': [], 'color': 'orange'},
        'Error Space 64': {'x_post': [], 'y_pre': [], 'color': 'red'}
    },
    "Mode 55": {
        'Error Space 4': {'x_post': [163.786], 'y_pre': [], 'color': 'blue'},
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

for mode_name, mode_data in all_modes_data.items():
    plt.figure(figsize=(8, 6))
    
    # Plot the scatter points for this specific mode
    for label, metrics in mode_data.items():
        plt.scatter(
            metrics['x_post'], 
            metrics['y_pre'], 
            c=metrics['color'], 
            label=label, 
            edgecolors='black',
            s=100,
            alpha=0.8
        )

    # Add the y = x break-even line
    plt.plot([0, 200], [0, 200], 'k--', alpha=0.5, label='y = x (No Area Change)')

    # Formatting
    plt.xlabel('Area POST R (Refactored)', fontsize=12, fontweight='bold')
    plt.ylabel('Area PRE (Original)', fontsize=12, fontweight='bold')
    plt.title(f'Final Circuit Area: Original vs Refactored - {mode_name}', fontsize=14, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc='upper left', framealpha=1.0)
    
    # Set the same axis limits for all graphs so they are easy to compare
    plt.xlim(0, 200)
    plt.ylim(0, 200)

    plt.tight_layout()
    plt.show()