from __future__ import annotations
from typing import Dict, Iterable, Iterator, List, Literal, Optional, Tuple, Union
import dataclasses as dc

import functools as ft
import math
import networkx as nx

import os
import json
import numpy as np
import itertools as it
from concurrent.futures import ThreadPoolExecutor, as_completed
from os.path import join as path_join
from sxpat.graph import *

from sxpat.graph.graph import SGraph, IOGraph
from sxpat.graph.node import Extras, Node, BoolConstant
from sxpat.newag import load_circuit_from_verilog
from sxpat.converting.legacy import iograph_to_sgraph, iograph_with_weights

from sxpat.specifications import Specifications, TemplateType, ErrorPartitioningType, MetricType
from sxpat.constants.misc import UNKNOWN, SAT
from sxpat.utils.filesystem import FS
from sxpat.utils.names import extract_name
from sxpat.utils.timer import Timer
from sxpat.utils.print import pprint
from sxpat.metrics import MetricsEstimator

from sxpat.definitions.templates import get_specialized as get_templater
from sxpat.definitions.distances import *
from sxpat.definitions.questions import exists_parameters, distribution_aware_questions
from sxpat.definitions.questions.max_distance_evaluation import MaxDistanceEvaluation

from sxpat.subgraph_extractions.legacy import *
from sxpat.subgraph_extractions.legacy.datatype import find_subgraph_feasible_hard_zones_datatype_bitvec
from sxpat.subgraph_extractions.manual import extract

from sxpat.solvers import get_specialized as get_solver
from sxpat.solvers import Z3DirectBitVecSolver
from sxpat.converting import set_bool_constants, prevent_assignment
from sxpat.converting import VerilogExporter


from sxpat.labelling.solver_labelling import Labelling as ZoneLabelling
from sxpat.labelling.solver_labelling import Zone, Interval
from sxpat.labelling.labelling import Labelling
from plot_zones import save_zone_heatmaps


ERROR_THRESHOLD_ARRAYS_PATH = 'input/error_threshold_arrays.json'

def are_circuits_equal(g1: SGraph, g2: SGraph) -> bool:
    class _Node(Node, Extras): ...

    def node_matcher(_n1: dict, _n2: dict) -> bool:
        n1: _Node = _n1[SGraph.K]
        n2: _Node = _n2[SGraph.K]
        return (
            type(n1) == type(n2)
            and n1.in_subgraph == n2.in_subgraph
        )

    return nx.is_isomorphic(g1._inner, g2._inner, node_match=node_matcher)

@dc.dataclass
class ExpandedCircuitData:
    id: str
    path: str
    area: float
    power: float
    delay: float
    error_to_origin: int = 0
    error_to_previous: int = 0


@dc.dataclass
class ResultCircuitsSelection:
    area_power_delay: ExpandedCircuitData
    area_delay_power: ExpandedCircuitData
    power_area_delay: ExpandedCircuitData
    power_delay_area: ExpandedCircuitData
    delay_area_power: ExpandedCircuitData
    delay_power_area: ExpandedCircuitData


def model_compare(a: ExpandedCircuitData, b: ExpandedCircuitData) -> int:
    if a.area != b.area:
        return -1 if a.area < b.area else 1
    if a.power != b.power:
        return -1 if a.power < b.power else 1
    if a.delay != b.delay:
        return -1 if a.delay < b.delay else 1
    return 0


def load_zone_ets(specs_obj: Specifications) -> np.ndarray | int:
    try: 
        with open(ERROR_THRESHOLD_ARRAYS_PATH, 'r') as f:
            vals = json.load(f)[specs_obj.threshold_array_idx]["values"]
            return np.asarray(vals) if isinstance(vals, list) else vals
    except Exception as e:
        print(f"Errore caricamento threshold array: {e}")
        return specs_obj.max_error


def explore_grid(specs_obj: Specifications):
    FS.copy(specs_obj.exact_benchmark, tmp := path_join(specs_obj.path.run.verilog, 'origin.v'))
    specs_obj.exact_benchmark = tmp
    FS.copy(specs_obj.current_benchmark, tmp := path_join(specs_obj.path.run.verilog, 'current.v'))
    specs_obj.current_benchmark = tmp

    exact_graph = load_circuit_from_verilog(specs_obj.exact_benchmark, specs_obj.path.run)
    exact_circuit_metrics = MetricsEstimator.estimate_metrics(
        specs_obj.path.synthesis, specs_obj.exact_benchmark, specs_obj.path.run.temporary
    )

    all_generated_circuits_data = [
        ExpandedCircuitData(
            'origin.v',
            path_join(specs_obj.path.run.verilog, 'origin.v'),
            exact_circuit_metrics.area,
            exact_circuit_metrics.power,
            exact_circuit_metrics.delay,
            0, 0
        )
    ]
    specs_obj.details_storage.add(
        origin_circuit_area=exact_circuit_metrics.area,
        origin_circuit_power=exact_circuit_metrics.power,
        origin_circuit_delay=exact_circuit_metrics.delay,
    )

    previous_graphs: List[SGraph] = []
    obtained_wce_exact = 0
    specs_obj.iteration = 0
    persistence = specs_obj.persistence
    persistence_limit = specs_obj.persistence
    prev_actual_error = 0 if specs_obj.subxpat else 1
    prev_given_error = 0

    if specs_obj.extraction_mode == 0:
        specs_obj.et = load_zone_ets(specs_obj=specs_obj)
        max_out_node = specs_obj.outputs

    if specs_obj.partial_labeling:
        print("partial labeling active")

    if specs_obj.error_partitioning is ErrorPartitioningType.ASCENDING:
        orig_et = (
            load_zone_ets(specs_obj=specs_obj)
            if specs_obj.zone_constraint
            else specs_obj.max_error
        )
        if isinstance(orig_et, (int, np.integer)):
            step = max(int(orig_et) // specs_obj.partition_divider, 1)
            list_values = list(range(step, int(orig_et) + 1, step))
            if list_values[-1] != orig_et:
                list_values.append(int(orig_et))
            et_array = iter(list_values)
        else:
            orig_et = np.asarray(orig_et)
            specs_obj.max_error = orig_et
            step = np.maximum(orig_et // specs_obj.partition_divider, 1)
            
            list_values = []
            current_step = step.copy()
            
            while np.all(current_step <= orig_et):
                list_values.append(current_step.copy())
                next_step = current_step + step
                if np.any(next_step > orig_et):
                    break
                current_step = next_step

            if len(list_values) == 0 or not np.array_equal(list_values[-1], orig_et):
                list_values.append(orig_et.copy())

            et_array = iter(list_values)

    elif specs_obj.error_partitioning is ErrorPartitioningType.EXPONENTIAL:
        et_array = iter([2**i for i in range(8)])
    #TODO error check for zone has to be implemented correctly
    while np.max(np.asarray(obtained_wce_exact)) <= np.max(np.asarray(specs_obj.max_error)) or specs_obj.extraction_mode == 0:
        specs_obj.iteration += 1
        specs_obj.stats_storage.stage(iteration=specs_obj.iteration)

        if not specs_obj.subxpat:
            if np.all(np.asarray(prev_actual_error) == 0): 
                break
            specs_obj.et = (
                load_zone_ets(specs_obj=specs_obj)
                if specs_obj.zone_constraint
                else specs_obj.max_error
            )

        elif specs_obj.extraction_mode == 0:
            if max_out_node == specs_obj.out_node:
                pprint.warning('The error space is exhausted!')
                break

        elif specs_obj.error_partitioning in (ErrorPartitioningType.ASCENDING, ErrorPartitioningType.EXPONENTIAL):
            if persistence == persistence_limit:
                persistence = 0
                try:
                    specs_obj.et = next(et_array)
                except StopIteration:
                    pprint.warning('The error space is exhausted!')
                    break
            else:
                persistence += 1

        elif specs_obj.error_partitioning is ErrorPartitioningType.DESCENDING:
            log2 = int(math.log2(specs_obj.max_error))
            specs_obj.et = 2 ** (log2 - specs_obj.iteration - 2)

        elif specs_obj.error_partitioning is ErrorPartitioningType.SMART_ASCENDING:
            if specs_obj.iteration == 1:
                specs_obj.et = 1
            else:
                if np.all(np.asarray(prev_actual_error) == 0) or persistence == persistence_limit:
                    specs_obj.et = prev_given_error * 2
                else:
                    specs_obj.et = prev_given_error
                    persistence += 1
            prev_given_error = specs_obj.et

        elif specs_obj.error_partitioning is ErrorPartitioningType.SMART_DESCENDING:
            specs_obj.et = specs_obj.max_error if specs_obj.iteration == 1 else math.ceil(prev_given_error / (2 if np.all(np.asarray(prev_actual_error) == 0) else 1))
            prev_given_error = specs_obj.et

        else:
            specs_obj.stats_storage.stage(ERROR='illegal_state__error_partitioning')
            specs_obj.stats_storage.commit()
            raise NotImplementedError('invalid status')

        et_arr = np.asarray(specs_obj.et)
        max_err_arr = np.asarray(specs_obj.max_error)

        if (np.any(et_arr > max_err_arr) and specs_obj.metric != MetricType.RELATIVE) or np.any(et_arr <= 0): 
            break

        specs_obj.stats_storage.stage(
            error_threshold=specs_obj.et,
            circuit_to_approximate=os.path.relpath(specs_obj.current_benchmark, specs_obj.path.run.base_folder),
        )
        pprint.info1(f'benchmark {specs_obj.current_benchmark}')
        pprint.info1(f'iteration {specs_obj.iteration} with et {specs_obj.et}, available error {specs_obj.max_error}'
                     if specs_obj.subxpat else
                     f'Only one iteration with et {specs_obj.et}')

        _time = Timer.now()
        current_graph = load_circuit_from_verilog(specs_obj.current_benchmark, specs_obj.path.run)
        _time = Timer.now() - _time
        specs_obj.stats_storage.stage(annotated_graphs_initialization_time=_time)
        print(f'annotated_graph_loading_time = {_time}')

        # Etichettatura del grafo
        if specs_obj.requires_labeling:
            print('started labelling')
            _time = Timer.now()

            weights = label_graph(current_graph, specs_obj)
            for i, n in enumerate(current_graph.outputs_names):
                weights[n] = 2 ** i

            saved_zone_weights = getattr(current_graph, 'zone_weights', None)
            current_graph = iograph_with_weights(current_graph, weights)

            if saved_zone_weights is not None:
                current_graph.zone_weights = saved_zone_weights

            _time = Timer.now() - _time
            specs_obj.stats_storage.stage(labelling_time=_time)
            print(f'labelling_time = {_time}')

        # Estrazione del sottografo
        _time = Timer.now()
        if not specs_obj.subxpat:
            # Prende solo i nodi interni escludendo gli I/O primari
            subgraph_nodes = [
                node.name for node in current_graph.nodes
                if node not in current_graph.inputs and node not in current_graph.outputs
            ]
        else:
            subgraph_nodes = extract_subgraph(current_graph, specs_obj)

        subgraph_is_available = len(subgraph_nodes) > 0
        current_graph = iograph_to_sgraph(current_graph, subgraph_nodes)
        _time = Timer.now() - _time
        previous_graphs.append(current_graph)

        specs_obj.stats_storage.stage(
            subgraph_extraction_time=_time,
            subgraph_nodes_count=len(current_graph.subgraph_nodes),
            subgraph_inputs_count=len(current_graph.subgraph_inputs),
            subgraph_outputs_count=len(current_graph.subgraph_outputs),
        )
        print(f'subgraph_extraction_time = {_time}')

        if specs_obj.debug:
            from sxpat.newag import export_annotated_graph
            _path = path_join(specs_obj.path.run.graphviz, f'{extract_name(specs_obj.current_benchmark)}_subgraph.gv')
            _p_path = os.path.relpath(_path, specs_obj.path.run.base_folder)
            export_annotated_graph(current_graph, _path)
            specs_obj.stats_storage.stage(subgraph_dot=_p_path)
            print(f'subgraph exported at {_path}')

        if not subgraph_is_available:
            prev_actual_error = 0
            pprint.warning('No subgraph available.')
            specs_obj.stats_storage.commit()
            continue

        if (
            specs_obj.extraction_mode not in (0, 6)
            and len(previous_graphs) >= 2
            and are_circuits_equal(previous_graphs[-2], previous_graphs[-1])
        ):
            prev_actual_error = 0
            pprint.warning('The subgraph is equal to the previous one. Skipping iteration ...')
            specs_obj.stats_storage.commit()
            continue

        # Esplorazione della griglia
        pprint.info2(f'Grid ({specs_obj.grid_param_1} X {specs_obj.grid_param_2}) and et={specs_obj.et} exploration started...')
        dominant_cells = []
        
        for lpp, ppo in CellIterator.factory(specs_obj):
            _cell_time = Timer.now()
            print(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration}: ', end='')

            if lpp > len(current_graph.subgraph_inputs):
                pprint.info3('SKIPPED (lpp > #subgraph_inputs)')
                continue

            if is_dominated((lpp, ppo), dominant_cells):
                pprint.info3('DOMINATED')
                continue

            update_context(specs_obj, lpp, ppo)
            specs_obj.stats_storage.stage(cell_coord_0=lpp, cell_coord_1=ppo)

            _time = Timer.now()
            param_circ, *param_circ_constr = get_templater(specs_obj).define(current_graph, specs_obj)
            _time_define = Timer.now() - _time

            _time = Timer.now()
            if specs_obj.metric.value == 'wae':
                base_question = exists_parameters.not_above_threshold_forall_inputs(
                    current_graph, param_circ, AbsoluteDifferenceOfInteger, specs_obj.et
                )
            elif specs_obj.metric.value == 'wre':
                base_question = distribution_aware_questions.cnn_error_constraint(current_graph, param_circ, specs_obj)

            _time_define += Timer.now() - _time
            specs_obj.stats_storage.stage(grid_phase_definition_time=_time_define)
            
            solver_instance = get_solver(specs_obj)
            solve_timer, solve = Timer.from_function(solver_instance.solve)
            question = [exact_graph, param_circ, *param_circ_constr, *base_question]

            models = []
            status = UNKNOWN
            for i in range(specs_obj.wanted_models):
                specs_obj.sub_iteration = f'ca{lpp}_cb{ppo}_m{i}'

                if len(models) > 0: 
                    question.append(prevent_assignment(models[-1], i - 1))

                _solve_attempt_start = Timer.now()
                status, model = solve(question, specs_obj)
                _solve_attempt_elapsed = Timer.now() - _solve_attempt_start

                print(f"\n  [DEBUG Model {i+1}/{specs_obj.wanted_models}] status={status} elapsed={_solve_attempt_elapsed:.2f}s")

                if status != SAT:
                    if status == UNKNOWN:
                        reason = getattr(solver_instance, 'reason_unknown', lambda: "N/A")()
                        print(f"  [DEBUG UNKNOWN REASON] Cell({lpp},{ppo}) model index {i} failed. Reason: {reason}")
                    break

                models.append(model)

            if len(models) > 0: 
                status = SAT

            _cell_time = Timer.now() - _cell_time
            specs_obj.stats_storage.stage(
                grid_phase_solution_time=solve_timer.total,
                status=status.upper(),
                cell_time=_cell_time,
            )

            if status != SAT:
                if status == UNKNOWN:
                    print(f"\n  [DEBUG DOMINANCE] Adding ({lpp},{ppo}) to dominant_cells due to UNKNOWN status.")
                    dominant_cells.append((lpp, ppo))

                pprint.warning(status.upper(), f'{_cell_time:.2f}s')
                specs_obj.stats_storage.commit()

            else:
                pprint.success(f'{status.upper()} ({len(models)} models found)', f'{_cell_time:.2f}s')

                cur_model_results: List[ExpandedCircuitData] = []
                for model_number, model in enumerate(models):
                    a_graph = set_bool_constants(param_circ, model, skip_missing=True)

                    circuit_id = f'gen_iter{specs_obj.iteration}_model{model_number}'
                    verilog_path = path_join(specs_obj.path.run.verilog, f'{circuit_id}.v')
                    VerilogExporter.to_file(
                        a_graph, verilog_path,
                        VerilogExporter.Info(model_number=model_number),
                    )

                    _metrics = MetricsEstimator.estimate_metrics(specs_obj.path.synthesis, verilog_path, specs_obj.path.run.temporary)
                    cur_model_results.append(ExpandedCircuitData(
                        circuit_id, verilog_path, _metrics.area, _metrics.power, _metrics.delay
                    ))

                pprint.info1('verifying all approximate circuits ...')
                verification_timer, _error_evaluation = Timer.from_function(error_evaluation)

                for candidate_data in cur_model_results:
                    _time = Timer.now()
                    cur_graph = load_circuit_from_verilog(specs_obj.current_benchmark, specs_obj.path.run)
                    _time = Timer.now() - _time
                    specs_obj.stats_storage.stage(erroreval_annotated_graphs_initialization_time=_time)

                    candidate_data.error_to_origin = _error_evaluation(exact_graph, cur_graph, specs_obj)
                    candidate_data.error_to_previous = _error_evaluation(current_graph, cur_graph, specs_obj)

                specs_obj.stats_storage.stage(verification_time=verification_timer.total)

                sorted_circuits = sorted(cur_model_results, key=ft.cmp_to_key(model_compare))
                best_model_data = sorted_circuits[0]
                #TODO error check for zone has to be implemented correctly
                if (np.max(np.asarray(best_model_data.error_to_origin)) > np.max(np.asarray(specs_obj.et))):
                    pprint.warning(f'Circuit violated maximum error boundary! Obtained: {best_model_data.error_to_origin}, Max allowed: {specs_obj.et}')
                else:
                    pprint.success(f'ErrorEval verification PASSED. ( wce = {best_model_data.error_to_origin} )')

                all_generated_circuits_data.extend(sorted_circuits)

                specs_obj.current_benchmark = best_model_data.path
                obtained_wce_exact = best_model_data.error_to_origin
                prev_actual_error = best_model_data.error_to_previous

                for i, circuit_data in enumerate(sorted_circuits):
                    specs_obj.stats_storage.stage(
                        circuit_path=os.path.relpath(circuit_data.path, specs_obj.path.run.base_folder),
                        circuit_error=circuit_data.error_to_origin,
                        circuit_area=circuit_data.area,
                        circuit_power=circuit_data.power,
                        circuit_delay=circuit_data.delay,
                        circuit_is_best=(i == 0),
                    )
                    specs_obj.stats_storage.commit()

                print_current_model(sorted_circuits, origin_circuit_data=exact_circuit_metrics)
                break

            prev_actual_error = 0
            if specs_obj.debug: 
                specs_obj.stats_storage.save()

        if status == SAT and best_model_data.area == 0:
            pprint.info3('Area zero found!\nTerminated.')
            break

    return ResultCircuitsSelection(
        area_power_delay=min(all_generated_circuits_data, key=lambda d: (d.area, d.power, d.delay, d.error_to_origin)),
        area_delay_power=min(all_generated_circuits_data, key=lambda d: (d.area, d.delay, d.power, d.error_to_origin)),
        power_area_delay=min(all_generated_circuits_data, key=lambda d: (d.power, d.area, d.delay, d.error_to_origin)),
        power_delay_area=min(all_generated_circuits_data, key=lambda d: (d.power, d.delay, d.area, d.error_to_origin)),
        delay_area_power=min(all_generated_circuits_data, key=lambda d: (d.delay, d.area, d.power, d.error_to_origin)),
        delay_power_area=min(all_generated_circuits_data, key=lambda d: (d.delay, d.power, d.area, d.error_to_origin)),
    )


def print_results(res: ResultCircuitsSelection) -> None:
    print("\n" + "=" * 50)
    print("           FINAL SELECTION RESULTS")
    print("=" * 50)
    print(f" Best Area (APD) : {res.area_power_delay.id} | Area: {res.area_power_delay.area}")
    print(f" Best Power(PAD) : {res.power_area_delay.id} | Power: {res.power_area_delay.power}")
    print(f" Best Delay(DAP) : {res.delay_area_power.id} | Delay: {res.delay_area_power.delay}")
    print("=" * 50 + "\n")


def error_evaluation(reference_circuit: IOGraph, current_circuit: IOGraph, specs_obj: Specifications) -> int:
    p_graph, c_graph = MaxDistanceEvaluation.define(current_circuit)
    status, model = Z3DirectBitVecSolver.solve((reference_circuit, p_graph, c_graph), specs_obj)

    assert status == SAT
    assert len(model) == 1

    return next(iter(model.values()))


class CellIterator:
    @classmethod
    def factory(cls, specs: Specifications) -> Iterator[Tuple[int, int]]:
        return {
            TemplateType.NON_SHARED: cls.non_shared,
            TemplateType.SHARED: cls.shared,
        }[specs.template](specs)

    @staticmethod
    def shared(specs: Specifications) -> Iterator[Tuple[int, int]]:
        max_pit = specs.max_pit
        yield (0, 1)
        for pit in range(1, max_pit + 1):
            for its in range(max(pit, specs.outputs), max(pit + 4, specs.outputs + 1)):
                yield (its, pit)

    @staticmethod
    def non_shared(specs: Specifications) -> Iterator[Tuple[int, int]]:
        max_lpp = specs.max_lpp
        max_ppo = specs.max_ppo
        yield (0, 1)
        for ppo in range(1, max_ppo + 1):
            for lpp in range(1, max_lpp + 1):
                yield (lpp, ppo)


def is_dominated(coords: Tuple[int, int], dominant_cells: Iterable[Tuple[int, int]]) -> bool:
    lpp, ppo = coords
    return any(lpp >= dom_lpp and ppo >= dom_ppo for dom_lpp, dom_ppo in dominant_cells)


def update_context(specs_obj: Specifications, lpp: int, ppo: int):
    specs_obj.lpp = lpp
    specs_obj.ppo = specs_obj.pit = ppo


def print_current_model(
    sorted_models_data: List[ExpandedCircuitData],
    origin_circuit_data: Optional[MetricsEstimator.Metrics] = None,
    normalize: bool = False
) -> None:
    from tabulate import tabulate

    data = []
    if origin_circuit_data is not None:
        origin_area, origin_power, origin_delay = origin_circuit_data.area, origin_circuit_data.power, origin_circuit_data.delay
        data.append(['Exact', origin_area, origin_power, origin_delay, 0])

        if normalize:
            sorted_models_data = [
                ExpandedCircuitData(
                    '',
                    model_data.path,
                    model_data.area / origin_area,
                    model_data.power / origin_power,
                    model_data.delay / origin_delay,
                    model_data.error_to_origin
                )
                for model_data in sorted_models_data
            ]

    data.extend(
        (model_data.id, model_data.area, model_data.power, model_data.delay, model_data.error_to_origin)
        for model_data in sorted_models_data
    )
    pprint.success(tabulate(data, headers=['Design ID', 'Area', 'Power', 'Delay', 'Error']))


def extract_subgraph(circuit: IOGraph, specs_obj: Specifications) -> List[str]:
    return {
        0: find_subgraph_output_nodes_ascendant,
        1: find_subgraph,
        2: find_subgraph_sensitivity,
        3: find_subgraph_sensitivity_no_io_constraints,
        4: find_subgraph_feasible,
        42: extract,
        5: find_subgraph_feasible_hard,
        55: find_subgraph_feasible_hard_datatype_bitvec,
        56: find_subgraph_feasible_hard_zones_datatype_bitvec,
        6: find_subgraph_feasible_hard_datatype_bitvec_mintreshold,
        100: slash_to_kill,
        11: find_subgraph_feasible_soft,
        12: find_subgraph_feasible_soft_outputs,
    }[specs_obj.extraction_mode](circuit, specs_obj)


def zone_generator(input1_interval: Tuple[int, int], input2_interval: Tuple[int, int], beta: int) -> List[Zone]:
    l_bound1, u_bound1 = input1_interval
    l_bound2, u_bound2 = input2_interval
    all_zones = []

    for start1 in range(l_bound1, u_bound1 + 1, beta):
        end1 = min(start1 + beta - 1, u_bound1)
        for start2 in range(l_bound2, u_bound2 + 1, beta):
            end2 = min(start2 + beta - 1, u_bound2)
            all_zones.append(Zone(Interval(start1, end1), Interval(start2, end2)))
    return all_zones


def get_constant_bits_for_interval(interval: Interval, num_bits: int, start_idx: int) -> Dict[str, bool]:
    min_val, max_val = interval.l_bound, interval.u_bound
    constant_bits = {}

    for bit_offset in range(num_bits - 1, -1, -1):
        bit_min = bool((min_val >> bit_offset) & 1)
        bit_max = bool((max_val >> bit_offset) & 1)

        if bit_min == bit_max:
            constant_bits[f"in{start_idx + bit_offset}"] = bit_min
        else:
            break

    return constant_bits


def _process_node_worker(
    node_name: str, 
    reference: IOGraph, 
    to_be_labelled: IOGraph, 
    specs_obj: Specifications, 
    zones_with_fixed_bits: List[Tuple[Zone, Dict[str, BoolConstant]]]
    ) -> Tuple[str, Dict[Zone, int], float]:
        start = Timer.now()
        labeller = ZoneLabelling(reference, to_be_labelled, specs=specs_obj)
        zone_dict = labeller.label_all_zones(node_name, zones_with_fixed_bits, specs_obj)
        elapsed = Timer.now() - start
        return node_name, zone_dict, elapsed




def label_graph(circuit: IOGraph, specs_obj: Specifications) -> Dict[str, int]:
    reference: IOGraph = circuit
    to_be_labelled: IOGraph = circuit

    if isinstance(specs_obj.et, (int, np.integer)):
        et_array = [int(specs_obj.et)]
    else:
        et_array = list(specs_obj.et)
    
    max_et = max(et_array)

    if specs_obj.zone_constraint:
        print("> ZONE CONSTRAINT ACTIVE: Running multi-zone labelling...", flush=True)

        # Recupero sicuro del grafo NetworkX interno
        graph = circuit._inner

        total_input_bits = len(circuit.inputs_names)
        bits_input_1 = total_input_bits // 2
        bits_input_2 = total_input_bits - bits_input_1
        
        input1_interval = (0, (2 ** bits_input_1) - 1)
        input2_interval = (0, (2 ** bits_input_2) - 1)

        zones = zone_generator(input1_interval, input2_interval, specs_obj.beta)
        zones_with_fixed_bits: List[Tuple[Zone, Dict[str, BoolConstant]]] = []

        for zone in zones:
            const_in1 = get_constant_bits_for_interval(zone.input_1, num_bits=bits_input_1, start_idx=0)
            const_in2 = get_constant_bits_for_interval(zone.input_2, num_bits=bits_input_2, start_idx=bits_input_1)

            fixed_bits_dict = {
                name: BoolConstant(name, value=val)
                for name, val in it.chain(const_in1.items(), const_in2.items())
            }
            zones_with_fixed_bits.append((zone, fixed_bits_dict))

        # Identify valid output nodes where weight (2^x) < max_et
        valid_outputs = set()
        for out_name in circuit.outputs_names:
            try:
                x = int(''.join(filter(str.isdigit, out_name)))
                if (2 ** x) < max_et:
                    valid_outputs.add(out_name)
            except Exception:
                valid_outputs.add(out_name)

        # Use NetworkX to find all ancestors of the valid outputs via circuit._inner
        valid_nodes = set(valid_outputs)
        for out_name in valid_outputs:
            if out_name in graph:
                valid_nodes.update(nx.ancestors(graph, out_name))

        all_nodes_to_process = [
            node.name for node in circuit.nodes 
            if node not in circuit.inputs and node not in circuit.outputs
        ]

        nodes_to_process = [n for n in all_nodes_to_process if n in valid_nodes]
        pruned_nodes = [n for n in all_nodes_to_process if n not in valid_nodes]

        # Log print for a-priori pruned nodes
        print(f"[A-PRIORI PRUNING] Filtered out {len(pruned_nodes)} nodes out of {len(all_nodes_to_process)} total nodes before labeling using NetworkX ancestors.")

        max_workers = 16
        print(f"\n> Esecuzione in parallelo su {max_workers} thread per {len(nodes_to_process)} nodi ({len(pruned_nodes)} pruned a-priori)...", flush=True)

        z_weights = {}
        
        for node_name in pruned_nodes:
            z_weights[node_name] = {-1: -1}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_process_node_worker, node_name, reference, to_be_labelled, specs_obj, zones_with_fixed_bits)
                for node_name in nodes_to_process
            ]

            for future in as_completed(futures):
                node_name, zone_dict, _ = future.result()
                z_weights[node_name] = zone_dict

        # --- COUNTER LOGIC FOR WEIGHT UNIFORMITY ---
        uniform_weights_count = 0
        varying_weights_count = 0

        for node_name, zone_dict in z_weights.items():
            # Ignoriamo i nodi prunati (-1 nel dizionario o valori di errore di pruning)
            if not zone_dict or -1 in zone_dict.values():
                continue
            
            # Estraiamo i pesi unici calcolati nelle varie zone
            unique_weights = set(zone_dict.values())
            
            if len(unique_weights) <= 1:
                uniform_weights_count += 1
            else:
                varying_weights_count += 1

        print(f"[WEIGHT ANALYSIS] Nodes with uniform weights across zones: {uniform_weights_count}")
        print(f"[WEIGHT ANALYSIS] Nodes with varying weights across zones: {varying_weights_count}")
        # ------------------------------------------

        circuit.zone_weights = z_weights
        return {node_name: max(zone_dict.values(), default=0) for node_name, zone_dict in z_weights.items()}

    else:
        labeller = Labelling(reference, to_be_labelled, specs=specs_obj)
        return labeller.label_all_nodes()