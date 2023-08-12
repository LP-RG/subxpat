import csv
from colorama import Fore, Style
import Z3Log

from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath
from sxpat.templateCreator import Template_SOP1ShareLogic
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *
from sxpat.config.config import *
from sxpat.synthesis import Synthesis
from sxpat.verification import erroreval_verification
from sxpat.stats import Stats
from sxpat.stats import *


def explore_grid(specs_obj: TemplateSpecs):
    print(
        Fore.BLUE + f'Grid ({specs_obj.lpp} X {specs_obj.pit}) and et={specs_obj.et} exploration started...' + Style.RESET_ALL)

    for pit in range(1, specs_obj.pit):
        for lpp in range(specs_obj.lpp):
            template_obj = Template_SOP1ShareLogic(specs_obj)
            template_obj.z3_generate_z3pyscript()
            template_obj.run_z3pyscript(specs_obj.et)
            print(f'{get_status(template_obj) = }')
            # if SAT

            # if UNSAT

            # if UNKNOWN







def is_last_cell(cur_lpp, cur_ppo, max_lpp, max_ppo) -> bool:
    if cur_lpp == max_lpp and cur_ppo == max_ppo:
        return True
    else:
        return False


def next_cell(cur_lpp, cur_ppo, max_lpp, max_ppo) -> (int, int):
    if is_last_cell(cur_lpp, cur_ppo, max_lpp, max_ppo):
        return cur_lpp + 1, cur_lpp + 1
    else:
        if cur_lpp < max_lpp:
            return cur_lpp + 1, cur_ppo
        else:
            return 0, cur_ppo + 1




def get_status(template_obj: Template_SOP1ShareLogic) -> str:
    """
    checks whether the current model was sat, unsat or unknown
    :param: the current template object
    :rtype: an str containing either of SAT, UNSAT, or UNKNOWN
    """
    template_obj.import_json_model()

    print(f'{template_obj.json_status = }')
    if template_obj.json_status == SAT:
        return SAT
    elif template_obj.json_status == UNSAT:
        return UNSAT
    elif template_obj.json_status == UNKNOWN:
        return UNKNOWN
