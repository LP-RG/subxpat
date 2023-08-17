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


def explore_grid_shared(specs_obj: TemplateSpecs) -> Stats:

    print(
        Fore.BLUE + f'Grid ({specs_obj.lpp} X {specs_obj.pit}) and et={specs_obj.et} SharedLogic started...' + Style.RESET_ALL)
    stats_obj = Stats(specs_obj)

    max_pit = specs_obj.pit
    max_lpp = specs_obj.lpp
    cur_lpp = -1
    cur_pit = -1
    pit = 1
    lpp = 0
    found = False
    while pit <= max_pit:
        if found:
            break
        while lpp <= max_lpp:
            if found:
                break
            elif lpp == 0 and pit > 1:
                lpp, pit = next_cell(lpp, pit, max_lpp, max_pit)
                continue

            else:
                specs_obj = set_current_context_shared(specs_obj, lpp, pit)

                template_obj = Template_SOP1ShareLogic(specs_obj)

                template_obj.z3_generate_z3pyscript()
                template_obj.run_z3pyscript(specs_obj.et, specs_obj.num_of_models, specs_obj.timeout)
                cur_status = get_status(template_obj)

                if cur_status == SAT:
                    synth_obj = Synthesis(specs_obj, template_obj.graph, template_obj.json_model,
                                          shared=specs_obj.shared, subxpat=specs_obj.subxpat)
                    synth_obj.export_verilog()
                    synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])

                    if erroreval_verification(specs_obj.exact_benchmark, synth_obj.ver_out_name[:-2], specs_obj.et):
                        print(
                        Fore.GREEN + f'Cell ({specs_obj.lpp} X {specs_obj.pit}) -> {SAT.upper()} (Area = {synth_obj.estimate_area()}) (ErrorEval -> PASS)' + Style.RESET_ALL)
                    else:
                        print(Fore.RED + f'ErrorEval -> FAILED' + Style.RESET_ALL)
                        exit()

                    stats_obj.grid.cells[lpp][pit].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=synth_obj.estimate_area(),
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=SAT)
                    cur_lpp = lpp
                    cur_pit = pit
                    found = True

                elif cur_status == UNSAT:
                    print(
                        Fore.YELLOW + f'Grid ({specs_obj.lpp} X {specs_obj.pit}) -> {UNSAT.upper()}' + Style.RESET_ALL)
                    stats_obj.grid.cells[lpp][pit].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=UNSAT)
                elif cur_status == UNKNOWN:
                    print(
                        Fore.MAGENTA + f'Grid ({specs_obj.lpp} X {specs_obj.pit}) -> {UNKNOWN.upper()}' + Style.RESET_ALL)
                    stats_obj.grid.cells[lpp][pit].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=UNKNOWN)
                lpp, pit = next_cell(lpp, pit, max_lpp, max_pit)

    # exploring the non-dominated cells
    if cur_pit != -1 and cur_lpp != -1:
        print(
            Fore.BLUE + f'Exploring the non-dominated cells...' + Style.RESET_ALL)

        for pit in range(cur_pit + 1, max_pit + 1):
            for lpp in range(1, cur_lpp):
                specs_obj = set_current_context_shared(specs_obj, lpp, pit)

                template_obj = Template_SOP1ShareLogic(specs_obj)

                template_obj.z3_generate_z3pyscript()
                template_obj.run_z3pyscript(specs_obj.et, specs_obj.num_of_models, specs_obj.timeout)
                cur_status = get_status(template_obj)

                if cur_status == SAT:
                    synth_obj = Synthesis(specs_obj, template_obj.graph, template_obj.json_model,
                                          shared=specs_obj.shared, subxpat=specs_obj.subxpat)

                    synth_obj.export_verilog()
                    synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])

                    if erroreval_verification(specs_obj.exact_benchmark, synth_obj.ver_out_name[:-2], specs_obj.et):
                        print(
                            Fore.GREEN + f'Cell ({specs_obj.lpp} X {specs_obj.pit}) -> found another {SAT.upper()} (ErrorEval -> PASS)' + Style.RESET_ALL)
                    else:
                        print(Fore.RED + f'ErrorEval -> FAILED' + Style.RESET_ALL)
                        exit()
                    stats_obj.grid.cells[lpp][pit].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=SAT)
                elif cur_status == UNSAT:
                    print(
                        Fore.YELLOW + f'Grid ({specs_obj.lpp} X {specs_obj.pit}) -> {UNSAT.upper()}' + Style.RESET_ALL)
                    stats_obj.grid.cells[lpp][pit].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=UNSAT)
                elif cur_status == UNKNOWN:
                    print(
                        Fore.MAGENTA + f'Grid ({specs_obj.lpp} X {specs_obj.pit}) -> {UNKNOWN.upper()}' + Style.RESET_ALL)
                    stats_obj.grid.cells[lpp][pit].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=UNKNOWN)
    return stats_obj


def explore_grid_xpat(specs_obj: TemplateSpecs) -> Stats:

    print(
        Fore.BLUE + f'Grid ({specs_obj.lpp} X {specs_obj.pit}) and et={specs_obj.et} Normal XPAT started...' + Style.RESET_ALL)
    stats_obj = Stats(specs_obj)


    max_lpp = specs_obj.lpp
    max_ppo = specs_obj.ppo

    cur_lpp = -1
    cur_ppo = -1

    ppo = 1
    lpp = 0
    found = False
    while ppo <= max_ppo:
        if found:
            break
        while lpp <= max_lpp:
            if found:
                break
            elif lpp == 0 and ppo > 1:
                lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)
                continue

            else:
                specs_obj = set_current_context_xpat(specs_obj, lpp, ppo)
                template_obj = Template_SOP1ShareLogic(specs_obj)

                template_obj.z3_generate_z3pyscript()
                template_obj.run_z3pyscript(specs_obj.et, specs_obj.num_of_models, specs_obj.timeout)
                cur_status = get_status(template_obj)

                if cur_status == SAT:
                    synth_obj = Synthesis(specs_obj, template_obj.graph, template_obj.json_model,
                                          shared=specs_obj.shared, subxpat=specs_obj.subxpat)
                    synth_obj.export_verilog()
                    synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])
                    if erroreval_verification(specs_obj.exact_benchmark, synth_obj.ver_out_name[:-2], specs_obj.et):
                        print(
                        Fore.GREEN + f'Cell ({specs_obj.lpp} X {specs_obj.ppo}) -> {SAT.upper()} (Area = {synth_obj.estimate_area()}) (ErrorEval -> PASS)' + Style.RESET_ALL)
                    else:
                        print(Fore.RED + f'ErrorEval -> FAILED' + Style.RESET_ALL)
                        exit()
                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=synth_obj.estimate_area(),
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=SAT)
                    cur_lpp = lpp
                    cur_ppo = ppo

                    found = True

                elif cur_status == UNSAT:
                    print(
                        Fore.YELLOW + f'Grid ({specs_obj.lpp} X {specs_obj.ppo}) -> {UNSAT.upper()}' + Style.RESET_ALL)
                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=UNSAT)
                elif cur_status == UNKNOWN:
                    print(
                        Fore.MAGENTA + f'Grid ({specs_obj.lpp} X {specs_obj.ppo}) -> {UNKNOWN.upper()}' + Style.RESET_ALL)
                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=UNKNOWN)
                lpp, ppo = next_cell(lpp, ppo, max_lpp, max_ppo)

    # exploring the non-dominated cells
    if cur_ppo != -1 and cur_lpp != -1:
        print(
            Fore.BLUE + f'Exploring the non-dominated cells...' + Style.RESET_ALL)
        for ppo in range(cur_ppo + 1, max_ppo + 1):
            for lpp in range(1, cur_lpp):
                specs_obj = set_current_context_xpat(specs_obj, lpp, ppo)

                template_obj = Template_SOP1ShareLogic(specs_obj)

                template_obj.z3_generate_z3pyscript()
                template_obj.run_z3pyscript(specs_obj.et, specs_obj.num_of_models, specs_obj.timeout)
                cur_status = get_status(template_obj)

                if cur_status == SAT:
                    synth_obj = Synthesis(specs_obj, template_obj.graph, template_obj.json_model,
                                          shared=specs_obj.shared, subxpat=specs_obj.subxpat)

                    synth_obj.export_verilog()
                    synth_obj.export_verilog(z3logpath.INPUT_PATH['ver'][0])
                    print(
                        Fore.GREEN + f'Cell ({specs_obj.lpp} X {specs_obj.ppo}) -> found another {SAT.upper()}' + Style.RESET_ALL)

                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=SAT)
                elif cur_status == UNSAT:
                    print(
                        Fore.YELLOW + f'Grid ({specs_obj.lpp} X {specs_obj.ppo}) -> {UNSAT.upper()}' + Style.RESET_ALL)
                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=UNSAT)
                elif cur_status == UNKNOWN:
                    print(
                        Fore.MAGENTA + f'Grid ({specs_obj.lpp} X {specs_obj.ppo}) -> {UNKNOWN.upper()}' + Style.RESET_ALL)
                    stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_id=0,
                                                                    this_iteration=1,
                                                                    this_area=-1,
                                                                    this_runtime=template_obj.get_json_runtime(),
                                                                    this_status=UNKNOWN)
    return stats_obj


def is_last_cell(cur_lpp, cur_pit, max_lpp, max_pit) -> bool:
    if cur_lpp == max_lpp and cur_pit == max_pit:
        return True
    else:
        return False


def next_cell(cur_lpp, cur_pit, max_lpp, max_pit) -> (int, int):
    if is_last_cell(cur_lpp, cur_pit, max_lpp, max_pit):
        return cur_lpp + 1, cur_pit + 1
    else:
        if cur_lpp < max_lpp:
            return cur_lpp + 1, cur_pit
        else:
            return 0, cur_pit + 1


def get_status(template_obj: Template_SOP1ShareLogic) -> str:
    """
    checks whether the current model was sat, unsat or unknown
    :param: the current template object
    :rtype: an str containing either of SAT, UNSAT, or UNKNOWN
    """
    template_obj.import_json_model()
    if template_obj.json_status == SAT:
        return SAT
    elif template_obj.json_status == UNSAT:
        return UNSAT
    elif template_obj.json_status == UNKNOWN:
        return UNKNOWN


def set_current_context_shared(specs_obj: TemplateSpecs, lpp: int, pit: int) -> TemplateSpecs:
    specs_obj.lpp = lpp
    specs_obj.pit = pit
    return specs_obj


def set_current_context_xpat(specs_obj: TemplateSpecs, lpp: int, ppo: int) -> TemplateSpecs:
    specs_obj.lpp = lpp
    specs_obj.ppo = ppo
    return specs_obj
