import os
import re
import argparse

def verify_weights(base_log_dir, min : bool):
    #betas tested
    betas = [1, 2, 4, 8, 16]
    
    #all extracted weights
    node_weights = {}
    
    
    # extract the weights
    for beta in betas:
        log_file = os.path.join(base_log_dir, f"beta_{beta:02d}", "log.out")
        
        if not os.path.exists(log_file):
            continue

        with open(log_file, "r") as f:
            current_node = None
            for line in f:
                # look for the "Node: ..." header and get everything behind it
                node_match = re.match(r"^Node:\s*(.+)", line.strip())
                if node_match:
                    current_node = node_match.group(1)
                    continue
                
                # look for the weight inside the zone line
                weight_match = re.search(r"Weight\s+(\d+)", line)
                if current_node and weight_match:
                    weight = int(weight_match.group(1))
                
                    # create an empty dictionary for an unseen node
                    if current_node not in node_weights:
                        node_weights[current_node] = {}
                    
                    # create an empty set for a new beta
                    if beta not in node_weights[current_node]:
                        node_weights[current_node][beta] = set()
                        
                    # then add the weights
                    node_weights[current_node][beta].add(weight)
                


    
    all_passed = True
    failed_nodes = 0

    master_betas = [16,8,4,2,1]

    for master_beta in master_betas:
    
        for node, beta_data in node_weights.items():
            if beta >= master_beta:
                    continue
            
            if beta not in beta_data:
                print(f"Node {node} is missing Beta {beta} data. Skipping.")
                continue

            b_weights = beta_data[master_betas]

            if not min:
            # b_val = min(b_weights)
                b_val = max(b_weights)
            
                for beta in betas:
                    if beta == master_beta or beta not in beta_data:
                        print(f"Node {node} is missing Beta {master_beta} data. Skipping.")
                        continue
                        
                    current_beta_weights = beta_data[beta]
                    #current_min = min(current_beta_weights)
                    current_max = max(current_beta_weights)
                    
                    # if there is no intersection between the Beta 16 weight and the current beta's weights => fail and its not <= then the min
                    if not b_weights.intersection(current_beta_weights) and b_val < current_max:
                        print(f"[FAIL] Node {node} at Beta {beta}:")
                        print(f"Beta {master_beta} weight {b_weights} not found in {current_beta_weights}")
                        print(f"Beta {master_beta} weight ({b_weights}) is strictly greater than the minimum weight in Beta {beta} ({current_max}).")
                        all_passed = False
                        failed_nodes += 1
            if min:
                b_val = min(b_weights)
        
                        
                for beta in betas:
                    if beta == master_beta or beta not in beta_data:
                        print(f"Node {node} is missing Beta {master_beta} data. Skipping.")
                        continue
                                    
                current_beta_weights = beta_data[beta]
                current_min = min(current_beta_weights)
                                
                                
                # if there is no intersection between the Beta 16 weight and the current beta's weights => fail and its not <= then the min
                if not b_weights.intersection(current_beta_weights) and b_val < current_min:
                    print(f"[FAIL] Node {node} at Beta {beta}:")
                    print(f"Beta {master_beta} weight {b_weights} not found in {current_beta_weights}")
                    print(f"Beta {master_beta} weight ({b_weights}) is strictly greater than the minimum weight in Beta {beta} ({current_min}).")
                    all_passed = False
                    failed_nodes += 1
    if all_passed:
        print(f"SUCCESS! Verified {len(node_weights)} nodes.")
    else:
        print(f"VERIFICATION FAILED. Found {failed_nodes} where the property did not hold.")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Verify extracted weights across different beta values.")
    
    parser.add_argument(
        "log_dir", 
        type=str, 
        help="The base directory to check (e.g., program_outputs or program_outputs_max_lab)"
    )

    parser.add_argument(
            "is_min_lab", 
            type=bool, 
            help="Is it min labeling (True), or is it max labeling (False)"
    )
    
    args = parser.parse_args()
    
    verify_weights(args.log_dir, args.is_min_lab)