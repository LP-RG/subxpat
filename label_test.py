import os
import json
from unittest.mock import Mock
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Tuple

from sxpat.specifications import Paths
from sxpat.utils.timer import Timer
from sxpat.newag import load_circuit_from_verilog
from sxpat.labelling.solver_labelling import Labelling


def worker_beta(beta: int, circuit_path: str, input1_zone: Tuple[int,int], input2_zone: Tuple[int,int]) -> Dict:
    """
    Worker function.
    """
    print(f"[Beta-{beta}] Starting evaluation...")
    _time = Timer.now()
    
    # create a unique specs for each beta
    specs = Mock()
    specs.min_labeling = True
    specs.iteration = 0
    specs.sub_iteration = ''
    
    # give each a temporary folder path
    run_folder = f'beta_{beta}'
    specs.path.run = Paths.RunFiles(run_folder, debug=True)
    
    # create dummy directories to deal with errors
    os.makedirs(f'output/{run_folder}/tmp', exist_ok=True)
    os.makedirs(f'output/{run_folder}/verilog', exist_ok=True)
    os.makedirs(f'output/{run_folder}/scripts', exist_ok=True)

    #load a fresh copy of the circuit and initiate the labeller
    circuit = load_circuit_from_verilog(circuit_path, specs.path.run)
    labeller = Labelling(circuit, circuit, specs=specs)

    #process the nodes
    beta_node_weights = {}
    for node in circuit.nodes:
        raw_zone_weights = labeller.label_all_zones(node.name, input1_zone, input2_zone, beta)
        safe_zone_weights = {str(zone): weight for zone, weight in raw_zone_weights.items()}
        beta_node_weights[node.name] = safe_zone_weights

    done_time = Timer.now() - _time
    print(f"[Beta-{beta}] Completed in {done_time:.2f} s.")
    
    return {
        "beta": beta,
        "labelling_time_seconds": done_time,
        "weights_per_node": beta_node_weights
    }


def test_zoning(circuit_path: str, num_inputs: int):
    """
    Executes a parallelized test to calculate node weights across 
    different input zone granularities (betas).
    """

    print(f"Setting up standalone test for: {circuit_path}")

    # calculate input zones directly using the provided num_inputs
    half_inputs = num_inputs // 2
    
    # calculate max possible values for the intervals
    max_val_1 = (2 ** half_inputs) - 1
    max_val_2 = (2 ** (num_inputs - half_inputs)) - 1
    
    input1_zone = (0, max_val_1)
    input2_zone = (0, max_val_2)
    print(f"Calculated base input zones: {input1_zone} and {input2_zone}")

    # define the granularity (beta) values
    betas_to_test = [32, 16, 8, 4, 2]
    all_results = {}

   
    max_threads = 2

    #launch
    with ThreadPoolExecutor(max_threads) as pool:
        futures = [
            pool.submit(worker_beta, beta, circuit_path, input1_zone, input2_zone) 
            for beta in betas_to_test
        ]
        
        for future in futures:
            result = future.result()
            all_results[f"beta_{result['beta']}"] = {
                "labelling_time_seconds": result["labelling_time_seconds"],
                "weights_per_node": result["weights_per_node"]
            }

    # export the final results to JSON
    output_file = "zone_testing_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=4)
        
    print(f"\nSuccess! Saved {output_file}")

if __name__ == '__main__':
    # circuit_file = 'benchmarks/v/mul_i16_o16.v' 
    circuit_file = 'benchmarks/v/adder_i8_o5.v'
    test_zoning(circuit_file, num_inputs=8)