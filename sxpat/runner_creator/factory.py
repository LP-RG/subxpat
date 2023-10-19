# sxpat libs
from sxpat.templateSpecs import TemplateSpecs

# package
from .runner_creator import RunnerCreator


class RunnerCreatorFactory:
    @classmethod
    def get(cls, specifications: TemplateSpecs) -> RunnerCreator:
        raise NotImplementedError("Work in progress.")
