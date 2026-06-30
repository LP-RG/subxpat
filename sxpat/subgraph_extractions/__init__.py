

from typing import List

from sxpat.graph.graph import IOGraph
from sxpat.specifications import Specifications
from sxpat.utils.print import pprint


def extract_subgraph(iograph: IOGraph, specs_obj: Specifications) -> List[str]:

    if len(iograph.nodes) == 0:
        pprint.warning('No gates are found in the graph! Skipping the subgraph extraction')
        return list()

    else:
        if specs_obj.requires_subgraph_extraction:
            if specs_obj.extraction_mode == 1:
                from sxpat.subgraph_extractions.legacy import find_subgraph
                pprint.info2(f"Partition with imax={specs_obj.imax} and omax={specs_obj.omax}. Looking for largest partition")
                subgraph_nodes = find_subgraph(iograph, specs_obj)

            elif specs_obj.extraction_mode == 2:
                from sxpat.subgraph_extractions.legacy import find_subgraph_sensitivity
                pprint.info2(f"Partition with sensitivity start... Using imax={specs_obj.imax}, omax={specs_obj.omax},"
                             f"and min_subgraph_size={specs_obj.min_subgraph_size}")

                iteration = 1
                cnt_nodes = 0
                specs_obj.sensitivity = 1
                n_outputs = len(self.output_dict)

                while (cnt_nodes < specs_obj.min_subgraph_size and iteration < n_outputs + 1):
                    pprint.info2(f"Sugraph iteration {iteration} ")
                    subgraph_nodes = find_subgraph_sensitivity(self, specs_obj)

                    iteration += 1
                    specs_obj.sensitivity = 2 ** iteration - 1
                    cnt_nodes = len(subgraph_nodes)

            elif specs_obj.extraction_mode == 3:
                from sxpat.subgraph_extractions.legacy import find_subgraph_sensitivity_no_io_constraints
                pprint.info2(f"Partition with sensitivity start... Using only min_subgraph_size={specs_obj.min_subgraph_size} parameter")

                iteration = 1
                cnt_nodes = 0
                specs_obj.sensitivity = 1
                n_outputs = len(self.output_dict)

                while (cnt_nodes < specs_obj.min_subgraph_size and iteration < n_outputs + 1):
                    pprint.info2(f"Sugraph iteration {iteration}")
                    subgraph_nodes = find_subgraph_sensitivity_no_io_constraints(self, specs_obj)

                    iteration += 1
                    specs_obj.sensitivity = 2 ** iteration - 1
                    cnt_nodes = len(subgraph_nodes)

            elif specs_obj.extraction_mode == 4:
                from sxpat.subgraph_extractions.legacy import find_subgraph_feasible
                pprint.info2(f"Partition with omax={specs_obj.omax} and feasibility constraints. Looking for largest partition")
                subgraph_nodes = find_subgraph_feasible(self, specs_obj)

            elif specs_obj.extraction_mode == 5:
                from sxpat.subgraph_extractions.legacy import find_subgraph_feasible_hard
                pprint.info2(f"Partition with omax={specs_obj.omax} and hard feasibility constraints. Looking for largest partition")
                subgraph_nodes = find_subgraph_feasible_hard(self, specs_obj)

            elif specs_obj.extraction_mode == 55:
                from sxpat.subgraph_extractions.legacy import find_subgraph_feasible_hard_datatype_bitvec
                pprint.info2(f"Partition with omax={specs_obj.omax} and hard constraints, imax, omax, assumptions, and BitVec, DataType. Looking for largest partition")
                subgraph_nodes = find_subgraph_feasible_hard_datatype_bitvec(self, specs_obj)

            elif specs_obj.extraction_mode == 6:
                from sxpat.subgraph_extractions.legacy import find_subgraph_feasible_hard_datatype_bitvec_mintreshold
                pprint.info2(f"Partition with hard constraints, imax={specs_obj.imax}, omax={specs_obj.omax}, assumptions, and BitVec, DataType. Looking for largest partition for smallest possible threshold")
                subgraph_nodes = find_subgraph_feasible_hard_datatype_bitvec_mintreshold(self, specs_obj)

            elif specs_obj.extraction_mode == 100:
                from sxpat.subgraph_extractions.legacy import slash_to_kill
                pprint.info2(f"Test with no imax, omax")
                subgraph_nodes = slash_to_kill(self, specs_obj)

            elif specs_obj.extraction_mode == 11:
                from sxpat.subgraph_extractions.legacy import find_subgraph_feasible_soft
                pprint.info2(f"Partition with omax={specs_obj.omax} and soft feasibility constraints. Looking for largest partition")

                subgraph_nodes = find_subgraph_feasible_soft(self, specs_obj)

            elif specs_obj.extraction_mode == 12:
                if self.subgraph_candidates:
                    pprint.info2(f"Selecting the next subgraph candidate")
                    subgraph_nodes = self.form_subgraph_from_partition()
                else:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and soft feasibility constraints on subgraph outputs. Looking for largest partition")
                    subgraph_nodes = self.find_subgraph_feasible_soft_outputs(specs_obj)  # Critian's subgraph extraction

            elif specs_obj.extraction_mode == 42:
                from sxpat.subgraph_extractions.manual import extract

                subgraph_nodes = extract(self.graph, specs_obj)

            else:
                raise Exception('invalid extraction mode!')

        else:
            subgraph_nodes = list(self.gate_dict.values())

        for gate in self.gate_dict.values():
            if gate in subgraph_nodes:
                self.graph.nodes[gate][SUBGRAPH] = 1
                self.graph.nodes[gate][COLOR] = RED
            else:
                self.graph.nodes[gate][SUBGRAPH] = 0
                self.graph.nodes[gate][COLOR] = WHITE

        self.subgraph_input_dict = self.extract_subgraph_inputs()
        self.subgraph_output_dict = self.extract_subgraph_outputs()
        self.subgraph_gate_dict = self.extract_subgraph_gates()
        self.extract_subgraph_fanin()  # TODO: only used for coloring
        self.extract_subgraph_fanout()  # TODO: only used for coloring

        self.subgraph_num_inputs = len(self.subgraph_input_dict)
        self.subgraph_num_outputs = len(self.subgraph_output_dict)
        self.subgraph_num_gates = len(self.subgraph_gate_dict)

        # logging
        if self.subgraph_num_gates > 0:
            pprint.success(f'subgraph found (#ofNodes={self.subgraph_num_gates})')
        else:
            pprint.warning('subgraph not found')

        return self.subgraph_num_gates != 0
