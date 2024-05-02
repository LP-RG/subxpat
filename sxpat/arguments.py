from __future__ import annotations
from typing import List

import argparse

from Z3Log.argument import Arguments as Z3Log_Arguments
from Z3Log.config.config import WAE, MONOTONIC, SINGLE


class CommaSplitAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, [s.strip() for s in values.split(',')])


# import dataclasses as dc
# @dc.dataclass
# class Arguments:
#     """Missing the ones from Z3Log"""

#     literal_per_product: int
#     product_per_output: int
#     subxpat: bool
#     subxpat_v2: bool
#     error_threshold: int
#     clean: bool
#     partitioning_percentage: int
#     iterations: int
#     grid: bool
#     multiple: bool
#     plot: bool
#     imax: int
#     omax: int
#     sensitivity: int
#     timeout: int
#     subgraph_size: int
#     mode: int
#     population: int
#     num_models: int
#     min_labeling: bool
#     shared: bool
#     products_in_total: int
#     parallel: bool
#     full_error_function: int
#     sub_error_function: int

#     @classmethod
#     def from_dict(cls, o: Dict[str, Any]) -> Arguments:
#         return cls(
#             o.lpp,
#             o.ppo,
#             o.subxpat,
#             o.subxpat_v2,
#             o.et,
#             o.clean,
#             o.partitioning_percentage,
#             o.iterations,
#             o.grid,
#             o.multiple,
#             o.plot,
#             o.imax,
#             o.omax,
#             o.sensitivity,
#             o.timeout,
#             o.subgraphsize,
#             o.mode,
#             o.population,
#             o.num_models,
#             o.min_labeling,
#             o.shared,
#             o.pit,
#             o.parallel,
#             o.full_error_function,
#             o.sub_error_function,
#         )


class Arguments(Z3Log_Arguments):
    def __init__(self, tmp_args: argparse):
        super().__init__(tmp_args)
        self.__literal_per_product: int = tmp_args.lpp
        self.__product_per_output: int = tmp_args.ppo
        self.__subxpat: bool = tmp_args.subxpat
        self.__subxpat_v2: bool = tmp_args.subxpat_v2
        self.__error_threshold: int = tmp_args.et
        self.__clean: bool = tmp_args.clean
        self.__partitioning_percentage: int = tmp_args.partitioning_percentage
        self.__iterations: int = tmp_args.iterations
        self.__grid: bool = tmp_args.grid
        self.__multiple: bool = tmp_args.multiple
        self.__plot: bool = tmp_args.plot
        self.__imax: int = tmp_args.imax
        self.__omax: int = tmp_args.omax
        self.__sensitivity: int = tmp_args.sensitivity
        self.__timeout: int = tmp_args.timeout
        self.__subgraph_size: int = tmp_args.subgraphsize
        self.__mode: int = tmp_args.mode
        self.__manual_nodes: List[str] = tmp_args.manual_nodes
        self.__population: int = tmp_args.population
        self.__num_models: int = tmp_args.num_models
        self.__min_labeling: bool = tmp_args.min_labeling
        self.__shared: bool = tmp_args.shared
        self.__products_in_total: int = tmp_args.pit
        self.__parallel: bool = tmp_args.parallel
        self.__full_error_function: int = tmp_args.full_error_function
        self.__sub_error_function: int = tmp_args.sub_error_function
        self.__et_partitioning: int = tmp_args.et_partitioning
        self.__lut: bool = tmp_args.lut
        self.__selectors_per_output: int = tmp_args.selectors_per_output

    @property
    def parallel(self):
        return self.__parallel

    @property
    def products_in_total(self):
        return self.__products_in_total

    @property
    def pit(self):
        return self.__products_in_total

    @property
    def shared(self):
        return self.__shared

    @property
    def min_labeling(self):
        return self.__min_labeling

    @property
    def num_models(self):
        return self.__num_models

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
    def selectors_per_output(self):
        return self.__selectors_per_output

    @property
    def spo(self):
        return self.__selectors_per_output

    @property
    def subxpat(self):
        return self.__subxpat

    @property
    def subxpat_v2(self):
        return self.__subxpat_v2

    @property
    def error_threshold(self):
        return self.__error_threshold

    @property
    def et(self):
        return self.__error_threshold

    @property
    def iterations(self):
        return self.__iterations

    @property
    def grid(self):
        return self.__grid

    @property
    def multiple(self):
        return self.__multiple

    @property
    def plot(self):
        return self.__plot

    @property
    def imax(self):
        return self.__imax

    @property
    def omax(self):
        return self.__omax

    @property
    def sensitivity(self):
        return self.__sensitivity

    @property
    def timeout(self):
        return self.__timeout

    @property
    def subgraph_size(self):
        return self.__subgraph_size

    @property
    def clean(self):
        return self.__clean

    @property
    def full_error_function(self):
        return self.__full_error_function

    @property
    def sub_error_function(self):
        return self.__sub_error_function

    @property
    def et_partitioning(self):
        return self.__et_partitioning

    @property
    def lut(self):
        return self.__lut


    @classmethod
    def parse(cls) -> Arguments:
        my_parser = argparse.ArgumentParser(description='converts different formats to one another',
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

        my_parser.add_argument('--spo', '-spo',
                               type=int,
                               default=2,
                               help='selectors-per-output')

        my_parser.add_argument('--et', '-et',
                               type=int,
                               default=3,
                               help='error-threshold')

        my_parser.add_argument('--samples', '-s',
                               default=100,
                               type=int,
                               help='number-of-monte-carlo-samples')

        my_parser.add_argument('--subxpat',
                               action='store_true',
                               help='activate-subxpat')
        my_parser.add_argument('--subxpat-v2',
                               action='store_true',
                               help='activate v2 of subxpat')

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

        my_parser.add_argument('--iterations', '-iterations',
                               type=int,
                               default=1)

        my_parser.add_argument('--grid',
                               action="store_true",
                               default=False)

        my_parser.add_argument('--multiple',
                               action="store_true",
                               default=False)

        my_parser.add_argument('--plot',
                               action="store_true",
                               default=False)

        my_parser.add_argument('-imax',
                               type=int,
                               default=3,
                               help='maximum-inputs-for-subgraph')

        my_parser.add_argument('-omax',
                               type=int,
                               default=2,
                               help='maximum-outputs-for-subgraph')

        my_parser.add_argument('-sensitivity',
                               type=int,
                               default=-1,
                               help='maximum-partitioning-sensitivity')

        my_parser.add_argument('-subgraphsize',
                               type=int,
                               default=10,
                               help='minimum-size-for-subgraphs')

        my_parser.add_argument('-timeout',
                               type=int,
                               default=10800,
                               help='the-timeout-for-every-cell-in-seconds(default 3 hours)')

        my_parser.add_argument('-mode',
                               type=int,
                               default=3,
                               help='selects-partitioning-algorithm [if 1=> imax,omax] \
                                    [if 2=> imax,omax,min_size,sensitivity] \
                                    [if 3=>min_size,sensitivity]')

        my_parser.add_argument('-manual-nodes',
                               default=[],
                               action=CommaSplitAction,
                               help='Comma separated list of nodes that must be part of the subgraph')

        my_parser.add_argument('-population',
                               type=int,
                               default=1,
                               help='selected-solutions-at-every-iteration')

        my_parser.add_argument('-num_models',
                               type=int,
                               default=1,
                               help='number-of-models')

        my_parser.add_argument('--clean',
                               action="store_true",
                               default=False,
                               help='cleans-output-directory-and-its-contents')

        my_parser.add_argument('--min_labeling',
                               action="store_true",
                               default=False,
                               help='[if true labels-gates-with-min-error] \
                                     [if false max-error]')

        my_parser.add_argument('--shared',
                               action="store_true",
                               default=False,
                               help='activates-logic-sharing')

        my_parser.add_argument('--pit', '-pit',
                               type=int,
                               default=5,
                               help='products-in-total')

        my_parser.add_argument('--parallel',
                               action="store_true",
                               default=False)

        my_parser.add_argument('--evaluate',
                               action="store_true",
                               default=False)

        # error functions
        my_parser.add_argument('--full_error_function',
                               choices=['1'],
                               default=1)
        my_parser.add_argument('--sub_error_function',
                               choices=['1', '2'],
                               default=1)

        my_parser.add_argument('--et-partitioning',
                               choices=['asc', 'desc'],
                               default='asc')

        my_parser.add_argument('--lut',
                               action="store_true",
                               default=False)


        tmp_args = my_parser.parse_args()

        return Arguments(tmp_args)

    def __repr__(self):
        return f'An object of class Arguments:\n' \
               f'{self.literals_per_product = }\n' \
               f'{self.products_per_output = }\n' \
               f'{self.products_in_total = }\n' \
               f'{self.subxpat = }\n' \
               f'{self.subxpat_v2 = }\n' \
               f'{self.et = }\n' \
               f'{self.clean = }\n' \
               f'{self.partitioning_percentage = }\n' \
               f'{self.iterations = }\n' \
               f'{self.grid = }\n' \
               f'{self.multiple = }\n' \
               f'{self.plot = }\n' \
               f'{self.imax = }\n' \
               f'{self.omax = }\n' \
               f'{self.sensitivity = }\n' \
               f'{self.timeout = }\n' \
               f'{self.subgraph_size = }\n' \
               f'{self.mode = }\n' \
               f'{self.manual_nodes = }\n' \
               f'{self.population = }\n' \
               f'{self.num_models = }\n'\
               f'{self.min_labeling = }\n' \
               f'{self.shared = }\n' \
               f'{self.parallel = }\n' \
               f'{self.full_error_function = }\n' \
               f'{self.sub_error_function = }\n' \
               f'{self.et_partitioning = }\n' \
               f'{self.clean = }\n'\
               f'{self.spo = }\n'\
               f'{self.lut = }'