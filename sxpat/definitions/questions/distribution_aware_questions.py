from typing import Dict, List, Sequence, Tuple, Union

import itertools as it
from unittest import case


from sxpat.converting import set_prefix
from sxpat.graph import *
from sxpat.graph.node import *
from sxpat.specifications import ConstantsType, MetricType, Specifications
from sxpat.utils.collections import flat, iterable_replace, pairwise

from .constraints_definition import nine, nine_prime, explicit_constraints 

from sxpat.specifications import CnnErrorConstraintTypes



def cnn_error_constraint(s_graph: SGraph, t_graph: PGraph,specs_obj: Specifications) -> List[Node]:
    
     #max_error: int, beta: int, alpha: int, c_constant: int, threshold_array_idx: int, constraint_type: CnnErrorConstraintTypes   
    constraint_type = specs_obj.cnn_constraint
    if(constraint_type == CnnErrorConstraintTypes.EXPLICIT):
        list_nodes = explicit_constraints(s_graph, t_graph, specs_obj.threshold_array_idx, specs_obj.beta)
    elif(constraint_type == CnnErrorConstraintTypes.NINE):
        list_nodes = nine(s_graph, t_graph, specs_obj.max_error, specs_obj.beta, specs_obj.alpha)
    elif(constraint_type == CnnErrorConstraintTypes.NINE_PRIME):
        list_nodes = nine_prime(s_graph, t_graph, specs_obj.max_error, specs_obj.beta, specs_obj.alpha, specs_obj.c_constant)
    else:
        raise ValueError(f'Unknown CNN constraint type: {constraint_type}')
    return [CGraph(list_nodes)]