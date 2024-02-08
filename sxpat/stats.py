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
    def __init__(self,
                 runtime: float = None,
                 area: float = None,
                 delay: float = None,
                 total_power: float = None,
                 id: int = None,
                 status: str = 'Unexplored',
                 cell: Tuple[int, int] = (-1, -1)):
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


class Result:
    def __init__(self, benchname: 'str', toolname: 'str') -> None:
        self.__tool = str(toolname)
        if benchname in list(sxpatconfig.BENCH_DICT.keys()):
            self.__benchmark = sxpatconfig.BENCH_DICT[benchname]
        else:
            self.__benchmark = benchname

        if self.tool_name == sxpatconfig.SUBXPAT:

            self.__error_array: list = self.extract_subxpat_error()
            self.__grid_files = self.get_grid_files()

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

        else:
            self.__verilog_files = self.get_verilog_files()
            if len(self.verilog_files) == 0:
                self.__status: bool = False
            else:
                self.__status: bool = True
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

                self.__area_iteration_dict: dict = {}
                self.__power_iteration_dict: dict = {}
                self.__delay_iteration_dict: dict = {}

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

    def __synthesize(self):
        syn_files: dict = {}
        for ver_file in self.verilog_files:
            design_in_path = f'experiments/{self.tool_name}/ver/{self.benchmark}/{ver_file}'
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
        for error in self.error_array:
            for key in self.synthesized_files.keys():
                if error == key:
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
                        area_dict[error] = float(area)
        return area_dict

    def extract_power(self):
        power_dict: dict = {}
        for error in self.error_array:
            for key in self.synthesized_files.keys():
                if error == key:
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

                            power_dict[error] = float(total_power)
                        else:
                            print(Fore.YELLOW + f'Warning!!! No power was found!' + Style.RESET_ALL)
                            power_dict[error] = 0
        return power_dict

    def extract_delay(self):
        delay_dict: dict = {}
        for error in self.error_array:
            for key in self.synthesized_files.keys():
                if error == key:

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
                            delay_dict[error] = float(time)
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
                if csv_file.startswith('grid_') and csv_file.endswith('.csv') and re.search(self.benchmark, csv_file):
                    cur_et = int(re.search('et(\d+)', csv_file).group(1))
                    if cur_et == et:
                        grid_files[csv_file] = et

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
        self.__imax: int = spec_obj.imax
        self.__omax: int = spec_obj.omax
        self.__grid_name: str = self.get_grid_name()
        self.__grid_path: str = self.get_grid_path()
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
        if self.max_sensitivity == -1:
            name = f'grid_{self.exact_name}_{self.lpp}X{self.ppo}_et{self.et}_imax{self.imax}_omax{self.omax}_without_sensitivity.{extension}'
        else:
            name = f'grid_{self.exact_name}_{self.lpp}X{self.ppo}_et{self.et}_imax{self.imax}_omax{self.omax}_sens{self.max_sensitivity}_graphsize{self.min_subgraph_size}.{extension}'
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
                            this_row.append((this_status, this_runtime, this_area, this_delay, this_total_power, this_cell))

                    if this_row:
                        row = [cell]
                        for field in this_row:
                            row.append(field)

                        csvwriter.writerow(row)

    def gather_results(self):
        mecals = Result(self.exact_name, sxpatconfig.MECALS)
        muscat = Result(self.exact_name, sxpatconfig.MUSCAT)
        xpat = Result(self.exact_name, sxpatconfig.XPAT)
        subxpat = Result(self.exact_name, sxpatconfig.SUBXPAT)
        self.plot_area(subxpat=subxpat,
                       xpat=xpat,
                       mecals=mecals,
                       muscat=muscat)
        self.plot_power(subxpat=subxpat,
                        xpat=xpat,
                        mecals=mecals,
                        muscat=muscat)
        self.plot_delay(subxpat=subxpat,
                        xpat=xpat,
                        mecals=mecals,
                        muscat=muscat)
        self.plot_iterations(sxpatconfig.AREA)

    def plot_area(self, subxpat: Result, xpat: Result, mecals: Result, muscat: Result):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Area')
        ax.set_title(f'{self.exact_name} Area comparison', fontsize=30)

        et_list = subxpat.error_array

        if muscat.status:
            ax.plot(et_list, muscat.area_dict.values(), label='MUSCAT', color='red', marker='s', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(et_list, mecals.area_dict.values(), label='MECALS', color='black', marker='s', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(et_list, xpat.area_dict.values(), label='XPAT', color='green', marker='D', markeredgecolor='black',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        ax.plot(et_list, subxpat.area_dict.values(), label='SubXPAT', color='blue', marker='D', markeredgecolor='black',
                markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        # ax.plot(uncomputed_et, uncomputed_area, label='N/A', color='red', marker='o', markeredgecolor='red',
        #         markeredgewidth=10, linestyle=None, linewidth=0, markersize=8)
        #
        plt.xticks(et_list)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_sens{self.max_sensitivity}_subgraphsize{self.min_subgraph_size}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_sens{self.max_sensitivity}_subgraphsize{self.min_subgraph_size}.pdf"
        plt.savefig(figurename_png)
        plt.savefig(figurename_pdf)

    def plot_power(self, subxpat: Result, xpat: Result, mecals: Result, muscat: Result):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Area')
        ax.set_title(f'{self.exact_name} Power comparison', fontsize=30)

        et_list = subxpat.error_array

        if muscat.status:
            ax.plot(et_list, muscat.power_dict.values(), label='MUSCAT', color='red', marker='s', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(et_list, mecals.power_dict.values(), label='MECALS', color='black', marker='s',
                    markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(et_list, xpat.power_dict.values(), label='XPAT', color='green', marker='D', markeredgecolor='black',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        ax.plot(et_list, subxpat.power_dict.values(), label='SubXPAT', color='blue', marker='D', markeredgecolor='black',
                markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        # ax.plot(uncomputed_et, uncomputed_area, label='N/A', color='red', marker='o', markeredgecolor='red',
        #         markeredgewidth=10, linestyle=None, linewidth=0, markersize=8)
        #
        plt.xticks(et_list)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/power_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_sens{self.max_sensitivity}_subgraphsize{self.min_subgraph_size}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/power_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_sens{self.max_sensitivity}_subgraphsize{self.min_subgraph_size}.pdf"
        plt.savefig(figurename_png)
        plt.savefig(figurename_pdf)

    def plot_delay(self, subxpat: Result, xpat: Result, mecals: Result, muscat: Result):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Area')
        ax.set_title(f'{self.exact_name} Delay comparison', fontsize=30)

        et_list = subxpat.error_array

        if muscat.status:
            ax.plot(et_list, muscat.delay_dict.values(), label='MUSCAT', color='red', marker='s', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(et_list, mecals.delay_dict.values(), label='MECALS', color='black', marker='s',
                    markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(et_list, xpat.delay_dict.values(), label='XPAT', color='green', marker='D', markeredgecolor='black',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        ax.plot(et_list, subxpat.delay_dict.values(), label='SubXPAT', color='blue', marker='D', markeredgecolor='black',
                markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        # ax.plot(uncomputed_et, uncomputed_area, label='N/A', color='red', marker='o', markeredgecolor='red',
        #         markeredgewidth=10, linestyle=None, linewidth=0, markersize=8)
        #
        plt.xticks(et_list)
        plt.legend(loc='best')
        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_sens{self.max_sensitivity}_subgraphsize{self.min_subgraph_size}.png"
        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_sens{self.max_sensitivity}_subgraphsize{self.min_subgraph_size}.pdf"
        plt.savefig(figurename_png)
        plt.savefig(figurename_pdf)

    def plot_pap(self):
        pass

    def plot_pdap(self):
        pass

    def plot_partitioning(self, metric: str = sxpatconfig.AREA):
        subxpat = Result(self.exact_name, sxpatconfig.SUBXPAT)
        self._get_partitioning_characteristics(subxpat)
        # for an error, extract the grid for each partitioning approach

    def plot_iterations(self, metric: str = sxpatconfig.AREA):
        subxpat = Result(self.exact_name, sxpatconfig.SUBXPAT)
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
            figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/{metric}_over_iterations_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_without_sensitivity.png"
            figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/{metric}_over_iterations_{self.exact_name}_{self.lpp}X{self.ppo}_it{self.iterations}_without_sensitivity.pdf"
            plt.savefig(figurename_png)
            plt.savefig(figurename_pdf)
        else:
            print(Fore.RED + f'ERROR!!! no iterations found => iteration_list variable is empty' + Style.RESET_ALL)

    def _get_num_iterations(self):
        subxpat = Result(self.exact_name, sxpatconfig.SUBXPAT)
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
                    print(f'{grid_file = }')
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
                    print(f'{subxpat.area_iteration_dict = }')

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
            exit()

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

                                        if cur_area < cur_area_list[iteration-1]:
                                            cur_area_list[iteration-1] = cur_area
                                            cur_power_list[iteration-1] = cur_power
                                            cur_delay_list[iteration-1] = cur_delay
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
