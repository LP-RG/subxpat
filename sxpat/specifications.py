from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, NamedTuple
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
    EXPONENTIAL = 'exp'

class TerminationMode(enum.Enum):
    NONE = 'none'
    TRIVIAL = 'trivial'
    PARETO = 'pareto'
    HYBRID = 'hybrid'
    PARETO_ANNEALED = 'pareto_annealed'
    SENTINEL = 'sentinel'
    PREDICTOR = 'predictor'

class EncodingType(enum.Enum):
    Z3_FUNC_INTEGER = 'z3int'
    Z3_FUNC_BITVECTOR = 'z3bvec'
    Z3_DIRECT_INTEGER = 'z3dint'
    Z3_DIRECT_BITVECTOR = 'z3dbvec'
    QBF = 'qbf'

class TemplateType(enum.Enum):
    NON_SHARED = 'nonshared'
    SHARED = 'shared'


class ConstantsType(enum.Enum):
    NEVER = 'never'
    ALWAYS = 'always'

class MetricType(enum.Enum):
    ABSOLUTE = 'wae'
    RELATIVE = 'wre'

class CnnErrorConstraintTypes(enum.Enum):
    EXPLICIT = 'explicit'
    NINE = 'nine'
    NINE_PRIME = 'nine_prime'
    ZONE_AET = 'zone_aet'

class EnumChoicesAction(argparse.Action):
    def __init__(self, *args, type: enum.Enum, **kwargs) -> None:
        super().__init__(*args, **kwargs, choices=[e.value for e in type])
        self.enum = type

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 value: str, option_string: str = None) -> None:
        setattr(namespace, self.dest, self.enum(value))


class Paths:
    _Output = NamedTuple('Output', [
        ('graphviz', str),
        ('verilog', str),
        ('solver_scripts', str),
    ])
    _output_graphviz_postdir = 'graphviz'
    _output_verilog_postdir = 'verilog'
    _output_solver_scripts_postdir = 'scripts'

    _Config = NamedTuple('Config', [
        ('liberty', str),
        ('abc_script', str),
    ])
    _config_default_base = 'config'
    _config_liberty_default = 'gscl45nm.lib'
    _config_abc_script_default = 'abc.script'

    def __init__(self, output_base: str) -> None:
        output_base = output_base.rstrip('/')
        self.output = self._Output(
            f'{output_base}/{self._output_graphviz_postdir}',
            f'{output_base}/{self._output_verilog_postdir}',
            f'{output_base}/{self._output_solver_scripts_postdir}',
        )
        self.config = self._Config(
            f'{self._config_default_base}/{self._config_liberty_default}',
            f'{self._config_default_base}/{self._config_abc_script_default}',
        )


@dc.dataclass
class Specifications:
    # files
    exact_benchmark: str
    current_benchmark: str  # rw
    # metric
    metric: MetricType
    
    #zone constraint
    zone_constraint: bool

    # labeling
    min_labeling: bool
    partial_labeling: bool

    # subgraph extraction
    extraction_mode: int
    imax: int
    omax: int
    min_subgraph_size: int
    num_subgraphs: int
    remove_most_significant_output: bool
    max_sensitivity: int
    sensitivity: int = dc.field(init=False, default=None)  # rw
    #Extraction_mode_0
    persistence_counter: int = dc.field(init=False, default=0)  # rw
    out_node: int = dc.field(init=False, default=0)  # rw\
    #Zone AE
    baseet: int
    beta: int
    alpha: int
    c_constant: int
    threshold_array_idx: int

    #relative error constraint
    cnn_constraint: CnnErrorConstraintTypes

    #TODO
    constraint_cutoff: int
    termination_mode: TerminationMode
    termination_zone_rank_from_max: int
    adaptive_termination_zone_rank: bool
    adaptive_termination_zone_rank_step_interval: int
    best_seen_guard_pct: float
    pareto_forgiveness: float
    pareto_forgiveness_decay: float
    pareto_min_forgiveness: float
    pareto_aggressive_after_stagnation: int
    pareto_area_weight: float
    pareto_power_weight: float
    pareto_delay_weight: float
    pareto_near_frontier_penalty: float
    pareto_dominated_penalty: float
    pareto_regret_scale: float
    pareto_temperature_init: float
    pareto_temperature_decay: float
    pareto_runtime_pressure_scale: float
    pareto_rng_seed: int
    sentinel_best_seen_patience: int
    sentinel_structural_stall_streak: int
    sentinel_same_subgraph_streak: int
    sentinel_negative_cell_ratio: float
    sentinel_marginal_gain_pct: float
    sentinel_min_runtime_fraction: float
    sentinel_min_timeout_count: int
    sentinel_best_seen_iteration_patience: int
    sentinel_min_beta: int
    predictor_model_path: str
    predictor_probability_threshold: float
    predictor_min_iteration: int

    # exploration (1)
    subxpat: bool
    template: TemplateType
    encoding: EncodingType
    constants: ConstantsType
    wanted_models: int
    iteration: int = dc.field(init=False, default=None)  # rw
    persistance: int 
    partition_divider: int
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
    skip_verification: bool
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
            and self.extraction_mode >= 2 and self.extraction_mode!=123
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

        _metric = parser.add_argument('--metric',
                                       type=MetricType,
                                       action=EnumChoicesAction,
                                       default=MetricType.ABSOLUTE,
                                       help='Metric used in subXPat execution, either absolute or relative error')

        _zone_constraint = parser.add_argument('--zone-constraint',
                                       type=int,
                                       default=None,
                                       help='')#TODO HELP

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
                                       choices=[0,1, 2, 3, 4, 5, 55, 11, 12],
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
        
        _remove = parser.add_argument('--remove-most-significant-output', '--remove-mso',
                                           action='store_true',
                                           help='before doing anything remove the most significant output of the circuit')

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

        _persistance = parser.add_argument('--persistance',
                                    type=int,
                                    default=1,
                                    help='The number of attempts made with partial ET (default: 2)')
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

        _parition_divider = parser.add_argument('--partition-divider', '--pardiv', 
                                                type=int, 
                                                default=8,
                                                help="The number that is used to divied the et to create the step when creating the linear partition (default: 8)")
        # > zone error stuff

        _baseet = parser.add_argument('--baseet',
                                    type=int,
                                    required=False,
                                    default= 100)
                                    #help='The maximum allowable error')

        _beta = parser.add_argument('--beta',
                                    type=int,
                                    required=False,
                                    help='The beta parameter used in the zone constraint')
        _alpha = parser.add_argument('--alpha',
                                    type=int,
                                    required=False,
                                    help='The alpha parameter used in the zone constraint')

        _c_constant = parser.add_argument('--c-constant',
                                    type=int,
                                    required=False,
                                    help='The C constant used in the zone constraint')
        
        _threshold_array_idx = parser.add_argument('--threshold-array-idx',
                                    type=int,
                                    required=False,
                                    help='The index of the threshold array (inside input/ver/error_threshold_arrays.json) that is going to be used in the explicit constraint definition (default: 0)')

        _cnn_constraint = parser.add_argument('--cnn-constraint',
                                    type=CnnErrorConstraintTypes,
                                    action=EnumChoicesAction,
                                    default=None, 
                                    help='Constraint definition to use when metric is relative (needed when --metric is wre)')

        _constraint_cutoff = parser.add_argument('--constraint-cutoff',
                                    type=int,
                                    required=False)
                                    #help='...')

        _termination_mode = parser.add_argument('--termination-mode',
                                    type=TerminationMode,
                                    action=EnumChoicesAction,
                                    default=TerminationMode.TRIVIAL,
                                    help='Termination behavior for extraction-mode 0: none, trivial, pareto, pareto_annealed, sentinel, or hybrid (default: trivial)')
        _termination_zone_rank_from_max = parser.add_argument(
                                    '--termination-zone-rank-from-max',
                                    type=int,
                                    default=0,
                                    help='For ZONE_AET trivial termination: 0 uses the largest unique zone threshold, 1 the next smaller level, and so on (default: 0)')
        _adaptive_termination_zone_rank = parser.add_argument(
                                    '--adaptive-termination-zone-rank',
                                    action='store_true',
                                    help='For ZONE_AET trivial termination: gradually increase the threshold-rank aggressiveness after accepted iterations stop improving the run-best design')
        _adaptive_termination_zone_rank_step_interval = parser.add_argument(
                                    '--adaptive-termination-zone-rank-step-interval',
                                    type=int,
                                    default=1,
                                    help='How many accepted non-improving iterations are needed before adaptive ranked termination moves one threshold level lower (default: 1)')
        _best_seen_guard_pct = parser.add_argument(
                                    '--best-seen-guard-pct',
                                    type=float,
                                    default=0.0,
                                    help='Block trivial termination when the current accepted design is worse than the run-best area by more than this percentage (default: 0.0, disabled)')
        _pareto_forgiveness = parser.add_argument(
                                    '--pareto-forgiveness',
                                    type=float,
                                    default=0.03,
                                    help='Base forgiveness band for pareto_annealed regret; points within this weighted relative regret are treated as near-frontier before stagnation decay is applied (default: 0.03)')
        _pareto_forgiveness_decay = parser.add_argument(
                                    '--pareto-forgiveness-decay',
                                    type=float,
                                    default=0.8,
                                    help='Per-stagnation decay factor applied to pareto_annealed forgiveness after accepted iterations stop improving the run-best design (default: 0.8)')
        _pareto_min_forgiveness = parser.add_argument(
                                    '--pareto-min-forgiveness',
                                    type=float,
                                    default=0.005,
                                    help='Minimum forgiveness floor for pareto_annealed after decay is applied (default: 0.005)')
        _pareto_aggressive_after_stagnation = parser.add_argument(
                                    '--pareto-aggressive-after-stagnation',
                                    type=int,
                                    default=2,
                                    help='Delay aggressive pareto_annealed decay/pressure until this many accepted non-improving iterations have accumulated (default: 2)')
        _pareto_area_weight = parser.add_argument(
                                    '--pareto-area-weight',
                                    type=float,
                                    default=0.85,
                                    help='Area weight in the pareto_annealed regret score (default: 0.85)')
        _pareto_power_weight = parser.add_argument(
                                    '--pareto-power-weight',
                                    type=float,
                                    default=0.05,
                                    help='Power weight in the pareto_annealed regret score (default: 0.05)')
        _pareto_delay_weight = parser.add_argument(
                                    '--pareto-delay-weight',
                                    type=float,
                                    default=0.10,
                                    help='Delay weight in the pareto_annealed regret score (default: 0.10)')
        _pareto_near_frontier_penalty = parser.add_argument(
                                    '--pareto-near-frontier-penalty',
                                    type=float,
                                    default=0.35,
                                    help='Stagnation-score increment for a near-frontier accepted point in pareto_annealed (default: 0.35)')
        _pareto_dominated_penalty = parser.add_argument(
                                    '--pareto-dominated-penalty',
                                    type=float,
                                    default=1.5,
                                    help='Base stagnation-score increment for a clearly dominated accepted point in pareto_annealed (default: 1.5)')
        _pareto_regret_scale = parser.add_argument(
                                    '--pareto-regret-scale',
                                    type=float,
                                    default=4.0,
                                    help='Extra stagnation-score multiplier applied to regret beyond the forgiveness band in pareto_annealed (default: 4.0)')
        _pareto_temperature_init = parser.add_argument(
                                    '--pareto-temperature-init',
                                    type=float,
                                    default=0.8,
                                    help='Initial annealing temperature for pareto_annealed stopping (default: 0.8)')
        _pareto_temperature_decay = parser.add_argument(
                                    '--pareto-temperature-decay',
                                    type=float,
                                    default=0.8,
                                    help='Per-iteration temperature decay for pareto_annealed in (0, 1] (default: 0.8)')
        _pareto_runtime_pressure_scale = parser.add_argument(
                                    '--pareto-runtime-pressure-scale',
                                    type=float,
                                    default=0.5,
                                    help='Extra stop-pressure multiplier for pareto_annealed based on elapsed runtime fraction and best-seen stagnation (default: 0.5)')
        _pareto_rng_seed = parser.add_argument(
                                    '--pareto-rng-seed',
                                    type=int,
                                    default=0,
                                    help='Deterministic RNG seed for pareto_annealed stop decisions (default: 0)')
        _sentinel_best_seen_patience = parser.add_argument(
                                    '--sentinel-best-seen-patience',
                                    type=int,
                                    default=2,
                                    help='Minimum non-improving accepted iterations before sentinel termination may fire (default: 2)')
        _sentinel_structural_stall_streak = parser.add_argument(
                                    '--sentinel-structural-stall-streak',
                                    type=int,
                                    default=3,
                                    help='How many structurally stalled iterations in a row trigger sentinel termination checks (default: 3)')
        _sentinel_same_subgraph_streak = parser.add_argument(
                                    '--sentinel-same-subgraph-streak',
                                    type=int,
                                    default=3,
                                    help='How many repeated-subgraph iterations in a row trigger sentinel termination checks (default: 3)')
        _sentinel_negative_cell_ratio = parser.add_argument(
                                    '--sentinel-negative-cell-ratio',
                                    type=float,
                                    default=0.85,
                                    help='Minimum fraction of negative grid outcomes (UNSAT/UNKNOWN/DOMINATED) to classify an iteration as structurally stalled for sentinel termination (default: 0.85)')
        _sentinel_marginal_gain_pct = parser.add_argument(
                                    '--sentinel-marginal-gain-pct',
                                    type=float,
                                    default=1.0,
                                    help='Minimum best-seen area improvement percent considered meaningful by sentinel termination (default: 1.0)')
        _sentinel_min_runtime_fraction = parser.add_argument(
                                    '--sentinel-min-runtime-fraction',
                                    type=float,
                                    default=0.25,
                                    help='Minimum elapsed runtime fraction (runtime/timeout) before negative-cell stall alone may trigger sentinel termination (default: 0.25)')
        _sentinel_min_timeout_count = parser.add_argument(
                                    '--sentinel-min-timeout-count',
                                    type=int,
                                    default=1,
                                    help='Minimum timeout/unknown-heavy cell count required for sentinel long-tail stopping, unless same-subgraph repetition already triggered it (default: 1)')
        _sentinel_best_seen_iteration_patience = parser.add_argument(
                                    '--sentinel-best-seen-iteration-patience',
                                    type=int,
                                    default=2,
                                    help='Minimum number of iterations since the run-best design was last improved before sentinel may stop early (default: 2)')
        _sentinel_min_beta = parser.add_argument(
                                    '--sentinel-min-beta',
                                    type=int,
                                    default=1,
                                    help='Minimum beta value for aggressive sentinel early stopping (default: 1)')
        _predictor_model_path = parser.add_argument(
                                    '--predictor-model-path',
                                    type=str,
                                    default='',
                                    help='Path to an offline learned predictor JSON model used by termination mode predictor')
        _predictor_probability_threshold = parser.add_argument(
                                    '--predictor-probability-threshold',
                                    type=float,
                                    default=0.80,
                                    help='Stop when offline predictor probability is at least this threshold (default: 0.80)')
        _predictor_min_iteration = parser.add_argument(
                                    '--predictor-min-iteration',
                                    type=int,
                                    default=3,
                                    help='Do not allow predictor-based stopping before this outer iteration (default: 3)')

        # > other stuff

        _enc = parser.add_argument('--encoding',
                                   type=EncodingType,
                                   action=EnumChoicesAction,
                                   default=EncodingType.Z3_FUNC_BITVECTOR,
                                   help='The encoding to use in solving')

        _timeout = parser.add_argument('--timeout',
                                       type=float,
                                       default=10800,
                                       help='The maximum time each cell is given to run (in seconds) (default: 3h)')

        _parallel = parser.add_argument('--parallel',
                                        action='store_true',
                                        help='Run in parallel whenever possible')

        _skip_verification = parser.add_argument('--skip-verification',
                                                 action='store_true',
                                                 help='Skip expensive post-solve error verification')

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

        #if the user specified a cnn constraint and did not specify the metric, set the metric to relative
        if raw_args.cnn_constraint is not None:
            raw_args.metric = MetricType.RELATIVE

        if raw_args.termination_zone_rank_from_max < 0:
            parser.error('--termination-zone-rank-from-max must be a non-negative integer')
        if raw_args.adaptive_termination_zone_rank_step_interval <= 0:
            parser.error('--adaptive-termination-zone-rank-step-interval must be a positive integer')
        if raw_args.best_seen_guard_pct < 0:
            parser.error('--best-seen-guard-pct must be a non-negative number')
        if raw_args.pareto_forgiveness < 0:
            parser.error('--pareto-forgiveness must be a non-negative number')
        if raw_args.pareto_forgiveness_decay <= 0 or raw_args.pareto_forgiveness_decay > 1:
            parser.error('--pareto-forgiveness-decay must be in the interval (0, 1]')
        if raw_args.pareto_min_forgiveness < 0:
            parser.error('--pareto-min-forgiveness must be a non-negative number')
        if raw_args.pareto_min_forgiveness > raw_args.pareto_forgiveness:
            parser.error('--pareto-min-forgiveness cannot exceed --pareto-forgiveness')
        if raw_args.pareto_aggressive_after_stagnation < 0:
            parser.error('--pareto-aggressive-after-stagnation must be a non-negative integer')
        if raw_args.pareto_area_weight < 0 or raw_args.pareto_power_weight < 0 or raw_args.pareto_delay_weight < 0:
            parser.error('--pareto-*-weight values must be non-negative')
        if (raw_args.pareto_area_weight + raw_args.pareto_power_weight + raw_args.pareto_delay_weight) <= 0:
            parser.error('At least one pareto weight must be strictly positive')
        if raw_args.pareto_near_frontier_penalty < 0:
            parser.error('--pareto-near-frontier-penalty must be a non-negative number')
        if raw_args.pareto_dominated_penalty <= 0:
            parser.error('--pareto-dominated-penalty must be a positive number')
        if raw_args.pareto_regret_scale < 0:
            parser.error('--pareto-regret-scale must be a non-negative number')
        if raw_args.pareto_temperature_init <= 0:
            parser.error('--pareto-temperature-init must be a positive number')
        if raw_args.pareto_temperature_decay <= 0 or raw_args.pareto_temperature_decay > 1:
            parser.error('--pareto-temperature-decay must be in the interval (0, 1]')
        if raw_args.pareto_runtime_pressure_scale < 0:
            parser.error('--pareto-runtime-pressure-scale must be a non-negative number')
        if raw_args.pareto_rng_seed < 0:
            parser.error('--pareto-rng-seed must be a non-negative integer')
        if raw_args.sentinel_best_seen_patience < 0:
            parser.error('--sentinel-best-seen-patience must be a non-negative integer')
        if raw_args.sentinel_structural_stall_streak <= 0:
            parser.error('--sentinel-structural-stall-streak must be a positive integer')
        if raw_args.sentinel_same_subgraph_streak <= 0:
            parser.error('--sentinel-same-subgraph-streak must be a positive integer')
        if raw_args.sentinel_negative_cell_ratio < 0 or raw_args.sentinel_negative_cell_ratio > 1:
            parser.error('--sentinel-negative-cell-ratio must be in the interval [0, 1]')
        if raw_args.sentinel_marginal_gain_pct < 0:
            parser.error('--sentinel-marginal-gain-pct must be a non-negative number')
        if raw_args.sentinel_min_runtime_fraction < 0 or raw_args.sentinel_min_runtime_fraction > 1:
            parser.error('--sentinel-min-runtime-fraction must be in the interval [0, 1]')
        if raw_args.sentinel_min_timeout_count < 0:
            parser.error('--sentinel-min-timeout-count must be a non-negative integer')
        if raw_args.sentinel_best_seen_iteration_patience < 0:
            parser.error('--sentinel-best-seen-iteration-patience must be a non-negative integer')
        if raw_args.sentinel_min_beta < 1:
            parser.error('--sentinel-min-beta must be a positive integer')
        if raw_args.predictor_probability_threshold < 0 or raw_args.predictor_probability_threshold > 1:
            parser.error('--predictor-probability-threshold must be in the interval [0, 1]')
        if raw_args.predictor_min_iteration < 1:
            parser.error('--predictor-min-iteration must be a positive integer')
        if raw_args.termination_mode is TerminationMode.PREDICTOR and not raw_args.predictor_model_path:
            parser.error('--predictor-model-path is required when --termination-mode predictor')


        # define dependencies
        dependencies: Dict[Tuple[argparse.Action, Optional[Any]], List[argparse.Action]] = defaultdict(list)
        dependencies = {
            # (source_argument, value | None): [dependent_arguments],
            (_subxpat, True): [_ex_mode],
            (_template, TemplateType.NON_SHARED): [_lpp, _ppo],
            (_template, TemplateType.SHARED): [_pit],
            (_ep, ErrorPartitioningType.ASCENDING): [_parition_divider],
            (_cnn_constraint, CnnErrorConstraintTypes.NINE): [_beta, _alpha, _baseet],
            (_cnn_constraint, CnnErrorConstraintTypes.NINE_PRIME): [_beta, _alpha, _c_constant, _baseet],
            (_cnn_constraint, CnnErrorConstraintTypes.EXPLICIT): [_beta, _threshold_array_idx],
            (_cnn_constraint, CnnErrorConstraintTypes.ZONE_AET): [_beta, _alpha, _baseet],
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
