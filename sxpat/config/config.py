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