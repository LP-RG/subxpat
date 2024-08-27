from .config.config import *


class TemplateSpecs:
    def __init__(self, **kwargs):
        self.__exact_benchamrk_name: str = kwargs[EXACT]
        self.__benchamrk_name: str = kwargs[BENCHMARK]
        self.__literals_per_product: int = None
        self.__products_per_output: int = None
        self.__max_literals_per_product: int = int(kwargs[LITERALS_PER_PRODUCT])
        self.__max_products_per_output: int = int(kwargs[PRODUCTS_PER_OUTPUT])
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
        self.__timeout = float(kwargs[TIMEOUT])
        self.__min_subgraph_size = kwargs[SUBGRAPHSIZE]
        self.__mode = kwargs[MODE]
        self.__manual_nodes = kwargs[MANUAL_NODES]
        self.__population = kwargs[POPULATION]
        self.__min_labeling = kwargs[MIN_LABELING]
        self.__template: int = int(kwargs[TEMPLATE])
        self.__products_in_total: int = None
        self.__max_products_in_total: int = int(kwargs[PRODUCTS_IN_TOTAL])
        self.__parallel: bool = kwargs[PARALLEL]

        self.__full_error_function: int = int(kwargs[FULL_ERROR_FUNCTION])
        self.__sub_error_function: int = int(kwargs[SUB_ERROR_FUNCTION])

        self.et_partitioning: str = kwargs[ET_PARTITIONING]

        self.__keep_unsat_candidate: bool = self.__subxpat_v2
        self.__partial_labeling: bool = kwargs[PARTIAL_LABELING]
        self.__num_subgraphs: int = kwargs[NUM_SUBGRAPHS]

        self.__encoding: int = kwargs[ENCODING]

        self.__number_of_levels: int = int(kwargs[NUMBER_OF_LEVELS])
        self.__actual_number_of_levels: int = None

    @property
    def template(self):
        return self.__template

    @property
    def num_lev(self):
        return self.__number_of_levels

    @property
    def lv(self):
        return self.__actual_number_of_levels

    @lv.setter
    def lv(self, new_value: int):
        self.__actual_number_of_levels = new_value

    @property
    def num_subgraphs(self):
        return self.__num_subgraphs

    @property
    def keep_unsat_candidate(self):
        return self.__keep_unsat_candidate

    @property
    def parallel(self):
        return self.__parallel

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
    def manual_nodes(self):
        return self.__manual_nodes

    @property
    def partitioning_percentage(self):
        return self.__partitioning_percentage

    @property
    def pp(self):
        return self.__partitioning_percentage


    @property
    def exact_benchmark(self):
        return self.__exact_benchamrk_name

    @exact_benchmark.setter
    def exact_benchmark(self, value):
        self.__exact_benchamrk_name = value

    @property
    def benchmark_name(self):
        return self.__benchamrk_name

    @benchmark_name.setter
    def benchmark_name(self, this_name):
        self.__benchamrk_name = this_name

    @property
    def max_lpp(self):
        return self.__max_literals_per_product

    @property
    def lpp(self):
        return self.__literals_per_product

    @lpp.setter
    def lpp(self, this_lpp):
        self.__literals_per_product = this_lpp

    @property
    def max_ppo(self):
        return self.__max_products_per_output

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
    def timeout(self, this_timeout: float):
        self.__timeout = float(this_timeout)

    @property
    def num_of_models(self):
        return self.__num_of_models

    @property
    def et(self):
        return self.__error_threshold

    @et.setter
    def et(self, value):
        self.__error_threshold = value

    @property
    def min_subgraph_size(self):
        return self.__min_subgraph_size

    @min_subgraph_size.setter
    def min_subgraph_size(self, this_subgraph_size):
        self.__min_subgraph_size = this_subgraph_size

    @property
    def max_pit(self):
        return self.__max_products_in_total

    @property
    def pit(self):
        return self.__products_in_total

    @pit.setter
    def pit(self, new_value: int):
        self.__products_in_total = new_value

    @property
    def max_its(self) -> int:
        return self.__max_products_in_total + 3

    @property
    def full_error_function(self):
        return self.__full_error_function

    @property
    def sub_error_function(self):
        return self.__sub_error_function

    @property
    def encoding(self):
        return self.__encoding

    @property
    def partial_labeling(self):
        return self.__partial_labeling

    # > computed

    @property
    def template_name(self):
        return {
            0: 'Sop1',
            1: 'SharedLogic',
            2: 'Multilevel',
        }[self.template]

    @property
    def requires_subgraph_extraction(self):
        return self.__subxpat or self.__subxpat_v2

    @property
    def grid_param_1(self) -> int:
        return {
            0: self.max_lpp,
            1: self.max_its,
            2: self.num_lev,
        }[self.template]

    @property
    def grid_param_2(self) -> int:
        return {
            0: self.max_ppo,
            1: self.max_pit,
            2: self.max_pit
        }[self.template]

    @property
    def total_number_of_cells_per_iter(self) -> int:
        # special_cell + ROWS * COLUMNS
        return 1 + self.grid_param_1 * self.grid_param_2

    def __repr__(self):
        return f'An object of Class TemplateSpecs:\n' \
               f'{self.template_name = }\n' \
               f'{self.exact_benchmark = }\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.lpp = }\n' \
               f'{self.ppo = }\n' \
               f'{self.pit = }\n' \
               f'{self.lv = }\n'\
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
               f'{self.manual_nodes = }\n' \
               f'{self.population = }\n' \
               f'{self.template = }\n'  \
               f'{self.parallel = }\n' \
               f'{self.min_labeling = }\n' \
               f'{self.full_error_function = }\n' \
               f'{self.sub_error_function = }\n' \
               f'{self.et_partitioning = }\n' \
               f'{self.partial_labeling = }\n' \
               f'{self.keep_unsat_candidate = }\n'
