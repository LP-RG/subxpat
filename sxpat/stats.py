import csv
import re
import os
from matplotlib import pyplot as plt
from typing import Tuple, List, Dict
from colorama import Fore, Style
import subprocess
from subprocess import PIPE
from shutil import copy

from Z3Log.config.config import *
from Z3Log.config.path import *

from sxpat.config import config as sxpatconfig
from sxpat.config import paths as sxpatpaths
from sxpat.templateSpecs import TemplateSpecs

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
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
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

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
               f'{self.status = }' \
               f'{self.runtime = }\n' \
               f'{self.area = }\n' \
               f'{self.total_power = }\n' \
               f'{self.delay = }\n' \
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
    def __init__(self, benchname: 'str', toolname: 'str', mode: int = 1, imax: int = 0, omax: int = 0, subgraphsize: int = 5) -> None:
        self.__tool = str(toolname)

        if self.tool_name == sxpatconfig.MECALS or self.tool_name == sxpatconfig.SUBXPAT or self.tool_name == sxpatconfig.XPAT:
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

        if self.tool_name == sxpatconfig.SUBXPAT:
            self.__mode = mode
            if self.mode == 1:
                self.__imax = imax
                self.__omax = omax
            elif self.mode == 2:
                print(Fore.RED + f'Warning! mode variable 2 is not correct! Not collecting subxpat results!' + Style.RESET_ALL)
            elif self.mode == 3:
                self.__subgraphsize = subgraphsize
            else:
                print(Fore.RED + f'Warning! mode variable was not correct! Not collecting subxpat results!' + Style.RESET_ALL)



            self.__error_array: list = self.extract_subxpat_error()
            self.__grid_files = self.get_grid_files()
            # print(f'{self.grid_files = }')
            # exit()


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
                # print(f'{self.synthesized_files = }')
                self.__delay_dict: dict = self.extract_delay()
                # print(f'{self.synthesized_files = }')

                self.__exact_area = float(-1)
                self.__exact_power = float(-1)
                self.__exact_delay = float(-1)

                self.clean()

                self.__area_iteration_dict: dict = {}
                self.__power_iteration_dict: dict = {}
                self.__delay_iteration_dict: dict = {}

        elif self.tool_name == sxpatconfig.MUSCAT or self.tool_name == sxpatconfig.XPAT:
            self.__et_str = self.get_et_str()
            # print(f'we are here 1')
            self.__verilog_files = self.get_verilog_files()
            # print(f'we are here 2')
            self.__pareto_files = self.get_pareto_files()
            if len(self.verilog_files) == 0 and len(self.pareto_files) == 0:
                self.__status: bool = False
            elif len(self.pareto_files) !=0:

                self.__status: bool = True
                self.__verilog_files = self.pareto_files.values()
                self.__error_array: list = self.extract_error()
                # print(f'{self.pareto_files = }')
                # print(f'{self.verilog_files = }')
                self.__pareto_files: dict = {}
                self.__synthesized_files: dict = {}
                self.__area_dict: dict = self.extract_area()
                # print(f'{self.area_dict = }')

                self.__delay_dict: dict = self.extract_delay()
                self.__power_dict: dict = self.extract_power()
                # print(f'{self.delay_dict = }')
                # print(f'{self.power_dict = }')

                self.__exact_area = float(-1)
                self.__exact_power = float(-1)
                self.__exact_delay = float(-1)
                self.clean()
                # exit()
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
            # print(f'{all_files = }')
            # print(f'{self.et_str = }')
            for file in all_files:
                if file.endswith('.v') and re.search(self.benchmark, file) and re.search(self.et_str, file):
                    pattern = f'{self.et_str}(\d+)'
                    # print(f'{re.search(pattern, file).group(1) = }')
                    # cur_et = re.search(pattern, file).group(1)
                    # cur_et = int(cur_et)
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
        # print(f'we are here')
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

    def __synthesize_muscat(self):
        syn_files: dict = {}
        for error in self.pareto_files.keys():
            design_in_path  = self.pareto_files[error]
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
            # print(f'{cur_et = }')
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
        i=0
        for error in self.error_array:
            for key in self.synthesized_files.keys():
                if error == key:
                    i += 1
                    printProgressBar(i, len(self.verilog_files), prefix=f'Synthesizing ({self.tool_name}):', suffix='Complete', length=50)
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

    def _extract_area_muscat(self):

        i = 0
        area_dict: dict = {}
        for error in self.error_array:
            for ver_file in self.verilog_files:

                if re.search(f'{self.et_str}{error}', ver_file):
                    i += 1
                    printProgressBar(i , len(self.verilog_files), prefix=f'Synthesizing ({self.tool_name}):', suffix='Complete', length=50)
                    ver_file = folder = f'experiments/{self.tool_name}/ver/{self.benchmark}/{ver_file}'
                    yosys_command = f"read_liberty {sxpatconfig.LIB_PATH}\n" \
                                    f"read_verilog {ver_file};\n" \
                                    f"synth -flatten;\n" \
                                    f"opt;\n" \
                                    f"opt_clean -purge;\n" \
                                    f"abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH};\n" \
                                    f"stat -liberty {sxpatconfig.LIB_PATH};\n"

                    process = subprocess.run([YOSYS, '-p', yosys_command], stdout=PIPE, stderr=PIPE)
                    if process.stderr:
                        raise Exception(Fore.RED + f'Yosys ERROR!!! in file {ver_file}\n {process.stderr.decode()}' + Style.RESET_ALL)
                    else:
                        # print(f'--------------------------------------------')
                        # print(process.stdout.decode())
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
        # print(f'{self.error_array = }')
        for error in self.error_array:
            for key in self.synthesized_files.keys():
                # print(f'{key}')
                if error == key:
                    # print(f'{error} == {key}')
                    syn_file = self.synthesized_files[error]
                    # print(f'{syn_file = }')
                    power_script = f'{syn_file[:-2]}_for_power.script'
                    module_name = self.extract_module_name(syn_file)
                    # print(f'{module_name = }')
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
                        # print(f'{process.stdout.decode() = }')
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
            sta_command = f"read_liberty {sxpatconfig.LIB_PATH}\n" \
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

    def _extract_delay_muscat(self):
        delay_dict: dict = {}

        for error in self.synthesized_files.keys():

            ver_file = self.synthesized_files[error]

            delay_script = f'{ver_file[:-2]}_for_delay.script'
            module_name = self.extract_module_name(ver_file)
            sta_command = f"read_liberty {sxpatconfig.LIB_PATH}\n" \
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
                raise Exception(
                    Fore.RED + f'Yosys ERROR!!! in file {ver_file} \n {process.stderr.decode()}' + Style.RESET_ALL)

            else:
                # print(f'{process.stdout.decode() = }')
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

                if self.mode == 1:
                    imax = f'imax{self.imax}'
                    omax = f'omax{self.omax}'
                    if csv_file.startswith('grid_') and csv_file.endswith('.csv') and re.search(self.benchmark,
                                                                                                csv_file) \
                            and re.search(imax, csv_file) and re.search(omax, csv_file):
                        # print(f'{csv_file = }')
                        cur_et = int(re.search('et(\d+)', csv_file).group(1))
                        if cur_et == et:
                            grid_files[csv_file] = et
                elif self.mode == 3:
                    subgraphsize = f'subgraphsize{self.subgraphsize}'
                    if csv_file.startswith('grid_') and csv_file.endswith('.csv') and re.search(self.benchmark,
                                                                                                csv_file) \
                            and re.search(subgraphsize, csv_file):
                        # print(f'{csv_file = }')
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
        if spec_obj.shared:
            self.__ppo: int = spec_obj.pit
        else:
            self.__ppo: int = spec_obj.ppo
        self.__et: int = spec_obj.et
        self.__max_sensitivity: int = spec_obj.max_sensitivity
        self.__min_subgraph_size: int = spec_obj.min_subgraph_size
        self.__iterations: int = spec_obj.iterations
        self.__number_of_models: int = spec_obj.num_of_models
        self.__imax: int = spec_obj.imax
        self.__omax: int = spec_obj.omax
        self.__mode: int = spec_obj.mode
        self.__grid_name: str = self.get_grid_name()
        self.__grid_path: str = self.get_grid_path()
        self.__specs_obj: TemplateSpecs = spec_obj
        self.__grid = Grid(spec_obj)


    @property
    def specs(self):
        return self.__specs_obj

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
        if self.max_sensitivity == -1 and self.mode !=3:
            name = f'grid_{self.exact_name}_{self.lpp}X{self.ppo}_et{self.et}_imax{self.imax}_omax{self.omax}_without_sensitivity.{extension}'
        elif self.mode == 3:
            name = f'grid_{self.exact_name}_{self.lpp}X{self.ppo}_et{self.et}_subgraphsize{self.min_subgraph_size}.{extension}'
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

    def gather_results(self):
        mecals = Result(self.exact_name, sxpatconfig.MECALS)
        xpat = Result(self.exact_name, sxpatconfig.XPAT)
        muscat = Result(self.exact_name, sxpatconfig.MUSCAT)
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

        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=1))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=2))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=3))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=4))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=5))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=10))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=15))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=20))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=25))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=30))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=35))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=40))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=45))
        subxpat.append(Result(self.exact_name, sxpatconfig.SUBXPAT, mode=3, subgraphsize=50))



        #
        self.plot_area(subxpat_list= subxpat,
                  xpat= xpat,
                  mecals= mecals,
                  muscat= muscat,
                  best=True)

        self.plot_area(subxpat_list=subxpat,
                       xpat=xpat,
                       mecals=mecals,
                       muscat=muscat,
                       best=False)
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

    def plot_area(self, subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result, best: bool =  True):
        fig, ax = plt.subplots()
        ax.set_xlabel(f'ET')
        ax.set_ylabel(ylabel=f'Area')
        ax.set_title(f'{self.exact_name} Area comparison', fontsize = 20)



        if muscat.status:
            ax.plot(muscat.error_array, muscat.area_dict.values(), label='MUSCAT', color='red', marker='o', markeredgecolor='red',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if mecals.status:
            ax.plot(mecals.error_array, mecals.area_dict.values(), label='MECALS', color='black', marker='o', markeredgecolor='black',
                    markeredgewidth=5, linestyle='dashed', linewidth=2, markersize=3)
        if xpat.status:
            ax.plot(xpat.error_array, xpat.area_dict.values(), label='XPAT', color='green', marker='D', markeredgecolor='green',
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
                    if subxpat.mode == 1:
                        label = f'SubXPAT_io_best'
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_best.pdf"
                    elif subxpat.mode == 3:
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_best.pdf"
                        label = f'SubXPAT_subgraphsize_best'
            ax.plot(subxpat_list[0].error_array, best_area_dict.values(), label=label, marker='D', markeredgecolor='blue',
            markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)
        else:

            for idx, subxpat in enumerate(subxpat_list):
                if subxpat.status:
                    if subxpat.mode == 1:

                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_io_multiple.pdf"

                        label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                    elif subxpat.mode == 3:

                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/area_{self.exact_name}_subgraph_multiple.pdf"

                        label = f'SubXPAT_subgraphsize{subxpat.subgraphsize}'
                    ax.plot(subxpat.error_array, subxpat.area_dict.values(), label=label,marker='D',
                        markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)

        plt.xticks(muscat.error_array)
        if len(subxpat_list) > 8:
            plt.legend()
            # Put a legend below current axis
            # plt.legend(loc='upper center', bbox_to_anchor=(1.5, 0.5),
            #           fancybox=True, shadow=True, ncol=5)
            # plt.tight_layout()
        else:
            plt.legend(loc='best')



        plt.savefig(figurename_png)
        # plt.savefig(figurename_pdf)

    def plot_power(self, subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result):
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
                if self.mode == 1:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                    label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                elif self.mode == 3:
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

    def plot_delay(self, subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result):
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
                if self.mode == 1:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                    label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                elif self.mode == 3:
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

    def plot_pap(self, subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result):
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
                if self.mode == 1:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                    label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                elif self.mode == 3:
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


    def plot_pdap(self, subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result):
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
                if self.mode == 1:
                    color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                    label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                elif self.mode == 3:
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

    def plot_adp(self, subxpat_list: List[Result], xpat: Result, mecals: Result, muscat: Result, best: bool = True):
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
                    if self.mode == 1:
                        label = f'SubXPAT_io_best'
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_io_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_io_best.pdf"
                    elif self.mode == 3:
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_subgraph_best.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_subgraph_best.pdf"
                        label = f'SubXPAT_subgraphsize_best'
            ax.plot(subxpat_list[0].error_array, [respective_delay_dict[key] * best_area_dict[key] for key in subxpat_list[0].area_dict.keys()],
                    label=label, marker='D', markeredgecolor='blue',
                    markeredgewidth=5, linestyle='solid', linewidth=2, markersize=3)
        else:
            for subxpat in subxpat_list:
                if subxpat.status:
                    if self.mode == 1:
                        figurename_png = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_io_multiple.png"
                        figurename_pdf = f"{sxpatpaths.OUTPUT_PATH['figure'][0]}/delay_area_{self.exact_name}_io_multiple.pdf"
                        color = sxpatconfig.SUBXPAT_COLOR_DICT[f'i{subxpat.imax}_o{subxpat.omax}']
                        label = f'SubXPAT_i{subxpat.imax}_o{subxpat.omax}'
                    elif self.mode == 3:
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
                    # print(f'{grid_file = }')
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
                    # print(f'{subxpat.area_iteration_dict = }')


        subxpat.partitioning_dict = partitioning_dict

    def _grid_file_is_valid(self, subxpat: Result, grid_file:str, imax:int=3, omax:int=2, sensitivity:bool=False,
                                      max_sensitivity:int = 100, min_subgraph_size:int = 10):
        valid = False
        if re.search(f'imax{imax}', grid_file) and re.search(f'omax{omax}', grid_file):
            if sensitivity:
                if re.search(f'without', grid_file):
                    valid = True
            else:
                if re.search(f'sens{max()}', grid_file) and re.search(f'subgraphsize{min_subgraph_size}', grid_file):
                    valid = True
        return valid


    def _get_iteration_characteristcs(self, subxpat: Result, imax:int=3, omax:int=2, sensitivity:bool=False,
                                      max_sensitivity:int = 100, min_subgraph_size:int = 10):

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




