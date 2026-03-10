INPUT_PATH = {
    'ver': ('input/ver', 'v'),
    'gv': ('input/gv', 'gv'),
    'aig': ('input/aig', 'aig'),
    'dot': ('input/gv', 'dot'),
    'app_ver': ('input/ver', 'v'),
    'app_gv': ('input/gv', 'gv'),
    'report': ('output/report', 'csv')
}
OUTPUT_PATH = {
    'ver': ('output/ver', 'v'),
    'gv': ('output/gv', 'gv'),
    'aig': ('output/aig', 'aig'),
    'dot': ('output/gv', 'dot'),
    'z3': ('output/z3', 'py'),
    'report': ('output/report', 'csv'),
    'figure': ('output/figure', 'pdf')
}

TEST_PATH = {
    'tb': ('test/ver', 'v'),
    'iver': ('test/ver', 'iv'),
    'vvp': ('test/ver', 'txt'),
    'z3': ('test/z3', 'txt'),
}

LOG_PATH = {
    'iver': ('test/ver', 'log'),
    'z3': ('test/z3', 'log'),
    'yosys': 'txt',
    'lsoracle': 'txt'
}

