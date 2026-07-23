from typing import Dict, List
from typing_extensions import Self

import re
import io
import math
import networkx as nx
import functools as ft
from colorama import Fore
from os.path import join as path_join
from z3 import (
    And, Not, Sum, Bool, Implies, BoolVal, If, Or, BitVecVal, Int, IntVal,
    Optimize, sat, is_true,
    Datatype, BoolSort, BitVecSort,
)

from Z3Log_patched.graph import Graph
from Z3Log_patched.verilog import Verilog

from Z3Log_patched.utils import convert_verilog_to_gv, get_pure_name
from sxpat.utils.print import pprint
from sxpat.utils.graph import is_selection_convex

from .specifications import Specifications, Paths
from .config.config import (
    SUBGRAPH, WEIGHT,
    COLOR, WHITE, RED, BLUE, OLIVE,
    LABEL, SHAPE, STRICT, DIGRAPH, NODE, STYLE, FILLED, FILLCOLOR,
)

from sxpat.component_manager import ComponentManager

class AnnotatedGraph(Graph):
    __cached_loading_callable = None

    def __init__(self, circuit_verilog_path: str, run_paths: Paths.RunFiles, is_clean: bool = False) -> None:
        circuit_name = get_pure_name(circuit_verilog_path)

        # prepare a clean Verilog
        Verilog(circuit_verilog_path, tmp_v := path_join(run_paths.verilog, f'{circuit_name}.v'), run_paths.temporary)

        # convert the clean Verilog into a Yosys GV
        convert_verilog_to_gv(tmp_v, tmp_gv := path_join(run_paths.temporary, f'{circuit_name}.gv'), run_paths.temporary)

        # initialize the super class using the Yosys GV
        super().__init__(tmp_gv, is_clean)

        self.set_output_dict(self.sort_dict(self.output_dict))

        self.__subgraph_candidates = []
        self.__subgraph = None
        self.__subgraph_input_dict: Dict[int, str] = None
        self.__subgraph_output_dict: Dict[int, str] = None
        self.__subgraph_gate_dict: Dict[int, str] = None
        self.__subgraph_fanin_dict = None
        self.__subgraph_fanout_dict = None
        self.__graph_intact_gate_dict = None

        self.__subgraph_num_inputs = None
        self.__subgraph_num_outputs = None
        self.__subgraph_num_gates = None
        self.__subgraph_num_fanin = None
        self.__subgraph_num_fanout = None

        self.__add_weights()

        self.__out_annotated_graph_path = path_join(run_paths.graphviz, f'{self.name}_subgraph.gv')

    @classmethod
    def cached_load(cls, circuit_verilog_path: str, run_paths: Paths.RunFiles, is_clean: bool = False) -> Self:
        if cls.__cached_loading_callable is None: cls.set_loading_cache_size(-1)
        return cls.__cached_loading_callable(circuit_verilog_path, run_paths, is_clean)

    @classmethod
    def set_loading_cache_size(cls, new_size: int) -> None:
        """
            Set the new size for the loading cache (minimum of 3: 1 exact + 1 current + 1 from model).

            @warning: a call to this method invalidates the previous cache
        """
        from copy import deepcopy

        new_size = max(3, new_size)
        if cls.__cached_loading_callable is not None: cls.__cached_loading_callable.cache_clear()

        def make_cached_function(cache_size: int):
            cached = ft.lru_cache(cache_size)(cls)
            return ft.wraps(cls)(lambda *a, **k: deepcopy(cached(*a, **k)))

        cls.__cached_loading_callable = make_cached_function(new_size)

    @property
    def subgraph_candidates(self):
        return self.__subgraph_candidates

    @subgraph_candidates.setter
    def subgraph_candidates(self, this_candidates):
        self.__subgraph_candidates = this_candidates

    @property
    def subgraph(self):
        """[DEPRECATED] Alias of `.graph`"""
        return self.graph

    @property
    def subgraph_out_path(self):
        return self.__out_annotated_graph_path

    @subgraph_out_path.setter
    def subgraph_out_path(self, this_subgraph_out_path):
        self.__out_annotated_graph_path = this_subgraph_out_path

    @property
    def subgraph_input_dict(self):
        return self.__subgraph_input_dict

    @subgraph_input_dict.setter
    def subgraph_input_dict(self, this_subgraph_input_dict):
        self.__subgraph_input_dict = this_subgraph_input_dict

    @property
    def subgraph_output_dict(self):
        return self.__subgraph_output_dict

    @subgraph_output_dict.setter
    def subgraph_output_dict(self, this_subgraph_output_dict):
        self.__subgraph_output_dict = this_subgraph_output_dict

    @property
    def subgraph_gate_dict(self):
        return self.__subgraph_gate_dict

    @subgraph_gate_dict.setter
    def subgraph_gate_dict(self, this_subgraph_gate_dict):
        self.__subgraph_gate_dict = this_subgraph_gate_dict

    @property
    def graph_intact_gate_dict(self):
        return self.__graph_intact_gate_dict

    @graph_intact_gate_dict.setter
    def graph_intact_gate_dict(self, this_graph_intact_gate_dict):
        self.__graph_intact_gate_dict = this_graph_intact_gate_dict

    @property
    def subgraph_fanin_dict(self):
        return self.__subgraph_fanin_dict

    @subgraph_fanin_dict.setter
    def subgraph_fanin_dict(self, this_subgraph_fanin_dict):
        self.__subgraph_fanin_dict = this_subgraph_fanin_dict

    @property
    def subgraph_fanout_dict(self):
        return self.__subgraph_fanout_dict

    @subgraph_fanout_dict.setter
    def subgraph_fanout_dict(self, this_subgraph_fanout_dict):
        self.__subgraph_fanout_dict = this_subgraph_fanout_dict

    @property
    def subgraph_num_inputs(self):
        return self.__subgraph_num_inputs

    @subgraph_num_inputs.setter
    def subgraph_num_inputs(self, this_subgraph_num_inputs):
        self.__subgraph_num_inputs = this_subgraph_num_inputs

    @property
    def subgraph_num_outputs(self):
        return self.__subgraph_num_outputs

    @subgraph_num_outputs.setter
    def subgraph_num_outputs(self, this_subgraph_num_outputs):
        self.__subgraph_num_outputs = this_subgraph_num_outputs

    @property
    def subgraph_num_gates(self):
        return self.__subgraph_num_gates

    @subgraph_num_gates.setter
    def subgraph_num_gates(self, this_subgraph_num_gates):
        self.__subgraph_num_gates = this_subgraph_num_gates

    @property
    def subgraph_num_fanin(self):
        return self.__subgraph_num_fanin

    @subgraph_num_fanin.setter
    def subgraph_num_fanin(self, this_subgraph_num_fanin):
        self.__subgraph_num_fanin = this_subgraph_num_fanin

    @property
    def subgraph_num_fanout(self):
        return self.__subgraph_num_fanout

    @subgraph_num_fanout.setter
    def subgraph_num_fanout(self, this_subgraph_num_fanout):
        self.__subgraph_num_fanout = this_subgraph_num_fanout

    def sort_dict(self, this_dict: Dict) -> Dict:
        return dict(sorted(this_dict.items(), key=lambda x: x[0]))

    def get_subgraph_name(self, specs_obj: Specifications):
        raise
        # """
        # returns: a unique gv file name for this experiment (that is determined by specs_obj)
        # """
        # _, extension = OUTPUT_PATH[GV]

        # # TODO: Morteza: this naming convention is not generic enough,
        # # I will try to add every type of specification of the experiment into the name so it wouldn't get overwritten
        # # new fields that are added:
        # # for subxpat_v2 => et_partitioning
        # # for all num_of_models, omax, imax
        # # as a precautionary measure, we also add the time stamp at the end of every generated file

        # # So we change the names from "grid_adder_i6_o4_10X20_et10_subxpat_v2_mode4_SOP1" to
        # # 'grid_adder_i6_o4_10X20_et10_subxpat_v2_desc_fef1_sef1_mode4_omax1_imax3_kucTrue_SOP1_time20240403:214107'

        # # let's divide our nomenclature into X parts: head (common), technique_specific, tail (common)

        # head = f'grid_{specs_obj.current_benchmark}_{specs_obj.lpp}X{specs_obj.pit if specs_obj.template is TemplateType.SHARED else specs_obj.ppo}_et{specs_obj.et}_'

        # tool_name = {
        #     (False, TemplateType.NON_SHARED): XPAT,
        #     (False, TemplateType.SHARED): SHARED_XPAT,
        #     (True, TemplateType.NON_SHARED): SUBXPAT,
        #     (True, TemplateType.SHARED): SHARED_SUBXPAT,
        # }[(specs_obj.subxpat, specs_obj.template)]

        # technique_specific = f'{tool_name}_{specs_obj.error_partitioning.value}_'

        # tail = f'mode{specs_obj.extraction_mode}_omax{specs_obj.omax}_imax{specs_obj.imax}_'
        # tail += f'{specs_obj.template_name}_time'

        # # Get the current date and time
        # current_time = datetime.datetime.now()
        # # Format the date and time to create a unique identifier
        # time_stamp = current_time.strftime("%Y%m%d:%H%M%S")

        # name = head + technique_specific + tail + time_stamp

        # return f'{name}.{extension}'

    def get_subgraph_path(self, specs: Specifications):
        raise
        # """
        # returns: the path where the grid .gv file should be stored
        # """
        # folder, _ = OUTPUT_PATH[GV]
        # path = f'{folder}/{self.get_subgraph_name(specs)}'
        # return path

    def __add_weights(self):
        for n in self.graph.nodes:
            self.graph.nodes[n][WEIGHT] = 1

    def __repr__(self):
        return f'An object of class AnnotatedGraph:\n' \
               f'{self.name = }\n' \
               f'{self.subgraph_num_inputs = }\n' \
               f'{self.subgraph_num_outputs = }\n' \
               f'{self.subgraph_num_gates = }\n'

    def extract_subgraph(self, specs_obj: Specifications):

        if self.num_gates == 0:
            pprint.with_color(Fore.LIGHTYELLOW_EX)('No gates are found in the graph! Skipping the subgraph extraction')
            return False

        else:
            if specs_obj.requires_subgraph_extraction:
                if specs_obj.extraction_mode == 1:
                    pprint.info2(f"Partition with imax={specs_obj.imax} and omax={specs_obj.omax}. Looking for largest partition")
                    subgraph_nodes = self.find_subgraph(specs_obj)  # Critian's subgraph extraction

                elif specs_obj.extraction_mode == 2:
                    pprint.info2(f"Partition with sensitivity start... Using imax={specs_obj.imax}, omax={specs_obj.omax},"
                                 f"and min_subgraph_size={specs_obj.min_subgraph_size}")
                    iteration = 1
                    cnt_nodes = 0
                    specs_obj.sensitivity = 1
                    n_outputs = len(self.output_dict)

                    while (cnt_nodes < specs_obj.min_subgraph_size and iteration < n_outputs + 1):
                        # specs_obj.sensitivity = iteration
                        pprint.with_color(Fore.LIGHTBLUE_EX)(f"Sugraph iteration {iteration} ")
                        subgraph_nodes = self.find_subgraph_sensitivity(specs_obj)

                        iteration += 1
                        specs_obj.sensitivity = 2 ** iteration - 1
                        cnt_nodes = len(subgraph_nodes)

                elif specs_obj.extraction_mode == 3:
                    pprint.info2(f"Partition with sensitivity start... Using only min_subgraph_size={specs_obj.min_subgraph_size} parameter")
                    iteration = 1
                    cnt_nodes = 0
                    specs_obj.sensitivity = 1
                    n_outputs = len(self.output_dict)

                    while (cnt_nodes < specs_obj.min_subgraph_size and iteration < n_outputs + 1):
                        # specs_obj.sensitivity = iteration
                        pprint.info2(f"Sugraph iteration {iteration}")
                        subgraph_nodes = self.find_subgraph_sensitivity_no_io_constraints(specs_obj)

                        iteration += 1
                        specs_obj.sensitivity = 2 ** iteration - 1
                        cnt_nodes = len(subgraph_nodes)

                elif specs_obj.extraction_mode == 4:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and feasibility constraints. Looking for largest partition")
                    subgraph_nodes = self.find_subgraph_feasible(specs_obj)  # Cristian's subgraph extraction

                elif specs_obj.extraction_mode == 5:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and hard feasibility constraints. Looking for largest partition")
                    subgraph_nodes = self.find_subgraph_feasible_hard(specs_obj)  # Critian's subgraph extraction

                elif specs_obj.extraction_mode == 55:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and hard constraints, imax, omax, assumptions, and BitVec, DataType. Looking for largest partition")
                    subgraph_nodes = self.find_subgraph_feasible_hard_limited_inputs_datatype_bitvec(specs_obj)  # Critian's subgraph extraction

                elif specs_obj.extraction_mode == 6:
                    pprint.info2(f"Partition with hard constraints, imax={specs_obj.imax}, omax={specs_obj.omax}, assumptions, and BitVec, DataType. Looking for largest partition for smallest possible threshold")
                    subgraph_nodes = self.find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold(specs_obj)

                elif specs_obj.extraction_mode == 100:
                    pprint.info2(f"Test with no imax, omax")
                    subgraph_nodes = self.slash_to_kill(specs_obj)

                elif specs_obj.extraction_mode == 11:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and soft feasibility constraints. Looking for largest partition")
                    subgraph_nodes = self.find_subgraph_feasible_soft(specs_obj)  # Critian's subgraph extraction

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
            self.subgraph_fanin_dict = self.extract_subgraph_fanin()
            self.subgraph_fanout_dict = self.extract_subgraph_fanout()
            self.graph_intact_gate_dict = self.extract_graph_intact_gates()

            self.subgraph_num_inputs = len(self.subgraph_input_dict)
            self.subgraph_num_outputs = len(self.subgraph_output_dict)
            self.subgraph_num_gates = len(self.subgraph_gate_dict)
            self.subgraph_num_fanin = len(self.subgraph_fanin_dict)
            self.subgraph_num_fanout = len(self.subgraph_fanout_dict)
            self.graph_num_intact_gates = len(self.__graph_intact_gate_dict)

            # logging
            if self.subgraph_num_gates > 0:
                pprint.success(f'subgraph found (#ofNodes={self.subgraph_num_gates})')
            else:
                pprint.warning('subgraph not found')

            return self.subgraph_num_gates != 0

    def find_subgraph(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """

        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph: nx.DiGraph = self.graph.copy(as_view=False)

        # Optimizer
        opt = Optimize()

        # COMPONENT START: Model Initialization
        G, input_literals, gate_literals, output_literals, input_edges, gate_edges, output_edges = \
            ComponentManager.prepare_circuit_model(tmp_graph, self.constant_dict, opt)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Signal Propagation Constraints (SP)
        partition_input_edges, partition_output_edges = ComponentManager.get_signal_propagation_minimal(
        input_edges, gate_edges, output_edges,
        input_literals, gate_literals, output_literals
        )
        # COMPONENT END: Signal Propagation Constraints (SP)

        # COMPONENT START: Sensitivity Budget Constraints (SB)
        gate_weight = ComponentManager.prepare_gate_weights(G, tmp_graph, self.gate_dict, WEIGHT)
        # COMPONENT END: Sensitivity Budget Constraints (SB)

        # COMPONENT START: Convexity and Structural Constraints (CS)
        ComponentManager.add_convexity(opt, G, gate_literals, gate_edges)
        # COMPONENT END: Convexity and Structural Constraints (CS)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_io_limits(
        opt, 
        specs_obj.imax, 
        specs_obj.omax, 
        partition_input_edges, 
        partition_output_edges
        )
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_maximization(opt, gate_literals, gate_weight)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # =========================== Skipping the nodes that are not labeled ================================
        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.exclude_skipped_nodes(opt, self.graph)
        # COMPONENT END: Optimization and Selection Constraints (OS)
        # ====================================================================================================

        # COMPONENT START: Optimization and Selection Constraints (OS)
        subgraph_nodes = ComponentManager.check_convexity(opt, self.graph, self.gate_dict)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        return subgraph_nodes

    def find_subgraph_sensitivity(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """

        sensitivity_t = specs_obj.sensitivity

        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph = self.graph.copy(as_view=False)

        # Optimizer
        opt = Optimize()

        # COMPONENT START: Model Initialization
        G, input_literals, gate_literals, output_literals, input_edges, gate_edges, output_edges = \
            ComponentManager.prepare_circuit_model(tmp_graph, self.constant_dict, opt)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Signal Propagation Constraints (SP)
        partition_input_edges, partition_output_edges, edge_w, edge_constraint = \
        ComponentManager.get_signal_propagation(
        input_edges, gate_edges, output_edges,
        input_literals, gate_literals, output_literals,
        tmp_graph, self.__gate_dict, WEIGHT
        )
        # COMPONENT END: Signal Propagation Constraints (SP)

        # COMPONENT START: Sensitivity Budget Constraints (SB)
        gate_weight = ComponentManager.prepare_gate_weights(G, tmp_graph, self.gate_dict, WEIGHT)
        # COMPONENT END: Sensitivity Budget Constraints (SB)

        # COMPONENT START: Convexity and Structural Constraints (CS)
        ComponentManager.add_convexity(opt, G, gate_literals, gate_edges)
        # COMPONENT END: Convexity and Structural Constraints (CS)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_io_limits(
        opt, 
        specs_obj.imax, 
        specs_obj.omax, 
        partition_input_edges, 
        partition_output_edges
        )
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # COMPONENT START: Sensitivity Budget Constraints (SB)
        ComponentManager.add_sensitivity_budget(opt, edge_w, edge_constraint, sensitivity_t)
        # COMPONENT END: Sensitivity Budget Constraints (SB)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_maximization(opt, gate_literals)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # =========================== Skipping the nodes that are not labeled ================================
        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.exclude_skipped_nodes(opt, self.graph)
        # COMPONENT END: Optimization and Selection Constraints (OS)
        # ====================================================================================================
        
        # COMPONENT START: Optimization and Selection Constraints (OS)
        subgraph_nodes = ComponentManager.check_convexity(opt, self.graph, self.gate_dict)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        return subgraph_nodes

    def find_subgraph_sensitivity_no_io_constraints(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        sensitivity_t = specs_obj.sensitivity

        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph = self.graph.copy(as_view=False)

        # Optimizer
        opt = Optimize()

        # COMPONENT START: Model Initialization
        G, input_literals, gate_literals, output_literals, input_edges, gate_edges, output_edges = \
            ComponentManager.prepare_circuit_model(tmp_graph, self.constant_dict, opt)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Signal Propagation Constraints (SP)
        partition_input_edges, partition_output_edges, edge_w, edge_constraint = \
        ComponentManager.get_signal_propagation(
        input_edges, gate_edges, output_edges,
        input_literals, gate_literals, output_literals,
        tmp_graph, self.__gate_dict, WEIGHT
        )
        # COMPONENT END: Signal Propagation Constraints (SP)

        # COMPONENT START: Sensitivity Budget Constraints (SB)
        gate_weight = ComponentManager.prepare_gate_weights(G, tmp_graph, self.gate_dict, WEIGHT)
        # COMPONENT END: Sensitivity Budget Constraints (SB)

        # COMPONENT START: Convexity and Structural Constraints (CS)
        ComponentManager.add_convexity(opt, G, gate_literals, gate_edges)
        # COMPONENT END: Convexity and Structural Constraints (CS)

        # COMPONENT START: Sensitivity Budget Constraints (SB)
        ComponentManager.add_sensitivity_budget(opt, edge_w, edge_constraint, sensitivity_t)
        # COMPONENT END: Sensitivity Budget Constraints (SB)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_maximization(opt, gate_literals)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # =========================== Skipping the nodes that are not labeled ================================
        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.exclude_skipped_nodes(opt, self.graph)
        # COMPONENT END: Optimization and Selection Constraints (OS)
        # ====================================================================================================

        # COMPONENT START: Optimization and Selection Constraints (OS)
        subgraph_nodes = ComponentManager.check_convexity(opt, self.graph, self.gate_dict)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        return subgraph_nodes

    def find_subgraph_feasible(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        
        feasibility_treshold = specs_obj.et

        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph = self.graph.copy(as_view=False)

        # Optimizer
        opt = Optimize()

        # COMPONENT START: Model Initialization
        G, input_literals, gate_literals, output_literals, input_edges, gate_edges, output_edges = \
            ComponentManager.prepare_circuit_model(tmp_graph, self.constant_dict, opt)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Signal Propagation Constraints (SP)
        partition_input_edges, partition_output_edges, edge_w, edge_constraint = \
        ComponentManager.get_signal_propagation(
        input_edges, gate_edges, output_edges,
        input_literals, gate_literals, output_literals,
        tmp_graph, self.__gate_dict, WEIGHT
        )
        # COMPONENT END: Signal Propagation Constraints (SP)

        # COMPONENT START: Model Initialization
        gate_weight = ComponentManager.extract_gate_weights(G, tmp_graph, self.gate_dict, WEIGHT)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Convexity and Structural Constraints (CS)
        ComponentManager.add_convexity(opt, G, gate_literals, gate_edges)
        # COMPONENT END: Convexity and Structural Constraints (CS)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_io_limits(
        opt, 
        specs_obj.imax, 
        specs_obj.omax, 
        partition_input_edges, 
        partition_output_edges
        )
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # COMPONENT START: Feasibility and Filtering Constraints (FF)
        feasibility_constraints = ComponentManager.get_feasibility(
            edge_w, gate_weight, feasibility_treshold, edge_constraint, strict=True
        )
        # COMPONENT END: Feasibility and Filtering Constraints (FF)

        # COMPONENT START: Feasibility and Filtering Constraints (FF)
        ComponentManager.add_feasibility_logic(opt, feasibility_constraints, mode='at_least_one')
        # COMPONENT END: Feasibility and Filtering Constraints (FF)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_maximization(opt, gate_literals)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # =========================== Skipping the nodes that are not labeled ================================
        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.exclude_skipped_nodes(opt, self.graph)
        # COMPONENT END: Optimization and Selection Constraints (OS)
        # ====================================================================================================
        
        # COMPONENT START: Optimization and Selection Constraints (OS)
        subgraph_nodes = ComponentManager.check_convexity(opt, self.graph, self.gate_dict)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        return subgraph_nodes

    def find_subgraph_feasible_hard(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """

        feasibility_treshold = specs_obj.et

        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph = self.graph.copy(as_view=False)

        # Optimizer
        opt = Optimize()

        # COMPONENT START: Model Initialization
        G, input_literals, gate_literals, output_literals, input_edges, gate_edges, output_edges = \
            ComponentManager.prepare_circuit_model(tmp_graph, self.constant_dict, opt)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Signal Propagation Constraints (SP)
        partition_input_edges, partition_output_edges, edge_w, edge_constraint = \
        ComponentManager.get_signal_propagation(
        input_edges, gate_edges, output_edges,
        input_literals, gate_literals, output_literals,
        tmp_graph, self.gate_dict, WEIGHT
        )
        # COMPONENT END: Signal Propagation Constraints (SP)

        # COMPONENT START: Model Initialization
        gate_weight = ComponentManager.extract_gate_weights(G, tmp_graph, self.gate_dict, WEIGHT)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Convexity and Structural Constraints (CS)
        ComponentManager.add_convexity(opt, G, gate_literals, gate_edges)
        # COMPONENT END: Convexity and Structural Constraints (CS)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_io_limits(
        opt, 
        specs_obj.imax, 
        specs_obj.omax, 
        partition_input_edges, 
        partition_output_edges
        )
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # COMPONENT START: Feasibility and Filtering Constraints (FF)
        feasibility_constraints = ComponentManager.get_feasibility(
            edge_w, gate_weight, feasibility_treshold, edge_constraint, strict=True
        )
        # COMPONENT END: Feasibility and Filtering Constraints (FF)

        # COMPONENT START: Feasibility and Filtering Constraints (FF)
        ComponentManager.add_feasibility_logic(
            opt, feasibility_constraints, 
            partition_output_edges=partition_output_edges, 
            mode='match_outputs'
        )
        # COMPONENT END: Feasibility and Filtering Constraints (FF)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_maximization(opt, gate_literals, gate_weight)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # =========================== Skipping the nodes that are not labeled ================================
        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.exclude_skipped_nodes(opt, self.graph)
        # COMPONENT END: Optimization and Selection Constraints (OS)
        # ====================================================================================================

        # COMPONENT START: Optimization and Selection Constraints (OS)
        subgraph_nodes = ComponentManager.check_convexity(opt, self.graph, self.gate_dict)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        return subgraph_nodes

    def find_subgraph_feasible_hard_limited_inputs_datatype_bitvec(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """

        omax = specs_obj.omax
        imax = specs_obj.imax
        feasibility_threshold = specs_obj.et

        opt = Optimize()

        # COMPONENT START: Bitvector Topology Management====================================================

        # COMPONENT START: Datatype Model Initialization
        Node, Edge, nodes, edges, NUM_BITS = ComponentManager.datatype_model_initialization(
            self.graph, WEIGHT, self.input_dict, self.gate_dict, self.output_dict, self.constant_dict, opt, self.num_outputs, self.num_gates
        )
        # COMPONENT END: Datatype Model Initialization

        # COMPONENT START: Datatype Signal Propagation Constraints
        unique_incoming_edges, unique_outgoing_edges, max_nodes = ComponentManager.datatype_signal_propagation_constraints(
            self.graph, nodes, Node, NUM_BITS
        )
        # COMPONENT END: Datatype Signal Propagation Constraints

        # COMPONENT START: Datatype Convexity and Structural Constraints
        ComponentManager.datatype_convexity_and_structural_constraints(
            self.graph, nodes, Node, opt
        )
        # COMPONENT END: Datatype Convexity and Structural Constraints

        # COMPONENT START: Datatype Feasibility and Filtering Constraints
        opt.add(ComponentManager.datatype_feasibility_and_filtering_constraints(
            edges, Node, Edge, NUM_BITS, feasibility_threshold, sum_mode=False
        ))
        # COMPONENT END: Datatype Feasibility and Filtering Constraints

        # COMPONENT START: Datatype Optimization and Selection Constraints
        return ComponentManager.datatype_optimization_and_selection_constraints(
            opt, max_nodes, self.graph, self.gate_dict, 
            imax=imax, omax=omax, 
            unique_incoming_edges=unique_incoming_edges, 
            unique_outgoing_edges=unique_outgoing_edges, 
            apply_io_limits=True
        )
        # COMPONENT END: Datatype Optimization and Selection Constraints

        # COMPONENT END: Bitvector Topology Management======================================================

    def get_null_subgraph(self) -> nx.DiGraph:
        """Returns a graph with subgraph information for the null subgraph"""
        subgraph = self.graph.copy()
        for gate_name in self.gate_dict.values():
            subgraph.nodes[gate_name][SUBGRAPH] = 0
            subgraph.nodes[gate_name][COLOR] = WHITE
        return subgraph

    def get_subgraph_nodes_count(self, graph: nx.DiGraph) -> int:
        return sum(
            graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1
            for gate_idx in self.gate_dict
        )

    def find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold(self, specs_obj: Specifications) -> List[str]:
        # store parameters that will be updated
        saved_et = specs_obj.et

        # get graph weights, then min/max (bounded)
        weights = sorted(frozenset(
            weight
            for gate_name in self.gate_dict.values()
            if (weight := self.graph.nodes[gate_name][WEIGHT]) >= 0
        ))
        if len(weights) == 0: return []
        min_weight = max(0, min(weights))
        max_weight = min(saved_et, max(weights))

        # use linear partition to find best match in weights
        partition_step = (max_weight - min_weight) / (8 - 1)
        linear_partition = [min_weight + partition_step * i for i in range(8)]
        actual_partition = sorted(frozenset(
            min(weights, key=lambda w: abs(w - p))
            for p in linear_partition
        ))

        # find subgraph
        # NOTE: given that the node with the smallest weight is a valid subgraph, this loop should only iterate once
        for (i, specs_obj.et) in enumerate(actual_partition):
            subgraph_nodes = self.find_subgraph_feasible_hard_limited_inputs_datatype_bitvec(specs_obj)  # Critian's subgraph extraction
            if len(subgraph_nodes) > 0: break

        # restore updated parameters
        specs_obj.et = saved_et

        return subgraph_nodes

    def slash_to_kill(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """

        omax = specs_obj.omax
        imax = specs_obj.imax
        feasibility_threshold = specs_obj.et

        opt = Optimize()

        # COMPONENT START: Bitvector Topology Management====================================================

        # COMPONENT START: Datatype Model Initialization
        Node, Edge, nodes, edges, NUM_BITS = ComponentManager.datatype_model_initialization(
            self.graph, WEIGHT, self.input_dict, self.gate_dict, self.output_dict, self.constant_dict, opt, self.num_outputs, self.num_gates
        )
        # COMPONENT END: Datatype Model Initialization

        # COMPONENT START: Datatype Signal Propagation Constraints
        unique_incoming_edges, unique_outgoing_edges, max_nodes = ComponentManager.datatype_signal_propagation_constraints(
            self.graph, nodes, Node, NUM_BITS
        )
        # COMPONENT END: Datatype Signal Propagation Constraints

        # COMPONENT START: Datatype Convexity and Structural Constraints
        ComponentManager.datatype_convexity_and_structural_constraints(
            self.graph, nodes, Node, opt
        )
        # COMPONENT END: Datatype Convexity and Structural Constraints

        # COMPONENT START: Datatype Parent-Child Connectivity Constraints
        ComponentManager.datatype_parent_child_constraints(
            self.graph, nodes, Node, opt
        )
        # COMPONENT END: Datatype Parent-Child Connectivity Constraints

        # COMPONENT START: Datatype Feasibility and Filtering Constraints
        opt.add(ComponentManager.datatype_feasibility_and_filtering_constraints(
            edges, Node, Edge, NUM_BITS, feasibility_threshold, sum_mode=True
        ))
        # COMPONENT END: Datatype Feasibility and Filtering Constraints

        # COMPONENT START: Datatype Optimization and Selection Constraints
        return ComponentManager.datatype_optimization_and_selection_constraints(
            opt, max_nodes, self.graph, self.gate_dict, 
            apply_io_limits=False
        )
        # COMPONENT END: Datatype Optimization and Selection Constraints

        # COMPONENT END: Bitvector Topology Management======================================================

    def find_subgraph_feasible_soft(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """

        feasibility_treshold = specs_obj.et

        tmp_graph = self.graph.copy(as_view=False)

        # Optimizer
        opt = Optimize()

        # COMPONENT START: Model Initialization
        G, input_literals, gate_literals, output_literals, input_edges, gate_edges, output_edges = \
            ComponentManager.prepare_circuit_model(tmp_graph, self.constant_dict, opt)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Signal Propagation Constraints (SP)
        partition_input_edges, partition_output_edges, edge_w, edge_constraint = \
        ComponentManager.get_signal_propagation(
            input_edges, gate_edges, output_edges,
            input_literals, gate_literals, output_literals,
            tmp_graph, self.__gate_dict, WEIGHT
        )
        # COMPONENT END: Signal Propagation Constraints (SP)

        # COMPONENT START: Model Initialization
        gate_weight = ComponentManager.extract_gate_weights(G, tmp_graph, self.gate_dict, WEIGHT)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Convexity and Structural Constraints (CS)
        ComponentManager.add_convexity(opt, G, gate_literals, gate_edges)
        # COMPONENT END: Convexity and Structural Constraints (CS)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_io_limits(
            opt, 
            specs_obj.imax, 
            specs_obj.omax, 
            partition_input_edges, 
            partition_output_edges
        )
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # COMPONENT START: Feasibility and Filtering Constraints (FF)
        feasibility_constraints = ComponentManager.get_feasibility(
            edge_w, gate_weight, feasibility_treshold, edge_constraint, strict=True
        )
        # COMPONENT END: Feasibility and Filtering Constraints (FF)

        # COMPONENT START: Feasibility and Filtering Constraints (FF)
        ComponentManager.add_feasibility_logic(opt, feasibility_constraints, mode='at_least_one')
        # COMPONENT END: Feasibility and Filtering Constraints (FF)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_maximization(opt, gate_literals)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # =========================== Skipping the nodes that are not labeled ================================
        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.exclude_skipped_nodes(opt, self.graph)
        # COMPONENT END: Optimization and Selection Constraints (OS)
        # ====================================================================================================

        # =========================== Coming up with a penalty for each subgraph =============================
        # COMPONENT START: Penalty-based Soft Constraints (PS)
        penalty = Int('penalty')

        output_individual_penalty = ComponentManager.get_penalty_terms(
            edge_w, gate_weight, feasibility_treshold, gate_literals
        )
        # COMPONENT END: Penalty-based Soft Constraints (PS)

        # COMPONENT START: Penalty-based Soft Constraints (PS)
        ComponentManager.apply_penalty(
            opt, 
            penalty, 
            output_individual_penalty, 
            2 * feasibility_treshold, 
            weight=1
        )
        # COMPONENT END: Penalty-based Soft Constraints (PS)
        # ===================================================================================================

        # ======================== Check for multiple subgraphs =============================================
        # COMPONENT START: Multi-Partition Iteration Engine (MPE)
        all_partitions = ComponentManager.extract_multiple_subgraphs(
            opt, G, specs_obj, mode='single', penalty=penalty
        )
        # COMPONENT END: Multi-Partition Iteration Engine (MPE)
        # ===================================================================================================

        # =======================Pick the Subgraph with the lowest penalty ==================================
        # COMPONENT START: Multi-Partition Iteration Engine (MPE)
        penalty, node_partition = ComponentManager.select_best_partition(all_partitions, mode='single')
        # COMPONENT END: Multi-Partition Iteration Engine (MPE)
        # ===================================================================================================

        return [self.gate_dict[idx] for idx in node_partition]

    def find_subgraph_feasible_soft_outputs(self, specs_obj: Specifications) -> List[str]:
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        imax = specs_obj.imax
        omax = specs_obj.omax
        feasibility_treshold = specs_obj.et

        tmp_graph = self.graph.copy(as_view=False)

        # Optimizer
        opt = Optimize()

        # COMPONENT START: Model Initialization
        G, input_literals, gate_literals, output_literals, input_edges, gate_edges, output_edges = \
            ComponentManager.prepare_circuit_model(tmp_graph, self.constant_dict, opt)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Signal Propagation Constraints (SP)
        partition_input_edges, partition_output_edges, partition_output_edges_penalty, edge_w, edge_constraint = \
            ComponentManager.get_signal_propagation_with_penalty(
                input_edges, gate_edges, output_edges,
                input_literals, gate_literals, output_literals,
                tmp_graph, self.__gate_dict, WEIGHT, feasibility_treshold
            )
        # COMPONENT END: Signal Propagation Constraints (SP)

        # COMPONENT START: Model Initialization
        gate_weight = ComponentManager.extract_gate_weights(G, tmp_graph, self.gate_dict, WEIGHT)
        # COMPONENT END: Model Initialization

        # COMPONENT START: Convexity and Structural Constraints (CS)
        ComponentManager.add_convexity(opt, G, gate_literals, gate_edges)
        # COMPONENT END: Convexity and Structural Constraints (CS)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_io_limits(
            opt, 
            specs_obj.imax, 
            specs_obj.omax, 
            partition_input_edges, 
            partition_output_edges
        )
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # COMPONENT START: Feasibility and Filtering Constraints (FF)
        feasibility_constraints = ComponentManager.get_feasibility(
            edge_w, gate_weight, feasibility_treshold, edge_constraint, strict=True
        )
        # COMPONENT END: Feasibility and Filtering Constraints (FF)

        # COMPONENT START: Feasibility and Filtering Constraints (FF)
        ComponentManager.add_feasibility_logic(opt, feasibility_constraints, mode='at_least_one')
        # COMPONENT END: Feasibility and Filtering Constraints (FF)

        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.add_maximization(opt, gate_literals)
        # COMPONENT END: Optimization and Selection Constraints (OS)

        # =========================== Skipping the nodes that are not labeled ================================
        # COMPONENT START: Optimization and Selection Constraints (OS)
        ComponentManager.exclude_skipped_nodes(opt, self.graph)
        # COMPONENT END: Optimization and Selection Constraints (OS)
        # ====================================================================================================

        # =========================== Coming up with a penalty for each subgraph =============================
        # COMPONENT START: Penalty-based Soft Constraints (PS)
        penalty_output = Int('penalty_output')
        penalty_gate = Int('penalty_gate')

        output_individual_penalty = ComponentManager.get_penalty_terms(
            edge_w, gate_weight, feasibility_treshold, gate_literals
        )
        # COMPONENT END: Penalty-based Soft Constraints (PS)

        # COMPONENT START: Penalty-based Soft Constraints (PS)
        ComponentManager.apply_penalty(
            opt, 
            penalty_output, 
            partition_output_edges_penalty, 
            omax * feasibility_treshold, 
            weight=100
        )
        ComponentManager.apply_penalty(
            opt, 
            penalty_gate, 
            output_individual_penalty, 
            omax * feasibility_treshold, 
            weight=1
        )
        # COMPONENT END: Penalty-based Soft Constraints (PS)
        # ====================================================================================================

        # ======================== Check for multiple subgraphs ==============================================
        # COMPONENT START: Multi-Partition Iteration Engine (MPE)
        all_partitions = ComponentManager.extract_multiple_subgraphs(
            opt, G, specs_obj, mode='multi'
        )
        # COMPONENT END: Multi-Partition Iteration Engine (MPE)
        # ====================================================================================================

        # =======================Pick the Subgraph with the lowest penalty ===================================
        # COMPONENT START: Multi-Partition Iteration Engine (MPE)
        penalty_output, penalty_gate, node_partition, sorted_partitions = ComponentManager.select_best_partition(
            all_partitions, mode='multi'
        )
        # COMPONENT END: Multi-Partition Iteration Engine (MPE)
        # ====================================================================================================
        self.subgraph_candidates = sorted_partitions

        return [self.gate_dict[idx] for idx in node_partition]

    def export_annotated_graph(self, filename: str = None):
        """
        exports the subgraph (annotated graph) to a GV (GraphViz) file
        :return:
        """
        with open(filename or self.subgraph_out_path, 'w') as f:
            f.write(f"{STRICT} {DIGRAPH} \"{self.name}\" {{\n")
            f.write(f"{NODE} [{STYLE} = {FILLED}, {FILLCOLOR} = {WHITE}]\n")
            for n in self.subgraph.nodes:
                self.export_node(n, f)
            for e in self.subgraph.edges:
                self.export_edge(e, f)
            f.write(f"}}\n")

    # TODO:for external modifications
    def evaluate_subgraph_error(self) -> float:
        """
        This function removes the annotated part (so called the subgraph) of the graph and the evaluates the error (which
        is a metric of choice)
        :return: the computed error
        """
        # 1) read the exact circuit
        # 2) create a copy of the self.graph and remove the annotated nodes, and consider it as an approximate graph
        return 0.0

    # TODO: fix checks!
    # The checks are done on the original graph instead of the annotated graph!
    def export_node(self, n, file_handler: io.TextIOBase):
        """
        exports node n as a line of file that is identified by file_hanlder
        :param n: the label of node n
        :param file_handler: the file object
        :return: nothing
        """
        if self.is_cleaned_pi(n) or self.is_cleaned_po(n):
            if WEIGHT in self.subgraph.nodes[n]:
                label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\""
            else:
                label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\""

            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            elif COLOR in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            if WEIGHT in self.subgraph.nodes[n]:
                weight = f'{WEIGHT} = {self.subgraph.nodes[n][WEIGHT]}'
            else:
                weight = f'{WEIGHT} = -1'
        elif self.is_cleaned_gate(n):
            label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\\n{n}\\n{self.subgraph.nodes[n][WEIGHT]}\""
            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            if WEIGHT in self.subgraph.nodes[n]:
                weight = f'{WEIGHT} = {self.subgraph.nodes[n][WEIGHT]}'
            else:
                weight = f'{WEIGHT} = -1'
        elif self.is_cleaned_constant(n):
            label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\\n{n}\""
            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            if WEIGHT in self.subgraph.nodes[n]:
                weight = f'{WEIGHT} = {self.subgraph.nodes[n][WEIGHT]}'
            else:
                weight = f'{WEIGHT} = -1'
        else:
            pprint.error(f'ERROR!!! a problem occurred while exporting an annotated graph {self.__out_annotated_graph_path}')
            raise
        line = f"{n} [{label}, {shape}, {color}, {weight}];\n"
        file_handler.write(line)

    def color_subgraph_node(self, n, this_color):
        """
        changes the color of node n to this_color.
        :param n: the label of node n
        :param this_color: the desired color
        :return: nothing
        """
        self.subgraph.nodes[n][COLOR] = this_color

    def is_subgraph_member(self, n):
        """
        checks whether node n belongs to the subgraph
        :param n: a node
        :return: True if node n belongs to the subgraph, otherwise returns False
        """
        if SUBGRAPH in self.subgraph.nodes[n]:
            if self.subgraph.nodes[n][SUBGRAPH] == 1:
                return True
            else:
                return False
        else:
            return False

    def is_subgraph_fanin(self, n):
        """
        checks whether node n is in the fanin logic of the subgraph
        :param n: a node
        :return: True if node n is in the fanin logic, otherwise returns False
        """
        if not self.is_subgraph_member(n):
            successors = list(self.subgraph.successors(n))
            for sn in successors:
                if self.is_subgraph_member(sn):
                    return True
        else:
            return False

    def is_subgraph_fanout(self, n):
        """
        checks whether node n is in the fanout logic of the subgraph
        :param n: a node
        :return: True if node n is in the fanout logic, otherwise returns False
        """
        if not self.is_subgraph_member(n):
            predecessors = list(self.subgraph.predecessors(n))
            for pn in predecessors:
                if self.is_subgraph_member(pn):
                    return True
        else:
            return False

    def is_subgraph_output(self, n):
        """
        checks whether node n is an output node of the subgraph; an output node is node that has an outgoing edge
        from the subgraph.
        :param n: a node
        :return: True if node n is in the fanout logic, otherwise returns False
        """
        if self.is_subgraph_member(n):
            successors = list(self.subgraph.successors(n))
            for sn in successors:
                if not self.is_subgraph_member(sn):
                    return True
        return False

    # TODO:
    # This part should generate a comment in verilog expressing:
    # Annotated subgraph inputs

    def is_subgraph_input(self, n):
        """
        checks whether node n is an input node of the subgraph; an input node is a (non-member) node that has an ingoing edge
        to the subgraph.
        :param n: a node
        :return: True if node n is in the fanout logic, otherwise returns False
        """
        if not self.is_subgraph_member(n):
            successors = list(self.subgraph.successors(n))
            for sn in successors:
                if self.is_subgraph_member(sn):
                    return True

        return False

    def extract_subgraph_gates(self) -> Dict[int, str]:
        """
        extracts subgraph gates and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: gate_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        s_gates_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())

        for n in self.subgraph.nodes:
            if SUBGRAPH in self.subgraph.nodes[n] and self.subgraph.nodes[n][SUBGRAPH] == 1:
                s_gates_dict[graph_gate_list.index(n)] = n

        return s_gates_dict

    def extract_graph_intact_gates(self):
        """
        extracts non-subgraph gates and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: gate_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        s_gates_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())

        for n in graph_gate_list:
            if not self.is_subgraph_member(n):
                s_gates_dict[graph_gate_list.index(n)] = n

        return s_gates_dict

    def extract_subgraph_inputs(self):
        """
        extracts subgraph inputs (non-member nodes) and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: subgraph_input_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        s_input_dict: Dict[int, str] = {}
        idx = 0
        for n in self.graph.nodes:
            if self.is_subgraph_input(n):
                s_input_dict[idx] = n
                idx += 1
        return s_input_dict

    def extract_subgraph_outputs(self):
        """
        extracts subgraph outputs and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: subgraph_output_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        tmp_output_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())
        idx = 0
        for n in self.subgraph.nodes:
            if self.is_subgraph_output(n):
                tmp_output_dict[idx] = n
                idx += 1
                self.color_subgraph_node(n, BLUE)
        # print(f'{tmp_output_dict = }')
        return tmp_output_dict

    # TODO
    # Deprecated
    def extract_subgraph_fanin(self):
        tmp_fanin_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())
        idx = 0
        for n in self.subgraph.nodes:
            if self.is_subgraph_fanin(n):
                tmp_fanin_dict[idx] = n
                idx += 1
                self.color_subgraph_node(n, OLIVE)
        return tmp_fanin_dict

    def extract_subgraph_fanout(self):
        tmp_fanout_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())
        idx = 0
        for n in self.subgraph.nodes:
            if self.is_subgraph_fanout(n):
                tmp_fanout_dict[idx] = n
                idx += 1
                self.color_subgraph_node(n, WHITE)
        return tmp_fanout_dict
