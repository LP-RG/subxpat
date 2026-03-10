# to be patched:
from Z3Log.graph import Graph as _Graph


import subprocess
from subprocess import PIPE
from colorama import Fore, Style
import networkx as nx
import re
from typing import Dict, List
from .config.path import *
from .config.config import *
import os
from .argument import Arguments
import time


class Graph(_Graph):
    def __init__(self, circuit_gv_path: str, temporary_path: str, is_clean: bool = False, address: str = None):
        """
        takes in a circuit and creates a networkx graph out of it
        :param benchmark_name: the input benchmark in gv format
        :param is_clean: leave empty for now
        """

        from .utils import get_pure_name

        self.__graph_name = circuit_name = get_pure_name(circuit_gv_path)
        self.__graph_out_path = circuit_gv_path

        # folder, extension = INPUT_PATH['gv'] # input/gv/
        # self.__graph_in_path = f'{folder}/{benchmark_name}.{extension}'
        # self.__graph_in_path = circuit_gv_path

        # folder, extension = OUTPUT_PATH['gv']  # output/gv
        # self.__graph_out_path = f'{folder}/{benchmark_name}.{extension}'

        self.__dot_in_path = f'{temporary_path}/output_gv/{circuit_name}.dot'
        self.__verilog_in_path = f'{temporary_path}/output_ver/{circuit_name}.v'


        self.__graph = self.import_graph(address)

        self.__sorted_node_list = None
        self.__is_clean = is_clean

        if not self.is_clean:
            self.clean_graph()
            self.sort_graph()

        self.remove_output_outgoing_edges()

        self.__input_dict = self.sort_dict(self.extract_inputs())
        self.__output_dict = self.sort_dict(self.extract_outputs())
        self.__gate_dict = self.sort_dict(self.extract_gates())
        self.__constant_dict = self.sort_dict(self.extract_constants())

        self.__num_inputs = len(self.__input_dict)
        self.__num_outputs = len(self.__output_dict)
        self.__num_gates = len(self.__gate_dict)
        self.__num_constants = len(self.__constant_dict)

    @property
    def in_path(self): raise RuntimeError('Why are you using this? talk with Marco')


    def fix_direction(self):
        # print(f'{self.dot_in_path = }')
        dot_command = f'{DOT} {self.dot_in_path} -Grankdir=TB -o {self.out_path}'
        subprocess.call([dot_command], shell=True)
        # print(f'{self.dot_in_path = }')
        os.remove(self.dot_in_path)