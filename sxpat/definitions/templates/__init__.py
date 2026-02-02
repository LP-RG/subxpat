"""
    ### Template definitions

    This module contains all the templates we have implemented.
    
    All of them share the same interface: `cls.define(SGraph, Specifications) -> Tuple[PGraph, Sequence[CGraph]]`

    @authors: Marco Biasion
"""

from typing import Type
from sxpat.specifications import Specifications, TemplateType, ConstantFalseType

from .Template import Template
from .simple_templates import ConstantTemplate, SwitchedTemplate
from .SharedTemplate import SharedTemplate
from .NonSharedTemplate import NonSharedFOutTemplate, NonSharedFProdTemplate
from .InputReplace import InputReplace
from .v2Phase1 import v2Phase1


__all__ = [
    # abstract
    'Template',
    # simple templates
    'ConstantTemplate', 'SwitchedTemplate',
    # DNF (Disjunctive Normal Form) templates
    'SharedTemplate', 'NonSharedFOutTemplate', 'NonSharedFProdTemplate',
    #
    'get_specialized',
]


def get_specialized(specs: Specifications) -> Type[Template]:
    # NOTE: If we change the system to a pipeline approach, this method will not be used

    # define parameters
    return {
        TemplateType.SHARED: {
            ConstantFalseType.OUTPUT: SharedTemplate,
        },
        TemplateType.NON_SHARED: {
            ConstantFalseType.OUTPUT: NonSharedFOutTemplate,
            ConstantFalseType.PRODUCT: NonSharedFProdTemplate,
        },
        TemplateType.INPUT_REPLACE: {
            ConstantFalseType.OUTPUT: InputReplace,
            ConstantFalseType.PRODUCT: InputReplace,
        },
        TemplateType.V2: {
            ConstantFalseType.OUTPUT: NonSharedFOutTemplate,
            ConstantFalseType.PRODUCT: NonSharedFProdTemplate,
        },
    }[specs.template][specs.constant_false]
