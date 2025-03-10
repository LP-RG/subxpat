from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import enum
import dataclasses as dc

import argparse
from pathlib import Path


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


class ConstantsType(enum.Enum):
    NEVER = 'never'
    ALWAYS = 'always'


class EnumChoicesAction(argparse.Action):
    def __init__(self, *args, type: enum.Enum, **kwargs) -> None:
        super().__init__(*args, **kwargs, choices=[e.value for e in type])
        self.enum = type

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 value: str, option_string: str = None) -> None:
        setattr(namespace, self.dest, self.enum(value))


@dc.dataclass
class Specifications:
    # files
    exact_benchmark: str
    current_benchmark: str  # rw

    # labeling
    min_labeling: bool
    partial_labeling: bool

    # subgraph extraction
    extraction_mode: int
    imax: int
    omax: int
    min_subgraph_size: int
    num_subgraphs: int
    max_sensitivity: int
    sensitivity: int = dc.field(init=False, default=None)  # rw

    # exploration (1)
    subxpat: bool
    template: TemplateType
    encoding: EncodingType
    constants: ConstantsType
    wanted_models: int
    iteration: int = dc.field(init=False, default=None)  # rw
    # exploration (2)
    max_lpp: int
    lpp: int = dc.field(init=False, default=None)  # rw
    max_ppo: int
    ppo: int = dc.field(init=False, default=None)  # rw
    max_pit: int
    pit: int = dc.field(init=False, default=None)  # rw
    its: int = dc.field(init=False, default=None)  # rw

    # error
    max_error: int
    et: int = dc.field(init=False, default=None)  # rw
    error_partitioning: ErrorPartitioningType

    # other
    timeout: float
    parallel: bool
    plot: bool
    clean: bool

    def __post_init__(self):
        object.__setattr__(self, 'exact_benchmark', Path(self.exact_benchmark).stem)
        object.__setattr__(self, 'current_benchmark', Path(self.current_benchmark).stem)

    # > computed

    @property
    def max_its(self) -> int:
        return self.max_pit + 3

    @property
    def template_name(self):
        return {
            TemplateType.NON_SHARED: 'Sop1',
            TemplateType.SHARED: 'SharedLogic',
        }[self.template]

    @property
    def requires_subgraph_extraction(self) -> bool:
        return (
            self.subxpat
        )

    @property
    def requires_labeling(self) -> bool:
        return (
            self.subxpat
            and self.extraction_mode >= 2
        )

    @property
    def grid_param_1(self) -> int:
        return {  # lazy
            TemplateType.NON_SHARED: lambda: self.max_lpp,
            TemplateType.SHARED: lambda: self.max_its,
        }[self.template]()

    @property
    def grid_param_2(self) -> int:
        return {  # lazy
            TemplateType.NON_SHARED: lambda: self.max_ppo,
            TemplateType.SHARED: lambda: self.max_pit,
        }[self.template]()

    @property
    def total_number_of_cells_per_iter(self) -> int:
        # special_cell + ROWS * COLUMNS
        return 1 + self.grid_param_1 * self.grid_param_2

    @classmethod
    def parse_args(cls):
        parser = argparse.ArgumentParser(description='Run the XPat system',
                                         epilog='Developed by Prof. Pozzi research team',
                                         formatter_class=argparse.RawTextHelpFormatter)

        # > files stuff

        _ex_bench = parser.add_argument(metavar='exact-benchmark',
                                        dest='exact_benchmark',
                                        type=str,
                                        help='Circuit to approximate (Verilog file in `input/ver/`)')

        _cur_bench = parser.add_argument('--current-benchmark', '--curr',
                                         type=str,
                                         default=None,
                                         help='Approximated circuit used to continue the execution (Verilog file in `input/ver/`) (default: same as exact-benchmark)')

        # > graph labeling stuff

        _min_lab = parser.add_argument('--min-labeling',
                                       action='store_true',
                                       help='Nodes are weighted using their minimum error, instead of maximum error')

        _part_lab = parser.add_argument('--partial-labeling',
                                        action='store_true',
                                        help='Weights are assigned only to relevant nodes')

        # > subgraph extraction stuff

        _ex_mode = parser.add_argument('--extraction-mode', '--mode',
                                       type=int,
                                       choices=[1, 2, 3, 4, 5, 55, 11, 12],
                                       default=55,
                                       help='Subgraph extraction algorithm to use (default: 55)')

        _imax = parser.add_argument('--input-max', '--imax',
                                    type=int,
                                    dest='imax',
                                    help='Maximum allowed number of inputs to the subgraph')

        _omax = parser.add_argument('--output-max', '--omax',
                                    type=int,
                                    dest='omax',
                                    help='Maximum allowed number of outputs from the subgraph')

        _msens = parser.add_argument('--max-sensitivity',
                                     type=int,
                                     help='Maximum partitioning sensitivity')

        _msub_size = parser.add_argument('--min-subgraph-size',
                                         type=int,
                                         help='Minimum valid size for the subgraph')

        _num_sub = parser.add_argument('--num-subgraphs',
                                       type=int,
                                       default=1,
                                       help='The number of attempts for subgraph extraction (default: 1)')

        # > exploration stuff

        _subxpat = parser.add_argument('--subxpat',
                                       action='store_true',
                                       help='Run SubXPAT iteratively, instead of standard XPAT')

        _consts = parser.add_argument('--constants',
                                      type=ConstantsType,
                                      action=EnumChoicesAction,
                                      default=ConstantsType.NEVER,
                                      help='Usage of constants (default: never)')
        
        _template = parser.add_argument('--template',
                                        type=TemplateType,
                                        default=TemplateType.NON_SHARED,
                                        action=EnumChoicesAction,
                                        help='Template logic (default: nonshared)')

        _lpp = parser.add_argument('--max-lpp', '--literals-per-product',
                                   type=int,
                                   help='The maximum number of literals per product')

        _ppo = parser.add_argument('--max-ppo', '--products-per-output',
                                   type=int,
                                   help='The maximum number of products per output')

        _pit = parser.add_argument('--max-pit', '--products-in-total',
                                   type=int,
                                   help='The maximum number of products in total')

        _nmod = parser.add_argument('--wanted-models',
                                    type=int,
                                    default=1,
                                    help='Wanted number of models to generate at each step (default: 1)')

        # > error stuff

        _et = parser.add_argument('--max-error', '-e',
                                  type=int,
                                  required=True,
                                  help='The maximum allowable error')

        _ep = parser.add_argument('--error-partitioning', '--epar',
                                  type=ErrorPartitioningType,
                                  action=EnumChoicesAction,
                                  default=ErrorPartitioningType.ASCENDING,
                                  help='The error partitioning algorithm to use (default: asc)')

        # > other stuff

        _enc = parser.add_argument('--encoding',
                                   type=EncodingType,
                                   action=EnumChoicesAction,
                                   default=EncodingType.Z3_BITVECTOR,
                                   help='The encoding to use in solving')

        _timeout = parser.add_argument('--timeout',
                                       type=float,
                                       default=10800,
                                       help='The maximum time each cell is given to run (in seconds) (default: 3h)')

        _parallel = parser.add_argument('--parallel',
                                        action='store_true',
                                        help='Run in parallel whenever possible')

        _plt = parser.add_argument('--plot',
                                   action='store_true',
                                   help='The system will be run as plotter (DEPRECATED?)')

        _clean = parser.add_argument('--clean',
                                     action='store_true',
                                     help='Reset the output folder before running')

        raw_args = parser.parse_args()

        # custom defaults
        if raw_args.current_benchmark is None:
            raw_args.current_benchmark = raw_args.exact_benchmark

        # define dependencies
        dependencies: Dict[Tuple[argparse.Action, Optional[Any]], List[argparse.Action]] = defaultdict(list)
        dependencies = {
            # (source_argument, value | None): [dependent_arguments],
            (_subxpat, True): [_ex_mode],
            (_template, TemplateType.NON_SHARED): [_lpp, _ppo],
            (_template, TemplateType.SHARED): [_pit],
        }

        # check dependencies
        for (source, value), dependents in dependencies.items():
            if value is None and getattr(raw_args, source.dest, None) is not None:
                for dep in dependents:
                    if getattr(raw_args, dep.dest, None) is None:
                        parser.error(f'missing argument: argument `{source.option_strings[0]}` requires argument `{dep.option_strings[0]}`')

            elif value is not None and getattr(raw_args, source.dest, None) == value:
                for dep in dependents:
                    if getattr(raw_args, dep.dest, None) is None:
                        parser.error(f'missing argument: argument `{source.option_strings[0]}` with value {value!r} requires argument `{dep.option_strings[0]}`')

        return cls(**vars(raw_args))

    def __repr__(self):
        """
        Procedurally generates the string representation of the object.  
        The string will contain the name of the class, followed by one line for each field (name/value pair).
        """
        fields = ''.join(f'   {k} = {v},\n' for k, v in vars(self).items())
        return f'{self.__class__.__name__}(\n{fields})'
