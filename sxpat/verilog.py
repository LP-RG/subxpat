import re
from subprocess import run, PIPE, DEVNULL
from typing import ClassVar, Dict, Iterable, List, Mapping, Sequence, Tuple


__all__ = ['synthesize_verilog_to_gate_level', 'YosysError']


class YosysError(Exception):
    """Yosys command failure error."""

    __slots__ = ['command', 'stderr']

    def __init__(self, command: str, stderr: str, *args):
        super().__init__(command, stderr, *args)
        self.command = command
        self.stderr = stderr


class synthesize_verilog_to_gate_level:
    YOSYS_COMMAND: ClassVar = """
        read_verilog {input_path};
        synth -flatten;
        opt;
        opt_clean -purge;
        abc -g NAND;
        opt;
        opt_clean -purge;
        splitnets -ports;
        opt;
        opt_clean -purge;
        write_verilog -noattr {output_path};
    """

    MODULE_PATTERN: ClassVar = re.compile(r'^\s*module\s+\w+\s*\((.+)\)', re.MULTILINE)
    SPACES_PATTERN: ClassVar = re.compile(r'\s+')

    INPUT_PATTERN: ClassVar = re.compile(r'^input (.+?)\s*$')
    OUTPUT_PATTERN: ClassVar = re.compile(r'^output (.+?)\s*$')
    RANGE_PATTERN: ClassVar = re.compile(r'\[(\d+):(\d+)\]')
    VECTOR_PATTERN: ClassVar = re.compile(r'(?:\[\d+:\d+\]\s*)?(.*)')
    PARTIAL_RELABEL_PATTERN: ClassVar = r'({key})([,;)\s\r\n$])'

    def __new__(cls, input_path: str, output_path: str):
        # compose command
        yosys_command = cls.YOSYS_COMMAND.format(input_path=input_path, output_path=output_path)

        # run process
        _process = run(['yosys', '-p', yosys_command], stdout=DEVNULL, stderr=PIPE, text=True)
        if _process.returncode: raise YosysError(yosys_command, _process.stderr)

        # post-processing
        cls.rename_variables(output_path, output_path)

    def rename_variables(cls, input_path: str, output_path: str):
        with open(input_path, 'r+') as _f:
            verilog = _f.read()
            lines = verilog.split(';')

        # EXTRACT PORT LIST
        # match the module signature (eg. module adder(a, b, c))
        match = cls.MODULE_PATTERN.search(verilog)
        if not match: raise RuntimeError(f'No signature was found in Verilog file `{input_path}`.')
        # extract port list (eg. [a, b, c])
        port_list = cls.SPACES_PATTERN.sub('', match.group(1)).split(',')

        # EXTRACT INPUTS/OUTPUTS
        input_dict, output_dict = cls.extract_inputs_outputs(lines, port_list)

        # RELABEL
        new_labels = cls.create_new_labels(port_list, input_dict, output_dict)
        lines = cls.relabel_variables(verilog.split('\n'), new_labels)

        with open(output_path, 'w') as _f:
            _f.writelines(f'{l}\n' for l in lines)

    def extract_inputs_outputs(cls, verilog_lines: List[str], port_list: Iterable[str]):
        # example input:
        #   module circuit(a, b, c, d)
        #   input [1:0] a;
        #   input [2:0]b;
        #   output d;
        #   output [3:0]c;
        # example output:
        #   input_dict = {0:(a, 2), 1:(b, 3)}
        #   output_dict = {3:(d, 1), 2:(c, 3)}

        ports = dict((p, i) for (i, p) in enumerate(port_list))
        input_dict: Dict[int, Tuple[str, int]] = dict()
        output_dict: Dict[int, Tuple[str, int]] = dict()

        for line in verilog_lines:
            line = line.strip()

            # extract inputs
            if match := cls.INPUT_PATTERN.search(line):
                # get all inputs on the line
                input_list = cls.SPACES_PATTERN.sub('', match.group(1)).split(',')
                input_list = cls.propagate_bitwidth(input_list)

                # store widths
                for inp in input_list:
                    name = cls.extract_name(inp)
                    if name not in ports:
                        raise Exception(f'Input {name} is not in the port list.')

                    _index = ports[name]
                    input_dict[_index] = (name, cls.compute_width(inp))

            # extract outputs
            elif match := cls.OUTPUT_PATTERN.search(line):
                # get all outputs on the line
                output_list = cls.SPACES_PATTERN.sub('', match.group(1)).split(',')
                output_list = cls.propagate_bitwidth(output_list)

                # store widths
                for out in output_list:
                    name = cls.extract_name(out)
                    if name not in ports:
                        raise Exception(f'Output {name} is not in the port list.')

                    _index = ports[name]
                    output_dict[_index] = (name, cls.compute_width(out))

        return (
            dict(sorted(input_dict.items())),
            dict(sorted(output_dict.items())),
        )

    def create_new_labels(cls, port_list: List, input_dict: Dict, output_dict: Dict):
        new_labels: Dict = {}
        for port_idx in input_dict:
            if input_dict[port_idx][0] == port_list[port_idx]:
                new_labels[port_list[port_idx]] = f'in{port_idx}'
            else:
                raise Exception(f'Error!!! {input_dict[port_idx][0]} is not equal to {port_list[port_idx]}')

        out_idx = 0
        for port_idx in output_dict:
            if output_dict[port_idx][0] == port_list[port_idx]:
                new_labels[port_list[port_idx]] = f'out{out_idx}'
                out_idx += 1
            else:
                raise Exception(f'Error!!! {output_dict[port_idx][0]} is not equal to {port_list[port_idx]}')
        return new_labels

    def relabel_variables(cls, verilog_lines: Iterable[str], labels: Mapping[str, str]) -> List[str]:
        """
            Relabel all variables with their new representation.

            :param verilog_lines: the lines to update
            :param labels: the mapping from old to new label
            :return: the updated list of lines
        """
        # copy
        verilog_lines = list(verilog_lines)

        # for all old/new pairs
        for (old, new) in labels.items():
            # compile the pattern
            pattern = re.compile(cls.PARTIAL_RELABEL_PATTERN.format(key=re.escape(old)))
            # update all lines
            for (i, line) in enumerate(verilog_lines):
                verilog_lines[i] = re.sub(pattern, lambda m: new + m.group(2), line)

        return verilog_lines

    def propagate_bitwidth(cls, inputs: Sequence[str]) -> List[str]:
        """
            Given a sequence of inputs, propagate the size of the first to the others.

            :param inputs: the raw sequence of inputs
            :return: the updated list of inputs

            Examples
            ---
            >>> propagate_bitwidth['[1:0]a', 'b']
            ['[1:0]a', '[1:0]b']
        """

        inputs = list(inputs)

        # if first is a vector, propagate its range to all others
        match = cls.RANGE_PATTERN.search(inputs[0])
        if match:
            vector_range = match.group(0)
            for i in range(1, len(inputs)):
                inputs[i] = vector_range + inputs[i]

        return inputs

    def extract_name(cls, variable: str) -> str:
        """
            Extract the name of the variable.

            :param variable: the raw string of the variable
            :return: the name of the variable
        """

        match = cls.VECTOR_PATTERN.search(variable)
        if match: return match.group(1)
        else: return variable

    def compute_width(cls, variable: str) -> int:
        """
            Compute the bit-width of the variable.

            :param variable: the raw string of the variable
            :return: the bit-width of the variable
        """

        match = cls.RANGE_PATTERN.search(variable)
        if match:
            _l_bound = int(match.group(1))
            _r_bound = int(match.group(2))
            return abs(_l_bound - _r_bound) + 1
        else:
            return 1


if __name__ == '__main__':
    import sys
    synthesize_verilog_to_gate_level(sys.argv[1], 'banana.v')

    from Z3Log_patched.verilog import Verilog
    import os
    os.makedirs('bpapaya_t', exist_ok=True)
    Verilog(sys.argv[1], 'bpapaya.v', 'bpapaya_t')
