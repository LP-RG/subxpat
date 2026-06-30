from sxpat.specifications import Paths

from os.path import join as path_join

from sxpat.converting.legacy import iograph_from_digraph

from sxpat.utils.names import extract_name
from sxpat.utils.formats.dot import load_yosys_dot
from sxpat.utils.formats.verilog import synthesize_verilog_to_notand_gate_level, convert_verilog_to_dot


def load_circuit_from_yosysdot(circuit_dot_path: str):
    # load the Yosys dot
    digraph = load_yosys_dot(circuit_dot_path)

    # convert to iograph
    return iograph_from_digraph(digraph)


def load_circuit_from_notand_verilog(circuit_verilog_path: str, run_paths: Paths.RunFiles):
    circuit_name = extract_name(circuit_verilog_path)

    # convert the not-and gate level Verilog into a Yosys dot
    convert_verilog_to_dot(
        circuit_verilog_path,
        tmp_gv := path_join(run_paths.temporary, f'{circuit_name}.dot'),
        run_paths.temporary,
    )

    #
    return load_circuit_from_yosysdot(tmp_gv)


def load_circuit_from_verilog(circuit_verilog_path: str, run_paths: Paths.RunFiles):
    circuit_name = extract_name(circuit_verilog_path)

    # prepare a not-and gate level Verilog
    synthesize_verilog_to_notand_gate_level(
        circuit_verilog_path,
        tmp_v := path_join(run_paths.temporary, f'{circuit_name}.v'),
    )

    #
    return load_circuit_from_notand_verilog(tmp_v, run_paths)

