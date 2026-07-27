import networkx as nx
import re
from z3 import Bool, is_true, Not, And, sat
import pprint
from sxpat.utils.print import pprint

class MultiPartitionIterationEngine:

    @staticmethod
    def extract_multiple_subgraphs(opt, G, specs_obj, mode='multi', penalty=None):
        """
        Extracts multiple subgraphs iteratively from the solver model based on mode.
        """
        all_partitions = {}
        count = specs_obj.num_subgraphs
        
        while count > 0:
            node_partition = []
            attempt_label = specs_obj.num_subgraphs - count + 1 if mode == 'multi' else count
            pprint.info1(f'Attempt {attempt_label}: ', end='')
            
            c = opt.check()
            if c == sat:
                # print(opt.model())
                m = opt.model()
                penalty_output = None
                penalty_gate = None
                current_penalty = None
                # print(f'{m = }')
                for t in m.decls():
                    t_str = str(t)
                    if mode == 'multi':
                        if 'penalty_output' in t_str:
                            # print(f'{t} = {m[t]}')
                            penalty_output = m[t].as_long()
                        if 'penalty_gate' in t_str:
                            # print(f'{t} = {m[t]}')
                            penalty_gate = m[t].as_long()
                        if 'g' not in t_str:  # Look only the literals associate to the gates
                            continue
                        if is_true(m[t]):
                            gate_id = int(t_str[2:])
                            node_partition.append(gate_id) # Gates inside the partition
                    else:  # mode == 'single'
                        if 'penalty' in t_str:
                            print(f'{t} = {m[t]}')
                            current_penalty = m[t].as_long()
                        if 'g' not in t_str:
                            continue
                        if is_true(m[t]):
                            gate_id = int(t_str[2:])
                            node_partition.append(gate_id) # Gates inside the partition
            else:
                count = 0
                break

            # COMPONENT START: Optimization and Selection Constraints (OS)
            from sxpat.component_manager import ComponentManager
            ComponentManager.validate_selection_convexity(G, node_partition)
            # COMPONENT END: Optimization and Selection Constraints (OS)

            if c == sat:
                if mode == 'multi':
                    block_clause = [d() == True if m[d] else d() == False for d in m.decls() if 'g_' in d.name()]
                    opt.add(Not(And(block_clause)))
                    all_partitions[count] = (penalty_output, penalty_gate, node_partition)
                else:
                    block_clause = [d() == True if m[d] else d() == False for d in m.decls() if 'g' in d.name()]
                    opt.add(Not(And(block_clause)))
                    current_penalty = m[penalty].as_long()
                    print(f'{current_penalty}, {node_partition}')
                    all_partitions[count] = (current_penalty, node_partition)
                
            count -= 1
            
        return all_partitions
    
    @staticmethod
    def select_best_partition(all_partitions, mode='multi'):
        """
        Sorts partitions and extracts the best one based on mode.
        """
        if not all_partitions:
            return None, None, None

        if mode == 'multi':
            sorted_partitions = dict(
                sorted(
                    all_partitions.items(),
                    key=lambda item: (-len(item[1][2]), item[1][0], item[1][1])
                )
            )
            for par in sorted_partitions:
                print(f'{sorted_partitions[par] = }')

            first_key = next(iter(sorted_partitions))
            penalty_output, penalty_gate, node_partition = sorted_partitions.pop(first_key)
            return penalty_output, penalty_gate, node_partition, sorted_partitions
        
        else:  # mode == 'single'
            sorted_partitions = dict(
                sorted(
                    all_partitions.items(),
                    key=lambda item: (-len(item[1][1]), item[1][0])
                )
            )
            for par in sorted_partitions:
                print(f'{sorted_partitions[par] = }')
            
            penalty, node_partition = next(iter(sorted_partitions.values()))
            print(f'{penalty, node_partition}')
            return penalty, node_partition