from __future__ import annotations
from typing import Tuple, List, Dict
import datetime  # precautionary measure
import csv
import re
import os
from matplotlib import pyplot as plt
from colorama import Fore, Style
import subprocess
from subprocess import PIPE
from shutil import copy

from Z3Log.config.config import *
from Z3Log.config.path import *

from sxpat.config import config as sxpatconfig
from sxpat.config import paths as sxpatpaths
from sxpat.specifications import Specifications, TemplateType


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    # TODO: Marco: we could use the `progress` package (https://pypi.org/project/progress/) that already does this (ShadyBar could be the best option).
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


class Model:
    def __init__(self, runtime: float = None,
                 area: float = None,
                 delay: float = None,
                 total_power: float = None,
                 id: int = 0,
                 iteration: int = 0,
                 status: str = 'Unexplored',
                 cell: Tuple[int, int] = (-1, -1),
                 et: int = -1,
                 labeling_time: float = -1,
                 subgraph_extraction_time: float = -1,
                 subgraph_number_inputs: int = -1,
                 subgraph_number_outputs: int = -1,
                 subxpat_phase1_time: float = -1,
                 subxpat_phase2_time: float = -1,
                 subxpat_v1_time: float = -1):
        self.__cell = cell
        self.__id = id
        self.__iteration = iteration
        self.__status = status
        self.__area = area
        # id is for the cases in which we have multiple models per cell
        # if single model per cell is selected, then let's give it id = 0 for consistency
        self.__delay = delay
        self.__total_power = total_power
        self.__et = et
        self.__labeling_time = labeling_time
        self.__subgraph_extraction_time = subgraph_extraction_time
        self.__subgraph_number_inputs = subgraph_number_inputs
        self.__subgraph_number_outputs = subgraph_number_outputs
        self.__subxpat_phase1_time = subxpat_phase1_time
        self.__subxpat_phase2_time = subxpat_phase2_time
        self.__subxpat_v1_time = subxpat_v1_time
        self.__runtime = runtime

    @property
    def iteration(self):
        return self.__iteration

    @property
    def et(self):
        return self.__et

    @property
    def labeling_time(self):
        return self.__labeling_time

    @property
    def subgraph_extraction_time(self):
        return self.__subgraph_extraction_time

    @property
    def subgraph_number_inputs(self):
        return self.__subgraph_number_inputs

    @property
    def subgraph_number_outputs(self):
        return self.__subgraph_number_outputs

    @property
    def subxpat_phase1_time(self):
        return self.__subxpat_phase1_time

    @property
    def subxpat_phase2_time(self):
        return self.__subxpat_phase2_time

    @property
    def runtime(self):
        return self.__runtime

    @runtime.setter
    def runtime(self, this_runtime):
        self.__runtime = this_runtime

    @property
    def subxpat_v1_time(self):
        return self.__subxpat_v1_time

    @property
    def area(self):
        return self.__area

    @area.setter
    def area(self, this_area):
        self.__area = this_area

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, this_id):
        self.__id = this_id

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, this_status):
        self.__status = this_status

    @property
    def cell(self):
        return self.__cell

    @cell.setter
    def cell(self, this_cell):
        self.__cell = this_cell

    @property
    def delay(self):
        return self.__delay

    @delay.setter
    def delay(self, this_delay):
        self.__delay = this_delay

    @property
    def total_power(self):
        return self.__total_power

    @total_power.setter
    def total_power(self, this_total_power):
        self.__total_power = this_total_power

    def __repr__(self):
        return f'An object of class Model:\n' \
               f'{self.status = }' \
               f'{self.runtime = }\n' \
               f'{self.area = }\n' \
               f'{self.total_power = }\n' \
               f'{self.delay = }\n' \
               f'{self.id = }\n'


class Cell:
    def __init__(self, spec_obj: Specifications):
        self.__exact_name: str = spec_obj.exact_benchmark
        self.__approximate_name: str = spec_obj.current_benchmark
        self.__lpp, self.__ppo = {
            TemplateType.NON_SHARED: lambda: (spec_obj.max_lpp, spec_obj.max_ppo),
            TemplateType.SHARED: lambda: (spec_obj.max_its, spec_obj.max_pit),
        }[spec_obj.template]()

        self.__et: int = spec_obj.max_error

        self.__models: Dict[int, Dict[int, Model]] = {}

    @property
    def exact_name(self):
        return self.__exact_name

    @property
    def approximate_name(self):
        return self.__approximate_name

    @property
    def lpp(self):
        return self.__lpp

    @property
    def ppo(self):
        return self.__ppo

    @property
    def et(self):
        return self.__et

    @property
    def models(self):
        return self.__models

    def store_model_info(self, model_info_obj: Model):
        self.models[model_info_obj.iteration] = {model_info_obj.id: model_info_obj}

    def __repr__(self):
        return f"An object of class Cell:\n" \
               f"{self.exact_name = }\n" \
               f"{self.et = }\n" \
               f"{self.models = }"


class Grid:
    def __init__(self, spec_obj: Specifications):
        self.__exact_name: str = spec_obj.exact_benchmark
        self.__approximate_name: str = spec_obj.current_benchmark

        self.__lpp, self.__ppo = {
            TemplateType.NON_SHARED: lambda: (spec_obj.max_lpp, spec_obj.max_ppo),
            TemplateType.SHARED: lambda: (spec_obj.max_its, spec_obj.max_pit),
        }[spec_obj.template]()

        self.__et: int = spec_obj.max_error

        # Since the rows and cols are predefined as lpp, and ppo (pit) then we're gonna use 2DList instead of a nested Dict
        self.__cells: List[List[Cell]] = [[Cell(spec_obj) for _ in range(self.ppo + 1)] for _ in range(self.lpp + 1)]

    @property
    def exact_name(self):
        return self.__exact_name

    @property
    def approximate_name(self):
        return self.__approximate_name

    @property
    def lpp(self):
        return self.__lpp

    @property
    def ppo(self):
        return self.__ppo

    @property
    def et(self):
        return self.__et

    @property
    def cells(self):
        return self.__cells

    def store_cell(self, this_cell: Cell, i: int, j: int):
        self.cells[i][j] = this_cell

    def __repr__(self):
        return f'An object of class Grid: \n' \
               f'{self.cells = }\n'


class Stats:
    def __init__(self, specs: Specifications):
        """
        stores the stats of an experiment (grid or cell) into an object
        """
        self.__template_name = specs.template_name
        self.__exact_name: str = specs.exact_benchmark
        self.__approximate_name: str = specs.current_benchmark

        self.__lpp, self.__ppo = {
            TemplateType.NON_SHARED: lambda: (specs.max_lpp, specs.max_ppo),
            TemplateType.SHARED: lambda: (specs.max_its, specs.max_pit),
        }[specs.template]()

        self.__et: int = specs.max_error

        self.__tool_name = {
            (False, TemplateType.NON_SHARED): sxpatconfig.XPAT,
            (False, TemplateType.SHARED): sxpatconfig.SHARED_XPAT,
            (True, TemplateType.NON_SHARED): sxpatconfig.SUBXPAT,
            (True, TemplateType.SHARED): sxpatconfig.SHARED_SUBXPAT,
        }[(specs.subxpat, specs.template)]

        self.__max_sensitivity: int = specs.max_sensitivity
        self.__min_subgraph_size: int = specs.min_subgraph_size

        self.__imax: int = specs.imax
        self.__omax: int = specs.omax
        self.__mode: int = specs.extraction_mode

        # This property should be assigned before calling the funciton "self.get_grid_name()"
        self.__specs: Specifications = specs

        self.__grid_name: str = self.get_grid_name()
        self.__grid_path: str = self.get_grid_path()

        self.__grid = Grid(specs)

    @property
    def tool_name(self):
        return self.__tool_name

    @property
    def template_name(self):
        return self.__template_name

    @property
    def specs(self):
        return self.__specs

    @property
    def mode(self):
        return self.__mode

    @property
    def imax(self):
        return self.__imax

    @property
    def omax(self):
        return self.__omax

    @property
    def grid_path(self):
        return self.__grid_path

    @property
    def grid_name(self):
        return self.__grid_name

    @property
    def max_sensitivity(self):
        return self.__max_sensitivity

    @property
    def min_subgraph_size(self):
        return self.__min_subgraph_size

    @property
    def exact_name(self):
        return self.__exact_name

    @property
    def approximate_name(self):
        return self.__approximate_name

    @property
    def lpp(self):
        return self.__lpp

    @property
    def ppo(self):
        return self.__ppo

    @property
    def et(self):
        return self.__et

    @property
    def grid(self):
        return self.__grid

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, this_status):
        self.__status = this_status

    @property
    def areas(self):
        return self.__areas

    @areas.setter
    def areas(self, this_areas):
        self.__areas = this_areas

    @property
    def runtimes(self):
        return self.__runtimes

    @runtimes.setter
    def runtimes(self, this_runtimes):
        self.__runtimes = this_runtimes

    @property
    def cells(self):
        return self.__cells

    @cells.setter
    def cells(self, this_cells):
        self.__cells = this_cells

    @property
    def json_paths(self):
        return self.__json_paths

    @json_paths.setter
    def json_paths(self, this_json_paths):
        self.__json_paths = this_json_paths

    @property
    def verilog_paths(self):
        return self.__verilog_paths

    @verilog_paths.setter
    def verilog_paths(self, this_verilog_paths):
        self.__verilog_paths = this_verilog_paths

    def get_grid_name(self):
        """
        returns: a unique grid file name for this experiment (that is determined by specs_obj)
        """
        _, extension = OUTPUT_PATH['report']

        # TODO: Morteza: this naming convention is not generic enough,
        # I will try to add every type of specification of the experiment into the name so it wouldn't get overwritten
        # new fields that are added:
        # for subxpat_v2 => et_partitioning
        # for all num_of_models, omax, imax
        # as a precautionary measure, we also add the time stamp at the end of every generated file

        # So we change the names from "grid_adder_i6_o4_10X20_et10_subxpat_v2_mode4_SOP1" to
        # 'grid_adder_i6_o4_10X20_et10_subxpat_v2_desc_fef1_sef1_mode4_omax1_imax3_kucTrue_SOP1_time20240403:214107'

        # let's divide our nomenclature into X parts: head (common), technique_specific, tail (common)

        head = f'grid_{self.exact_name}_{self.lpp}X{self.ppo}_et{self.et}_'

        technique_specific = f'{self.tool_name}_{self.specs.error_partitioning.value}_'
        technique_specific += f'enc{self.specs.encoding.value}_'

        tail = f'mode{self.specs.extraction_mode}_omax{self.specs.omax}_imax{self.specs.imax}_const{self.specs.constants.value}_'
        tail += f'{self.template_name}_time'

        # Get the current date and time
        current_time = datetime.datetime.now()
        # Format the date and time to create a unique identifier
        time_stamp = current_time.strftime("%Y%m%d:%H%M%S")

        name = head + technique_specific + tail + time_stamp

        return f'{name}.{extension}'

    def get_grid_path(self):
        """
        returns: the path where the grid .csv file should be stored
        """
        folder, _ = OUTPUT_PATH['report']
        path = f'{folder}/{self.grid_name}'
        print(f'{path = }')
        return path

    def store_grid(self):
        """
        dumps the contents of grid object while preserving its structure, onto .csv file with the name self.grid_name and at the address self.grid_path
        returns: None
        """

        with open(f'{self.grid_path}',
                  'w') as f:
            csvwriter = csv.writer(f)

            # TODO: iterate through all the fields with something like the the command below:
            # header = []
            # for attr in Model.__dict__.keys():
            #     header.append(f"{attr.replace('_Model__', '')}")
            # header = tuple(header)

            header = ('cell', 'iteration', 'model_id', 'status', 'runtime', 'area', 'delay', 'total_power', 'et',
                      'labeling_time', 'subgraph_extraction', 'subgraph_inputs', 'subgraph_outputs', 'subxpat_phase1', 'subxpat_phase2')
            csvwriter.writerow(header)
            # iterate over cells (lppXppo)
            for ppo in range(self.ppo + 1):
                for lpp in range(self.lpp + 1):
                    cell = f'({lpp}X{ppo})'
                    # ToDo: for a given cell, iterate through all the models retrieved and find the best one
                    # For now: for each given cell, report the first one
                    for iteration in self.grid.cells[lpp][ppo].models.keys():
                        for m_id in self.grid.cells[lpp][ppo].models[iteration].keys():
                            row = []
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].cell)
                            row.append(iteration)
                            row.append(m_id)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].status)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].runtime)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].area)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].delay)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].total_power)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].et)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].labeling_time)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].subgraph_extraction_time)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].subgraph_number_inputs)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].subgraph_number_outputs)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].subxpat_phase1_time)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].subxpat_phase2_time)
                            row.append(self.grid.cells[lpp][ppo].models[iteration][m_id].subxpat_v1_time)
                            row = tuple(row)
                            csvwriter.writerow(row)

    def gather_results(self):
        mecals = Result(self.specs, self.exact_name, sxpatconfig.MECALS)

        muscat = Result(self.specs, self.exact_name, sxpatconfig.MUSCAT)
        mecals.status = False
        muscat.status = False
        shared_xpat = Result(self.specs, self.exact_name, sxpatconfig.SHARED_XPAT)
        xpat = Result(self.specs, self.exact_name, sxpatconfig.XPAT)

        #
        shared_subxpat = []
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=1))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=2))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=3))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=4))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=5))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=10))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=15))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=20))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=25))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=30))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=35))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=40))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=45))
        # shared_subxpat.append(Result(self.exact_name, sxpatconfig.SHARED_SUBXPAT, mode=3, subgraphsize=50))

        # mecals.status = False
        # xpat.status = False
        # muscat.status = False
        subxpat = []
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=2, omax=1))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=2, omax=2))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=3, omax=1))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=3, omax=2))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=3, omax=3))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=4, omax=1))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=4, omax=2))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=4, omax=3))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=1, imax=4, omax=4))

        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=1))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=2))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=3))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=4))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=5))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=10))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=15))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=20))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=25))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=30))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=35))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=40))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=45))
        # subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=50))

        #
        self.plot_area(shared_xpat=shared_xpat, shared_subxpat_list=shared_subxpat,
                       subxpat_list=subxpat,
                       xpat=xpat,
                       mecals=mecals,
                       muscat=muscat,
                       best=True)

        # self.plot_area(shared_xpat = shared_xpat, shared_subxpat_list= shared_subxpat,
        #                subxpat_list=subxpat,
        #                xpat=xpat,
        #                mecals=mecals,
        #                muscat=muscat,
        #                best=False)
        # self.plot_power(subxpat_list= subxpat,
        #                xpat=xpat,
        #                mecals=mecals,
        #                muscat=muscat)
        # self.plot_delay(subxpat_list= subxpat,
        #                xpat=xpat,
        #                mecals=mecals,
        #                muscat=muscat)
        # #
        # self.plot_pap(subxpat_list= subxpat,
        #                xpat=xpat,
        #                mecals=mecals,
        #                muscat=muscat)
        # #
        # self.plot_adp(subxpat_list= subxpat,
        #                xpat=xpat,
        #                mecals=mecals,
        #                muscat=muscat,
        #                best=True)
        # self.plot_adp(subxpat_list=subxpat,
        #               xpat=xpat,
        #               mecals=mecals,
        #               muscat=muscat,
        #               best=False)
        # #
        # self.plot_pdap(subxpat_list= subxpat,
        #                xpat=xpat,
        #                mecals=mecals,
        #                muscat=muscat)
        # self.plot_iterations(sxpatconfig.AREA)

    def get_cmap(self, n, name='hsv'):
        '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
        RGB color; the keyword argument name must be a standard mpl colormap name.'''
        return plt.cm.get_cmap(name, n)

    def plot_area(self, shared_subxpat_list: List[Result], subxpat_list: List[Result], shared_xpat: Result, xpat: Result, mecals: Result, muscat: Result, best: bool = True):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Area')
        ax.set_title(f'{self.exact_name} Area comparison', fontsize=20)

        if muscat.status:
            ax.plot(muscat.error_array, muscat.area_dict.values(), label='MUSCAT', color='red', marker='o', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(mecals.error_array, mecals.area_dict.values(), label='MECALS', color='black', marker='o', markeredgecolor='black',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(xpat.error_array, xpat.area_dict.values(), label='XPAT', color='green', marker='D', markeredgecolor='green',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        if shared_xpat.status:
            ax.plot(shared_xpat.error_array, shared_xpat.area_dict.values(), label='SHARED_XPAT', color='blue', marker='D',
                    markeredgecolor='blue',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        if best:
            best_area_dict: Dict = {}
            for idx, subxpat in enumerate(subxpat_list):
                if subxpat.status:
                    for et in subxpat.error_array:
                        if et in best_area_dict.keys():
                            if subxpat.area_dict[et] < best_area_dict[et]:
                                best_area_dict[et] = subxpat.area_dict[et]

                        else:
                            best_area_dict[et] = subxpat.area_dict[et]
                    if subxpat.extraction_mode == 1:
                        label = f'SubXPAT_io_best'
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_best.pdf"
                    elif subxpat.extraction_mode == 3:
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_best.pdf"
                        label = f'SubXPAT_subgraphsize_best'
            if subxpat_list:
                ax.plot(subxpat_list[0].error_array, best_area_dict.values(), label=label, marker='D', markeredgecolor='blue',
                        markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

            figurename_png = None
            figurename_pdf = None
            shared_best_area_dict: Dict = {}
            for idx, shared in enumerate(shared_subxpat_list):
                if shared.status:
                    for et in shared.error_array:
                        if et in shared_best_area_dict.keys():
                            if shared.area_dict[et] < shared_best_area_dict[et]:
                                shared_best_area_dict[et] = shared.area_dict[et]

                        else:
                            shared_best_area_dict[et] = shared.area_dict[et]
                    if shared.extraction_mode == 1:
                        label = f'Shared_SubXPAT_io_best'
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_best.pdf"
                    elif shared.extraction_mode == 3:
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_best.pdf"
                        label = f'Shared_SubXPAT_subgraphsize_best'
            if shared_subxpat_list != []:
                ax.plot(shared_subxpat_list[0].error_array, shared_best_area_dict.values(), label=label, marker='D',
                        markeredgecolor='black',
                        markeredgewidth=5, linestyle='dotted', linewidth=2, markersize=3)
        else:

            for idx, subxpat in enumerate(subxpat_list):
                if subxpat.status:
                    if subxpat.extraction_mode == 1:

                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_multiple.pdf"

                        label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                    elif subxpat.extraction_mode == 3:

                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_multiple.pdf"

                        label = f'SubXPAT_subgraphsize{subxpat.subgraphsize}'
                    ax.plot(subxpat.error_array, subxpat.area_dict.values(), label=label, marker='D',
                            markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

            for idx, shared in enumerate(shared_subxpat_list):
                if shared.status:
                    if shared.extraction_mode == 1:

                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_multiple.pdf"

                        label = f'Shared_SubXPAT_i{shared.imax}_o{shared.omax}'
                    elif shared.extraction_mode == 3:

                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_multiple.pdf"

                        label = f'Shared_SubXPAT_subgraphsize{shared.subgraphsize}'
                    ax.plot(shared.error_array, shared.area_dict.values(), label=label, marker='D',
                            markeredgewidth=5, linestyle='dotted', linewidth=2, markersize=3)

        plt.xticks(muscat.error_array)
        if len(subxpat_list) > 8:
            plt.legend()
            pass
            # Put a legend below current axis
            # plt.legend(loc='upper center', bbox_to_anchor=(1.5, 0.5),
            #           fancybox=True, shadow=True, ncol=5)
            # plt.tight_layout()
        else:
            # plt.legend(loc='best')
            pass

        plt.legend()
        if not figurename_png:
            figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_xpat_vs_shared.png"
        plt.savefig(figurename_png)
        # plt.savefig(figurename_pdf)

    def plot_power(self, shared_subxpat_list: List[Result], subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Power')
        ax.set_title(f'{self.exact_name} Power comparison', fontsize=20)

        if muscat.status:
            ax.plot(muscat.error_array, muscat.power_dict.values(), label='MUSCAT', color='red', marker='o', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(mecals.error_array, mecals.power_dict.values(), label='MECALS', color='black', marker='o',
                    markeredgecolor='black',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(xpat.error_array, xpat.power_dict.values(), label='XPAT', color='green', marker='D', markeredgecolor='green',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        for subxpat in subxpat_list:
            if subxpat.status:
                if self.extraction_mode == 1:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                    label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                elif self.extraction_mode == 3:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'subgraphsize{subxpat.subgraphsize}']
                    label = f'SubXPAT_subgraphsize{subxpat.subgraphsize}'
                ax.plot(subxpat.error_array, subxpat.power_dict.values(), label=label, color=color, marker='D', markeredgecolor=color,
                        markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        # ax.plot(uncomputed_et, uncomputed_area, label='N/A', color='red', marker='o', markeredgecolor='red',
        #         markeredgewidth=10, linestyle=None, linewidth=0, markersize=8)
        #
        plt.xticks(muscat.error_array)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/power_{self.exact_name}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/power_{self.exact_name}.pdf"
        plt.savefig(figurename_png)
        # plt.savefig(figurename_pdf)

    def plot_delay(self, shared_subxpat_list: List[Result], subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Delay')
        ax.set_title(f'{self.exact_name} Delay comparison', fontsize=20)

        if muscat.status:
            ax.plot(muscat.error_array, muscat.delay_dict.values(), label='MUSCAT', color='red', marker='o', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(mecals.error_array, mecals.delay_dict.values(), label='MECALS', color='black', marker='o',
                    markeredgecolor='black',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(xpat.error_array, xpat.delay_dict.values(), label='XPAT', color='green', marker='D', markeredgecolor='green',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)
        for subxpat in subxpat_list:
            # color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
            if subxpat.status:
                if self.extraction_mode == 1:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                    label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                elif self.extraction_mode == 3:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'subgraphsize{subxpat.subgraphsize}']
                    label = f'SubXPAT_subgraphsize{subxpat.subgraphsize}'
                ax.plot(subxpat.error_array, subxpat.delay_dict.values(), label=label, color=color, marker='D', markeredgecolor=color,
                        markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        # ax.plot(uncomputed_et, uncomputed_area, label='N/A', color='red', marker='o', markeredgecolor='red',
        #         markeredgewidth=10, linestyle=None, linewidth=0, markersize=8)
        #
        plt.xticks(muscat.error_array)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_{self.exact_name}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_{self.exact_name}.pdf"
        plt.savefig(figurename_png)
        # plt.savefig(figurename_pdf)

    def plot_pap(self, shared_subxpat_list: List[Result], subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'PAP')
        ax.set_title(f'{self.exact_name} Power X Area comparison', fontsize=20)

        if muscat.status:
            ax.plot(muscat.error_array, [muscat.power_dict[key] * muscat.area_dict[key] for key in muscat.power_dict.keys()], label='MUSCAT', color='red', marker='o', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(mecals.error_array, [mecals.power_dict[key] * mecals.area_dict[key] for key in mecals.power_dict.keys()], label='MECALS', color='black', marker='o',
                    markeredgecolor='black',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(xpat.error_array, [xpat.power_dict[key] * xpat.area_dict[key] for key in xpat.power_dict.keys()], label='XPAT', color='green', marker='D', markeredgecolor='green',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)
        for subxpat in subxpat_list:
            if subxpat.status:
                if self.extraction_mode == 1:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                    label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                elif self.extraction_mode == 3:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'subgraphsize{subxpat.subgraphsize}']
                    label = f'SubXPAT_subgraphsize{subxpat.subgraphsize}'
                ax.plot(subxpat.error_array, [subxpat.power_dict[key] * subxpat.area_dict[key] for key in subxpat.power_dict.keys()],
                        label=label, color=color, marker='D', markeredgecolor=color,
                        markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        #
        plt.xticks(muscat.error_array)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/power_area_product_{self.exact_name}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/power_area_product_{self.exact_name}.pdf"
        plt.savefig(figurename_png)
        # plt.savefig(figurename_pdf)

    def plot_pdap(self, shared_subxpat_list: List[Result], subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'PDAP')
        ax.set_title(f'{self.exact_name} Power X Delay X Area comparison', fontsize=20)

        if muscat.status:
            ax.plot(muscat.error_array, [muscat.delay_dict[key] * muscat.power_dict[key] * muscat.power_dict[key] for key in muscat.power_dict.keys()],
                    label='MUSCAT', color='red', marker='o', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(mecals.error_array, [mecals.delay_dict[key] * mecals.power_dict[key] * mecals.power_dict[key] for key in mecals.power_dict.keys()],
                    label='MECALS', color='black', marker='o',
                    markeredgecolor='black',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(xpat.error_array, [xpat.delay_dict[key] * xpat.power_dict[key] * xpat.power_dict[key] for key in xpat.power_dict.keys()],
                    label='XPAT', color='green', marker='D', markeredgecolor='green',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)
        for subxpat in subxpat_list:
            if subxpat.status:
                if self.extraction_mode == 1:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                    label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                elif self.extraction_mode == 3:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'subgraphsize{subxpat.subgraphsize}']
                    label = f'SubXPAT_subgraphsize{subxpat.subgraphsize}'
                ax.plot(subxpat.error_array, [subxpat.delay_dict[key] * subxpat.power_dict[key] * subxpat.power_dict[key] for key in subxpat.power_dict.keys()],
                        label=label, color='blue', marker='D', markeredgecolor=color,
                        markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        #
        plt.xticks(muscat.error_array)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/power_area_delay_product_{self.exact_name}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/power_area_delay_product_{self.exact_name}.pdf"
        plt.savefig(figurename_png)
        # plt.savefig(figurename_pdf)

    def plot_adp(self, shared_subxpat_list: List[Result], subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result, best: bool = True):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'DAP')
        ax.set_title(f'{self.exact_name} Delay X Area comparison', fontsize=20)

        if muscat.status:
            ax.plot(muscat.error_array, [muscat.delay_dict[key] * muscat.area_dict[key] for key in muscat.power_dict.keys()],
                    label='MUSCAT', color='red', marker='o', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(mecals.error_array, [mecals.delay_dict[key] * mecals.area_dict[key] for key in mecals.area_dict.keys()],
                    label='MECALS', color='black', marker='o',
                    markeredgecolor='black',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(xpat.error_array, [xpat.delay_dict[key] * xpat.area_dict[key] for key in xpat.area_dict.keys()],
                    label='XPAT', color='green', marker='D', markeredgecolor='green',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        if best:
            best_area_dict: Dict = {}
            respective_delay_dict: Dict = {}
            for idx, subxpat in enumerate(subxpat_list):
                if subxpat.status:
                    for et in subxpat.error_array:
                        if et in best_area_dict.keys():
                            if subxpat.area_dict[et] < best_area_dict[et]:
                                best_area_dict[et] = subxpat.area_dict[et]
                                respective_delay_dict[et] = subxpat.delay_dict[et]
                        else:
                            best_area_dict[et] = subxpat.area_dict[et]
                            respective_delay_dict[et] = subxpat.delay_dict[et]
                    if self.extraction_mode == 1:
                        label = f'SubXPAT_io_best'
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_io_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_io_best.pdf"
                    elif self.extraction_mode == 3:
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_subgraph_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_subgraph_best.pdf"
                        label = f'SubXPAT_subgraphsize_best'
            ax.plot(subxpat_list[0].error_array, [respective_delay_dict[key] * best_area_dict[key] for key in subxpat_list[0].area_dict.keys()],
                    label=label, marker='D', markeredgecolor='blue',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)
        else:
            for subxpat in subxpat_list:
                if subxpat.status:
                    if self.extraction_mode == 1:
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_io_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_io_multiple.pdf"
                        color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                        label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                    elif self.extraction_mode == 3:
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_product_{self.exact_name}_subgraph_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_product_{self.exact_name}_subgraph_multiple.pdf"
                        color = sxpatconfig.SUBXPAT_COLOR_DICT[f'subgraphsize{subxpat.subgraphsize}']
                        label = f'SubXPAT_subgraphsize{subxpat.subgraphsize}'
                    ax.plot(subxpat.error_array, [subxpat.delay_dict[key] * subxpat.area_dict[key] for key in subxpat.area_dict.keys()],
                            label=label, color=color, marker='D', markeredgecolor='blue',
                            markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        #
        plt.xticks(muscat.error_array)
        plt.legend(loc='best')

        plt.savefig(figurename_png)
        # plt.savefig(figurename_pdf)

    def plot_partitioning(self, metric: str = sxpatconfig.AREA):
        subxpat = Result(self.specs, self.exact_name, sxpatconfig.SUBXPAT)
        self._get_partitioning_characteristics(subxpat)
        # for an error, extract the grid for each partitioning approach

    def plot_iterations(self, metric: str = sxpatconfig.AREA):
        subxpat = Result(self.specs, self.exact_name, sxpatconfig.SUBXPAT)
        self._get_iteration_characteristcs(subxpat)

        fig, ax = plt.subplots()
        ax.set_xlabel(f'iterations')
        ax.set_ylabel(ylabel=f'{metric}')
        ax.set_title(f'{self.exact_name} {metric} over iterations', fontsize=30)
        iteration_list = []
        for idx, error in enumerate(subxpat.error_array):
            iteration_list = list(range(1, len(subxpat.area_iteration_dict[error]) + 1))
            if metric == sxpatconfig.AREA:
                ax.plot(iteration_list, subxpat.area_iteration_dict[error], label=f'ET={error}', color=sxpatconfig.COLOR_DICT[idx], marker='D', markeredgecolor=sxpatconfig.COLOR_DICT[idx],
                        markeredgewidth=3, linestyle='solid', linewidth=2, markersize=2)
            elif metric == sxpatconfig.POWER:
                ax.plot(iteration_list, subxpat.power_iteration_dict[error], label=f'ET={error}', color=sxpatconfig.COLOR_DICT[idx], marker='D', markeredgecolor=sxpatconfig.COLOR_DICT[idx],
                        markeredgewidth=3, linestyle='solid', linewidth=2, markersize=2)
            elif metric == sxpatconfig.DELAY:
                ax.plot(iteration_list, subxpat.delay_iteration_dict[error], label=f'ET={error}', color=sxpatconfig.COLOR_DICT[idx], marker='D', markeredgecolor=sxpatconfig.COLOR_DICT[idx],
                        markeredgewidth=3, linestyle='solid', linewidth=2, markersize=2)
            else:
                print(Fore.RED + f'ERROR!!! metric {metric} is not correct. Choose among AREA, POWER, and DELAY!' + Style.RESET_ALL)

        if len(iteration_list) > 0:
            plt.xticks(iteration_list)
            plt.legend(loc='best')
            figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/{metric}_over_iterations_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.specs.iteration}_without_sensitivity.png"
            figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/{metric}_over_iterations_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.specs.iteration}_without_sensitivity.pdf"
            plt.savefig(figurename_png)
            plt.savefig(figurename_pdf)
        else:
            print(Fore.RED + f'ERROR!!! no iterations found => iteration_list variable is empty' + Style.RESET_ALL)

    def _get_num_iterations(self):
        subxpat = Result(self.specs, self.exact_name, sxpatconfig.SUBXPAT)
        iterations = -1

        folder, _ = OUTPUT_PATH['report']
        with open(f'{folder}/{list(subxpat.grid_files.keys())[0]}', 'r') as gf:
            csvreader = csv.reader(gf)
            for line in csvreader:
                if re.search('iterations', line[0]):
                    iterations = len(line) - 1
                    break
        return iterations

    def _get_partitioning_characteristics(self, subxpat: Result):
        partitioning_dict: Dict = {}
        for error in subxpat.error_array:
            for grid_file in subxpat.grid_files.keys():
                if re.search(f'et{error}', grid_file):
                    cur_imax = int(re.search(f'imax(\d+)', grid_file).group(1))
                    cur_omax = int(re.search(f'omax(\d+)', grid_file).group(1))
                    cur_sensitivity = False if re.search(f'without', grid_file) else True
                    if cur_sensitivity:
                        cur_max_sensitivity = int(re.search('sens(\d+)', grid_file).group(1))
                        cur_min_subgraph_size = int(re.search('graphsize(\d+)', grid_file).group(1))
                    else:
                        cur_max_sensitivity = -1
                        cur_min_subgraph_size = -1
                    self._get_iteration_characteristcs(subxpat, imax=cur_imax, omax=cur_omax, sensitivity=cur_sensitivity,
                                                       max_sensitivity=cur_max_sensitivity, min_subgraph_size=cur_min_subgraph_size)

        subxpat.partitioning_dict = partitioning_dict

    def _grid_file_is_valid(self, subxpat: Result, grid_file: str, imax: int = 3, omax: int = 2, sensitivity: bool = False,
                            max_sensitivity: int = 100, min_subgraph_size: int = 10):
        valid = False
        if re.search(f'imax{imax}', grid_file) and re.search(f'omax{omax}', grid_file):
            if sensitivity:
                if re.search(f'without', grid_file):
                    valid = True
            else:
                if re.search(f'sens{max()}', grid_file) and re.search(f'subgraphsize{min_subgraph_size}', grid_file):
                    valid = True
        return valid

    def _get_iteration_characteristcs(self, subxpat: Result, imax: int = 3, omax: int = 2, sensitivity: bool = False,
                                      max_sensitivity: int = 100, min_subgraph_size: int = 10):

        iterations = self._get_num_iterations()
        area_iteration_dict = {}
        power_iteration_dict = {}
        delay_iteration_dict = {}
        if iterations == -1:
            print(Fore.RED + f'ERROR!!! number of iterations is -1 for these results!' + Style.RESET_ALL)
            exit(1)

        folder, _ = OUTPUT_PATH['report']
        for grid_file in subxpat.grid_files.keys():

            if grid_file:
                error = subxpat.grid_files[grid_file]
                cur_area_list = [float('inf')] * iterations
                cur_power_list = [float('inf')] * iterations
                cur_delay_list = [float('inf')] * iterations
                with open(f'{folder}/{grid_file}', 'r') as gf:
                    csvreader = csv.reader(gf)
                    for line in csvreader:
                        if not re.search('iterations', line[0]) and not re.search('cell', line[0]):
                            for iteration, column in enumerate(line):
                                if not re.search('\d+X\d+', column):
                                    result = column.strip().replace('(', '').replace(')', '').split(',')
                                    if re.search('SAT', result[0]) and not re.search('UNSAT', result[0]):
                                        cur_area = float(result[2])
                                        cur_power = float(result[4])
                                        cur_delay = float(result[3])

                                        if cur_area < cur_area_list[iteration - 1]:
                                            cur_area_list[iteration - 1] = cur_area
                                            cur_power_list[iteration - 1] = cur_power
                                            cur_delay_list[iteration - 1] = cur_delay
                area_iteration_dict[error] = cur_area_list
                power_iteration_dict[error] = cur_power_list
                delay_iteration_dict[error] = cur_delay_list

                subxpat.area_iteration_dict = area_iteration_dict
                subxpat.power_iteration_dict = power_iteration_dict
                subxpat.delay_iteration_dict = delay_iteration_dict

    def __repr__(self):
        return f'An object of class Stats:\n' \
               f'{self.exact_name = }\n' \
               f'{self.approximate_name = }\n' \
               f'{self.lpp = }\n' \
               f'{self.ppo = }\n' \
               f'{self.et = }\n' \
               f'{self.grid = }\n'


class Result:
    def __init__(self,
                 specs: Specifications,
                 benchname: str,
                 toolname: str,
                 mode: int = 1,
                 imax: int = 0,
                 omax: int = 0,
                 subgraphsize: int = 5,
                 ) -> None:
        self.__tool = str(toolname)
        self.specs = specs

        if self.tool_name == sxpatconfig.MECALS or self.tool_name == sxpatconfig.SUBXPAT or self.tool_name == sxpatconfig.XPAT or self.tool_name == sxpatconfig.SHARED_SUBXPAT or self.tool_name == sxpatconfig.SHARED_XPAT:
            if benchname in list(sxpatconfig.BENCH_DICT.keys()):
                self.__benchmark = sxpatconfig.BENCH_DICT[benchname]
            else:
                self.__benchmark = benchname
        elif self.tool_name == sxpatconfig.MUSCAT:
            if benchname in list(sxpatconfig.BENCH_DICT.keys()):
                self.__benchmark = benchname
            elif benchname in list(sxpatconfig.BENCH_DICT.values()):
                for key in sxpatconfig.BENCH_DICT.keys():
                    if sxpatconfig.BENCH_DICT[key] == benchname:
                        self.__benchmark = key
                        break
            else:
                self.__benchmark = benchname

        if self.tool_name == sxpatconfig.SUBXPAT or self.tool_name == sxpatconfig.SHARED_SUBXPAT:
            self.__mode = mode
            if self.extraction_mode == 1:
                self.__imax = imax
                self.__omax = omax
            elif self.extraction_mode == 2:
                print(Fore.RED + f'Warning! mode variable 2 is not correct! Not collecting subxpat results!' + Style.RESET_ALL)
            elif self.extraction_mode == 3:
                self.__subgraphsize = subgraphsize
            else:
                print(Fore.RED + f'Warning! mode variable was not correct! Not collecting subxpat results!' + Style.RESET_ALL)

            self.__error_array: list = self.extract_subxpat_error()
            self.__grid_files = self.get_grid_files()

            if len(self.grid_files) == 0:
                self.__status: bool = False
            else:

                self.__status: bool = True
                self.__area_dict: dict = None
                self.__power_dict: dict = None
                self.__delay_dict: dict = None
                self.__runtime_dict: dict = None
                self.extract_subxpat_characteristics()

                self.__exact_area = float(-1)
                self.__exact_power = float(-1)
                self.__exact_delay = float(-1)

                self.__area_iteration_dict: dict = {}
                self.__power_iteration_dict: dict = {}
                self.__delay_iteration_dict: dict = {}

                self.__partitioning_dict: List[bool, int, int, int, int] = {}

        elif self.tool_name == sxpatconfig.MECALS:
            self.__verilog_files = self.get_verilog_files()
            if len(self.verilog_files) == 0:
                self.__status: bool = False
            else:
                self.clean()
                self.__status: bool = True
                self.et_str = self.get_et_str()
                self.__synthesized_files = self.synthesize()

                self.__error_array: list = self.extract_error()

                self.__area_dict: dict = self.extract_area()

                self.__power_dict: dict = self.extract_power()

                self.__delay_dict: dict = self.extract_delay()

                self.__exact_area = float(-1)
                self.__exact_power = float(-1)
                self.__exact_delay = float(-1)

                self.clean()

                self.__area_iteration_dict: dict = {}
                self.__power_iteration_dict: dict = {}
                self.__delay_iteration_dict: dict = {}

        elif self.tool_name == sxpatconfig.XPAT or self.tool_name == sxpatconfig.SHARED_XPAT:
            self.__error_array: list = self.extract_subxpat_error()
            self.__grid_files = self.get_grid_files()

            if len(self.grid_files) == 0:
                self.__status: bool = False
            else:

                self.__status: bool = True
                self.__area_dict: dict = None
                self.__power_dict: dict = None
                self.__delay_dict: dict = None
                self.__runtime_dict: dict = None
                self.extract_subxpat_characteristics()

                self.__exact_area = float(-1)
                self.__exact_power = float(-1)
                self.__exact_delay = float(-1)

                self.__area_iteration_dict: dict = {}
                self.__power_iteration_dict: dict = {}
                self.__delay_iteration_dict: dict = {}

                self.__partitioning_dict: List[bool, int, int, int, int] = {}

        elif self.tool_name == sxpatconfig.MUSCAT or self.tool_name == sxpatconfig.XPAT:
            self.__et_str = self.get_et_str()
            self.__verilog_files = self.get_verilog_files()
            self.__pareto_files = self.get_pareto_files()
            if len(self.verilog_files) == 0 and len(self.pareto_files) == 0:
                self.__status: bool = False

            elif len(self.pareto_files) != 0:
                self.__status: bool = True
                self.__verilog_files = self.pareto_files.values()
                self.__error_array: list = self.extract_error()
                self.__pareto_files: dict = {}
                self.__synthesized_files: dict = {}
                self.__area_dict: dict = self.extract_area()

                self.__delay_dict: dict = self.extract_delay()
                self.__power_dict: dict = self.extract_power()

                self.__exact_area = float(-1)
                self.__exact_power = float(-1)
                self.__exact_delay = float(-1)
                self.clean()

            elif len(self.pareto_files) == 0:
                self.__status: bool = True
                self.__error_array: list = self.extract_error()

                self.__pareto_files: dict = {}
                self.__synthesized_files: dict = {}
                self.__area_dict: dict = self.extract_area()

                self.__delay_dict: dict = self.extract_delay()
                self.__power_dict: dict = self.extract_power()

                self.__exact_area = float(-1)
                self.__exact_power = float(-1)
                self.__exact_delay = float(-1)
                self.export_pareto_files()
                self.clean()

    def __repr__(self):
        return f"An object of <class package.Result>\n" \
               f"{self.tool_name    = }\n" \
               f"{self.benchmark = }\n" \
               f"{self.exact_area = }\n" \
               f"{self.exact_power = }\n" \
               f"{self.exact_delay = }\n" \
               f"{self.error_array = }\n" \
               f"{self.area_dict = }\n" \
               f"{self.power_dict = }\n" \
               f"{self.delay_dict = }"

    @property
    def subgraphsize(self):
        return self.__subgraphsize

    @property
    def mode(self):
        return self.__mode

    @property
    def imax(self):
        return self.__imax

    @property
    def omax(self):
        return self.__omax

    @property
    def pareto_files(self):
        return self.__pareto_files

    @pareto_files.setter
    def pareto_files(self, this_files):
        self.__pareto_files = this_files

    @property
    def partitioning_dict(self):
        return self.__partitioning_dict

    @partitioning_dict.setter
    def partitioning_dict(self, this_dict):
        self.__partitioning_dict = this_dict

    @property
    def area_iteration_dict(self):
        return self.__area_iteration_dict

    @area_iteration_dict.setter
    def area_iteration_dict(self, this_dict):
        self.__area_iteration_dict = this_dict

    @property
    def power_iteration_dict(self):
        return self.__power_iteration_dict

    @power_iteration_dict.setter
    def power_iteration_dict(self, this_dict):
        self.__power_iteration_dict = this_dict

    @property
    def delay_iteration_dict(self):
        return self.__delay_iteration_dict

    @delay_iteration_dict.setter
    def delay_iteration_dict(self, this_dict):
        self.__delay_iteration_dict = this_dict

    @property
    def grid_files(self):
        return self.__grid_files

    @property
    def exact_power(self):
        return self.__exact_power

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, this_status):
        self.__status = this_status

    @property
    def exact_area(self):
        return self.__exact_area

    @property
    def exact_delay(self):
        return self.__exact_delay

    @property
    def verilog_files(self):
        return self.__verilog_files

    @verilog_files.setter
    def verilog_files(self, this_verilog_files):
        self.__verilog_files = this_verilog_files

    @property
    def synthesized_files(self):
        return self.__synthesized_files

    @synthesized_files.setter
    def synthesized_files(self, this_syn_files):
        self.__synthesized_files = this_syn_files

    @property
    def benchmark(self):
        return self.__benchmark

    @benchmark.setter
    def benchmark(self, this_benchmark):
        self.__benchmark = this_benchmark

    @property
    def tool_name(self):
        return self.__tool

    @tool_name.setter
    def tool_name(self, this_tool_name):
        self.__tool = this_tool_name

    @property
    def area_dict(self):
        return self.__area_dict

    @area_dict.setter
    def area_dict(self, this_dict):
        self.__area_dict = this_dict

    @property
    def power_dict(self):
        return self.__power_dict

    @power_dict.setter
    def power_dict(self, this_dict):
        self.__power_dict = this_dict

    @property
    def error_array(self):
        return self.__error_array

    @property
    def delay_dict(self):
        return self.__delay_dict

    @delay_dict.setter
    def delay_dict(self, this_dict):
        self.__delay_dict = this_dict

    @property
    def et_str(self):
        return self.__et_str

    @et_str.setter
    def et_str(self, this_et_str):
        self.__et_str = this_et_str

    def get_pareto_files(self):
        pareto_files: dict = {}
        folder = f'experiments/{self.tool_name}/pareto_ver/{self.benchmark}'
        if os.path.exists(folder):
            all_files = [f for f in os.listdir(folder)]
            for file in all_files:
                if file.endswith('.v') and re.search(self.benchmark, file) and re.search(self.et_str, file):
                    pattern = f'{self.et_str}(\d+)'
                    cur_et = int(re.search(pattern, file).group(1))

                    pareto_files[cur_et] = file
            return pareto_files
        else:
            return {}

    def export_pareto_files(self):
        folder = f'experiments/{self.tool_name}/pareto_ver/{self.benchmark}'
        os.makedirs(folder, exist_ok=True)

        existing_files = [f for f in os.listdir(folder)]
        for error in self.pareto_files.keys():
            ver_path = self.pareto_files[error]
            ver_file = ver_path.split('/')[-1]
            if ver_file not in existing_files:
                copy(ver_path, folder)

    def clean(self):
        folder = f'experiments/{self.tool_name}/ver/{self.benchmark}'
        all_files = [f for f in os.listdir(folder)]

        for file in all_files:
            if re.search('_syn', file) or file.endswith('script'):
                os.remove(f'{folder}/{file}')

    def get_et_str(self):
        if self.tool_name == sxpatconfig.XPAT:
            self.et_str = 'et'
        elif self.tool_name == sxpatconfig.MUSCAT:
            self.et_str = 'wc'
        elif self.tool_name == sxpatconfig.MECALS:
            self.et_str = 'wce'
        return self.et_str

    def get_verilog_files(self):
        folder = f'experiments/{self.tool_name}/ver'
        all_folders = [f for f in os.listdir(folder)]
        benchmark_folder = None
        for fold in all_folders:
            if re.search(self.benchmark, fold):
                benchmark_folder = fold
        if benchmark_folder:
            all_verilogs = [f for f in os.listdir(f'{folder}/{benchmark_folder}/')]
        else:
            print(Fore.RED + f'ERROR!!! for tool {self.tool_name} there is no benchmark folder for benchmark {self.benchmark}' + Style.RESET_ALL)
            return []

        benchmark_verilogs = []
        for verilog in all_verilogs:
            if re.search(self.benchmark, verilog) and verilog.endswith('.v') and not re.search('_syn', verilog):
                benchmark_verilogs.append(f'{verilog}')
        return benchmark_verilogs

    def synthesize(self):
        if self.tool_name == sxpatconfig.MECALS:
            return self.__synthesize_mecals()
        elif self.tool_name == sxpatconfig.MUSCAT or self.tool_name == sxpatconfig.XPAT:
            return self.__synthesize_muscat()

    def __synthesize_mecals(self):
        syn_files: dict = {}
        for ver_file in self.verilog_files:
            design_in_path = f'experiments/{self.tool_name}/ver/{self.benchmark}/{ver_file}'
            design_out_path = f'{design_in_path[:-2]}_syn.v'
            yosys_command = f"read_verilog {design_in_path};\n" \
                            f"synth -flatten;\n" \
                            f"opt;\n" \
                            f"opt_clean -purge;\n" \
                            f"abc -liberty {self.specs.path.synthesis.cell_library} -script {self.specs.path.synthesis.abc_script};\n" \
                            f"write_verilog -noattr {design_out_path}"

            process = subprocess.run([YOSYS, '-p', yosys_command], stdout=PIPE, stderr=PIPE)
            if process.stderr:
                raise Exception(Fore.RED + f'Yosys ERROR!!! in file {design_in_path}\n {process.stderr.decode()}' + Style.RESET_ALL)

            cur_et = int(re.search(f'{self.et_str}(\d+)', design_out_path).group(1))
            syn_files[cur_et] = design_out_path

        return syn_files

    def __synthesize_muscat(self):
        syn_files: dict = {}
        for error in self.pareto_files.keys():
            design_in_path = self.pareto_files[error]
            design_out_path = f'{design_in_path[:-2]}_syn.v'
            yosys_command = f"read_verilog {design_in_path};\n" \
                            f"synth -flatten;\n" \
                            f"opt;\n" \
                            f"opt_clean -purge;\n" \
                            f"abc -liberty {self.specs.path.synthesis.cell_library} -script {self.specs.path.synthesis.abc_script};\n" \
                            f"write_verilog -noattr {design_out_path}"

            process = subprocess.run([YOSYS, '-p', yosys_command], stdout=PIPE, stderr=PIPE)
            if process.stderr:
                raise Exception(Fore.RED + f'Yosys ERROR!!! in file {design_in_path}\n {process.stderr.decode()}' + Style.RESET_ALL)

            cur_et = int(re.search(f'{self.et_str}(\d+)', design_out_path).group(1))
            syn_files[cur_et] = design_out_path

        return syn_files

    def extract_error(self):
        et_array = []

        for file in self.verilog_files:

            pattern = f'{self.et_str}(\d+)'
            if re.search(pattern, file):
                cur_et = int(re.search(f'{self.et_str}(\d+)', file).group(1))
                et_array.append(cur_et)

        et_array = list(set(et_array))
        et_array.sort()
        return et_array

    def extract_area(self):
        if self.tool_name == sxpatconfig.MECALS:
            return self._extract_area_mecals()
        elif self.tool_name == sxpatconfig.MUSCAT or self.tool_name == sxpatconfig.XPAT:
            return self._extract_area_muscat()

    def _extract_area_mecals(self):
        area_dict: dict = {}
        i = 0
        for error in self.error_array:
            for key in self.synthesized_files.keys():
                if error == key:
                    i += 1
                    printProgressBar(i, len(self.verilog_files), prefix=f'Synthesizing ({self.tool_name}):', suffix='Complete', length=50)
                    syn_file = self.synthesized_files[error]
                    yosys_command = f"read_liberty {self.specs.path.synthesis.cell_library}\n" \
                                    f"read_verilog {syn_file};\n" \
                                    f"synth -flatten;\n" \
                                    f"opt;\n" \
                                    f"opt_clean -purge;\n" \
                                    f"abc -liberty {self.specs.path.synthesis.cell_library} -script {self.specs.path.synthesis.abc_script};\n" \
                                    f"stat -liberty {self.specs.path.synthesis.cell_library};\n"

                    process = subprocess.run([YOSYS, '-p', yosys_command], stdout=PIPE, stderr=PIPE)
                    if process.stderr:
                        raise Exception(Fore.RED + f'Yosys ERROR!!! in file {syn_file}\n {process.stderr.decode()}' + Style.RESET_ALL)
                    else:

                        if re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()):
                            area = re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()).group(1)

                        elif re.search(r"Don't call ABC as there is nothing to map", process.stdout.decode()):
                            area = 0
                        else:
                            raise Exception(Fore.RED + 'Yosys ERROR!!!\nNo useful information in the stats log!' + Style.RESET_ALL)
                        area_dict[error] = float(area)
        return area_dict

    def _extract_area_muscat(self):

        i = 0
        area_dict: dict = {}
        for error in self.error_array:
            for ver_file in self.verilog_files:

                if re.search(f'{self.et_str}{error}', ver_file):
                    i += 1
                    printProgressBar(i, len(self.verilog_files), prefix=f'Synthesizing ({self.tool_name}):', suffix='Complete', length=50)
                    ver_file = folder = f'experiments/{self.tool_name}/ver/{self.benchmark}/{ver_file}'
                    yosys_command = f"read_liberty {self.specs.path.synthesis.cell_library}\n" \
                                    f"read_verilog {ver_file};\n" \
                                    f"synth -flatten;\n" \
                                    f"opt;\n" \
                                    f"opt_clean -purge;\n" \
                                    f"abc -liberty {self.specs.path.synthesis.cell_library} -script {self.specs.path.synthesis.abc_script};\n" \
                                    f"stat -liberty {self.specs.path.synthesis.cell_library};\n"

                    process = subprocess.run([YOSYS, '-p', yosys_command], stdout=PIPE, stderr=PIPE)
                    if process.stderr:
                        raise Exception(Fore.RED + f'Yosys ERROR!!! in file {ver_file}\n {process.stderr.decode()}' + Style.RESET_ALL)
                    else:
                        if re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()):
                            area = re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()).group(1)

                        elif re.search(r"Don't call ABC as there is nothing to map", process.stdout.decode()):
                            area = 0
                        else:
                            area = 0
                            # raise Exception(Fore.RED + f'Yosys ERROR!!!\nNo useful information in the stats log! for {ver_file}' + Style.RESET_ALL)

                        area_dict[ver_file] = float(area)

        min_area_dict: Dict = {}
        pareto_file_dict: Dict = {}
        for error in self.error_array:
            min_area = float('inf')
            min_ver = f''
            for ver_file in area_dict.keys():
                if re.search(f'{self.et_str}{error}', ver_file):
                    if area_dict[ver_file] < min_area:
                        min_area = area_dict[ver_file]
                        min_ver = ver_file

            min_area_dict[error] = min_area
            pareto_file_dict[error] = min_ver

        self.pareto_files = pareto_file_dict
        self.synthesized_files = self.synthesize()

        return min_area_dict

    def extract_power(self):
        if self.tool_name == sxpatconfig.MECALS:
            return self._extract_power_mecals()
        elif self.tool_name == sxpatconfig.MUSCAT or self.tool_name == sxpatconfig.XPAT:
            return self._extract_power_muscat()

    def _extract_power_mecals(self):

        power_dict: dict = {}
        for error in self.error_array:
            for key in self.synthesized_files.keys():
                if error == key:
                    syn_file = self.synthesized_files[error]
                    power_script = f'{syn_file[:-2]}_for_power.script'
                    module_name = self.extract_module_name(syn_file)
                    sta_command = f"read_liberty {self.specs.path.synthesis.cell_library}\n" \
                                  f"read_verilog {syn_file}\n" \
                                  f"link_design {module_name}\n" \
                                  f"create_clock -name clk -period 1\n" \
                                  f"set_input_delay -clock clk 0 [all_inputs]\n" \
                                  f"set_output_delay -clock clk 0 [all_outputs]\n" \
                                  f"report_checks\n" \
                                  f"report_power -digits 12\n" \
                                  f"exit"
                    with open(power_script, 'w') as ds:
                        ds.writelines(sta_command)
                    process = subprocess.run([sxpatconfig.OPENSTA, power_script], stdout=PIPE, stderr=PIPE)
                    if process.stderr:
                        raise Exception(Fore.RED + f'Yosys ERROR!!!\n {process.stderr.decode()}' + Style.RESET_ALL)
                    else:
                        pattern = r"Total\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+[^0-9]*\d+)\s+"
                        if re.search(pattern, process.stdout.decode()):
                            total_power_str = re.search(pattern, process.stdout.decode()).group(4)

                            if re.search(r'e[^0-9]*(\d+)', total_power_str):
                                total_power = float(re.search(r'(\d+.\d+)e[^0-9]*\d+', total_power_str).group(1))
                                sign = (re.search(r'e([^0-9]*)(\d+)', total_power_str).group(1))
                                if sign == '-':
                                    sign = -1
                                else:
                                    sign = +1
                                exponant = int(re.search(r'e([^0-9]*)(\d+)', total_power_str).group(2))
                                total_power = total_power * (10 ** (sign * exponant))
                            else:
                                total_power = total_power_str

                            power_dict[error] = float(total_power)
                        else:
                            print(Fore.YELLOW + f'Warning!!! No power was found!' + Style.RESET_ALL)
                            power_dict[error] = 0
        return power_dict

    def _extract_power_muscat(self):
        power_dict: dict = {}

        for error in self.synthesized_files.keys():

            ver_file = self.synthesized_files[error]

            delay_script = f'{ver_file[:-2]}_for_delay.script'
            module_name = self.extract_module_name(ver_file)
            sta_command = f"read_liberty {self.specs.path.synthesis.cell_library}\n" \
                          f"read_verilog {ver_file}\n" \
                          f"link_design {module_name}\n" \
                          f"create_clock -name clk -period 1\n" \
                          f"set_input_delay -clock clk 0 [all_inputs]\n" \
                          f"set_output_delay -clock clk 0 [all_outputs]\n" \
                          f"report_checks\n" \
                          f"report_power -digits 12\n" \
                          f"exit"
            with open(delay_script, 'w') as ds:
                ds.writelines(sta_command)
            process = subprocess.run([sxpatconfig.OPENSTA, delay_script], stdout=PIPE, stderr=PIPE)
            if process.stderr:
                raise Exception(
                    Fore.RED + f'Yosys ERROR!!! in file {ver_file} \n {process.stderr.decode()}' + Style.RESET_ALL)
            pattern = r"Total\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+[^0-9]*\d+)\s+"
            if re.search(pattern, process.stdout.decode()):
                total_power_str = re.search(pattern, process.stdout.decode()).group(4)

                if re.search(r'e[^0-9]*(\d+)', total_power_str):
                    total_power = float(re.search(r'(\d+.\d+)e[^0-9]*\d+', total_power_str).group(1))
                    sign = (re.search(r'e([^0-9]*)(\d+)', total_power_str).group(1))
                    if sign == '-':
                        sign = -1
                    else:
                        sign = +1
                    exponant = int(re.search(r'e([^0-9]*)(\d+)', total_power_str).group(2))
                    total_power = total_power * (10 ** (sign * exponant))
                else:
                    total_power = total_power_str

                power_dict[error] = float(total_power)
            else:
                print(Fore.YELLOW + f'Warning!!! No power was found!' + Style.RESET_ALL)
                power_dict[error] = 0

        return power_dict

    def extract_delay(self):
        if self.tool_name == sxpatconfig.MECALS:
            return self._extract_delay_mecals()
        elif self.tool_name == sxpatconfig.MUSCAT or self.tool_name == sxpatconfig.XPAT:
            return self._extract_delay_muscat()

    def _extract_delay_mecals(self):
        delay_dict: dict = {}
        for error in self.error_array:
            for key in self.synthesized_files.keys():
                if error == key:

                    syn_file = self.synthesized_files[error]
                    delay_script = f'{syn_file[:-2]}_for_delay.script'
                    module_name = self.extract_module_name(syn_file)
                    sta_command = f"read_liberty {self.specs.path.synthesis.cell_library}\n" \
                                  f"read_verilog {syn_file}\n" \
                                  f"link_design {module_name}\n" \
                                  f"create_clock -name clk -period 1\n" \
                                  f"set_input_delay -clock clk 0 [all_inputs]\n" \
                                  f"set_output_delay -clock clk 0 [all_outputs]\n" \
                                  f"report_checks -digits 6\n" \
                                  f"exit"
                    with open(delay_script, 'w') as ds:
                        ds.writelines(sta_command)
                    process = subprocess.run([sxpatconfig.OPENSTA, delay_script], stdout=PIPE, stderr=PIPE)
                    if process.stderr:
                        raise Exception(Fore.RED + f'Yosys ERROR!!! in file {syn_file} \n {process.stderr.decode()}' + Style.RESET_ALL)

                    else:
                        if re.search('(\d+.\d+).*data arrival time', process.stdout.decode()):
                            time = re.search('(\d+.\d+).*data arrival time', process.stdout.decode()).group(1)
                            delay_dict[error] = float(time)
                        else:
                            print(Fore.YELLOW + f'Warning!!! in file {syn_file} No delay was found!' + Style.RESET_ALL)
                            delay_dict[error] = 0
        return delay_dict

    def _extract_delay_muscat(self):
        delay_dict: dict = {}

        for error in self.synthesized_files.keys():

            ver_file = self.synthesized_files[error]

            delay_script = f'{ver_file[:-2]}_for_delay.script'
            module_name = self.extract_module_name(ver_file)
            sta_command = f"read_liberty {self.specs.path.synthesis.cell_library}\n" \
                          f"read_verilog {ver_file}\n" \
                          f"link_design {module_name}\n" \
                          f"create_clock -name clk -period 1\n" \
                          f"set_input_delay -clock clk 0 [all_inputs]\n" \
                          f"set_output_delay -clock clk 0 [all_outputs]\n" \
                          f"report_checks -digits 6\n" \
                          f"exit"
            with open(delay_script, 'w') as ds:
                ds.writelines(sta_command)
            process = subprocess.run([sxpatconfig.OPENSTA, delay_script], stdout=PIPE, stderr=PIPE)
            if process.stderr:
                raise Exception(Fore.RED + f'Yosys ERROR!!! in file {ver_file} \n {process.stderr.decode()}' + Style.RESET_ALL)

            else:
                if re.search('(\d+.\d+).*data arrival time', process.stdout.decode()):
                    time = re.search('(\d+.\d+).*data arrival time', process.stdout.decode()).group(1)
                    delay_dict[error] = float(time)
                else:
                    print(Fore.YELLOW + f'Warning!!! in file {ver_file} No delay was found!' + Style.RESET_ALL)
                    delay_dict[error] = 0

        return delay_dict

    def extract_module_name(self, this_path: str = None):

        with open(this_path, 'r') as dp:
            contents = dp.readlines()
            for line in contents:
                if re.search(r'module\s+(.*)\(', line):
                    modulename = re.search(r'module\s+(.*)\(', line).group(1)

        return modulename

    def extract_subxpat_error(self):
        n_o = int(re.search(f'.*o(\d+).*', self.benchmark).group(1))
        max_error = 2 ** (n_o - 1)
        if max_error <= 8:
            et_array = list(range(1, max_error + 1))
        else:
            step = max_error // 8
            et_array = list(range(step, max_error + 1, step))
        return et_array

    def get_grid_files(self):
        grid_files: dict = {}
        all_csv_files = [f for f in os.listdir(OUTPUT_PATH['report'][0])]
        for et in self.error_array:
            for csv_file in all_csv_files:
                if re.search(f'{self.tool_name}', csv_file):
                    if self.tool_name == sxpatconfig.SHARED_SUBXPAT:
                        if self.extraction_mode == 1:
                            imax = f'imax{self.imax}'
                            omax = f'omax{self.omax}'
                            if (csv_file.startswith('grid_') and csv_file.endswith('.csv') and re.search(self.benchmark, csv_file)
                                    and re.search(imax, csv_file) and re.search(omax, csv_file)):
                                cur_et = int(re.search('et(\d+)', csv_file).group(1))
                                if cur_et == et:
                                    grid_files[csv_file] = et
                        elif self.extraction_mode == 3:
                            subgraphsize = f'subgraphsize{self.subgraphsize}'
                            if (csv_file.startswith('grid_') and csv_file.endswith('.csv')
                                    and re.search(self.benchmark, csv_file) and re.search(subgraphsize, csv_file)):
                                cur_et = int(re.search('et(\d+)', csv_file).group(1))
                                if cur_et == et:
                                    grid_files[csv_file] = et
                    elif self.tool_name == sxpatconfig.SUBXPAT:
                        if self.extraction_mode == 1:
                            imax = f'imax{self.imax}'
                            omax = f'omax{self.omax}'
                            if (csv_file.startswith('grid_') and csv_file.endswith('.csv') and re.search(self.benchmark, csv_file)
                                    and re.search(imax, csv_file) and re.search(omax, csv_file) and not re.search(sxpatconfig.SHARED_SUBXPAT, csv_file)):
                                cur_et = int(re.search('et(\d+)', csv_file).group(1))
                                if cur_et == et:
                                    grid_files[csv_file] = et
                        elif self.extraction_mode == 3:
                            subgraphsize = f'subgraphsize{self.subgraphsize}'
                            if (csv_file.startswith('grid_') and csv_file.endswith('.csv')
                                    and re.search(self.benchmark, csv_file) and re.search(subgraphsize, csv_file)):
                                cur_et = int(re.search('et(\d+)', csv_file).group(1))
                                if cur_et == et:
                                    grid_files[csv_file] = et
                    elif self.tool_name == sxpatconfig.SHARED_XPAT:
                        if csv_file.startswith('grid_') and csv_file.endswith('.csv') and re.search(self.benchmark, csv_file):
                            cur_et = int(re.search('et(\d+)', csv_file).group(1))
                            if cur_et == et:
                                grid_files[csv_file] = et
                    elif self.tool_name == sxpatconfig.XPAT:
                        if (csv_file.startswith('grid_') and csv_file.endswith('.csv') and re.search(self.benchmark, csv_file)
                                and not re.search(sxpatconfig.SHARED_XPAT, csv_file)):
                            cur_et = int(re.search('et(\d+)', csv_file).group(1))
                            if cur_et == et:
                                grid_files[csv_file] = et

        print(f'{grid_files = }')
        return grid_files

    def extract_subxpat_characteristics(self):
        folder, _ = OUTPUT_PATH['report']

        power_dict = {}
        area_dict = {}
        delay_dict = {}
        cell_dict = {}
        runtime_dict = {}

        for cur_grid_file in self.grid_files.keys():
            cur_et = self.grid_files[cur_grid_file]
            with open(f'{folder}/{cur_grid_file}', 'r') as gf:
                min_area = float('inf')
                min_power = 0
                min_delay = 0
                min_runtime = 0
                min_cell = (0, 0)

                csvreader = csv.reader(gf)
                for line in csvreader:
                    if not re.search('iterations', line[0]) and not re.search('cell', line[0]):
                        for column in line:
                            if not re.search('\d+X\d+', column):
                                result = column.strip().replace('(', '').replace(')', '').split(',')
                                if re.search('UNSAT', result[0]):
                                    cur_status = 'UNSAT'
                                    cur_runtime = float(result[1])
                                    cur_area = -1
                                    cur_delay = -1
                                    cur_power = -1
                                    cur_cell = (int(result[5]), int(result[6]))
                                    min_runtime += cur_runtime

                                elif re.search('Unexplored', result[0]):
                                    cur_status = 'UNEXPLORED'
                                    cur_runtime = -1
                                    cur_area = -1
                                    cur_delay = -1
                                    cur_power = -1
                                    cur_cell = -1

                                elif re.search('unknown', result[0]):
                                    cur_status = 'UNKNOWN'
                                    cur_runtime = float(result[1])
                                    cur_area = -1
                                    cur_delay = -1
                                    cur_power = -1
                                    cur_cell = (int(result[5]), int(result[6]))
                                    min_runtime += cur_runtime
                                else:
                                    cur_status = 'SAT'
                                    cur_runtime = float(result[1])
                                    cur_area = float(result[2])
                                    cur_delay = float(result[3])
                                    cur_power = float(result[4])
                                    cur_cell = (int(result[5]), int(result[6]))

                                    if cur_area < min_area and cur_area != -1:
                                        min_area = cur_area
                                        min_power = cur_power
                                        min_delay = cur_delay
                                        min_cell = cur_cell
                                        min_runtime += cur_runtime
            area_dict[cur_et] = min_area
            power_dict[cur_et] = min_power
            delay_dict[cur_et] = min_delay
            runtime_dict[cur_et] = min_runtime
            cell_dict[cur_et] = min_cell

        self.area_dict = area_dict
        self.power_dict = power_dict
        self.delay_dict = delay_dict
