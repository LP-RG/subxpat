from abc import abstractmethod
import json
from typing import Dict, Tuple

from sxpat.config.config import SolverStatus
from sxpat.config.config import ResultFields as rf


class Executor:
    def __init__(self) -> None:
        raise NotImplementedError(f"Class `{self.__class__.__name__}` is an abstract class.")

    @abstractmethod
    def run(self):
        raise NotImplementedError(f"Method `{self.__class__.__name__}.run` is abstract.")

    @staticmethod
    def _load_result(output_path: str) -> Tuple[SolverStatus, Dict[str, bool]]:
        with open(output_path, "r") as ifile:
            # only one model was searched for
            output = json.load(ifile)[0]

        # extract and return
        return (
            SolverStatus(output[rf.RESULT.value]),
            output.get(rf.MODEL.value, None)
        )
