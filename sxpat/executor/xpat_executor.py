import json
import os
import subprocess
from typing import Any, Dict
from sxpat.distance_function import DistanceFunction
from sxpat.utils.name import runner_name
from z_marco.ma_graph import MaGraph
from sxpat.runner_creator.xpat_creator import XPatRunnerCreator
from .executor import Executor

from Z3Log.config.config import PYTHON3
from sxpat.config.config import ResultFields as rf
from z_marco.utils import pprint


class XPatExecutor(Executor):
    def __init__(self,
                 exact_graph: MaGraph, exact_name: str,
                 literals_per_product: int, products_per_output: int,
                 error_function: DistanceFunction,
                 error_threshold: int,
                 #  *,
                 # TODO: future
                 #  wanted_models_count: int = 1,
                 #  execution_timeout: float = float('infinity')
                 ) -> None:

        self.exact_name = exact_name
        self.literals_per_product = literals_per_product
        self.products_per_output = products_per_output

        self.error_function = error_function
        self.error_threshold = error_threshold

        # TODO: future
        # self.wanted_models_count = wanted_models_count
        # self.execution_timeout = execution_timeout

        self.creator = XPatRunnerCreator(
            exact_graph, exact_name,
            literals_per_product, products_per_output,
            error_function
        )

    @property
    def script_path(self) -> str:
        return runner_name(
            main_name=self.exact_name,
            literals_per_product=self.literals_per_product,
            products_per_output=self.products_per_output,
            distance_function_name=self.error_function.abbreviation,
            implementation="XPAT"
        )

    def run(self):
        # generate script
        print(f"Generating script ({self.script_path})")
        # TODO: Should we generate the file everytime or skip if already present?
        # if not os.path.exists(self.script_path):
        with open(self.script_path, "w") as file:
            print(file)
            self.creator.generate_script(file)

        # run the process
        print(f"Running script ({self.script_path})")
        process = subprocess.run(
            [
                PYTHON3,
                self.script_path,
                str(self.error_threshold),
                # TODO: future
                # str(self.wanted_models_count),
                # str(self.execution_timeout)
            ],
            stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )

        # if error
        if process.returncode or process.stderr:
            message = f"Runner {self.script_path} exited with code#{process.returncode}"
            pprint.error(f"[ERROR] {message}", process.stderr.decode())
            raise ChildProcessError(message)

        # load result
        print("Gathering results")
        output_path = self.creator.gen_json_outfile_name().format(ET=self.error_threshold)
        return self._load_result(output_path)
