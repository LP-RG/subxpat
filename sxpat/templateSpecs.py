from .config.config import *


class TemplateSpecs:
    def __init__(self, **kwargs):
        self.__template_name: str = kwargs[NAME].upper()
        self.__benchamrk_name: str = kwargs[BENCHMARK]
        self.__literals_per_product: int = int(kwargs[LITERALS_PER_PRODUCT])
        self.__products_per_output: int = int(kwargs[PRODUCTS_PER_OUTPUT])
        self.__subxpat: bool = kwargs[SUBXPAT]
        self.__shared: bool = kwargs[SHARED]
        self.__num_of_models = kwargs[NUM_OF_MODELS]
        self.__error_threshold = kwargs[TEMPLATE_SPEC_ET]
        self.__products_in_total: int = int(kwargs[PRODUCTS_IN_TOTAL])

    @property
    def template_name(self):
        return self.__template_name

    @property
    def benchmark_name(self):
        return self.__benchamrk_name

    @property
    def literals_per_product(self):
        return self.__literals_per_product

    @property
    def lpp(self):
        return self.__literals_per_product

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

    def __repr__(self):
        return f'An object of Class TemplateSpecs:\n' \
               f'{self.template_name = }\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.lpp = }\n' \
               f'{self.pit = }\n' \
               f'{self.subxpat = }\n' \
               f'{self.shared = }\n' \
               f'{self.num_of_models = }\n' \
               f'{self.et = }\n'
