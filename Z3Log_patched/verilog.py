from typing import Tuple

from os.path import join as path_join

# to be patched:
from Z3Log.verilog import Verilog as _Verilog

__all__ = ['Verilog']


class Verilog(_Verilog):
    def __init__(self, input_verilog_path: str, output_verilog_path: str, temporary_path: str):
        # imports
        from .utils import get_pure_name

        # store name and in/out paths
        self.__circuit_name = circuit_name = get_pure_name(input_verilog_path)
        self.__circuit_in_path = input_verilog_path
        self.__circuit_out_path = output_verilog_path

        # others
        self.__tmp_verilog = path_join(temporary_path, f'{circuit_name}_tmp.v')
        self.__num_inputs, self.__num_outputs = self.extract_module_io()

        # synthesize
        self.synthesize_to_gate_level(self.in_path, self.out_path)

        # other fields were removed from the initialization as they are not used

    @property
    def aig_out_path(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def testbench(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def samples(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def iverilog_out_path(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def iverilog_log_path(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def vvp_in_path(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def vvp_out_path(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    def set_samples(self, samples): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def sample_results(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    def set_sample_results(self, results): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')

    # methods

    def import_results(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    def import_circuit(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    def unwrap_variables(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    def create_test_bench(self, samples): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    def run_test_bench(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')

    def extract_module_io(self) -> Tuple[int, int]:
        # imports
        import re
        import os
        import subprocess
        from .config.config import YOSYS as yosys_path

        clean_verilog = self.in_path
        yosys_command = f'read_verilog {clean_verilog}; synth -flatten; opt; opt_clean; techmap; write_verilog {self.tmp};'
        process = subprocess.run([yosys_path, '-p', yosys_command], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if process.stderr.decode():
            raise Exception(f'ERROR!!! yosys cannot do its pass on file {clean_verilog}\n{process.stderr.decode()}')

        with open(self.tmp) as tmp_file:
            inp = {}
            inp_count = 0
            out = {}
            out_count = 0
            modulename = None
            line = tmp_file.readline()
            while line:
                tokens = re.split('[ ()]', line.strip().strip(';').strip())

                if len(tokens) > 0 and tokens[0] == 'module' and modulename is None:
                    modulename = tokens[1]
                    port_list = re.split('[,()]', line.strip().strip(';').strip())[1:]
                    port_list = [s.strip() for s in port_list if s.strip() != '']

                if len(tokens) == 2 and (tokens[0] == 'input' or tokens[0] == 'output'):
                    if tokens[0] == 'input':
                        inp[tokens[1]] = 1
                        inp_count += 1
                    if tokens[0] == 'output':
                        out[tokens[1]] = 1
                        out_count += 1

                if len(tokens) == 3 and (tokens[0] == 'input' or tokens[0] == 'output'):
                    range_str = tokens[1][1:-1].split(':')
                    range_int = list(map(int, range_str))
                    length = max(range_int) - min(range_int) + 1
                    if tokens[0] == 'input':
                        inp[tokens[2]] = length
                        inp_count += length
                    if tokens[0] == 'output':
                        out[tokens[2]] = length
                        out_count += length

                line = tmp_file.readline()

        os.remove(self.tmp)

        return inp_count, out_count

    # there are many not overidden methods, those are valid and use the properties/fields we fixed
