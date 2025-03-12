from typing import Type
from sxpat.specifications import Specifications, TemplateType

from .Template import Template
from .SharedTemplate import SharedTemplate
from .NonSharedTemplate import NonSharedTemplate


__all__ = ['get_specialized',
           'SharedTemplate', 'NonSharedTemplate']


def get_specialized(specs: Specifications) -> Type[Template]:
    # NOTE: If we change the system to a pipeline approach, this method will not be used
    return {
        TemplateType.SHARED: SharedTemplate,
        TemplateType.NON_SHARED: NonSharedTemplate,
    }[specs.encoding]
