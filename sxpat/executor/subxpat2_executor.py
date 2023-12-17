import json
import os
import subprocess
from time import time
from typing import Any, Dict
from sxpat.distance_function import DistanceFunction
from z_marco.ma_graph import MaGraph
from sxpat.runner_creator.subxpat_v2_phase1_creator import SubXPatV2Phase1RunnerCreator
from sxpat.runner_creator.xpat_creator_function import XPatRunnerCreator

from Z3Log.config.config import PYTHON3
from sxpat.config.config import ResultFields as rf
from z_marco.utils import pprint


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

        self.phase1_creator = SubXPatV2Phase1RunnerCreator(
            full_graph, sub_graph, exact_name,
            circuit_error_function,
            subcircuit_error_function
        )

        self.phase2_creator = XPatRunnerCreator(
            sub_graph, exact_name,
            literals_per_product, products_per_output,
            subcircuit_error_function
        )

    def _phase1(self) -> int:
        # generate script
        script_path = self.phase1_creator.get_script_name()
        print(f"Generating phase1 script {script_path}")
        with open(script_path, "w") as file:
            file.write(self.phase1_creator.generate_script())

        # run process
        print(f"Running phase1 script {script_path}")
        process = subprocess.run(
            [
                PYTHON3,
                script_path,
                str(self.error_threshold),
            ],
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
        print(f"Running phase2 script {script_path}")
        process = subprocess.run(
            [
                PYTHON3,
                script_path,
                str(max_sub_distance),
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
        output_path = self.phase2_creator.gen_json_outfile_name().format(ET=max_sub_distance)
        with open(output_path, "r") as ifile:
            # only one model was searched for
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
        status, model = self._phase2(max_sub_distance - 1)
        print(f"p2_time = {(time() - p2_start):.6f}")

        return status, model
