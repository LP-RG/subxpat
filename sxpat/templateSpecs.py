from .config.config import *


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
        self.__sensitivity = kwargs[SENSITIVITY]

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
    def sensitivity(self):
        return self.__sensitivity

    @sensitivity.setter
    def sensitivity(self, this_sens):
        self.__sensitivity = this_sens


    @property
    def num_of_models(self):
        return self.__num_of_models


    @property
    def et(self):
        return self.__error_threshold

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
               f'{self.sensitivity = }'
