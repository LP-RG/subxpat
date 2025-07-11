from __future__ import annotations
from typing import Any, Dict, List, Tuple, Union
import enum
import dataclasses as dc

import re
import argparse
from pathlib import Path
import os.path


__all__ = [
    'Specifications',
    # enums
    'ErrorPartitioningType', 'EncodingType',
    'TemplateType', 'ConstantsType',
]


class Dependency:
    SrcItem = Union[argparse.Action, Tuple[argparse.Action, Any]]
    TrgtItem = Union[argparse.Action, Tuple[argparse.Action, List[Any]]]


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


class Paths:
    @dc.dataclass(frozen=True)
    class Output:
        base_folder: str = 'output'
        graphviz: str = dc.field(default='graphviz', init=False)
        verilog: str = dc.field(default='verilog', init=False)
        solver_scripts: str = dc.field(default='scripts', init=False)

        def __post_init__(self) -> None:
            object.__setattr__(self, 'graphviz', os.path.join(self.base_folder, self.graphviz))
            object.__setattr__(self, 'verilog', os.path.join(self.base_folder, self.verilog))
            object.__setattr__(self, 'solver_scripts', os.path.join(self.base_folder, self.solver_scripts))

    @dc.dataclass(frozen=True)
    class Synthesis:
        cell_library: str = 'config/gscl45nm.lib'
        abc_script: str = dc.field(default='config/abc.script', init=False)

    def __init__(self, output_base: str, cell_library: str) -> None:
        self.output = self.Output(output_base)
        self.synthesis = self.Synthesis(cell_library)

    def __repr__(self):
        params = ', '.join(f'{name}={getattr(self, name)!r}' for name in vars(self).keys())
        return f'{self.__class__.__qualname__}({params})'


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
    slash_to_kill: bool
    error_for_slash: int

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

    # config
    path: Paths

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
    def outputs(self) -> int:
        """Get the number of outputs of the circuit."""
        # TODO: Temporary implementation.
        return int(re.search('_o(\d+)', self.exact_benchmark)[1])

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

        # > graph labeling
        _lab_group = parser.add_argument_group('Labeling')

        _max_lab = _lab_group.add_argument('--max-labeling',
                                           action='store_false',
                                           dest='min_labeling',
                                           help='Nodes are weighted using their maximum error, instead of minimum error')

        _part_lab = _lab_group.add_argument('--no-partial-labeling',
                                            action='store_false',
                                            dest='partial_labeling',
                                            help='Weights are assigned to all nodes, not only to the relevant ones')

        # > subgraph extraction stuff
        _subex_group = parser.add_argument_group('Subgraph extraction')

        _ex_mode = _subex_group.add_argument('--extraction-mode', '--mode',
                                             type=int,
                                             choices=[1, 2, 3, 4, 5, 55, 6, 11, 12],
                                             default=55,
                                             help='Subgraph extraction algorithm to use (default: 55)')

        _imax = _subex_group.add_argument('--input-max', '--imax',
                                          type=int,
                                          dest='imax',
                                          help='Maximum allowed number of inputs to the subgraph')

        _omax = _subex_group.add_argument('--output-max', '--omax',
                                          type=int,
                                          dest='omax',
                                          help='Maximum allowed number of outputs from the subgraph')

        _msens = _subex_group.add_argument('--max-sensitivity',
                                           type=int,
                                           help='Maximum partitioning sensitivity')

        _msub_size = _subex_group.add_argument('--min-subgraph-size',
                                               type=int,
                                               help='Minimum valid size for the subgraph')

        _num_sub = _subex_group.add_argument('--num-subgraphs',
                                             type=int,
                                             default=1,
                                             help='The number of attempts for subgraph extraction (default: 1)')

        _slash = _subex_group.add_argument('--slash-to-kill',
                                           action='store_true',
                                           help='Enable the slash pass for the first iteration')

        _error_slash = _subex_group.add_argument('--error-for-slash',
                                                 type=int,
                                                 help='The error to use for the slash pass')

        # > execution stuff
        _explor_group = parser.add_argument_group('Execution')

        _subxpat = _explor_group.add_argument('--subxpat',
                                              action='store_true',
                                              help='Run SubXPAT iteratively, instead of standard XPAT')

        _consts = _explor_group.add_argument('--constants',
                                             type=ConstantsType,
                                             action=EnumChoicesAction,
                                             default=ConstantsType.ALWAYS,
                                             help='Usage of constants (default: always)')

        _template = _explor_group.add_argument('--template',
                                               type=TemplateType,
                                               default=TemplateType.NON_SHARED,
                                               action=EnumChoicesAction,
                                               help='Template logic (default: nonshared)')

        _lpp = _explor_group.add_argument('--max-lpp', '--max-literals-per-product',
                                          type=int,
                                          help='The maximum number of literals per product')

        _ppo = _explor_group.add_argument('--max-ppo', '--max-products-per-output',
                                          type=int,
                                          help='The maximum number of products per output')

        _pit = _explor_group.add_argument('--max-pit', '--products-in-total',
                                          type=int,
                                          help='The maximum number of products in total')

        _nmod = _explor_group.add_argument('--wanted-models',
                                           type=int,
                                           default=1,
                                           help='Wanted number of models to generate at each step (default: 1)')

        _enc = _explor_group.add_argument('--encoding',
                                          type=EncodingType,
                                          action=EnumChoicesAction,
                                          default=EncodingType.Z3_BITVECTOR,
                                          help='The encoding to use in solving (default: z3bvec)')

        # > error stuff
        _error_group = parser.add_argument_group('Error')

        _et = _error_group.add_argument('--max-error', '-e',
                                        type=int,
                                        required=True,
                                        help='The maximum allowable error')

        _ep = _error_group.add_argument('--error-partitioning', '--epar',
                                        type=ErrorPartitioningType,
                                        action=EnumChoicesAction,
                                        default=ErrorPartitioningType.ASCENDING,
                                        help='The error partitioning algorithm to use (default: asc)')

        # > config
        _cfg_group = parser.add_argument_group('Configuration')

        # NOTE: this is not yet documented in the README as it currently does nothing
        _out_fold = _cfg_group.add_argument('--output',
                                            type=str,
                                            default=Paths.Output.base_folder,
                                            help=f'(WIP) The base directory for the output (default: {Paths.Output.base_folder})')

        _cfg_lib = _cfg_group.add_argument('--cell-library',
                                           type=str,
                                           default=Paths.Synthesis.cell_library,
                                           help=f'The cell library file to use in the metrics estimation (default: {Paths.Synthesis.cell_library})')

        # > other stuff
        _misc_group = parser.add_argument_group('Miscellaneous')

        _timeout = _misc_group.add_argument('--timeout',
                                            type=float,
                                            default=10800,
                                            help='The maximum time each cell is given to run (in seconds) (default: 3h)')

        _parallel = _misc_group.add_argument('--parallel',
                                             action='store_true',
                                             help='Run in parallel whenever possible')

        _plt = _misc_group.add_argument('--plot',
                                        action='store_true',
                                        help='The system will be run as plotter (DEPRECATED?)')

        _clean = _misc_group.add_argument('--clean',
                                          action='store_true',
                                          help='Reset the output folder before running')

        raw_args = parser.parse_args()

        # custom defaults
        if raw_args.current_benchmark is None: raw_args.current_benchmark = raw_args.exact_benchmark

        # define dependencies
        # the structure for each dependency is:
        # - source: [target0, ..., targetN]
        # a source must be either:
        # - (argument_object, value) # here the dependency is checked only if the argument has the given value
        # - argument_object          # here the dependency is checked no matter the actual value
        # a target must be either:
        # - (argument_object, value) # here the dependency is accepted only if the argument has the given value
        # - argument_object          # here the dependency is accepted if the argument is present
        dependencies: Dict[Dependency.SrcItem, List[Dependency.TrgtItem]] = {
            (_subxpat, True): [_ex_mode],
            (_template, TemplateType.NON_SHARED): [_lpp, _ppo],
            (_template, TemplateType.SHARED): [_pit],
            (_ex_mode, 55): [_imax, _omax],
            (_slash, True): [_error_slash],
        }

        # check dependencies
        for (source, targets) in dependencies.items():
            src_has_value = isinstance(source, tuple)
            src_action = source[0] if src_has_value else source
            if src_has_value: src_value = source[1]

            # skip if source not present
            if not hasattr(raw_args, src_action.dest): continue
            # skip if source wants a specific value which is not the current one
            if src_has_value and src_value != getattr(raw_args, src_action.dest): continue

            src_message = ''.join((
                f'missing or wrong argument: argument `{src_action.option_strings[0]}`',
                f' with value {arg_value_to_string(src_value)}' if src_has_value else '',
                ' requires argument',
            ))

            # verify targets
            for target in targets:
                trgt_has_values = isinstance(target, tuple)
                trgt_action = target[0] if trgt_has_values else target
                if trgt_has_values: trgt_values = target[1]

                # target not present
                if not hasattr(raw_args, trgt_action.dest) or getattr(raw_args, trgt_action.dest) is None:
                    parser.error(f'{src_message} `{trgt_action.option_strings[0]}`')

                # target has wrong value
                if trgt_has_values and getattr(raw_args, trgt_action.dest) not in trgt_values:
                    # improved messages error messages
                    if len(trgt_values) == 1:
                        if trgt_action.const == True: msg = 'to not be used'
                        elif trgt_action.const == False: msg = 'to be used'
                        else: msg = f'to have the following value: {arg_value_to_string(trgt_values[0])}'
                    else:
                        msg = f'to have one of the following values: {", ".join(map(arg_value_to_string, trgt_values))}'

                    parser.error(f'{src_message} `{trgt_action.option_strings[0]}` {msg}')

        # construct instance
        raw_args.path = Paths(getdelattr(raw_args, _out_fold.dest),
                              getdelattr(raw_args, _cfg_lib.dest))

        return cls(**vars(raw_args))

    def __repr__(self):
        """
            Procedurally generates the string representation of the object.  
            The string will contain the name of the class, followed by one line for each field (name/value pair).
        """
        fields = ''.join(f'   {k} = {v},\n' for k, v in vars(self).items())
        return f'{self.__class__.__name__}(\n{fields})'


def arg_value_to_string(value: Union[str, int, bool, enum.Enum, Any]) -> str:
    if isinstance(value, enum.Enum): value = value.value
    return repr(value)


def getdelattr(o: object, name: str):
    val = getattr(o, name)
    delattr(o, name)
    return val
