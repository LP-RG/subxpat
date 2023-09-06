# OpenSTA for power and delay analysis
OPENSTA = 'sta'

# Synthesis with Yosys
LIB_PATH='config/gscl45nm.lib'
ABC_SCRIPT_PATH='config/abc.script'

# TemplateSpecs constants
#   properties
NAME = 'name'
LITERALS_PER_PRODUCT = 'literals_per_product'
PRODUCTS_PER_OUTPUT = 'products_per_output'
BENCHMARK = 'benchmark_name'
NUM_OF_MODELS = 'num_of_models'
SUBXPAT = 'subxpat'
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
INTVAL= 'IntVal'
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


# json fields
RESULT = 'result'
TOTAL_TIME = 'total_time'
MODEL = 'model'

JSON_TRUE = 'true'
JSON_FALSE = 'false'

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

AREA = 'Area'
POWER = 'Power'
DELAY = 'Delay'
RUNTIME = 'Runtime'
