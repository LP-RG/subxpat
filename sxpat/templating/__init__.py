from typing import Type
from sxpat.specifications import Specifications, TemplateType, ConstantFalseType

from .Template import Template
from .SharedTemplate import SharedTemplate
from .NonSharedTemplate import NonSharedFOutTemplate, NonSharedFProdTemplate
from .InputReplace import InputReplace


__all__ = ['get_specialized',
           'Template',
           'SharedTemplate', 'NonSharedFOutTemplate', 'NonSharedFProdTemplate']


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
    }[specs.template][specs.constant_false]
