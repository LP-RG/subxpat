from sxpat.specifications import Specifications, EncodingType

from .Z3Solver import Z3IntSolver, Z3BitVecSolver


__all__ = ['get_specialized',
           'Z3IntSolver', 'Z3BitVecSolver']


def get_specialized(specs: Specifications):
    # NOTE: If we change the sistem to a pipeline approach, this method will not be used
    return {
        EncodingType.Z3_INTEGER: Z3IntSolver,
        EncodingType.Z3_BITVECTOR: Z3BitVecSolver,
        # EncodingType.QBF: ,
    }[specs.encoding]
