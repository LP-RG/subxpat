from shutil import move
from subprocess import call
from os.path import join as path_join

from .config.config import YOSYS as yosys_path


# discarded:
# from Z3Log.utils import setup_folder_structure
# from Z3Log.utils import clean_all
# from Z3Log.utils import check_graph_equality
# from Z3Log.utils import fix_direction

# replaced:
# from Z3Log.utils import get_pure_name
# from Z3Log.utils import convert_verilog_to_gv


def get_pure_name(file_path: str) -> str:
    if file_path is None: return None
    return (
        file_path
        .rsplit('/', maxsplit=1)[-1]
        .split('.')[0]
    )


def convert_verilog_to_gv(input_verilog_path: str, output_gv_path: str, temporary_path: str):
    # prepare
    tmp_dot_path = path_join(temporary_path, 'cvtgv_to_fd.dot')
    yosys_command = f"""
        read_verilog {input_verilog_path}
        opt
        clean
        show -prefix {tmp_dot_path[:-4]} -format dot
    """

    # run
    with open(path_join(temporary_path, 'yosys_convert_verilog_to_gv.log'), 'w') as f:
        # run yosys command (dump log to temporary file)
        retcode = call([yosys_path, '-p', yosys_command], stdout=f)
        assert retcode == 0

    # move .dot to .gv
    move(tmp_dot_path, output_gv_path)


def setup_folder_structure(*args, **kwargs): raise RuntimeError('Why are you using this? talk with Marco')
def clean_all(*args, **kwargs): raise RuntimeError('Why are you using this? talk with Marco')
def check_graph_equality(*args, **kwargs): raise RuntimeError('Why are you using this? talk with Marco')
def fix_direction(*args, **kwargs): raise RuntimeError('Why are you using this? talk with Marco')
