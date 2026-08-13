import os
import re
import matplotlib.pyplot as plt

def extract_and_plot_times(base_log_dir="program_outputs"):
    betas = [1, 2, 4, 8, 16]
    input_space = 16
    
    nr_zones = []
    total_times = []
    single_node_times = []

    print(f"Scanning '{base_log_dir}' for labelling times...\n")

    for beta in betas:
        log_file = os.path.join(base_log_dir, f"beta_{beta:02d}", "log.out")
        
        if not os.path.exists(log_file):
            print(f"Warning: Could not find log file for Beta {beta}.")
            continue

        with open(log_file, "r") as f:
            log_content = f.read()
            
            # Extract total time
            match_total = re.search(r"labelling_time\s*=\s*([\d\.]+)", log_content)
            # Extract single node time
            match_single = re.search(r"average_node_time\s*=\s*([\d\.]+)", log_content)
            
            if match_total and match_single:
                t_total = float(match_total.group(1))
                t_single = float(match_single.group(1))

                zones = (input_space // beta) * (input_space // beta)
                
                nr_zones.append(zones)
                total_times.append(t_total)
                single_node_times.append(t_single)
                
                print(f"Beta {beta:02d} | Nr. of Zones {zones} -> Total: {t_total:.2f}s | Per Node: {t_single:.4f}s")
            else:
                print(f"Warning: Missing time data in Beta {beta} log.")

    if not nr_zones:
        print("\nNo data found to plot.")
        return

    sorted_data = sorted(zip(nr_zones, total_times, single_node_times), reverse=True)
    nr_zones_sorted = [d[0] for d in sorted_data]
    total_times_sorted = [d[1] for d in sorted_data]
    single_node_times_sorted = [d[2] for d in sorted_data]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Total time labeling plot
    ax1.plot(nr_zones_sorted, total_times_sorted, marker='o', linestyle='-', color='b', linewidth=2)
    ax1.set_title("Total Labelling Time vs. Number of Zones", fontsize=13, pad=10)
    ax1.set_xlabel("Number of Zones")
    ax1.set_ylabel("Total Time (Seconds)")
    ax1.set_xticks(nr_zones_sorted)
    ax1.grid(True, linestyle='--', alpha=0.7)

    # Single node labeling plot
    ax2.plot(nr_zones_sorted, single_node_times_sorted, marker='s', linestyle='-', color='r', linewidth=2)
    ax2.set_title("Average Single Node Time vs. Number of Zones", fontsize=13, pad=10)
    ax2.set_xlabel("Number of Zones")
    ax2.set_ylabel("Time Per Node (Seconds)")
    ax2.set_xticks(nr_zones_sorted)
    ax2.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    output_image = "labelling_time_curves_nrzones.png"
    plt.savefig(output_image, dpi=300)
    print(f"\nSuccess! Curves saved as '{output_image}'.")

if __name__ == "__main__":
    extract_and_plot_times()