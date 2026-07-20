from typing import Literal, NamedTuple, overload

import re
import functools as ft
from textwrap import dedent

import subprocess

from sxpat.utils.filesystem import FS
from sxpat.utils.formats.verilog import synthesize_verilog_to_notand_gate_level
from sxpat.utils.names import extract_name
from sxpat.utils.decorators import make_utility_class

from sxpat.specifications import Paths


__all__ = ['MetricsEstimator']


@make_utility_class
class MetricsEstimator:
    """
    :authors: Marco Biasion
    """

    MODULE_NAME_PATTERN = re.compile(r'module\s+([a-zA-Z0-9_$]+)\s*\(')

    AREA_ANY_PATTERN = re.compile(r'Chip area for module .*?: (\S+)$', re.M)
    AREA_ZERO_PATTERN = re.compile(r'Don\'t call ABC as there is nothing to map')
    DELAY_PATTERN = re.compile(r'^\s+(\S+)\s+data arrival time\n\n', re.M)
    POWER_PATTERN = re.compile(r'^Total\s+\S+\s+\S+\s+\S+\s+(\S+)\s+', re.M)

    YOSYS_BASE_COMMAND = dedent("""
        read_verilog "{verilog_path}";

        # TODO:MARCO: test that we do not have issues/differences by removing the following lines
        # synth -flatten;
        # opt;
        # opt_clean -purge;

        # apply lib and specific passes
        synth;
        abc -liberty {lib_path} -script {abc_script_path};
        stat -liberty {lib_path};

        write_verilog -noattr "{metrics_verilog_path}";
    """).strip()

    # TODO: can we replace this with ABC or yosys? (https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/synthesis/abc.html)
    STA_BASE_COMMAND = dedent("""
        read_liberty "{lib_path}";
        read_verilog "{metrics_verilog_path}";
        link_design "{module_name}";
        create_clock -name clk -period 1;
        set_input_delay -clock clk 0 [all_inputs];
        set_output_delay -clock clk 0 [all_outputs];
        report_checks -digits 12;
        report_power -digits 12;
        exit;
    """).strip()

    Metrics = NamedTuple('Metrics', [('area', float), ('power', float), ('delay', float)])

    @classmethod
    @overload
    def estimate_metrics(
        cls,
        syn_paths: Paths.Synthesis,
        verilog_path: str,
        temporary_path: str,
    ) -> Metrics:
        """
        Sythesize a circuit and estimate its metrics.
        """

    @classmethod
    @overload
    def estimate_metrics(
        cls,
        syn_paths: Paths.Synthesis,
        verilog_path: str,
        temporary_path: str,
        cached: Literal[True],
    ) -> Metrics:
        """
        Sythesize a circuit and estimate its metrics.

        Cached on the assumption that the same `syn_paths`/`verilog_path` generate the same results.
        """

    @classmethod
    def estimate_metrics(
        cls,
        syn_paths: Paths.Synthesis,
        verilog_path: str,
        temporary_path: str,
        cached: bool = False,
    ) -> Metrics:
        if cached: return cls._estimate_metrics_cached(syn_paths, verilog_path, temporary_path)
        else: return cls._estimate_metrics(syn_paths, verilog_path, temporary_path)

    @classmethod
    def _estimate_metrics(
        cls,
        syn_paths: Paths.Synthesis,
        circuit_in_verilog_path: str,
        temporary_path: str,
    ) -> Metrics:
        # compute names and paths
        circuit_name = extract_name(circuit_in_verilog_path)
        norm_verilog_path = FS.join(temporary_path, f'{circuit_name}_norm.v')
        metrics_verilog_path = FS.join(temporary_path, f'{circuit_name}_for_metrics.v')
        module_name = cls._extract_module_name(circuit_in_verilog_path)

        # > define commands
        # yosys command to get area and to generate metrics verilog
        yosys_command = cls.YOSYS_BASE_COMMAND.format(
            # circuit
            verilog_path=norm_verilog_path,
            metrics_verilog_path=metrics_verilog_path,
            # config
            lib_path=syn_paths.cell_library,
            abc_script_path=syn_paths.abc_script,
        )
        # sta command to get delay and power
        sta_command = cls.STA_BASE_COMMAND.format(
            # circuit
            metrics_verilog_path=metrics_verilog_path,
            module_name=module_name,
            # config
            lib_path=syn_paths.cell_library,
        )

        # > execute commands
        # normalize verilog
        synthesize_verilog_to_notand_gate_level(
            circuit_in_verilog_path,
            norm_verilog_path,
        )
        print(circuit_in_verilog_path)
        print(norm_verilog_path)
        input()
        # compute area and prepare metrics file
        yosys_result = subprocess.run(
            ['yosys'], input=yosys_command,
            capture_output=True, text=True,
            check=True,
        )
        # compute power and delay
        sta_result = subprocess.run(
            ['sta'], input=sta_command,
            capture_output=True, text=True,
            check=True,
        )
        print(yosys_result.stdout)
        input()
        print(sta_result.stdout)
        input()


        # > parse results
        # area
        if m := cls.AREA_ANY_PATTERN.search(yosys_result.stdout): area = float(m.group(1))
        elif m := cls.AREA_ZERO_PATTERN.search(yosys_result.stdout): area = 0.0
        else: raise Exception('Yosys ERROR!\nNo useful information in the stats log!')
        # power
        if m := cls.POWER_PATTERN.search(sta_result.stdout): power = float(m.group(1))
        else: power = 0.0
        # delay
        if m := cls.DELAY_PATTERN.search(sta_result.stdout): delay = float(m.group(1))
        else: delay = 0.0

        a = cls.Metrics(area, power, delay)
        print(a)
        input()
        return a

    @classmethod
    @ft.lru_cache(None)
    def _estimate_metrics_cached(
        cls,
        paths: Paths.Synthesis,
        verilog_path: str,
        temporary_path: str,
    ) -> Metrics:
        return cls._estimate_metrics(paths, verilog_path, temporary_path)

    @classmethod
    def _extract_module_name(
        cls,
        verilog_path: str,
    ) -> str:
        verilog_str = FS.readfile(verilog_path)

        if m := cls.MODULE_NAME_PATTERN.search(verilog_str): return m.group(1)
        else: raise RuntimeError(f'No module name found in {verilog_path}')
