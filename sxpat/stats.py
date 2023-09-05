import csv
import re
import os
from matplotlib import pyplot as plt
from typing import Tuple, List, Dict
from colorama import Fore, Style
import subprocess
from subprocess import PIPE

from Z3Log.config.config import *
from Z3Log.config.path import *

from sxpat.config import config as sxpatconfig
from sxpat.config import paths as sxpatpaths
from sxpat.templateSpecs import TemplateSpecs


class Model:
    def __init__(self, runtime: float = None, area: float = None, delay: float = None, total_power: float = None,
                 id: int = None, status: str = 'Unexplored', cell: Tuple[int, int] = (-1, -1)):
        self.__runtime = runtime
        self.__area = area
        self.__id = id
        self.__status = status
        self.__cell = cell
        self.__delay = delay
        self.__total_power = total_power


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
               f'{self.runtime = }\n' \
               f'{self.area = }\n' \
               f'{self.id = }\n'


class Cell:
    def __init__(self, spec_obj: TemplateSpecs):
        self.__exact_name: str = spec_obj.exact_benchmark
        self.__approximate_name: str = spec_obj.benchmark_name
        self.__lpp: int = spec_obj.lpp
        self.__ppo: int = spec_obj.ppo
        self.__coordinates: Tuple[int, int] = (spec_obj.lpp, spec_obj.ppo)
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


    def store_model_info(self, this_model_id: int = 0, this_iteration: int = 0,
                         this_area: float = None, this_delay: float = -1, this_total_power: float = -1,
                         this_runtime: float = None,
                         this_status: str = 'SAT',
                         this_cell: Tuple[int, int] = (-1, -1)):
        self.models[this_iteration - 1][this_model_id] = Model(this_runtime, this_area, this_delay, this_total_power,
                                                               this_model_id, this_status, this_cell)

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
        self.__et: int = spec_obj.et
        self.__pap: int = spec_obj.partitioning_percentage
        self.__iterations: int = spec_obj.iterations

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
        self.__et: int = spec_obj.et
        self.__max_sensitivity: int = spec_obj.max_sensitivity
        self.__min_subgraph_size: int = spec_obj.min_subgraph_size
        self.__iterations: int = spec_obj.iterations
        self.__grid_name: str = self.get_grid_name()
        self.__grid_path: str = self.get_grid_path()
        self.__imax: int = spec_obj.imax
        self.__omax: int = spec_obj.omax
        self.__grid = Grid(spec_obj)

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

    def get_grid_name(self):
        _, extension = OUTPUT_PATH['report']
        name = f'grid_{self.exact_name}_{self.lpp}X{self.ppo}_et{self.et}_sens{self.max_sensitivity}_graphsize{self.min_subgraph_size}.{extension}'
        return name


    def get_grid_path(self):
        folder, _ = OUTPUT_PATH['report']
        path = f'{folder}/{self.grid_name}'
        return path

    def store_grid(self):
        folder, extension = OUTPUT_PATH['report']

        with open(f'{self.grid_path}',
                  'w') as f:
            csvwriter = csv.writer(f)
            iteration_range = list(range(1, self.iterations + 1))

            header = ['iterations']
            subheader = ['cell']
            for i in iteration_range:
                header.append(str(i))
                subheader.append(('status', 'runtime', 'area', 'delay', 'total_power', 'cell'))
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
                            this_cell = self.grid.cells[lpp][ppo].models[i][0].cell
                            this_delay = self.grid.cells[lpp][ppo].models[i][0].delay
                            this_total_power = self.grid.cells[lpp][ppo].models[i][0].total_power
                            this_row.append((this_status, this_runtime, this_area, this_delay,this_total_power, this_cell))

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
                                    for col_idx in range(1, self.iterations):

                                        this_entry = cols[col_idx]

                                        this_entry = this_entry.strip().replace('(', '').replace(')', '').split(',')

                                        if re.search('SAT', this_entry[0]) and not re.search('UNSAT', this_entry[0]):
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
                                    for col_idx in range(1, self.iterations):

                                        this_entry = cols[col_idx]

                                        this_entry = this_entry.strip().replace('(', '').replace(')', '').split(',')

                                        if re.search('SAT', this_entry[0]) or re.search('UNSAT', this_entry[0]):
                                            cur_runtime += float(this_entry[1])

            runtime_array.append(cur_runtime)
        return runtime_array

    def plot_area(self):
        print(f'plotting area...')
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Area')
        ax.set_title(f'{self.exact_name} area: SubXPAT vs. MUSCAT')
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
        ax.plot(et_list, subxpat_area_list, label='SubXPAT', color='blue', marker='D', markeredgecolor='black',
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
        ax.set_title(f'{self.exact_name} Runtimes: SubXPAT')
        et_list = self.get_et_array()

        subxpat_runtime_list = self.get_subxpat_runtime(et_list)


        ax.plot(et_list, subxpat_runtime_list, label='SubXPAT', color='blue', marker='D', markeredgecolor='black',
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




class Result:
    def __init__(self, benchname: 'str', toolname: 'str') -> None:
        self.__tool = str(toolname)
        if benchname in list(sxpatconfig.BENCH_DICT.keys()):
            self.__benchmark = sxpatconfig.BENCH_DICT[benchname]
        else:
            self.__benchmark = benchname
        self.__verilog_files = self.get_verilog_files()
        self.et_str = self.get_et_str()
        self.__synthesized_files = self.__synthesize()
        self.__error_array: list = self.extract_error()

        self.__area_dict: dict = self.extract_area()
        self.__power_dict: dict = self.extract_power()
        self.__delay_dict: dict = self.extract_delay()

        self.__exact_area = float(-1)
        self.__exact_power = float(-1)
        self.__exact_delay = float(-1)

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
    def exact_power(self):
        return self.__exact_power

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

    @property
    def power_dict(self):
        return self.__power_dict

    @property
    def error_array(self):
        return self.__error_array

    @property
    def delay_dict(self):
        return self.__delay_dict

    @property
    def et_str(self):
        return self.__et_str

    @et_str.setter
    def et_str(self, this_et_str):
        self.__et_str = this_et_str

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
            print(Fore.RED + f'ERROR!!! there is no benchmark folder for benchmark {self.benchmark}' + Style.RESET_ALL)
            exit()

        benchmark_verilogs = []
        for verilog in all_verilogs:
            if re.search(self.benchmark, verilog) and verilog.endswith('.v') and not re.search('_syn', verilog):
                benchmark_verilogs.append(f'{verilog}')
        return benchmark_verilogs

    def __synthesize(self):
        syn_files: dict = {}
        for ver_file in self.verilog_files:
            design_in_path  = f'experiments/{self.tool_name}/ver/{self.benchmark}/{ver_file}'
            design_out_path = f'{design_in_path[:-2]}_syn.v'
            yosys_command = f"read_verilog {design_in_path};\n" \
                            f"synth -flatten;\n" \
                            f"opt;\n" \
                            f"opt_clean -purge;\n" \
                            f"abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH};\n" \
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
            if re.search(f'{self.et_str}(\d+)', file):
                cur_et = int(re.search(f'{self.et_str}(\d+)', file).group(1))
                et_array.append(cur_et)
        et_array.sort()
        return et_array

    def extract_area(self):
        area_dict: dict = {}
        for error in self.synthesized_files.keys():
            syn_file = self.synthesized_files[error]
            yosys_command = f"read_liberty {sxpatconfig.LIB_PATH}\n" \
                            f"read_verilog {syn_file};\n" \
                            f"synth -flatten;\n" \
                            f"opt;\n" \
                            f"opt_clean -purge;\n" \
                            f"abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH};\n" \
                            f"stat -liberty {sxpatconfig.LIB_PATH};\n"

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
                area_dict[error] = area
        return area_dict

    def extract_power(self):
        power_dict: dict = {}
        for error in self.synthesized_files.keys():
            syn_file = self.synthesized_files[error]
            power_script = f'{syn_file[:-2]}_for_power.script'
            module_name = self.extract_module_name(syn_file)
            sta_command = f"read_liberty {sxpatconfig.LIB_PATH}\n" \
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


                    power_dict[error] = total_power
                else:
                    print(Fore.YELLOW + f'Warning!!! No power was found!' + Style.RESET_ALL)
                    power_dict[error] = 0
        return power_dict

    def extract_delay(self):
        delay_dict: dict = {}
        for error in self.synthesized_files.keys():
            syn_file = self.synthesized_files[error]
            delay_script = f'{syn_file[:-2]}_for_delay.script'
            module_name = self.extract_module_name(syn_file)
            sta_command = f"read_liberty {sxpatconfig.LIB_PATH}\n" \
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
            # print(f'{process.stdout.decode() = }')
                if re.search('(\d+.\d+).*data arrival time', process.stdout.decode()):
                    time = re.search('(\d+.\d+).*data arrival time', process.stdout.decode()).group(1)
                    delay_dict[error] = time
                else:
                    print(Fore.YELLOW + f'Warning!!! in file {syn_file} No delay was found!' + Style.RESET_ALL)
                    delay_dict[error] = 0
        return delay_dict



    def extract_module_name(self, this_path: str = None):

        with open(this_path, 'r') as dp:
            contents = dp.readlines()
            for line in contents:
                if re.search(r'module\s+(.*)\(', line):
                    modulename = re.search(r'module\s+(.*)\(', line).group(1)

        return modulename