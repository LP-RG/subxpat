from __future__ import annotations
from abc import abstractmethod
import itertools
import re
from typing import Any, Callable, Collection, Dict, Iterable, Iterator, Mapping, Tuple, Union

from sxpat.annotatedGraph import AnnotatedGraph
import sxpat.config.config as sxpat_cfg
from sxpat.templateSpecs import TemplateSpecs
from .encoding import Encoding


NOTHING = object()


def mapping_inv(mapping: Mapping, value: Any, default: Any = NOTHING) -> Any:
    key = next((k for (k, v) in mapping.items() if v == value), default)
    if key is NOTHING:
        raise ValueError('The value does not match with any pair in the mapping.')
    return key


class TemplateManager:
    def __init__(self, exact_graph: AnnotatedGraph, current_graph: AnnotatedGraph,
                 specs: TemplateSpecs, encoding: Encoding) -> None:
        self._exact_graph = exact_graph
        self._current_graph = current_graph
        self._specs = specs
        self._encoding = encoding

    @staticmethod
    def factory(graph: AnnotatedGraph, specs: TemplateSpecs) -> TemplateManager:
        # create required Encoding object
        encoding = Encoding.factory(specs.encoding, graph.num_inputs, graph.num_outputs)

        # select and return TemplateManager object
        return {
            False: SOPManager,
            True: SOPSManager,
        }[specs.shared](graph, specs, encoding)

    @abstractmethod
    def _generate_script(self) -> None:
        pass

    @abstractmethod
    def _run_script(self) -> None:
        pass

    @abstractmethod
    def _parse_result(self) -> Dict:
        pass

    def run(self) -> Dict:
        # generate z3 python script
        self._generate_script()

        # run the generated script
        self._run_script()

        # parse the results
        results = self._parse_result()

        return results


class ProductTemplateManager(TemplateManager):
    @staticmethod
    def _gen_declare_gate(name: str) -> str:
        return f"{name} = Bool('{name}')"

    @staticmethod
    def _gen_declare_bool_function(name: str, inputs_count: int) -> str:
        return f"{name} = Function('{name}', {', '.join(itertools.repeat('BoolSort()', inputs_count + 1))})"

    def _gen_declare_enc_function(self, name: str) -> str:
        return f'{name} = {self._encoding.function(name)}'

    @staticmethod
    def _gen_call_function(name: str, inputs: Iterable[str]) -> str:
        return f'{name}({", ".join(inputs)})'

    def _gen_inputs_as_arguments(self) -> str:
        return ', '.join(self._exact_graph.input_dict.values())

    def _use_exact_var(self, node_name: str) -> str:
        # is input
        if node_name in self._exact_graph.input_dict.values():
            return node_name

        # is constant
        if node_name in self._exact_graph.constant_dict.values():
            return sxpat_cfg.Z3_GATES_DICTIONARY[self._exact_graph.graph.nodes[node_name][sxpat_cfg.LABEL]]

        # is gate
        if node_name in self._exact_graph.gate_dict.value():
            node_i = mapping_inv(self._exact_graph.gate_dict, node_name)
            var_name = f'{sxpat_cfg.EXACT_WIRES_PREFIX}{self._exact_graph.num_inputs + node_i}'
            args = ','.join(self._exact_graph.input_dict.values())
            return f'{var_name}({args})'

        # is output
        if node_name in self._exact_graph.output_dict.values():
            node_i = mapping_inv(self._exact_graph.output_dict, node_name)
            var_name = f'{sxpat_cfg.EXACT_WIRES_PREFIX}{sxpat_cfg.OUT}{node_i}'
            args = ','.join(self._exact_graph.input_dict.values())
            return f'{var_name}({args})'

    def _use_approx_var(self, node_name: str) -> str:
        if node_name in self._exact_graph.input_dict.values():
            return node_name

        # is constant
        if node_name in self._current_graph.constant_dict.values():
            return sxpat_cfg.Z3_GATES_DICTIONARY[self._current_graph.graph.nodes[node_name][sxpat_cfg.LABEL]]

        # is gate
        if node_name in list(self._current_graph.gate_dict.values()):
            # is subgraph gate
            if self._current_graph.is_subgraph_member(node_name):
                # get subgraph inputs sorted, all graph-inputs first (sorted by id) followed by the gates (sorted by id)
                subpgraph_inputs = list(self._current_graph.subgraph_input_dict.values())
                def is_input(n): return n in self._exact_graph.input_dict.values()
                for i, node in enumerate(subpgraph_inputs):
                    if not is_input(node):
                        gate_i = mapping_inv(self._current_graph.gate_dict, node)
                        subpgraph_inputs[i] = self._gen_call_function(
                            f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{self._exact_graph.num_inputs + gate_i}',
                            self._exact_graph.input_dict.values()
                        )
                subpgraph_inputs.sort(key=lambda n: int(re.search(r'\d+', n).group()))

                node_i = mapping_inv(self._current_graph.gate_dict, node_name)
                var_name = f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{self._exact_graph.num_inputs + node_i}'
                return self._gen_call_function(var_name, subpgraph_inputs)

            # is not subgraph gate
            else:
                node_i = mapping_inv(self._current_graph.gate_dict, node_name)
                var_name = f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{self._exact_graph.num_inputs + node_i}'
                args = ','.join(self._exact_graph.input_dict.values())
                return f'{var_name}({args})'

        # is output
        if node_name in self._exact_graph.output_dict.values():
            node_i = mapping_inv(self._exact_graph.output_dict, node_name)
            var_name = f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{sxpat_cfg.OUT}{node_i}'
            args = ','.join(self._exact_graph.input_dict.values())
            return f'{var_name}({args})'

    def _generate_product(self, parameter_pair_gen: Callable[[int], Tuple[str, str]]) -> str:
        multiplexers = []
        for input_i, input_name in self._current_graph.subgraph_input_dict.items():
            p_l, p_s = parameter_pair_gen(input_i)
            multiplexers.append(f'Or(Not({p_s}), {p_l} == {self._use_approx_var(input_name)})')

        return f'And({", ".join(multiplexers)})'


class SOPManager(ProductTemplateManager):
    @staticmethod
    def _input_parameters(output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        partial_parameter = f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}_{sxpat_cfg.TREE_PREFIX}{product_i}_{sxpat_cfg.INPUT_LITERAL_PREFIX}{input_i}'
        return (f'{partial_parameter}_{sxpat_cfg.LITERAL_PREFIX}', f'{partial_parameter}_{sxpat_cfg.SELECT_PREFIX}')

    def _output_parameter(output_i: int) -> str:
        return f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}'

    def _generate_script(self) -> None:
        # utility references
        input_dict = self._exact_graph.input_dict
        output_dict = self._exact_graph.output_dict
        exact_gates_dict = self._exact_graph.gate_dict
        exact_const_dict = self._exact_graph.constant_dict
        current_gates_dict = self._current_graph.gate_dict
        current_const_dict = self._current_graph.constant_dict

        builder = Builder.from_file('./template.py')

        # ET_ENC
        builder.update(ET_ENC=f"ET_ENC = {self._encoding.output_value('ET')}")

        # abs_diff_def
        builder.update(abs_diff_def=self._encoding.abs_diff('a', 'b'))

        # ini_defs
        builder.update(ini_defs='\n'.join(
            self._gen_declare_gate(input_name)
            for input_name in input_dict.values()
        ))

        # functions (function_exact, function_approximate)
        builder.update(function_exact=self._encoding.function('fe'))
        builder.update(function_approximate=self._encoding.function('fa'))

        # gen_inputs_arguments
        builder.update(gen_inputs_arguments=self._gen_inputs_as_arguments())

        # error
        builder.update(error=self._encoding.output_variable('error'))

        # params_declaration
        builder.update(params_declaration='\n'.join(itertools.chain(
            (
                self._gen_declare_gate(self._output_parameter(output_i))
                for output_i in output_dict.keys()
            ),
            itertools.chain.from_iterable(
                (
                    self._gen_declare_gate((pars := self._input_parameters(output_i, product_i, input_i))[0]),
                    self._gen_declare_gate(pars[1])
                )
                for output_i in output_dict.keys()
                for product_i in range(self._specs.ppo)
                for input_i in input_dict.keys()
            ),
        )))

        # exact_wires_declaration
        builder.update(exact_wires_declaration='\n'.join(
            self._gen_declare_bool_function(f'{sxpat_cfg.EXACT_WIRES_PREFIX}{len(input_dict) + gate_i}', len(input_dict))
            for gate_i in itertools.chain(exact_gates_dict.keys(), exact_const_dict.keys())
        ))

        # approximate_declaration
        builder.update(approximate_declaration='\n'.join(
            (
                self._gen_declare_bool_function(f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(input_dict) + gate_i}', len(self._current_graph.subgraph_num_inputs))
                if self._current_graph.is_subgraph_member(gate_name) else
                self._gen_declare_bool_function(f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(input_dict) + gate_i}', len(input_dict))
            )
            for gate_i, gate_name in itertools.chain(exact_gates_dict.items(), exact_const_dict.items())
        ))

        # exact_outputs_declaration
        builder.update(exact_outputs_declaration='\n'.join(
            self._gen_declare_enc_function(f'{sxpat_cfg.EXACT_OUTPUT_PREFIX}{sxpat_cfg.OUT}{output_i}')
            for output_i in output_dict.keys()
        ))

        # approximate_outputs_declaration
        builder.update(approximate_outputs_declaration='\n'.join(
            self._gen_declare_enc_function(f'{sxpat_cfg.APPROXIMATE_OUTPUT_PREFIX}{sxpat_cfg.OUT}{output_i}')
            for output_i in output_dict.keys()
        ))

        # exact_wires_constraints
        def get_preds(name: str) -> Collection[str]: return tuple(self._exact_graph.graph.predecessors(name))
        def get_func(name: str) -> str: return self._exact_graph.graph.nodes[name][sxpat_cfg.LABEL]
        lines = []
        for gate_i, gate_name in exact_gates_dict.items():
            gate_preds = get_preds(gate_name)
            gate_func = get_func(gate_name)
            assert (gate_func, len(gate_preds)) in [
                (sxpat_cfg.NOT, 1),
                (sxpat_cfg.AND, 2),
                (sxpat_cfg.OR, 2),
            ], 'invalid gate function/predecessors combination'

            preds = tuple(self._use_exact_var(gate_pred) for gate_pred in gate_preds)
            name = f'{sxpat_cfg.EXACT_WIRES_PREFIX}{self._exact_graph.num_inputs + gate_i}'
            lines.append(
                f'{self._gen_call_function(name, self.exact_graph.input_dict.values())}'
                f' == {sxpat_cfg.TO_Z3_GATE_DICT[gate_func]}({", ".join(preds)}),'
            )
        builder.update(exact_wires_constraints='\n'.join(f'{sxpat_cfg.TAB}{line}' for line in lines))

        # exact_output_constraints
        lines = []
        for output_name in output_dict.values():
            output_preds = get_preds(output_name)
            assert len(output_preds) == 1, 'an output must have exactly one predecessor'

            pred = self._use_exact_var(output_preds[0])
            output = self._use_exact_var(output_name)
            lines.append(f'{output} == {pred},')
        builder.update(exact_output_constraints='\n'.join(f'{sxpat_cfg.TAB}{line}' for line in lines))

        # exact_aggregated_output
        function_call = self._gen_call_function('fe', input_dict.values())
        aggregated_output = self._encoding.aggregate_variables(tuple(
            self._use_exact_var(output_dict[output_i])
            for output_i in range(self._exact_graph.num_outputs)
        ))
        builder.update(exact_aggregated_output=f'{sxpat_cfg.TAB}{function_call} == {aggregated_output},')

        # approximate_wires_constraints
        

        # approximate_output_constraints

        # approximate_aggregated_output
        function_call = self._gen_call_function('fa', input_dict.values())
        aggregated_output = self._encoding.aggregate_variables(tuple(
            self._use_approx_var(output_dict[output_i])
            for output_i in range(self._exact_graph.num_outputs)
        ))
        builder.update(exact_aggregated_output=f'{sxpat_cfg.TAB}{function_call} == {aggregated_output},')

        # boolean_outputs
        # approximate_outputs
        # forall_solver

        # solver (both forall and verification)
        builder.update(solver=self._encoding.solver)

        # difference_constraint (add new encoding function for > ?)

        # data_object

        # output_path (maybe needs function to set pat)
        builder.update(output_path=self._specs.json_out_path)

    def _run_script(self) -> None:
        pass

    def _parse_result(self) -> Dict:
        pass


class SOPSManager(ProductTemplateManager):
    def _generate_script(self) -> None:
        pass

    def _run_script(self) -> None:
        pass

    def _parse_result(self) -> Dict:
        pass


class Builder:
    LEFT_DELIMITER = '{{{{'
    RIGHT_DELIMITER = '}}}}'
    MAGIC_STRING_1 = 'zqwezrtyzuiozpaszdfgzhjkzlzxzcvbznm1z234z567z890z'
    MAGIC_STRING_2 = 'zmnbzvcxzzlkzjhgzfdszapoziuyztrezwq0z987z654z321z'

    def __init__(self, string: str) -> 'Builder':
        self._string = string
        self._kwargs = dict()

    @ classmethod
    def from_file(cls, filename: str) -> Builder:
        with open(filename, 'r') as ifile:
            return cls(ifile.read())

    def update(self, **kwargs: Dict[str, str]) -> None:
        self._kwargs.update(kwargs)

    def finalize(self) -> str:
        return (self._string
                .replace(self.LEFT_DELIMITER, self.MAGIC_STRING_1)
                .replace(self.RIGHT_DELIMITER, self.MAGIC_STRING_2)
                .replace('{', '{{')
                .replace('}', '}}')
                .replace(self.MAGIC_STRING_1, '{')
                .replace(self.MAGIC_STRING_2, '}')
                .format(**self._kwargs))

    def __str__(self) -> str:
        return f'{self._string!r} <- {self._kwargs}'
