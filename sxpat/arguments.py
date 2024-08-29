from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import enum
import dataclasses as dc

import argparse
from pathlib import Path
import operator as op


class ErrorPartitioningType(enum.Enum):
    ASCENDING = 'asc'
    DESCENDING = 'desc'
    SMART_ASCENDING = 'smart_asc'
    SMART_DESCENDING = 'smart_desc'


class EncodingType(enum.Enum):
    Z3_INTEGER = 'z3int'
    Z3_BITVECTOR = 'z3bvec'
    QBF = 'qbf'


class TemplateType(enum.Enum):
    NON_SHARED = 'nonshared'
    SHARED = 'shared'


class EnumChoicesAction(argparse.Action):
    def __init__(self, *args, type: enum.Enum, **kwargs) -> None:
        super().__init__(*args, **kwargs, choices=[e.value for e in type])
        self.enum = type

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 value: str, option_string: str = None) -> None:
        setattr(namespace, self.dest, self.enum(value))


@dc.dataclass(frozen=True)
class Arguments:
    # files
    exact_benchmark: str
    current_benchmark: str

    # labeling
    min_labeling: bool
    partial_labeling: bool

    # subgraph extraction
    extraction_mode: int
    input_max: int
    output_max: int
    imax = property(op.attrgetter('input_max'))
    omax = property(op.attrgetter('output_max'))
    min_subgraph_size: int
    num_subgraphs: int

    # exploration (1)
    subxpat: bool
    template: TemplateType
    encoding: EncodingType
    num_models: int
    # exploration (2)
    literals_per_product: int
    products_per_output: int
    products_in_total: int
    lpp = property(op.attrgetter('literals_per_product'))
    ppo = property(op.attrgetter('products_per_output'))
    pit = property(op.attrgetter('products_in_total'))

    # error
    error_threshold: int
    et = property(op.attrgetter('error_threshold'))
    error_partitioning: ErrorPartitioningType

    # other
    timeout: float
    plot: bool
    parallel: bool
    clean: bool

    def __post_init__(self):
        object.__setattr__(self, 'exact_benchmark', Path(self.exact_benchmark).stem)
        object.__setattr__(self, 'current_benchmark', Path(self.current_benchmark).stem)

    @staticmethod
    def parse() -> Arguments:
        dependencies: Dict[Tuple[argparse.Action, Optional[Any]], List[argparse.Action]] = defaultdict(list)
        parser = argparse.ArgumentParser(description='converts different formats to one another',
                                         formatter_class=argparse.RawTextHelpFormatter)

        # > files stuff

        _ex_bench = parser.add_argument(metavar='exact-benchmark',
                                        dest='exact_benchmark',
                                        type=str,
                                        help='Circuit to approximate. Must be in the input/ver/ folder')

        _cur_bench = parser.add_argument('--current-benchmark', '--curr',
                                         type=str,
                                         default=None,
                                         help='Approximated circuit to continue from. Must be in the input/ver/ folder')

        # > graph labeling stuff

        _min_lab = parser.add_argument('--min-labeling',
                                       action='store_true',
                                       help='Nodes are weighted using their minimum error, instead of maximum error')

        _part_lab = parser.add_argument('--partial-labeling',
                                        action='store_true',
                                        help='Assign weight only to relevant nodes')

        # > subgraph extraction stuff

        _ex_mode = parser.add_argument('--extraction-mode', '--mode',
                                       choices=[1, 2, 3, 4, 5, 55, 11, 12],
                                       type=int,
                                       help='Subgraph extraction algorithm to use')

        _imax = parser.add_argument('--input-max', '--imax',
                                    type=int,
                                    help='Maximum allowed number of inputs to the subgraph')

        _omax = parser.add_argument('--output-max', '--omax',
                                    type=int,
                                    help='Maximum allowed number of outputs from the subgraph')

        # the value is never used, but a field in specs is needed for one algorithm
        # my_parser.add_argument('-sensitivity',

        _msub_size = parser.add_argument('--min-subgraph-size',
                                         type=int,
                                         help='Minimum valid size for the subgraph')

        _num_sub = parser.add_argument('--num-subgraphs',
                                       type=int,
                                       default=1,
                                       help='The number of attempts for subgraph extraction')

        # > exploration stuff

        _subxpat = parser.add_argument('--subxpat',
                                       action='store_true',
                                       help='Run the system as SubXPAT instead of XPat')

        _template = parser.add_argument('--template',
                                        type=TemplateType,
                                        action=EnumChoicesAction,
                                        help='Select template logic')

        _lpp = parser.add_argument('--literals-per-product', '--lpp',
                                   type=int,
                                   help='The max number of literals per product to use')
        dependencies[(_template, TemplateType.NON_SHARED)].append(_lpp)

        _ppo = parser.add_argument('--products-per-output', '--ppo',
                                   type=int,
                                   help='The max number of products per output to use')
        dependencies[(_template, TemplateType.NON_SHARED)].append(_ppo)

        _pit = parser.add_argument('--products-in-total', '--pit',
                                   type=int,
                                   help='The max number of products to use in total')
        dependencies[(_template, TemplateType.SHARED)].append(_pit)

        _nmod = parser.add_argument('--num-models',
                                    type=int,
                                    default=1,
                                    help='Number of models to generate for each step')

        # > error stuff

        _et = parser.add_argument('--error-threshold', '--et', '-e',
                                  type=int,
                                  help='The maximum allowable error')

        _ep = parser.add_argument('--error-partitioning', '--epar',
                                  type=ErrorPartitioningType,
                                  action=EnumChoicesAction,
                                  default=ErrorPartitioningType.ASCENDING,
                                  help='The error partitioning algorithm to use')

        # > other stuff

        _enc = parser.add_argument('--encoding',
                                   type=EncodingType,
                                   action=EnumChoicesAction,
                                   default=EncodingType.Z3_BITVECTOR,
                                   help='The encoding to use in solving the approximation')

        _plt = parser.add_argument('--plot',
                                   action='store_true',
                                   help='The system will be run as plotter (DEPRECATED?)')

        _timeout = parser.add_argument('--timeout',
                                       type=float,
                                       default=10800,
                                       help='The maximum time each cell is given to run in seconds (default: 3h)')

        _parallel = parser.add_argument('--parallel',
                                        action='store_true',
                                        help='Run in parallel what is possilbe')

        _clean = parser.add_argument('--clean',
                                     action='store_true',
                                     help='Reset the output folder before running')

        raw_args = parser.parse_args()

        # default dependencies
        if raw_args.current_benchmark is None:
            raw_args.current_benchmark = raw_args.exact_benchmark

        # required dependencies
        for (source, value), dependents in dependencies.items():
            if value is None and getattr(raw_args, source.dest, None) is not None:
                for dep in dependents:
                    if getattr(raw_args, dep.dest, None) is None:
                        raise AttributeError(f'Argument `{source.option_strings[0]}` with value {value!r} requires argument `{dep.option_strings[0]}`')

            elif value is not None and getattr(raw_args, source.dest, None) == value:
                for dep in dependents:
                    if getattr(raw_args, dep.dest, None) is None:
                        raise AttributeError(f'Argument `{source.option_strings[0]}` requires argument `{dep.option_strings[0]}`')

        return Arguments(**vars(raw_args))

    def __repr__(self):
        """
        Procedurally generates the string representation of the object.  
        The string will contain the name of the class, followed by one line for each field (name/value pair).
        """
        fields = ''.join(f'   {k} = {v},\n' for k, v in vars(self).items())
        return f'{self.__class__.__name__}(\n{fields})'
