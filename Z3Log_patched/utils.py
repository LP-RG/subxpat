# discarded:
# from Z3Log.utils import setup_folder_structure
# from Z3Log.utils import clean_all
# from Z3Log.utils import check_graph_equality

# replaced:
# from Z3Log.utils import get_pure_name
# from Z3Log.utils import fix_direction
# from Z3Log.utils import convert_verilog_to_gv


def get_pure_name(file_path: str) -> str:
    if file_path is None: return None
    return (
        file_path
        .rsplit('/', maxsplit=1)[-1]
        .split('.')[0]
    )


def fix_direction(input_gv_path: str, output_gv_path: str):
    # imports
    from .config.config import DOT as dot_path
    from subprocess import call

    # run
    call([dot_path, input_gv_path, '-Grankdir=TB', '-o', output_gv_path])


def convert_verilog_to_gv(input_verilog_path: str, output_gv_path: str, temporary_path: str):
    # imports
    from .config.config import YOSYS as yosys_path
    from subprocess import call, DEVNULL
    import os

    # prepare
    tmp_dot_path = f'{temporary_path}/cvtgv_to_fd.dot'
    yosys_command = f"""
        read_verilog {input_verilog_path}
        opt
        clean
        show -prefix {tmp_dot_path[:-4]} -format dot
    """

    # run
    call([yosys_path, '-p', yosys_command], stdout=DEVNULL)
    fix_direction(tmp_dot_path, output_gv_path)
    os.remove(tmp_dot_path)


def setup_folder_structure(): raise RuntimeError('Why are you using this? talk with Marco')
def clean_all(): raise RuntimeError('Why are you using this? talk with Marco')
def check_graph_equality(*args, **kwargs): raise RuntimeError('Why are you using this? talk with Marco')
