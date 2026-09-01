from typing import Iterator, Protocol
from abc import abstractmethod


class ConfigurationExploration[T](Protocol):
    @abstractmethod
    def get_next(self) -> T | None: ...
    @abstractmethod
    def give_result(self, configuration: T, status: str) -> None: ...

    def __iter__(self): return self

    def __next__(self) -> T:
        _next = self.get_next()
        if _next is None: raise StopIteration()
        return _next


class BiDimDomBase(ConfigurationExploration[tuple[int, int]]):
    _iter: Iterator[tuple[int, int]]

    def __init__(self) -> None:
        super().__init__()
        self._doms: list[tuple[int, int]] = list()

    def _is_dominated(self, configuration: tuple[int, int]) -> bool:
        (conf0, conf1) = configuration
        return any(
            conf0 >= dom_conf0 and conf1 >= dom_conf1
            for (dom_conf0, dom_conf1) in self._doms
        )

    def give_result(self, configuration: tuple[int, int], status: str) -> None:
        if status in ('sat', 'unknown'):
            self._doms.append(configuration)

    def get_next(self) -> tuple[int, int] | None:
        conf = next(self._iter, None)
        while conf is not None and self._is_dominated(conf):
            conf = next(self._iter, None)
        return conf


class NonShared_Exploration(BiDimDomBase):
    def __init__(self, max_lpp: int, max_ppo: int, subgraph_inputs_count: int) -> None:
        super().__init__()
        self._iter = self.__iterator(min(max_lpp, subgraph_inputs_count), max_ppo)

    @classmethod
    def __iterator(cls, max_lpp: int, max_ppo: int) -> Iterator[tuple[int, int]]:
        # special cell
        yield (0, 1)

        # grid cells
        for ppo in range(1, max_ppo + 1):
            for lpp in range(1, max_lpp + 1):
                yield (lpp, ppo)


class Shared_Exploration(BiDimDomBase):
    def __init__(self, max_pit: int, subgraph_outputs_count: int) -> None:
        super().__init__()
        self._iter = self.__iterator(max_pit, subgraph_outputs_count)

        import sys
        print('[WARNING] the shared exploration may have issues.', file=sys.stderr)

    @classmethod
    def __iterator(cls, max_pit: int, subgraph_outputs_count: int) -> Iterator[tuple[int, int]]:
        # special cell
        yield (0, 1)

        # grid cells
        for pit in range(1, max_pit + 1):
            for its in range(max(pit, subgraph_outputs_count), max(pit + 3 + 1, subgraph_outputs_count + 1)):
                yield (its, pit)
