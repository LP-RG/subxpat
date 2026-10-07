from __future__ import annotations
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping, Union
import enum
import dataclasses as dc

import time
import re
import tempfile
import argparse
import functools as ft
import os.path

from sxpat.utils.filesystem import FS
from sxpat.utils.functions import int_to_strbase
from sxpat.utils.storage import AppendStorage, LiveStorage
from sxpat.utils.argument_parser import add_dataclass_options


__all__ = [
    'Specifications',
    # enums
    'ErrorPartitioningType', 'EncodingType',
    'TemplateType', 'ConstantsType',
]


class Dependency:
    SourceItem = Union[str, tuple[str, Any]]
    TargetItem = Union[str, tuple[str, list[Any]]]


class ErrorPartitioningType(enum.Enum):
    ASCENDING = 'asc'
    DESCENDING = 'desc'
    SMART_ASCENDING = 'smart_asc'
    SMART_DESCENDING = 'smart_desc'


class EncodingType(enum.Enum):
    Z3_FUNC_INTEGER = 'z3int'
    Z3_FUNC_BITVECTOR = 'z3bvec'
    Z3_DIRECT_INTEGER = 'z3dint'
    Z3_DIRECT_BITVECTOR = 'z3dbvec'
    QBF = 'qbf'


class TemplateType(enum.Enum):
    NON_SHARED = 'nonshared'
    SHARED = 'shared'


class DistanceType(enum.Enum):
    ABSOLUTE_DIFFERENCE_OF_INTEGERS = 'adoi'
    ABSOLUTE_DIFFERENCE_OF_WEIGHTED_SUM = 'adows'
    HAMMING_DISTANCE = 'hd'
    WEIGHTED_HAMMING_DISTANCE = 'whd'


class ConstantsType(enum.Enum):
    NEVER = 'never'
    ALWAYS = 'always'


class ConstantFalseType(enum.Enum):
    OUTPUT = 'output'
    PRODUCT = 'product'


class EnumChoicesAction(argparse.Action):
    """
    Custom argparse.Action that will use our custom Enum.

    :authors: Marco Biasion
    """

    def __init__(self, *args, type: type[enum.Enum], **kwargs) -> None:
        super().__init__(*args, **kwargs, choices=[e.value for e in type])
        self.enum = type

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 value: str, option_string: str | None = None) -> None:
        setattr(namespace, self.dest, self.enum(value))


@dc.dataclass(init=False, frozen=True)
class Paths:
    @dc.dataclass(frozen=True)
    class RunFiles:
        run_id: dc.InitVar[str]
        # main folders
        base_folder: str = 'output'
        verilog: str = dc.field(default='verilog', init=False)
        # main files
        run_details: str = dc.field(default='run_details.csv', init=False)
        run_stats: str = dc.field(default='run_stats.csv', init=False)
        # debug folders
        graphviz: str = dc.field(default='graphviz', init=False)
        solver_scripts: str = dc.field(default='scripts', init=False)
        # temporary files and folders
        temporary: str = dc.field(default='tmp', init=False)
        debug: dc.InitVar[bool] = False

        def __post_init__(self, run_id: str, debug: bool) -> None:
            # main folders
            object.__setattr__(self, 'base_folder', os.path.join(self.base_folder, run_id))
            object.__setattr__(self, 'verilog', os.path.join(self.base_folder, self.verilog))
            # main files
            object.__setattr__(self, 'run_details', os.path.join(self.base_folder, self.run_details))
            object.__setattr__(self, 'run_stats', os.path.join(self.base_folder, self.run_stats))

            # temporary folder
            tempdir = os.path.join(self.base_folder, self.temporary)
            if not debug:
                _tempdir = tempfile.gettempdir()
                if _tempdir != os.path.curdir and _tempdir != os.path.abspath(os.path.curdir):
                    tempdir = os.path.join(_tempdir, run_id)
            object.__setattr__(self, 'temporary', tempdir)

            # debug folders
            object.__setattr__(self, 'debug', debug)
            if debug:
                object.__setattr__(self, 'solver_scripts', os.path.join(self.base_folder, self.solver_scripts))
                object.__setattr__(self, 'graphviz', os.path.join(self.base_folder, self.graphviz))
            else:
                object.__setattr__(self, 'solver_scripts', os.path.join(self.temporary, self.solver_scripts))
                object.__setattr__(self, 'graphviz', os.path.join(self.temporary, self.graphviz))

        @property
        def folders(self) -> Iterable[str]:
            #
            yield from (
                self.base_folder,
                self.verilog,
            )
            #
            yield from (
                self.temporary,
                self.solver_scripts,
                self.graphviz,
            )

    @dc.dataclass(frozen=True)
    class Synthesis:
        cell_library: str = 'config/gscl45nm.lib'
        abc_script: str = dc.field(default='config/abc.script', init=False)

    @dc.dataclass(frozen=True)
    class Tools:
        cqesto: str = 'cqesto'

    run: RunFiles
    synthesis: Synthesis
    tools: Tools

    def __init__(self, output_base: str, run_id: str, cell_library: str, cqesto: str, keep_temporary: bool) -> None:
        object.__setattr__(self, 'run', self.RunFiles(run_id, output_base, keep_temporary))
        object.__setattr__(self, 'synthesis', self.Synthesis(cell_library))
        object.__setattr__(self, 'tools', self.Tools(cqesto))

    def __repr__(self):
        params = ', '.join(f'{name}={getattr(self, name)!r}' for name in vars(self).keys())
        return f'{self.__class__.__qualname__}({params})'


def writable_with_default[_T](default: _T) -> _T:
    return dc.field(init=False, default=default, metadata={'writable': True})


class CustomDefaultS[T]:
    def __init__(self, func: Callable[[Specifications], T]) -> None: self._func = func
    def __call__(self, spec: Specifications) -> T: return self._func(spec)


@dc.dataclass(kw_only=True)
class Specifications:
    """
    State of the framework. Contains the arguments (constants), and the mutable data.

    :authors: Marco Biasion, Morteza Rezaalipour
    """

    # to automatically generate the argument for a specific field, add the 'argument' key in the metadata.
    # some attributes are automatically extracted from the field:
    # - field type annotation : will be used for the type of the argument value
    # - default value         : will be use for the default value of the argument
    # other attributes can be added to customise the parsing, inside the dictionary at 'argument' (all are optional):
    # - 'positional: bool      : will change the construction to the argument to make it positional (default: False)
    # - 'args':      list[str] : the list of argument names, prevent the default generation of the argument name (default: None)
    # - 'aliases':   list[str] : extra argument names to use, in addition to the default argument name (default: None)
    # - 'help':      str       : the help message to show in the command line help (default: '')
    # - 'group':     str       : under which group to show the argument in the command line help (default: None)
    # - 'choices':   list[Any] : the possible values for the argument (default: None)
    # - 'action':    Action    : the specific argparse.Action to use for that argument (default: None)

    # to add dependencies between the fields, add the mapping 'dependencies':{} in the metadata.
    # the mapping 'requires':{} represents the mapping from values to the current field 
    #   to their required other fields, to be present or to have a specific value
    # the mapping 'required_by':{} is NOT IMPLEMENTED yet

    # to add a dynamic default value, you can use the following classes:
    # - CustomDefaultS: this requires a function that takes only a Specifications like object, and return the default value.

    # if a field is variable, meaning that its value can change during normal execution
    #   you should add the mapping 'writable':True in the metadata

    # benchmark
    exact_benchmark: str = dc.field(
        metadata={
            'argument': {
                'positional': True,
                'help': 'Circuit to approximate (in Verilog format)',
            },
        },
    )
    current_benchmark: str = dc.field(  # rw
        default=CustomDefaultS(lambda s: s.exact_benchmark),  # pyright: ignore[reportAssignmentType]
        metadata={
            'writable': True,
            'argument': {
                'aliases': ['--curr'],
                'help': 'Approximated circuit used to continue the execution (in Verilog format) (default: same as exact-benchmark)',
            },
        },
    )
    outputs: int = dc.field(init=False)

    # labeling
    min_labeling: bool = dc.field(
        default=True,
        metadata={
            'argument': {
                'args': ['--max-labeling'],
                'help': 'Nodes are weighted using their maximum error, instead of minimum error',
                'group': 'Labeling',
            }
        },
    )
    partial_labeling: bool = dc.field(
        default=True,
        metadata={
            'argument': {
                'help': 'Weights are assigned to all nodes, not only to the relevant ones',
                'group': 'Labeling',
            }
        },
    )

    # subgraph extraction
    extraction_mode: int = dc.field(
        default=55,
        metadata={
            'argument': {
                'aliases': ['--mode'],
                'choices': [0, 1, 2, 3, 4, 5, 55, 6, 100, 11, 12, 42],
                'help': 'Subgraph extraction algorithm to use (default: 55)',
                'group': 'Subgraph extraction',
            },
            'dependencies': {
                'requires': {
                    55: ['imax', 'omax'],
                }
            }
        },
    )
    #
    imax: int = dc.field(
        metadata={
            'argument': {
                'aliases': ['--input-max'],
                'help': 'Maximum allowed number of inputs to the subgraph',
                'group': 'Subgraph extraction',
            }
        },
    )
    omax: int = dc.field(
        metadata={
            'argument': {
                'aliases': ['--output-max'],
                'help': 'Maximum allowed number of outputs from the subgraph',
                'group': 'Subgraph extraction',
            }
        },
    )
    #
    max_sensitivity: int = dc.field(
        metadata={
            'argument': {
                'help': 'Maximum partitioning sensitivity',
                'group': 'Subgraph extraction',
            }
        },
    )
    sensitivity: int = dc.field(  # rw
        init=False,
        metadata={'writable': True},
    )
    #
    persistance: int = dc.field(
        metadata={
            'argument': {
                'help': 'max-persistance for subgraph extraction 0',
                'group': 'Subgraph extraction',
            }
        },
    )
    persistance_counter: int = dc.field(  # rw
        init=False,
        default=0,
        metadata={'writable': True},
    )
    #
    min_subgraph_size: int = dc.field(
        metadata={
            'argument': {
                'help': 'Minimum valid size for the subgraph',
                'group': 'Subgraph extraction',
            }
        },
    )
    num_subgraphs: int = dc.field(
        default=1,
        metadata={
            'argument': {
                'help': 'The number of attempts for subgraph extraction (default: 1)',
                'group': 'Subgraph extraction',
            }
        },
    )
    #
    slash_to_kill: bool = dc.field(
        default=False,
        metadata={
            'argument': {
                'help': 'Enable the slash pass for the first iteration',
                'group': 'Subgraph extraction',
            },
            'dependencies': {
                'requires': {
                    True: ['error_for_slash'],
                }
            }
        },
    )
    error_for_slash: int = dc.field(
        metadata={
            'argument': {
                'help': 'The error to use for the slash pass',
                'group': 'Subgraph extraction',
            }
        },
    )
    #
    out_node: int = dc.field(  # rw
        init=False,
        default=0,
        metadata={'writable': True},
    )

    # exploration (1)
    subxpat: bool = dc.field(
        default=False,
        metadata={
            'argument': {
                'help': 'Run SubXPAT iteratively, instead of standard XPAT',
                'group': 'Execution',
            },
            'dependencies': {
                'requires': {
                    True: ['extraction_mode'],
                }
            },
        },
    )
    template: TemplateType = dc.field(
        default=TemplateType.NON_SHARED,
        metadata={
            'argument': {
                'action': EnumChoicesAction,
                'help': 'Template logic (default: nonshared)',
                'group': 'Execution',
            },
            'dependencies': {
                'requires': {
                    TemplateType.NON_SHARED: ['max_lpp', 'max_ppo'],
                    TemplateType.SHARED: ['max_pit'],
                }
            }
        },
    )
    encoding: EncodingType = dc.field(
        default=EncodingType.Z3_FUNC_BITVECTOR,
        metadata={
            'argument': {
                'action': EnumChoicesAction,
                'help': 'The encoding to use in solving (default: z3bvec)',
                'group': 'Execution',
            }
        },
    )
    constants: ConstantsType = dc.field(
        default=ConstantsType.ALWAYS,
        metadata={
            'argument': {
                'action': EnumChoicesAction,
                'help': 'Usage of constants (default: always)',
                'group': 'Execution',
            }
        },
    )
    constant_false: ConstantFalseType = dc.field(
        default=ConstantFalseType.OUTPUT,
        metadata={
            'argument': {
                'action': EnumChoicesAction,
                'help': 'Representation of false constants from the subgraph (default: output)',
                'group': 'Execution',
            },
            'dependencies': {
                'requires': {
                    # template variants only implemented by some templates
                    ConstantFalseType.PRODUCT: [
                        ('template', [TemplateType.NON_SHARED]),
                    ],
                }
            }
        },
    )
    wanted_models: int = dc.field(
        default=1,
        metadata={
            'argument': {
                'help': 'Wanted number of models to generate at each step (default: 1)',
                'group': 'Execution',
            }
        },
    )
    iteration: int = dc.field(  # rw
        init=False,
        metadata={'writable': True},
    )
    sub_iteration: str = dc.field(  # rw
        init=False,
        metadata={'writable': True},
    )
    # exploration (2)
    max_lpp: int = dc.field(
        metadata={
            'argument': {
                'aliases': ['--max-literals-per-product'],
                'help': 'The maximum number of literals per product',
                'group': 'Execution',
            }
        },
    )
    lpp: int = dc.field(  # rw
        init=False,
        metadata={'writable': True},
    )
    max_ppo: int = dc.field(metadata={
        'argument': {
            'aliases': ['--max-products-per-output'],
            'help': 'The maximum number of products per output',
            'group': 'Execution',
        }
    })
    ppo: int = dc.field(  # rw
        init=False,
        metadata={'writable': True},
    )
    max_pit: int = dc.field(
        metadata={
            'argument': {
                'aliases': ['--products-in-total'],
                'help': 'The maximum number of products in total',
                'group': 'Execution',
            }
        },
    )
    pit: int = dc.field(  # rw
        init=False,
        metadata={'writable': True},
    )
    its: int = dc.field(  # rw
        init=False,
        metadata={'writable': True},
    )

    # error
    max_error: int = dc.field(
        metadata={
            'argument': {
                'aliases': ['-e'],
                'required': True,
                'help': 'The maximum allowable error',
                'group': 'Error',
            }
        },
    )
    et: int = dc.field(  # rw
        init=False,
        metadata={'writable': True},
    )
    error_partitioning: ErrorPartitioningType = dc.field(
        default=ErrorPartitioningType.ASCENDING,
        metadata={
            'argument': {
                'aliases': ['--epar'],
                'action': EnumChoicesAction,
                'help': 'The error partitioning algorithm to use (default: asc)',
                'group': 'Error',
            }
        },
    )

    # files and folders
    path_output: dc.InitVar[str] = dc.field(
        default=Paths.RunFiles.base_folder,
        metadata={
            'argument': {
                'args': ['--output'],
                'help': f'The base directory for the output (default: {Paths.RunFiles.base_folder})',
                'group': 'Files and folders',
            }
        },
    )
    path_cell_library: dc.InitVar[str] = dc.field(
        default=Paths.Synthesis.cell_library,
        metadata={
            'argument': {
                'args': ['--cell-library'],
                'help': f'The cell library file to use in the metrics estimation (default: {Paths.Synthesis.cell_library})',
                'group': 'Files and folders',
            }
        })
    path_cqesto: dc.InitVar[str] = dc.field(default=Paths.Tools.cqesto, metadata={
        'argument': {
            'args': ['--cqesto'],
            'help': f'The path of the executable of cqesto (default: {Paths.Tools.cqesto})',
            'group': 'Files and folders',
        }
    },
    )
    path: Paths = dc.field(init=False)  # writable once
    should_archive: bool = dc.field(
        default=False,
        metadata={
            'argument': {
                'args': ['--archive'],
                'help': 'If the generated files should be archived at the end of the execution',
                'group': 'Files and folders',
            }
        },
    )

    # other
    debug: bool = dc.field(
        default=False,
        metadata={
            'argument': {
                'help': 'If the system should be run in debug mode',
                'group': 'Miscellaneous',
            }
        },
    )
    timeout: float = dc.field(
        default=10800,
        metadata={
            'argument': {
                'help': 'The maximum time each cell is given to run (in seconds) (default: 3h)',
                'group': 'Miscellaneous',
            }
        },
    )
    parallel: bool = dc.field(
        default=False,
        metadata={
            'argument': {
                'help': 'Run in parallel whenever possible',
                'group': 'Miscellaneous',
            }
        },
    )
    timestamp: int = dc.field(
        init=False,
        default_factory=lambda: int(time.time()),
    )
    run_id: str = dc.field(init=False)

    # storage
    stats_storage: LiveStorage = dc.field(  # writable once
        init=False,
        metadata={'writable': True},
    )
    details_storage: AppendStorage = dc.field(  # writable once
        init=False,
        metadata={'writable': True},
    )

    def __post_init__(self, path_output: str, path_cell_library: str, path_cqesto: str):
        # > computed constants
        # output size
        benchmark_name = os.path.basename(self.exact_benchmark)
        match = re.search(r'_o(\d+)', benchmark_name)
        if match is None:
            raise ValueError(f'Unable to parse the number of outputs from benchmark name {benchmark_name!r}.')
        self.outputs = int(match.group(1))
        # run id
        _base = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.run_id = FS.get_unique_name(
            int_to_strbase(self.timestamp, _base)
            .rjust(8, _base[0])  # with padding, the naming order is safe for another ~6.5k years (as of 2026AD)
            + '_',
            id_size=4,
        )

        # construct path object
        self.path = Paths(
            path_output, self.run_id,
            path_cell_library,
            path_cqesto,
            self.debug
        )

    # > computed

    @property
    def max_its(self) -> int:
        return self.max_pit + 3

    @property
    def template_name(self) -> str:
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
            and self.extraction_mode != 42
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

    @classmethod
    def parse_args(cls):
        parser = argparse.ArgumentParser(
            description='Run the XPAT system',
            epilog='Developed by Prof. Pozzi research team',
            formatter_class=argparse.RawTextHelpFormatter,
            add_help=False,
        )
        parser.add_argument(
            '-?', '-h', '--help', action='help',
            help='Show this help message and exit',
        )

        add_dataclass_options(Specifications, parser)

        raw_args = parser.parse_args()

        # custom defaults
        for f in dc.fields(Specifications):
            if isinstance(f.default, CustomDefaultS):
                _cd = getattr(raw_args, f.name)
                setattr(raw_args, f.name, _cd(raw_args))

        # check dependencies
        fields_dict = {f.name: f for f in dc.fields(cls)}
        for field in fields_dict.values():
            requires = field.metadata.get('dependencies', {}).get('requires', None)
            if not requires: continue

            source_dest = field.name
            source_action = fields_dict[source_dest].metadata['argument']['_action']
            for (if_value, then_requires) in requires.items():
                source_has_value = if_value is not None

                # skip if source not present
                if (_v := getattr(raw_args, source_dest, None)) is None:
                    continue
                # skip if source wants a specific value which is not the current one
                if source_has_value and if_value != _v:
                    continue

                source_message = ''.join((
                    f'missing or wrong argument: argument `{source_action.option_strings[0]}`',
                    f' with value {arg_value_to_string(if_value)}' if source_has_value else '',
                    ' requires argument',
                ))

                # verify targets
                for required in then_requires:
                    required_has_values = isinstance(required, tuple)
                    if required_has_values:
                        target_dest = required[0]
                        target_values = required[1]
                    else:
                        target_dest = required
                        target_values = []

                    if (
                        # target not present
                        (_v := getattr(raw_args, target_dest, None)) is None
                        # target has wrong value
                        or required_has_values and _v not in target_values
                    ):
                        target_action = fields_dict[target_dest].metadata['argument']['_action']

                        # improved error message
                        if len(target_values) == 1:
                            if target_action.const == True: msg = 'to not be used'
                            elif target_action.const == False: msg = 'to be used'
                            else: msg = f'to have the following value: {arg_value_to_string(target_values[0])}'
                        elif len(target_values) > 1:
                            msg = f'to have one of the following values: {", ".join(map(arg_value_to_string, target_values))}'
                        else:
                            msg = ''

                        parser.error(f'{source_message} `{target_action.option_strings[0]}` {msg}')

        # construct specifications object
        return cls(**vars(raw_args))

    def __repr__(self):
        """
        Procedurally generates the string representation of the object.  
        The string will contain the name of the class, followed by one line for each field (name/value pair).
        """
        fields = ''.join(f'   {k} = {v!r},\n' for k, v in vars(self).items())
        return f'{self.__class__.__name__}(\n{fields})'

    @ft.cached_property
    def constant_fields(self) -> Mapping[str, Any]:
        """
        Returns a mapping containing all key/value pairs matching fields not marked as `writable`.
            - fields that are instances of dataclasses are recursively explored, each subfield being returned as 'key.subkey...'/value.
            - fields that are instances of enumerators are returned as 'key'/enum.value.
        """

        def extract(dc_obj, prefix: str) -> dict[str, Any]:
            constant_fields = dict()

            for field in dc.fields(dc_obj):
                # skip writable fields
                if field.metadata.get('writable', False): continue

                value = getattr(dc_obj, field.name)

                if dc.is_dataclass(value):
                    constant_fields.update(extract(value, prefix + field.name + '.'))
                elif isinstance(value, enum.Enum):
                    constant_fields[prefix + field.name] = value.value
                else:
                    constant_fields[prefix + field.name] = value

            return constant_fields

        return MappingProxyType(extract(self, ''))


def arg_value_to_string(value: Union[str, int, bool, enum.Enum, Any]) -> str:
    if isinstance(value, enum.Enum): value = value.value
    return repr(value)


class ___prototype:
    """
    prototype for a new (and more structured) (and easier) argument dependency system.

    :authors: Marco Biasion
    """

    # type DependencyChecker = Callable[[Specifications], Literal[-2, -1, 1]]

    # def make_dependency(field_name: str, field_value: Any = ...) -> DependencyChecker:
    #     def is_respected(specs: Specifications):
    #         if not any(f.name == field_name for f in dc.fields(Specifications)):
    #             raise AttributeError(f'Field `{field_name}` does not exist in `{Specifications}`.')

    #         if field_value is ...:
    #             return 1 if getattr(specs, field_name, None) is not None else -2
    #         else:
    #             return 1 if getattr(specs, field_name, None) == field_value else -1

    #     return is_respected

    # 'dependencies': {
    #     True: [make_dependency('extraction_mode')],
    # }

    # ERROR_MSGS = {
    #     -2: dedent('''
    #         wrong argument: argument `{arg}` with value `{arg_val}`
    #          requires argument `{dep}` to have one of the following values {dep_vals}.
    #     ''').strip().replace('\n', ''),
    #     -1: dedent('''
    #         missing argument: argument `{arg}` with value `{arg_val}`
    #          requires argument `{dep}`.
    #     ''').strip().replace('\n', ''),
    # }
    # def get_metavar(action: argparse.Action): return action.metavar or action.
    # for f in dc.fields(Specifications):
    #     _arg_metadata: dict[str, Any] | None = f.metadata.get('argument', None)
    #     if _arg_metadata is None: continue
    #     print(f.name, _arg_metadata)

    #     _deps: dict[Any, list[DependencyChecker]] | None = _arg_metadata.get('dependencies', None)
    #     if _deps is None: continue

    #     actual_value = getattr(specs, f.name)
    #     for (if_value, dep_checkers) in _deps.items():
    #         if actual_value != if_value: continue
    #         for _check in dep_checkers:
    #             errcode = _check(specs)
    #             # if errcode < 0:
    #             #     parser.error(ERROR_MSGS[errcode].format(arg=f.name))
