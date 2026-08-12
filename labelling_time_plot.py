import os
import re
import matplotlib.pyplot as plt

def extract_and_plot_times(base_log_dir="program_outputs"):
    betas = [1, 2, 4, 8, 16]
    
    valid_betas = []
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
                
                valid_betas.append(beta)
                total_times.append(t_total)
                single_node_times.append(t_single)
                
                print(f"Beta {beta:02d} -> Total: {t_total:.2f}s | Per Node: {t_single:.4f}s")
            else:
                print(f"Warning: Missing time data in Beta {beta} log.")

    if not valid_betas:
        print("\nNo data found to plot.")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # total time labeling plot
    ax1.plot(valid_betas, total_times, marker='o', linestyle='-', color='b', linewidth=2)
    ax1.set_title("Total Labelling Time vs. Beta", fontsize=13, pad=10)
    ax1.set_xlabel("Beta (Step Size)")
    ax1.set_ylabel("Total Time (Seconds)")
    ax1.set_xticks(valid_betas)
    ax1.grid(True, linestyle='--', alpha=0.7)

    # single node labeling plot
    ax2.plot(valid_betas, single_node_times, marker='s', linestyle='-', color='r', linewidth=2)
    ax2.set_title("Average Single Node Time vs. Beta", fontsize=13, pad=10)
    ax2.set_xlabel("Beta (Step Size)")
    ax2.set_ylabel("Time Per Node (Seconds)")
    ax2.set_xticks(valid_betas)
    ax2.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    output_image = "labelling_time_curves.png"
    plt.savefig(output_image, dpi=300)
    print(f"\nSuccess! Curves saved as '{output_image}'.")

if __name__ == "__main__":
    extract_and_plot_times()