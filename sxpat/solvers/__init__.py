from typing import Type

from sxpat.specifications import Specifications, EncodingType

from .Solver import *
from .Z3Solver import *


__all__ = [
    'get_specialized',
    'Solver',
    'Z3FuncIntSolver', 'Z3FuncBitVecSolver',
    'Z3DirectIntSolver', 'Z3DirectBitVecSolver',
]


def get_specialized(specs: Specifications) -> Type[Solver]:
    # NOTE: If we change the system to a pipeline approach, this method will not be necessary
    return {
        EncodingType.Z3_FUNC_INTEGER: Z3FuncIntSolver,
        EncodingType.Z3_FUNC_BITVECTOR: Z3FuncBitVecSolver,
        EncodingType.Z3_DIRECT_INTEGER: Z3DirectIntSolver,
        EncodingType.Z3_DIRECT_BITVECTOR: Z3DirectBitVecSolver,
        # EncodingType.QBF: SomethingSolver,
    }[specs.encoding]
