import os
import re
import matplotlib.pyplot as plt

def extract_and_plot_area(base_log_dir="program_outputs_global"):
    betas = [16, 8, 4, 2, 1]
    input_space = 16
    
    nr_zones = []
    extracted_areas = []

    print(f"Scanning '{base_log_dir}' for area metrics...\n")

    for beta in betas:
        log_file = os.path.join(base_log_dir, f"beta_{beta:02d}", "log.out")
        
        if not os.path.exists(log_file):
            print(f"Warning: Could not find log file for Beta {beta}.")
            continue

        with open(log_file, "r") as f:
            log_content = f.read()
            
            area_match = re.search(r"[|│]\s*area->power->delay\s*[|│]\s*[^|│]+\s*[|│]\s*([\d\.\-eE]+)\s*[|│]", log_content)
            
            if area_match:
                area_val = float(area_match.group(1))
                zones = (input_space // beta) * (input_space // beta)
                
                nr_zones.append(zones)
                extracted_areas.append(area_val)
                
            else:
                print(f"Missing 'area->power->delay' data in Beta {beta} log.")

    if not nr_zones:
        print("\nNo data found to plot.")
        return
        
  
    nr_zones_str = [str(z) for z in nr_zones] 
    
    plt.figure(figsize=(8, 5))
    
    plt.plot(nr_zones_str, extracted_areas, marker='D', linestyle='-', color='g', linewidth=2, markersize=8)
    
    plt.title("Circuit Area (area->power->delay) vs. Number of Zones", fontsize=14, pad=15)
    plt.xlabel("Number of Zones", fontsize=12)
    plt.ylabel("Area", fontsize=12)
    
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    output_image = "area_vs_zones.png"
    plt.savefig(output_image, dpi=300)
    print(f"\nSuccess! Curve saved as '{output_image}'.")

if __name__ == "__main__":
    extract_and_plot_area()