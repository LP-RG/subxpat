from .config.config import *


class TemplateSpecs:
    def __init__(self, **kwargs):
        self.__template_name: str = kwargs[NAME].upper()
        self.__benchmark_name: str = kwargs[BENCHMARK]
        self.__exact_benchmark: str = kwargs[EXACT]
        self.__literals_per_product: int = int(kwargs[LITERALS_PER_PRODUCT])
        self.__products_per_output: int = int(kwargs[PRODUCTS_PER_OUTPUT])
        self.__subxpat: bool = kwargs[SUBXPAT]
        self.__shared: bool = kwargs[SHARED]
        self.__num_of_models = kwargs[NUM_OF_MODELS]
        self.__error_threshold = kwargs[TEMPLATE_SPEC_ET]
        self.__products_in_total: int = int(kwargs[PRODUCTS_IN_TOTAL])
        self.__partitioning_percentage = kwargs[PARTITIONING_PERCENTAGE]
        self.__iterations = kwargs[ITERATIONS]
        self.__timeout: int = int(kwargs[TIMEOUT])

    @property
    def partitioning_percentage(self):
        return self.__partitioning_percentage

    @property
    def pp(self):
        return self.__partitioning_percentage

    @property
    def iterations(self):
        return self.__iterations

    @property
    def template_name(self):
        return self.__template_name

    @property
    def benchmark_name(self):
        return self.__benchmark_name

    @property
    def exact_benchmark(self):
        return self.__exact_benchmark

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
    def subxpat(self):
        return self.__subxpat

    @property
    def shared(self):
        return self.__shared

    @property
    def num_of_models(self):
        return self.__num_of_models


    @property
    def et(self):
        return self.__error_threshold

    @property
    def timeout(self):
        return self.__timeout

    def __repr__(self):
        return f'An object of Class TemplateSpecs:\n' \
               f'{self.template_name = }\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.exact_benchmark = }\n' \
               f'{self.lpp = }\n' \
               f'{self.pit = }\n' \
               f'{self.subxpat = }\n' \
               f'{self.shared = }\n' \
               f'{self.num_of_models = }\n' \
               f'{self.et = }\n' \
               f'{self.timeout = }\n'
