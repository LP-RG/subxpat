from typing import Dict, Tuple
from Z3Log.config.path import OUTPUT_PATH as _OUTPUT_PATH, INPUT_PATH


__all__ = ['INPUT_PATH', 'OUTPUT_PATH']


OUTPUT_PATH: Dict[str, Tuple[str, str]] = {
    **_OUTPUT_PATH,
    'json': ('output/json', 'json'),
    'html': ('output/html', 'html'),
    'figure': ('output/figure', 'pdf'),
    'area': ('experiments/area', 'txt'),
    'power': ('experiments/area', 'txt'),
    'delay': ('experiments/area', 'txt'),
    'runtime': ('experiments/runtime', 'txt')
}
