import dataclasses as dc
from typing import Any

from .config.config import *


@dc.dataclass
class _TemplateSpecs:

    template_name: str
    exact_benchmark: str
    benchmark_name: str

    literals_per_product: int
    lpp = property(lambda s: s.literals_per_product)
    products_per_output: int
    ppo = property(lambda s: s.products_per_output)

    subxpat: bool
    num_of_models: int

    error_treshold: int
    et = property(lambda s: s.error_treshold)
    partitioning_percentage: Any
    pp = property(lambda s: s.partitioning_percentage)

    iterations: Any
    grid: Any
    imax: Any
    omax: Any
    max_sensitivity: Any
    sensitivity: Any
    timeout: Any
    min_subgraph_size: Any
    min_subgraph_size: Any

    def __post_init__(self):
        raise Exception("Refactoring in stand by. [assigned: Marco]")

        self.template_name = self.template_name.upper()
        self.literals_per_product = int(self.literals_per_product)
        self.products_per_output = int(self.products_per_output)
        self.num_of_models = int(self.num_of_models)
        self.error_treshold = int(self.error_treshold)

    def __repr__(self):
        return "\n".join(
            f'An object of Class TemplateSpecs:',
            f' > {self.template_name = }',
            f' > {self.exact_benchmark = }',
            f' > {self.benchmark_name = }',
            f' > {self.lpp = }',
            f' > {self.ppo = }',
            f' > {self.subxpat = }',
            f' > {self.num_of_models = }',
            f' > {self.et = }',
            f' > {self.partitioning_percentage = }',
            f' > {self.iterations = }',
            f' > {self.grid = }',
            f' > {self.imax = }',
            f' > {self.omax = }',
            f' > {self.max_sensitivity = }',
            f' > {self.sensitivity = }',
            f' > {self.timeout = }',
            f' > {self.min_subgraph_size = }',
        )


class TemplateSpecs:
    def __init__(self, **kwargs):
        self.__template_name: str = kwargs[NAME].upper()
        self.__exact_benchamrk_name: str = kwargs[EXACT]
        self.__benchamrk_name: str = kwargs[BENCHMARK]
        self.__literals_per_product: int = int(kwargs[LITERALS_PER_PRODUCT])
        self.__products_per_output: int = int(kwargs[PRODUCTS_PER_OUTPUT])
        self.__subxpat: bool = kwargs[SUBXPAT]
        self.__num_of_models = kwargs[NUM_OF_MODELS]
        self.__error_threshold = kwargs[TEMPLATE_SPEC_ET]
        self.__partitioning_percentage = kwargs[PARTITIONING_PERCENTAGE]
        self.__iterations = kwargs[ITERATIONS]
        self.__grid = kwargs[GRID]
        self.__imax = kwargs[IMAX]
        self.__omax = kwargs[OMAX]
        self.__max_sensitivity = kwargs[SENSITIVITY]
        self.__sensitivity = 0
        self.__timeout = kwargs[TIMEOUT]
        self.__min_subgraph_size = kwargs[SUBGRAPHSIZE]

    @property
    def partitioning_percentage(self):
        return self.__partitioning_percentage

    @property
    def pp(self):
        return self.__partitioning_percentage

    @property
    def template_name(self):
        return self.__template_name

    @property
    def exact_benchmark(self):
        return self.__exact_benchamrk_name

    @property
    def benchmark_name(self):
        return self.__benchamrk_name

    @benchmark_name.setter
    def benchmark_name(self, this_name):
        self.__benchamrk_name = this_name

    @property
    def literals_per_product(self):
        return self.__literals_per_product

    @property
    def lpp(self):
        return self.__literals_per_product

    @lpp.setter
    def lpp(self, this_lpp):
        self.__literals_per_product = this_lpp

    @property
    def products_per_output(self):
        return self.__products_per_output

    @property
    def ppo(self):
        return self.__products_per_output

    @ppo.setter
    def ppo(self, this_ppo):
        self.__products_per_output = this_ppo

    @property
    def subxpat(self):
        return self.__subxpat

    @property
    def iterations(self):
        return self.__iterations

    @iterations.setter
    def iterations(self, this_iteration: int):
        self.__iterations = this_iteration

    @property
    def grid(self):
        return self.__grid

    @property
    def imax(self):
        return self.__imax

    @imax.setter
    def imax(self, this_imax):
        self.__imax = this_imax

    @property
    def omax(self):
        return self.__omax

    @omax.setter
    def omax(self, this_omax):
        self.__omax = this_omax

    @property
    def max_sensitivity(self):
        return self.__max_sensitivity

    @max_sensitivity.setter
    def max_sensitivity(self, this_sens):
        self.__max_sensitivity = this_sens

    @property
    def sensitivity(self):
        return self.__sensitivity

    @sensitivity.setter
    def sensitivity(self, this_sensitivity):
        self.__sensitivity = this_sensitivity

    @property
    def timeout(self):
        return self.__timeout

    @timeout.setter
    def timeout(self, this_timeout):
        self.__timeout = this_timeout

    @property
    def num_of_models(self):
        return self.__num_of_models

    @property
    def et(self):
        return self.__error_threshold

    @property
    def min_subgraph_size(self):
        return self.__min_subgraph_size

    @min_subgraph_size.setter
    def min_subgraph_size(self, this_subgraph_size):
        self.__min_subgraph_size = this_subgraph_size

    def __repr__(self):
        return f'An object of Class TemplateSpecs:\n' \
               f'{self.template_name = }\n' \
               f'{self.exact_benchmark = }\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.lpp = }\n' \
               f'{self.ppo = }\n' \
               f'{self.subxpat = }\n' \
               f'{self.num_of_models = }\n' \
               f'{self.et = }\n' \
               f'{self.partitioning_percentage = }\n' \
               f'{self.iterations = }\n' \
               f'{self.grid = }\n' \
               f'{self.imax = }\n' \
               f'{self.omax = }\n' \
               f'{self.max_sensitivity = }\n' \
               f'{self.sensitivity = }\n' \
               f'{self.timeout = }\n' \
               f'{self.min_subgraph_size = }'
