# discarded:
# from Z3Log.utils import setup_folder_structure
# from Z3Log.utils import clean_all
# from Z3Log.utils import check_graph_equality
# from Z3Log.utils import fix_direction
# from Z3Log.utils import convert_verilog_to_gv

# replaced:
# from Z3Log.utils import get_pure_name

__all__ = ['get_pure_name']


def get_pure_name(file_path: str) -> str:
    if file_path is None: return None
    return (
        file_path
        .rsplit('/', maxsplit=1)[-1]
        .split('.')[0]
    )


def setup_folder_structure(*args, **kwargs): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
def clean_all(*args, **kwargs): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
def check_graph_equality(*args, **kwargs): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
def fix_direction(*args, **kwargs): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
def convert_verilog_to_gv(*args, **kwargs): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
