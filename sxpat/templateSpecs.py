from .config.config import *


class TemplateSpecs:
    def __init__(self, **kwargs):
        self.__template_name: str = kwargs[NAME].upper()
        self.__exact_benchamrk_name: str = kwargs[EXACT]
        self.__benchamrk_name: str = kwargs[BENCHMARK]
        self.__literals_per_product: int = int(kwargs[LITERALS_PER_PRODUCT])
        self.__products_per_output: int = int(kwargs[PRODUCTS_PER_OUTPUT])
        self.__subxpat: bool = kwargs[SUBXPAT]
        self.__subxpat_v2: bool = kwargs[SUBXPAT_V2]
        self.__num_of_models = kwargs[NUM_OF_MODELS]
        self.__error_threshold = kwargs[TEMPLATE_SPEC_ET]
        self.__partitioning_percentage = kwargs[PARTITIONING_PERCENTAGE]

        self.__iterations = kwargs[ITERATIONS] if self.subxpat else 1
        self.__grid = kwargs[GRID]
        self.__imax = kwargs[IMAX]
        self.__omax = kwargs[OMAX]
        self.__max_sensitivity = kwargs[SENSITIVITY]
        self.__sensitivity = 0
        self.__timeout = kwargs[TIMEOUT]
        self.__min_subgraph_size = kwargs[SUBGRAPHSIZE]
        self.__mode = kwargs[MODE]
        self.__population = kwargs[POPULATION]
        self.__min_labeling = kwargs[MIN_LABELING]
        self.__shared = kwargs[SHARED]
        self.__products_in_total: int = int(kwargs[PRODUCTS_IN_TOTAL])
        self.__parallel: bool = kwargs[PARALLEL]

        self.__full_error_function: int = int(kwargs[FULL_ERROR_FUNCTION])
        self.__sub_error_function: int = int(kwargs[SUB_ERROR_FUNCTION])

    @property
    def parallel(self):
        return self.__parallel

    @property
    def shared(self):
        return self.__shared

    @property
    def min_labeling(self):
        return self.__min_labeling

    @property
    def population(self):
        return self.__population

    @property
    def mode(self):
        return self.__mode

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
    def subxpat_v2(self):
        return self.__subxpat_v2
    
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

    @property
    def products_in_total(self):
        return self.__products_in_total

    @property
    def pit(self):
        return self.__products_in_total

    @pit.setter
    def pit(self, this_pit):
        self.__products_in_total = this_pit

    @property
    def full_error_function(self):
        return self.__full_error_function

    @property
    def sub_error_function(self):
        return self.__sub_error_function

    def __repr__(self):
        return f'An object of Class TemplateSpecs:\n' \
               f'{self.template_name = }\n' \
               f'{self.exact_benchmark = }\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.lpp = }\n' \
               f'{self.ppo = }\n' \
               f'{self.pit = }\n' \
               f'{self.subxpat = }\n' \
               f'{self.subxpat_v2 = }\n' \
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
               f'{self.min_subgraph_size = }\n' \
               f'{self.mode = }\n' \
               f'{self.population = }\n' \
               f'{self.shared = }\n'  \
               f'{self.parallel = }\n' \
               f'{self.min_labeling = }'
