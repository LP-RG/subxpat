# tools
YOSYS = 'yosys'
SLANG = 'slang'
LSORACLE = 'lsoracle'
IVERILOG = 'iverilog'
VVP = 'vvp'
DOT = 'dot'

# regex constants
POSSIBLE_GATES=f'and|AND|or|OR|not|NOT'
CONST_1 = f"1'1"
CONST_0 = f"1'0"

INPUT_SHAPE = 'circle'
OUTPUT_SHAPE = 'doublecircle'
GATE_SHAPE = 'invhouse'
CONSTANT_SHAPE = 'square'

# for z3
Z3_GATES_DICTIONARY = {
    'and':'And',
    'AND':'And',
    'or':'Or',
    'OR':'Or',
    'not':'Not',
    'NOT':'Not',
    'T': 'True',
    'True': 'True',
    'true': 'True',
    'TRUE': 'True',
    'F': 'False',
    'False': 'False',
    'false': 'False',
    'FALSE': 'False'
}
REDUNDANT_FIELDS=[
    'height', 'width', 'pos',
    'color', 'fontcolor',
    'rects',
    'contraction', 'contraction',
    'style'
]

# random constants

Z3BOOL = 'Bool'
Z3XOR = 'Xor'
Z3INT = 'Int'

MITER = 'miter'
EXACT = 'exact'
APPROXIMATE = 'approx'
XOR = 'xor'
INT = 'int'

PYTHON3 = 'python3'
Z3 = 'z3py'
SHAPE = 'shape'
LABEL = 'label'
PRUNED = 'pruned'
TAB = '\t'


TMP = 'tmp'
LOG = 'log'

# strategies
MONOTONIC = 'monotonic'
BISECTION = 'bisection'
KIND_BISECTION = 'kind'
MC = 'mc'
DEFAULT_STRATEGY = MONOTONIC

# optimization
OPTIMIZE = 'optimize'
MAXIMIZE = 'maximize'




# Experiments
QOR = 'qor'
RANDOM = 'random'
SINGLE = 'labeling'

# Metrics
WAE = 'wae'
WRE = 'wre'
WHD = 'whd'

# CSV FILE
EXPERIMENT = 'Experiment'
WCE = 'WCE'
TOTAL_RUNTIME = 'Total Runtime'
SAT_RUNTIME = 'SAT Runtime'
UNSAT_RUNTIME = 'UNSAT Runtime'
N_SATS = 'Number of SAT calls'
N_UNSATS = 'Number of UNSAT calls'
JUMPS = 'Jumps'
TEST = 'test'


# PLOTTING
SCATTER = 'scatter_plot'
AVERAGE = 'average_plot'

SMALL_SIZE = 10
MEDIUM_SIZE = 12
BIGGER_SIZE = 15



