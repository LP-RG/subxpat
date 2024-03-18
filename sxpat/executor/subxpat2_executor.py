import json
import os
import subprocess
from time import time
from typing import Any, Dict, Tuple
from sxpat.distance_function import DistanceFunction
from z_marco.ma_graph import MaGraph
from sxpat.runner_creator.subxpat_v2_phase1_creator import SubXPatV2Phase1RunnerCreator
from sxpat.runner_creator.xpat_creator_function import XPatRunnerCreator

from Z3Log.config.config import PYTHON3
from sxpat.config.config import ResultFields as rf
from z_marco.utils import pprint


NOTHING = object()


class SubXPatV2Executor:
    def __init__(self,
                 # inputs
                 full_graph: MaGraph,
                 sub_graph: MaGraph,
                 exact_name: str,
                 # parameters
                 literals_per_product: int,
                 products_per_output: int,
                 # error
                 circuit_error_function: DistanceFunction,
                 subcircuit_error_function: DistanceFunction,
                 error_threshold: int,
                 #  *,
                 # TODO: future
                 #  wanted_models_count: int = 1,
                 #  execution_timeout: float = float('infinity')
                 ) -> None:

        # store info
        self.full_graph = full_graph
        self.sub_graph = sub_graph
        self.exact_name = exact_name

        self.literals_per_product = literals_per_product
        self.products_per_output = products_per_output

        # store error stuff
        self.circuit_error_function = circuit_error_function
        self.subcircuit_error_function = subcircuit_error_function
        self.error_threshold = error_threshold

        # TODO: future
        # self.wanted_models_count = wanted_models_count
        # self.execution_timeout = execution_timeout

    def set_graphs(self, full_graph: MaGraph, sub_graph: MaGraph):
        self.full_graph = full_graph
        self.sub_graph = sub_graph

    def set_error_functions(self, circuit_error_function: DistanceFunction, subcircuit_error_function: DistanceFunction):
        self.circuit_error_function = circuit_error_function
        self.subcircuit_error_function = subcircuit_error_function

    def set_context(self, exact_benchmark, error_threshold, literals_per_product, products_per_output, iteration):
        self.exact_name = exact_benchmark
        self.error_threshold = error_threshold
        self.literals_per_product = literals_per_product
        self.products_per_output = products_per_output
        self.iteration = iteration

    def _phase1(self, arguments: Tuple[int, int, float] = None) -> int:
        # create creator object
        self.phase1_creator = SubXPatV2Phase1RunnerCreator(
            self.full_graph, self.sub_graph, self.exact_name,
            self.circuit_error_function,
            self.subcircuit_error_function
        )

        # generate script
        script_path = self.phase1_creator.get_script_name()
        print(f"Generating phase1 script {script_path}")
        with open(script_path, "w") as file:
            file.write(self.phase1_creator.generate_script())

        # update arguments (et, num_models, timeout)
        arguments = arguments or [self.error_threshold]
        arguments = [str(a) for a in arguments]

        # run process
        print(f"Running phase1 script {script_path} with arguments {arguments}")
        process = subprocess.run(
            [PYTHON3, script_path, *arguments],
            stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        # if error
        if process.returncode or process.stderr:
            message = f"Runner {script_path} exited with code#{process.returncode}"
            pprint.error(f"[ERROR] {message}", process.stderr.decode())
            raise ChildProcessError(message)

        # exctract result
        print(f"Gathering results of phase1 script {script_path}")
        lines = process.stdout.decode("utf-8").split("\n")
        status, max_sub_distance = lines[0:2]
        if status == 'sat':
            max_sub_distance = int(max_sub_distance)
        elif status == 'unsat':
            max_sub_distance = 2**31 - 1
        else:
            raise RuntimeError(f"Invalid solver result: '{status}'")

        return max_sub_distance

    def _phase2(self, max_sub_distance: int):
        # create creator object
        self.phase2_creator = XPatRunnerCreator(
            self.sub_graph, self.exact_name,
            self.literals_per_product, self.products_per_output,
            self.subcircuit_error_function,
            self.iteration
        )

        # generate script
        script_path = self.phase2_creator.get_script_name(
            f"{self.exact_name}_sub",
            self.literals_per_product,
            self.products_per_output,
            self.subcircuit_error_function.abbreviation
        )
        print(f"Generating phase2 script {script_path}")
        with open(script_path, "w") as file:
            file.write(self.phase2_creator.generate_script())

        # run script
        print(f"Running phase2 script {script_path} with arguments [{max_sub_distance-1}]")
        process = subprocess.run(
            [
                PYTHON3,
                script_path,
                # todo:hack: temporarily set 1 model max and 1 hour timeout
                str(max_sub_distance - 1), str(1), str(1 * 60 * 60)
            ],
            stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        # if error
        if process.returncode or process.stderr:
            message = f"Runner {script_path} exited with code#{process.returncode}"
            pprint.error(f"[ERROR] {message}", process.stderr.decode())
            raise ChildProcessError(message)

        # load result
        print(f"Gathering results of phase2 script {script_path}")
        output_path = self.phase2_creator.gen_json_outfile_name().format(ET=max_sub_distance-1)
        with open(output_path, "r") as ifile:
            # todo:temporary: only one model is searched for
            output: Dict[str, Any] = json.load(ifile)[0]

        # extract and return
        status: str = output[rf.RESULT.value]
        model: Dict[str, bool] = output.get(rf.MODEL.value, None)
        return status, model

    def run(self):
        # phase 1
        p1_start = time()
        max_sub_distance = self._phase1()
        print(f"D = {max_sub_distance}")
        print(f"p1_time = {(time() - p1_start):.6f}")

        # phase 2
        p2_start = time()
        status, model = self._phase2(max_sub_distance)
        print(f"p2_time = {(time() - p2_start):.6f}")

        return status, model

    def gen_json_outfile_name(self, et):
        return self.phase2_creator.gen_json_outfile_name(et)
