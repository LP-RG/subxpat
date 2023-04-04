from .config.config import *


class TemplateSpecs:
    def __init__(self, **kwargs):
        self.__template_name: str = kwargs[NAME].upper()
        self.__benchamrk_name: str = kwargs[BENCHMARK]
        self.__literals_per_product: int = int(kwargs[LITERALS_PER_PRODUCT])
        self.__products_per_output: int = int(kwargs[PRODUCTS_PER_OUTPUT])
        self.__subxpat: bool = kwargs[SUBXPAT]
        self.__num_of_models = kwargs[NUM_OF_MODELS]

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
    def subxpat(self):
        return self.__subxpat

    @property
    def num_of_models(self):
        return self.__num_of_models


    def __repr__(self):
        return f'An object of Class TemplateSpecs:\n' \
               f'{self.template_name = }\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.lpp = }\n' \
               f'{self.ppo = }\n' \
               f'{self.subxpat = }\n' \
               f'{self.num_of_models = }\n'
