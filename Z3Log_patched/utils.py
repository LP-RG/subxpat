from shutil import move
from subprocess import call

from Z3Log.config.config import YOSYS as yosys_path
from Z3Log.config.path import OUTPUT_PATH

__all__ = [
    'setup_folder_structure',
    'clean_all',
    'check_graph_equality',
    'fix_direction',
    'get_pure_name',
    'convert_verilog_to_gv',
]

# kept:
from Z3Log.utils import setup_folder_structure
from Z3Log.utils import clean_all
from Z3Log.utils import check_graph_equality
from Z3Log.utils import fix_direction
from Z3Log.utils import get_pure_name

# replaced:
# from Z3Log.utils import convert_verilog_to_gv


def convert_verilog_to_gv(file_name: str):

    # prepare
    file_name = get_pure_name(file_name)
    #
    folder, extension = OUTPUT_PATH['ver']
    verilog_in_path = f'{folder}/{file_name}.{extension}'
    folder, extension = OUTPUT_PATH['gv']
    gv_out_path = f'{folder}/{file_name}.{extension}'
    #
    yosys_command = f"""
        read_verilog {verilog_in_path}
        opt
        clean
        show -prefix {gv_out_path[:-3]} -format dot
    """

    # run
    with open(f'yosys_graph.log', 'w') as y:
        # run yosys command (dump log to temporary file)
        retcode = call([yosys_path, '-p', yosys_command], stdout=y)
        assert retcode == 0

    # move .dot to .gv
    move(gv_out_path[:-3] + '.dot', gv_out_path)
