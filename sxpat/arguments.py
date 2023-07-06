import argparse
import sys
import typing
from Z3Log.argument import Arguments
from Z3Log.config.config import *


class Arguments(Arguments):
    def __init__(self, tmp_args: argparse):
        super().__init__(tmp_args)
        self.__literal_per_product: int = tmp_args.lpp
        self.__product_per_output: int = tmp_args.ppo
        self.__subxpat: bool = tmp_args.subxpat
        self.__error_threshold: int = tmp_args.et
        self.__clean: bool = tmp_args.clean
        self.__partitioning_percentage = tmp_args.partitioning_percentage

    @property
    def partitioning_percentage(self):
        return self.__partitioning_percentage

    @property
    def literals_per_product(self):
        return self.__literal_per_product

    @property
    def lpp(self):
        return self.__literal_per_product

    @property
    def products_per_output(self):
        return self.__product_per_output

    @property
    def ppo(self):
        return self.__product_per_output

    @property
    def subxpat(self):
        return self.__subxpat

    @property
    def error_threshold(self):
        return self.__error_threshold

    @property
    def et(self):
        return self.__error_threshold

    @property
    def clean(self):
        return self.__clean

    @classmethod
    def parse(cls):
        my_parser = argparse.ArgumentParser(description='converts different formats to one another',
                                            prog=sys.argv[0],
                                            usage='%(prog)s benchmark-name|benchmark-path')

        my_parser.add_argument('benchmark',
                               type=str,
                               default=None,
                               help='benchmark-name')
        my_parser.add_argument('--lpp', '-lpp',
                               type=int,
                               default=3,
                               help='literals-per-product')

        my_parser.add_argument('--ppo', '-ppo',
                               type=int,
                               default=2,
                               help='products-per-output')

        my_parser.add_argument('--et', '-et',
                               type=int,
                               default=3,
                               help='error-threshold')

        my_parser.add_argument('--samples', '-s',
                               default=100,
                               type=int,
                               help='number-of-monte-carlo-samples')

        my_parser.add_argument('--subxpat', '-subxpat',
                               type=bool,
                               default=True,
                               help='activate-subxpat')

        my_parser.add_argument('--approximate_benchmark', '-app',
                               type=str,
                               default=None,
                               help='approximate-benchmark-name in gv/verilog format')
        my_parser.add_argument('--metric', '-metric',
                               type=str,
                               default=WAE,
                               help='the-desired-worst-case-error-metric')
        my_parser.add_argument('--precision', '-p',
                               type=int,
                               default=2,
                               help='number-of-decimal-points-for-wre')
        my_parser.add_argument('--strategy', '-strategy',
                               type=str,
                               default=MONOTONIC,
                               help='the-solver-strategy-to-find-metric')
        my_parser.add_argument('--optimization', '-opt',
                               type=str,
                               default=None,
                               help='the-solver-optimization (Solver, Optimize, Maximize)')
        my_parser.add_argument('--experiment', '-e',
                               type=str,
                               default=SINGLE,
                               help="the-experiment-name [SINGLE|QOR|RANDOM]")
        my_parser.add_argument('--pruning_percentage', '-pp',
                               type=int,
                               default=10,
                               help='gate-percentage-carved-out')

        my_parser.add_argument('--partitioning_percentage', '-pap',
                               type=int,
                               default=10,
                               help='partitioning_percentage')

        my_parser.add_argument('--clean',
                               type=bool,
                               default=False)

        tmp_args = my_parser.parse_args()

        return Arguments(tmp_args)

    def __repr__(self):
        return f'An object of class Arguments:\n' \
               f'{self.literals_per_product = }\n' \
               f'{self.products_per_output = }\n' \
               f'{self.subxpat = }\n' \
               f'{self.et = }\n' \
               f'{self.__clean = }\n' \
               f'{self.partitioning_percentage = }\n'
