import json
from time import time as time_now
from typing import Optional, Text, Tuple

from sxpat.distance_function import WeightedAbsoluteDifference, HammingDistance, WeightedHammingDistance
from sxpat.executor.subxpat2_executor import SubXPatV2Executor

from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.templateCreator import Template_SOP1
from sxpat.templateSpecs import TemplateSpecs

import sxpat.config.config as sxpat_config
from sxpat.config import paths as sxpatpaths


from z_marco.ma_graph import MaGraph, extract_subgraph


class Template_V2(Template_SOP1):
    is_two_phase_kind = True

    def __init__(self, template_specs: TemplateSpecs):
        super().__init__(template_specs)

        self.executor = SubXPatV2Executor(
            None, None, template_specs.exact_benchmark,
            None, None,
            None, None,
            template_specs.et
        )

        self.full_error_function = template_specs.full_error_function
        self.sub_error_function = template_specs.sub_error_function

    def set_new_context(self, template_specs: TemplateSpecs):
        super().set_new_context(template_specs)
        self.et = template_specs.et
        self.timeout = template_specs.timeout

        self.executor.set_context(self.exact_benchmark, self.et, self.lpp, self.ppo, self.iterations)

    def set_graph_and_update_functions(self, annotated_graph: AnnotatedGraph):
        # > Graphs

        # convert AnnotatedGraph to MaGraph(s)
        full_graph = MaGraph.from_digraph(annotated_graph.subgraph)
        sub_graph = extract_subgraph(annotated_graph)

        self.executor.set_graphs(full_graph, sub_graph)

        # > Distance functions

        # define distance/error function of graph
        if self.full_error_function == 1:
            circuit_distance_function = WeightedAbsoluteDifference(
                full_graph.inputs,
                [2 ** int(out_name.strip("out")) for out_name in full_graph.outputs]
            )
        else:
            raise RuntimeError("Should never raise this")

        # define distance/error function of subgraph
        if self.sub_error_function == 1:
            subcircuit_distance_function = WeightedAbsoluteDifference(
                sub_graph.inputs,
                [annotated_graph.subgraph.nodes[n][sxpat_config.WEIGHT] for n in sub_graph.unaliased_outputs]
            )
        elif self.sub_error_function == 2:
            subcircuit_distance_function = HammingDistance(
                sub_graph.inputs
            )
        elif self.sub_error_function == 3:
            subcircuit_distance_function = WeightedHammingDistance(
                sub_graph.inputs,
                [annotated_graph.subgraph.nodes[n][sxpat_config.WEIGHT] for n in sub_graph.unaliased_outputs]
            )
        else:
            raise RuntimeError("Should not ever raise this")

        self.executor.set_error_functions(circuit_distance_function, subcircuit_distance_function)

        return full_graph, sub_graph

    def run_phase1(self, arguments: Tuple) -> Tuple[bool, Optional[Text]]:
        self.max_sub_distance = self.executor._phase1(arguments)
        print(f"D = {self.max_sub_distance}")

        # fail conditions
        if self.max_sub_distance <= 0:
            return (False, f'invalid subcircuit distance: {self.max_sub_distance}')
        if self.max_sub_distance == self.executor.subcircuit_error_function.min_distance:
            return (False, f'subcircuit distance equals minimum possible distance')

        # success
        return (True, None)

    def run_phase2(self):
        status, model = self.executor._phase2(self.max_sub_distance, self.timeout)

        return status, model

    # @override
    def import_json_model(self, this_path=None):
        self.json_model = []
        self.json_status = []
        if this_path:
            self.json_in_path(this_path)
        else:
            self.json_in_path = self.executor.gen_json_outfile_name(self.max_sub_distance - 1)

        with open(self.json_in_path, 'r') as f:
            data = json.load(f)
        for d in data:
            for key in d.keys():
                if key == sxpat_config.RESULT:
                    if d[key] == sxpat_config.SAT:
                        self.json_model.append(d[sxpat_config.MODEL])
                        self.json_status.append(sxpat_config.SAT)
                    elif d[key] == sxpat_config.UNSAT:
                        self.json_model.append(None)
                        self.json_status.append(sxpat_config.UNSAT)
                    else:
                        self.json_model.append(None)
                        self.json_status.append(sxpat_config.UNKNOWN)
