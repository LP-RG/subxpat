from __future__ import annotations
from abc import abstractmethod


class VerifierCreator:
    @abstractmethod
    def generate_script(self, path: str = None) -> None:
        pass


class IterativeVerifierCreator(VerifierCreator):
    def __init__(self) -> None:
        raise NotImplementedError("This feature is planned for the future.")


class OptimizeVerifierCreator(VerifierCreator):
    def __init__(self) -> None:
        raise NotImplementedError("This feature is planned for the future.")
