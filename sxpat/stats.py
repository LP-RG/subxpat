import csv
import re
import os
from matplotlib import pyplot as plt
from typing import Tuple, List, Dict
from colorama import Fore, Style
import subprocess

from Z3Log.config.config import *
from Z3Log.config.path import *

from sxpat.config import config as sxpatconfig
from sxpat.config import paths as sxpatpaths
from sxpat.templateSpecs import TemplateSpecs


class Model:
    def __init__(self, runtime: float = None, area: float = None, id: int = None, status: str = 'Unexplored'):
        self.__runtime = runtime
        self.__area = area
        self.__id = id
        self.__status = status

    @property
    def runtime(self):
        return self.__runtime

    @runtime.setter
    def runtime(self, this_runtime):
        self.__runtime = this_runtime

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

    def __repr__(self):
        return f'An object of class Model:\n' \
               f'{self.runtime = }\n' \
               f'{self.area = }\n' \
               f'{self.id = }\n'


class Cell:
    def __init__(self, spec_obj: TemplateSpecs):
        self.__exact_name: str = spec_obj.exact_benchmark
        self.__approximate_name: str = spec_obj.benchmark_name
        self.__lpp: int = spec_obj.lpp
        self.__ppo: int = spec_obj.pit
        self.__coordinates: Tuple[int, int] = (spec_obj.lpp, spec_obj.pit)
        self.__et: int = spec_obj.et
        self.__pap: int = spec_obj.partitioning_percentage
        self.__iterations: int = spec_obj.iterations
        self.__num_of_models: int = spec_obj.num_of_models
        self.__models = [[Model() for n in range(self.num_of_models)] for i in range(self.iterations)]

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
    def coordinates(self):
        return self.__coordinates

    @property
    def et(self):
        return self.__et

    @property
    def pap(self):
        return self.__pap

    @property
    def iterations(self):
        return self.__iterations

    @iterations.setter
    def iterations(self, this_iterations):
        self.__iterations = this_iterations

    @property
    def num_of_models(self):
        return self.__num_of_models

    @property
    def models(self):
        return self.__models

    def store_model_info(self, this_model_id: int = 0, this_iteration: int = 0, this_area: float = None,
                         this_runtime: float = None,
                         this_status: str = 'SAT'):
        self.models[this_iteration - 1][this_model_id] = Model(this_runtime, this_area, this_model_id, this_status)

    def __repr__(self):
        return f"An object of class Cell:\n" \
               f"{self.exact_name = }\n" \
               f"{self.coordinates = }\n" \
               f"{self.et = }\n" \
               f"{self.models = }"


class Grid:
    def __init__(self, spec_obj: TemplateSpecs):
        self.__exact_name: str = spec_obj.exact_benchmark
        self.__approximate_name: str = spec_obj.benchmark_name
        self.__lpp: int = spec_obj.lpp
        self.__ppo: int = spec_obj.ppo
        self.__pit: int = spec_obj.pit
        self.__et: int = spec_obj.et
        self.__pap: int = spec_obj.partitioning_percentage
        self.__iterations: int = spec_obj.iterations
        if spec_obj.shared:
            self.__cells: List[List[Cell]] = [[Cell(spec_obj) for _ in range(self.pit + 1)] for _ in range(self.lpp + 1)]
        else:
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
    def pit(self):
        return self.__pit

    @property
    def et(self):
        return self.__et

    @property
    def pap(self):
        return self.__pap

    @property
    def iterations(self):
        return self.__iterations

    @iterations.setter
    def iterations(self, this_iterations):
        self.__iterations = this_iterations

    @property
    def cells(self):
        return self.__cells

    def store_cell(self, this_cell: Cell, i: int, j: int):
        self.cells[i][j] = this_cell

    def __repr__(self):
        return f'An object of class Grid: \n' \
               f'{self.cells = }\n'


class Stats:
    def __init__(self, spec_obj: TemplateSpecs):
        """
        stores the stats of an experiment (grid or cell) into an object
        """
        self.__exact_name: str = spec_obj.exact_benchmark
        self.__approximate_name: str = spec_obj.benchmark_name
        self.__lpp: int = spec_obj.lpp
        self.__ppo: int = spec_obj.ppo
        self.__pit: int = spec_obj.pit
        self.__et: int = spec_obj.et
        self.__pap: int = spec_obj.partitioning_percentage
        self.__iterations: int = spec_obj.iterations
        self.__grid = Grid(spec_obj)

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
    def pit(self):
        return self.__pit

    @property
    def et(self):
        return self.__et

    @property
    def pap(self):
        return self.__pap

    @property
    def iterations(self):
        return self.__iterations

    @iterations.setter
    def iterations(self, this_iterations):
        self.__iterations = this_iterations

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
    def num_models(self):
        return self.__number_of_models

    @num_models.setter
    def num_models(self, this_num_models):
        self.__number_of_models = this_num_models

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

    def store_grid(self):
        folder, extension = OUTPUT_PATH['report']

        with open(f'{folder}/grid_{self.exact_name}_{self.lpp}X{self.ppo}_et{self.et}_pap{self.pap}.{extension}',
                  'w') as f:
            csvwriter = csv.writer(f)
            iteration_range = list(range(1, self.iterations + 1))

            header = ['iterations']
            subheader = ['cell']
            for i in iteration_range:
                header.append(str(i))
                subheader.append(('status', 'runtime', 'area'))
            csvwriter.writerow(header)
            csvwriter.writerow(subheader)

            for ppo in range(self.ppo + 1):
                for lpp in range(self.lpp + 1):
                    cell = f'({lpp}X{ppo})'
                    this_row = []
                    for i in range(self.iterations):
                        if ppo == 0 or (lpp == 0 and ppo > 1):
                            continue
                        else:

                            this_area = self.grid.cells[lpp][ppo].models[i][0].area
                            this_status = self.grid.cells[lpp][ppo].models[i][0].status
                            this_runtime = self.grid.cells[lpp][ppo].models[i][0].runtime
                            this_row.append((this_status, this_runtime, this_area))

                    if this_row:
                        row = [cell]
                        for field in this_row:
                            row.append(field)

                        csvwriter.writerow(row)

    def plot_grid(self):
        pass


    def get_et_array(self):
        folder = f'experiments/area/muscat/{self.exact_name}'
        all_areas = [f for f in os.listdir(folder)]
        et_array = []
        for area in all_areas:
            if re.search('.*et(\d+).*', area):
                this_et = int(re.search('.*et(\d+).*', area).group(1))
                et_array.append(this_et)

        return sorted(et_array)

    def get_muscat_area(self, et_array):
        folder = f'experiments/area/muscat/{self.exact_name}'
        all_areas = [f for f in os.listdir(folder)]
        area_array = []
        for et in et_array:
            for area in all_areas:
                if re.search(f'.*et{et}.*', area):
                    with open(f'{folder}/{area}', 'r') as a:
                        this_area = float(a.readline())
                        area_array.append(this_area)

        return area_array

    def get_subxpat_area(self, et_array):
        folder, extension = OUTPUT_PATH['report']
        all_reports = [f for f in os.listdir(folder)]
        area_array = []
        for et in et_array:
            min_area = float('inf')
            for report in all_reports:
                if re.search('grid', report) and re.search(f'{self.exact_name}', report):
                    if re.search(f'.*et{et}.*', report):
                        with open(f'{folder}/{report}', 'r') as f:
                            rows = csv.reader(f)
                            for cols in rows:

                                if re.search('\(\d+X\d+\)', cols[0]):
                                    for col_idx in range(1, self.iterations + 1):

                                        this_entry = cols[col_idx]

                                        this_entry = this_entry.strip().replace('(', '').replace(')', '').split(',')

                                        if re.search(f'{sxpatconfig.SAT}', this_entry[0]) and\
                                                not re.search(sxpatconfig.UNSAT, this_entry[0]) and\
                                                not re.search(sxpatconfig.UNKNOWN, this_entry[0]):
                                            area = float(this_entry[2])

                                            if min_area > area:
                                                min_area = area
            if min_area == float('inf'):
                min_area = -1
            area_array.append(min_area)
        return area_array

    def get_subxpat_runtime(self, et_array):
        folder, extension = OUTPUT_PATH['report']
        all_reports = [f for f in os.listdir(folder)]
        runtime_array = []
        for et in et_array:
            cur_runtime = 0
            for report in all_reports:
                if re.search('grid', report) and re.search(f'{self.exact_name}', report):
                    if re.search(f'.*et{et}.*', report):
                        with open(f'{folder}/{report}', 'r') as f:
                            rows = csv.reader(f)
                            for cols in rows:
                                if re.search('\(\d+X\d+\)', cols[0]):
                                    for col_idx in range(1, self.iterations + 1):

                                        this_entry = cols[col_idx]

                                        this_entry = this_entry.strip().replace('(', '').replace(')', '').split(',')

                                        if re.search(f'{sxpatconfig.SAT}', this_entry[0]) and \
                                                not re.search(sxpatconfig.UNSAT, this_entry[0]) and \
                                                not re.search(sxpatconfig.UNKNOWN, this_entry[0]):
                                            cur_runtime += float(this_entry[1])

            runtime_array.append(cur_runtime)
        return runtime_array

    def plot_area(self):
        print(f'plotting area...')
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Area')
        ax.set_title(f'{self.exact_name} area: SharedLogic vs. XPAT')
        et_list = self.get_et_array()
        muscat_area_list = self.get_muscat_area(et_list)
        subxpat_area_list = self.get_subxpat_area(et_list)


        uncomputed_area = []
        uncomputed_et = []
        for idx, area in enumerate(subxpat_area_list):
            if area == -1:
                uncomputed_area.append(area)
                uncomputed_et.append(et_list[idx])




        ax.plot(et_list, muscat_area_list, label='MUSCAT',color='red', marker='s', markeredgecolor='red',
                markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        ax.plot(et_list, subxpat_area_list, label='SharedLogic', color='blue', marker='D', markeredgecolor='black',
                markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        ax.plot(uncomputed_et, uncomputed_area, label='N/A', color='red', marker='o', markeredgecolor='red',
                markeredgewidth=10, linestyle=None, linewidth=0, markersize = 8)

        plt.xticks(et_list)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_pap{self.pap}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_pap{self.pap}.pdf"
        plt.savefig(figurename_png)
        plt.savefig(figurename_pdf)

    def plot_runtime(self):
        print(f'plotting runtime...')
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Runtime')
        ax.set_title(f'{self.exact_name} Runtimes: SharedLogic vs. XPAT')
        et_list = self.get_et_array()

        subxpat_runtime_list = self.get_subxpat_runtime(et_list)
        print(f'{subxpat_runtime_list= }')

        ax.plot(et_list, subxpat_runtime_list, label='SharedLogic', color='blue', marker='D', markeredgecolor='black',
                markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        plt.xticks(et_list)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/runtimes_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_pap{self.pap}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/runtimes_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_pap{self.pap}.pdf"
        plt.savefig(figurename_png)
        plt.savefig(figurename_pdf)

    def __repr__(self):
        return f'An object of class Stats:\n' \
               f'{self.exact_name = }\n' \
               f'{self.approximate_name = }\n' \
               f'{self.lpp = }\n' \
               f'{self.ppo = }\n' \
               f'{self.et = }\n' \
               f'{self.grid = }\n'
