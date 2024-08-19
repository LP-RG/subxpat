from typing import Dict, Tuple
from Z3Log.config.path import *

OUTPUT_PATH: Dict[str, Tuple[str, str]] = {
    **OUTPUT_PATH,
    'json': ('output/json', 'json'),
    'html': ('output/html', 'html'),
    'figure': ('output/figure', 'pdf'),
    'area': ('experiments/area', 'txt'),
    'power': ('experiments/area', 'txt'),
    'delay': ('experiments/area', 'txt'),
    'runtime': ('experiments/runtime', 'txt')
}
