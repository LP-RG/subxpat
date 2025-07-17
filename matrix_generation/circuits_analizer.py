from vpadanalyzer.synthesis import Synthesis
import os
import sys
import sub_xpat_circuits_generator

import multiplier_outputs_plotting

def circuits_analizer(input_path):
    """
    Analizza un circuito e restituisce la sua area, potenza e ritardo.
    """
    area = Synthesis.area(input_path)
    power = Synthesis.power(input_path)
    delay = Synthesis.delay(input_path)
    return {"file": os.path.basename(input_path), "area": area, "power": power, "delay": delay}

def create_matrices(multipliers_folder, bitwidth, output_plot_path):
    if not os.path.isdir(multipliers_folder):
        print(f"Errore: La cartella '{multipliers_folder}' non esiste.")
        return []
    os.makedirs(output_plot_path, exist_ok=True)
    # Raccoglie i dati di tutti i file
    for filename in sorted(os.listdir(multipliers_folder)):  # Ordina i file per nome
        input_path = os.path.join(multipliers_folder, filename)
        if os.path.isfile(input_path):
            name = filename.split(".")[0]
            sub_xpat_circuits_generator.generate_approx_mult_function(input_path, bitwidth)
            import sub_x_pat_simulator
            sub_x_pat_simulator.multiplier_test(bitwidth,os.path.join(output_plot_path,name + ".npy"))
            multiplier_outputs_plotting.plots(name,os.path.join(output_plot_path,name + ".npy"),output_plot_path)

def analyze_multipliers(multipliers_folder):
    if not os.path.isdir(multipliers_folder):
        print(f"Errore: La cartella '{multipliers_folder}' non esiste.")
        return []
    # Raccoglie i dati di tutti i file
    multipliers_data = []
    for filename in sorted(os.listdir(multipliers_folder)):  # Ordina i file per nome
        input_path = os.path.join(multipliers_folder, filename)
        if os.path.isfile(input_path):
            data = circuits_analizer(input_path)
            multipliers_data.append(data)
    return multipliers_data


if __name__ == "__main__":
    if(len(sys.argv) != 4):
        raise NotImplementedError
    multipliers_folder = sys.argv[1]
    bitwidth = sys.argv[2]
    bitwidth = int(bitwidth)

    output_path = sys.argv[3]
    print("Analisi dei moltiplicatori:")

    results = analyze_multipliers(multipliers_folder)
    create_matrices(multipliers_folder, bitwidth, output_path)
    os.remove("sub_x_pat_multiplier.py")
    if results:
        print("\n--- Risultati Ordinati per Nome del File ---")
        for data in results:
            print(f"File: {data['file']}, Area = {data['area']}, Power = {data['power']}, Delay = {data['delay']}")

        output_filename = "circuits_area_power.txt"
        output_full_path_file = os.path.join(output_path,output_filename)
        with open(output_full_path_file, "w") as f:
            for data in results:
                f.write(f"File: {data['file']}, Area = {data['area']}, Power = {data['power']}\n")
        print(f"\nI dati dell'area sono stati scritti nel file '{output_full_path_file}'.")

    
    

