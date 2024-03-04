import csv
from colorama import Style, Fore
import os
from shutil import copy

from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.z3solver import Z3solver
from Z3Log.config import path as z3logpath

from sxpat.verification import erroreval_verification

def main():
    folder = 'experiments/mecals/ver/'
    benchmark_folders = [f for f in os.listdir(folder)]

    for cur_folder in benchmark_folders:
        cur_benchmark = cur_folder
        # select file
        cur_verilogs = [f for f in os.listdir(f'{folder}/{cur_folder}')]


        for cur_ver in cur_verilogs:
            # get claimed wce
            cur_claimed_wce = int(re.search('wce(\d+)', cur_ver).group(1))
            print(f'{cur_ver = }')
            # copy to input/ver for errorEval
            source = f'{folder}/{cur_folder}/{cur_ver}'
            # change module name
            with open(source, 'r') as rf:
                lines = rf.readlines()

            for line_idx, line in enumerate(lines):
                if re.search(r'module (\\\(null\))', line):
                    # print(line)
                    modulename = re.search(r'module (\\\(null\))', line).group(1)
                    # print(f"{modulename}")
                    line = line.replace(modulename, 'top')
                    lines[line_idx] = line
                    # print(line)

            for line_idx, line in enumerate(lines):
                if re.search(r'module (top)', line):
                    # print(line)
                    modulename = re.search(r'module (top)', line).group(1)
                    # print(f"{modulename}")
                    line = line.replace(modulename, cur_ver[:-2])
                    lines[line_idx] = line
                    # print(line)

            with open(f'{source}', 'w') as wf:
                wf.writelines(lines)

            #
            dest = f'input/ver/{cur_ver}'
            copy(source, dest)
            #
            #
            # get cur_wce using errorEval
            erroreval_verification(cur_benchmark, cur_ver[:-2], cur_claimed_wce)
            #
            #

            os.remove(dest)

        # get the wce
        # compare the wce with the claimed one
        # say pass or fail
        pass



if __name__ == "__main__":
    main()