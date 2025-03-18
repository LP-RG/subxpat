from typing import NamedTuple

import re
import subprocess

from sxpat.utils.utils import pprint, color
from .config import config as sxpatconfig


__all__ = ['MetricsEstimator']


class MetricsEstimator:
    MODULE_NAME_PATTERN = re.compile(r'module\s+([a-zA-Z0-9_$]+)\s*\(')

    AREA_ANY_PATTERN = re.compile(r'Chip area for module .*?: (\S+)$', re.M)
    AREA_ZERO_PATTERN = re.compile(r'Don\'t call ABC as there is nothing to map')
    DELAY_PATTERN = re.compile(r'^\s+(\S+)\s+data arrival time\n\n', re.M)
    POWER_PATTERN = re.compile(r'^Total\s+\S+\s+\S+\s+\S+\s+(\S+)\s+', re.M)

    YOSYS_BASE_COMMAND = '; '.join((
        f'read_verilog "{{verilog_path}}"',
        f'synth -flatten',
        f'opt',
        f'opt_clean -purge',
        f'abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH}',
        f'stat -liberty {sxpatconfig.LIB_PATH}',
        f'write_verilog -noattr "{{metrics_verilog_path}}"',
    ))
    STA_BASE_COMMAND = '; '.join((
        f'read_liberty "{sxpatconfig.LIB_PATH}"',
        f'read_verilog "{{metrics_verilog_path}}"',
        f'link_design "{{module_name}}"',
        f'create_clock -name clk -period 1',
        f'set_input_delay -clock clk 0 [all_inputs]',
        f'set_output_delay -clock clk 0 [all_outputs]',
        f'report_checks -digits 12',
        f'report_power -digits 12',
        f'exit',
    ))

    Metrics = NamedTuple('Metrics', [('area', float), ('power', float), ('delay', float)])

    def __new__(cls):
        raise NotImplementedError(f'{cls.__qualname__} is a utility class and as such cannot be instantiated')

    @classmethod
    def estimate_metrics(cls, verilog_path: str) -> Metrics:
        # compute names and paths
        metrics_verilog_path = f'{verilog_path[:-2]}_for_metrics.v'
        module_name = cls._extract_module_name(verilog_path)

        # > define commands
        # yosys command to get area and to generate metrics verilog
        yosys_command = cls.YOSYS_BASE_COMMAND.format(verilog_path=verilog_path,
                                                      metrics_verilog_path=metrics_verilog_path)
        # sta command to get delay and power
        sta_command = cls.STA_BASE_COMMAND.format(metrics_verilog_path=metrics_verilog_path,
                                                  module_name=module_name)

        # > execute commands
        yosys_result = subprocess.run([sxpatconfig.YOSYS, '-QT'],
                                      input=yosys_command, text=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sta_result = subprocess.run([sxpatconfig.OPENSTA, '-no_splash'],
                                    input=sta_command, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # > guards for failures
        if yosys_result.returncode != 0:
            raise Exception(color.error(f'Yosys ERROR!\n{yosys_result.stderr}'))
        if sta_result.returncode != 0:
            raise Exception(color.error(f'OpenSTA ERROR!\n{sta_result.stderr}'))

        with open('yosys.log', 'w') as f:
            f.write(yosys_result.stdout)
        with open('sta.log', 'w') as f:
            f.write(sta_result.stdout)

        # > parse results
        # area
        if m := cls.AREA_ANY_PATTERN.search(yosys_result.stdout):
            area = float(m.group(1))
        elif m := cls.AREA_ZERO_PATTERN.search(yosys_result.stdout):
            area = 0.0
        else:
            raise Exception(color.error('Yosys ERROR!\nNo useful information in the stats log!'))
        # power
        if m := cls.POWER_PATTERN.search(sta_result.stdout):
            power = float(m.group(1))
        else:
            pprint.warning('OpenSTA Warning! Design has 0 power consumption!')
            power = 0.0
        # delay
        if m := cls.DELAY_PATTERN.search(sta_result.stdout):
            delay = float(m.group(1))
        else:
            pprint.warning('OpenSTA Warning! Design has 0 delay!')
            delay = 0.0

        return cls.Metrics(area, power, delay)

    @classmethod
    def _extract_module_name(cls, verilog_path: str):
        with open(verilog_path, 'r') as f:
            verilog_str = f.read()

        if m := cls.MODULE_NAME_PATTERN.search(verilog_str):
            return m.group(1)
        else:
            raise RuntimeError(f'No module name found in {verilog_path}')
