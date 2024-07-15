from enum import Enum
from Z3Log.config.config import *

# OpenSTA for power and delay analysis
OPENSTA = 'sta'

# Synthesis with Yosys
LIB_PATH = 'config/gscl45nm.lib'
ABC_SCRIPT_PATH = 'config/abc.script'

# TemplateSpecs constants
#   properties
NAME = 'name'
LITERALS_PER_PRODUCT = 'literals_per_product'
PRODUCTS_PER_OUTPUT = 'products_per_output'
BENCHMARK = 'benchmark_name'
NUM_OF_MODELS = 'num_of_models'
SUBXPAT = 'subxpat'
SUBXPAT_V2 = 'subxpat_v2'
TEMPLATE_SPEC_ET = 'et'
PARTITIONING_PERCENTAGE = 'partitioning_percentage'
ITERATIONS = 'iterations'
GRID = 'grid'
EXACT = 'exact'
IMAX = 'imax'
OMAX = 'omax'
SENSITIVITY = 'sensitivity'
TIMEOUT = 'timeout'
SUBGRAPHSIZE = 'subgraph_size'
MODE = 'mode'
MANUAL_NODES = 'manual_nodes'
POPULATION = 'population'
MIN_LABELING = 'min_labeling'
PARALLEL = 'parallel'
ENCODING = 'encoding'

FULL_ERROR_FUNCTION = 'full_error_function'
SUB_ERROR_FUNCTION = 'sub_error_function'
ET_PARTITIONING = 'et_partitioning'
PARTIAL_LABELING = 'partial_labeling'
NUM_SUBGRAPHS = 'num_subgraphs'

# shared
SHARED = 'shared'
PRODUCTS_IN_TOTAL = 'products_in_total'
SHARED_PARAM_PREFIX = 'p'
SHARED_PRODUCT_PREFIX = 'pr'
SHARED_OUTPUT_PREFIX = 'o'
SHARED_SELECT_PREFIX = 's'
SHARED_LITERAL_PREFIX = 'l'
SHARED_INPUT_LITERAL_PREFIX = 'i'


#   NetworkX
NOT = 'not'
AND = 'and'
OR = 'or'

#   Z3 related
#       keywords
BOOLSORT = 'BoolSort()'
INTSORT = 'IntSort()'
FUNCTION = 'Function'
Z3_AND = 'And'
Z3_OR = 'Or'
Z3_NOT = 'Not'
SUM = 'Sum'
INTVAL = 'IntVal'
SOLVER = 'Solver()'
ADD = 'add'
FORALL = 'ForAll'
IF = 'If'
IMPLIES = 'Implies'

#       variable names
F_EXACT = 'fe'
F_APPROXIMATE = 'fa'
PARAM_PREFIX = 'p_o'
SELECT_PREFIX = 's'
LITERAL_PREFIX = 'l'
TREE_PREFIX = 't'
INPUT_LITERAL_PREFIX = 'i'
NODE_LITERAL_PREFIX = 'nd'
EXACT_WIRES_PREFIX = 'e'
EXACT_OUTPUT_PREFIX = 'e'
APPROXIMATE_WIRE_PREFIX = 'a'
APPROXIMATE_OUTPUT_PREFIX = 'a'
OUT = 'out'
PRODUCT_PREFIX = 'p_o'

TO_Z3_GATE_DICT = {
    NOT: Z3_NOT,
    AND: Z3_AND,
    OR: Z3_OR
}

EXACT_CIRCUIT = 'exact_circuit'
APPROXIMATE_CIRCUIT = 'approximate_circuit'
FORALL_SOLVER = 'forall_solver'
DIFFERENCE = 'difference'
ET = 'ET'
VERIFICATION_SOLVER = 'verification_solver'
ERROR = 'error'

# random constants
GV = 'gv'
JSON = 'json'

LPP = 'lpp'
PPO = 'ppo'
PAP = 'pap'
ITER = 'iter'
PIT = 'pit'
DST = 'dst'


class NameParameters(Enum):
    LPP = 'lpp'
    PPO = 'ppo'
    PIT = 'pit'
    PAP = 'pap'
    ITER = 'iter'
    DST = 'dst'


# Graph related
LABEL = 'label'
SHAPE = 'shape'

SUBGRAPH = 'subgraph'
# GraphViz colors
RED = 'red'
BLUE = 'skyblue3'
GREEN = 'green'
GREY = 'grey'
WHITE = 'white'
AQUA = 'aqua'
GOLD = 'gold'
OLIVE = 'olive'
TEAL = 'teal'

DIGRAPH = 'digraph'
STRICT = 'strict'
COLOR = 'fillcolor'
FILLCOLOR = 'fillcolor'
NODE = 'node'
STYLE = 'style'
FILLED = 'filled'


# result json fields
class ResultFields(Enum):
    RESULT = 'result'
    TOTAL_TIME = 'total_time'
    MODEL = 'model'


RESULT = 'result'
TOTAL_TIME = 'total_time'
MODEL = 'model'

JSON_TRUE = 'true'
JSON_FALSE = 'false'


class SolverStatus(Enum):
    SAT = 'sat'
    UNSAT = 'unsat'
    UNKNOWN = 'unknown'


SAT = 'sat'
UNSAT = 'unsat'
UNKNOWN = 'unknown'
EMPTY = 'empty'


# Verilog
VER_NOT = '~'
VER_AND = '&'
VER_OR = '|'
VER_ASSIGN = 'assign'
VER_WIRE = 'wire'
VER_INPUT = 'input'
VER_OUTPUT = 'output'
VER_MODULE = 'module'
VER_ENDMODULE = 'endmodule'
VER_WIRE_PREFIX = 'w_'
VER_JSON_WIRE_PREFIX = 'j_'
VER_INPUT_PREFIX = 'in'


WEIGHT = 'weight'


# Other tools
MECALS = 'mecals'
MUSCAT = 'muscat'
XPAT = 'xpat'
BLASYS = 'blasys'
SHARED_SUBXPAT = 'shared_subxpat'
SHARED_XPAT = 'shared_xpat'
SUBXPAT_V2 = 'subxpat_v2'

# for plotting
BENCH_DICT = {'abs_diff_2': 'abs_diff_i4_o3', 'abs_diff_4': 'abs_diff_i8_o5', 'abs_diff_6': 'abs_diff_i12_o7',
              'adder_2': 'adder_i4_o3', 'adder_4': 'adder_i8_o5', 'adder_6': 'adder_i12_o7',
              'mul_2': 'mul_i4_o4', 'mul_4': 'mul_i8_o8', 'mul_6': 'mul_i12_o12',
              'madd_2': 'madd_i6_o4', 'madd_3': 'madd_i9_o6',
              'sad_2': 'sad_i10_o3'
              }

COLOR_DICT = ['blue', 'red', 'black', 'green',
              'purple', 'olive', 'orange', 'brown',
              'gray', 'pink', 'cyan']


SUBXPAT_COLOR_DICT = {'i2_o1': 'blue',
                      'i2_o2': 'purple',
                      'i3_o1': 'olive',
                      'i3_o2': 'orange',
                      'i3_o3': 'brown',
                      'i4_o1': 'gray',
                      'i4_o2': 'pink',
                      'i4_o3': 'cyan',
                      'subgraphsize5': 'blue',
                      'subgraphsize10': 'purple',
                      'subgraphsize15': 'olive',
                      'subgraphsize20': 'orange',
                      'subgraphsize25': 'brown',
                      'subgraphsize30': 'gray',
                      'subgraphsize35': 'pink',
                      'subgraphsize40': 'cyan',
                      'subgraphsize45': 'yellow',
                      'subgraphsize50': 'violet'
                      }

AREA = 'Area'
POWER = 'Power'
DELAY = 'Delay'
RUNTIME = 'Runtime'
