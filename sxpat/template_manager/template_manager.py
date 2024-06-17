from __future__ import annotations
from abc import abstractmethod
import functools
import itertools
import pathlib
import re
from typing import Any, Callable, Collection, Dict, Iterable, Iterator, Mapping, Tuple, Union

from sxpat.annotatedGraph import AnnotatedGraph
import sxpat.config.config as sxpat_cfg
import sxpat.config.paths as sxpat_paths
from sxpat.templateSpecs import TemplateSpecs
from .encoding import Encoding


NOTHING = object()


def mapping_inv(mapping: Mapping, value: Any, default: Any = NOTHING) -> Any:
    key = next((k for (k, v) in mapping.items() if v == value), default)
    if key is NOTHING:
        raise ValueError('The value does not match with any pair in the mapping.')
    return key


def pairwise_iter(iterable: Iterable) -> Iterator:
    """iterate pair-wise (AB, BC, CD, ...)"""
    return zip(iterable, itertools.islice(iterable, 1, None))


class TemplateManager:
    def __init__(self, exact_graph: AnnotatedGraph, current_graph: AnnotatedGraph,
                 specs: TemplateSpecs, encoding: Encoding) -> None:
        self._exact_graph = exact_graph
        self._current_graph = current_graph
        self._specs = specs
        self._encoding = encoding

    @staticmethod
    def factory(specs: TemplateSpecs,
                exact_graph: AnnotatedGraph,
                current_graph: AnnotatedGraph,
                ) -> TemplateManager:
        # create required Encoding object
        encoding = Encoding.factory(
            specs.encoding,
            exact_graph.num_inputs,
            exact_graph.num_outputs
        )

        # select and return TemplateManager object
        return {
            False: SOPManager,
            True: SOPSManager,
        }[specs.shared](
            exact_graph,
            current_graph,
            specs,
            encoding
        )

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

    # utility getters
    @property
    def inputs(self) -> Dict[int, str]:
        """The inputs of the grph. (.exact is equal to .current)"""
        return self._exact_graph.input_dict

    @property
    def outputs(self) -> Dict[int, str]:
        """The outputs of the graph. (.exact is equal to .current)"""
        return self._exact_graph.output_dict

    @functools.cached_property
    def subgraph_inputs(self) -> Dict[int, str]:
        """The inputs of the subgraph, sorted by id (inputs first, gates second)."""

        def is_input(n): return n in self._exact_graph.input_dict.values()
        subpgraph_inputs = list(self._current_graph.subgraph_input_dict.values())

        for i, node in enumerate(subpgraph_inputs):
            if not is_input(node):
                gate_i = mapping_inv(self._current_graph.gate_dict, node)
                subpgraph_inputs[i] = self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{self._exact_graph.num_inputs + gate_i}',
                    self._exact_graph.input_dict.values()
                )
        subpgraph_inputs.sort(key=lambda n: int(re.search(r'\d+', n).group()))

        return dict(enumerate(subpgraph_inputs))

    @property
    def subgraph_outputs(self) -> Dict[int, str]:
        """The outputs of the subgraph."""
        return self._current_graph.subgraph_output_dict

    @property
    def exact_gates(self) -> Dict[int, str]:
        """The gates of the exact graph."""
        return self._exact_graph.gate_dict

    @property
    def exact_constants(self) -> Dict[int, str]:
        """The constants of the exact graph."""
        return self._exact_graph.constant_dict

    @property
    def current_gates(self) -> Dict[int, str]:
        """The gates of the current graph."""
        return self._current_graph.gate_dict

    @property
    def current_constants(self) -> Dict[int, str]:
        """The constants of the current graph."""
        return self._current_graph.constant_dict


class ProductTemplateManager(TemplateManager):

    # utility string methods

    @staticmethod
    def _gen_declare_gate(name: str) -> str:
        return f'{name} = Bool("{name}")'

    @staticmethod
    def _gen_declare_bool_function(name: str, inputs_count: int) -> str:
        return f'{name} = Function("{name}", {", ".join(itertools.repeat("BoolSort()", inputs_count + 1))})'

    def _gen_declare_enc_function(self, name: str) -> str:
        return f'{name} = {self._encoding.function(name)}'

    @staticmethod
    def _gen_call_function(name: str, inputs: Iterable[str]) -> str:
        return f'{name}({", ".join(inputs)})'

    # utility variable usage methods

    def _use_exact_var(self, node_name: str) -> str:
        # is input
        if node_name in self.inputs.values():
            return node_name

        # is constant
        if node_name in self.exact_constants.values():
            return sxpat_cfg.Z3_GATES_DICTIONARY[self._exact_graph.graph.nodes[node_name][sxpat_cfg.LABEL]]

        # is gate
        if node_name in self.exact_gates.values():
            node_i = mapping_inv(self.exact_gates, node_name)
            return self._gen_call_function(
                f'{sxpat_cfg.EXACT_WIRES_PREFIX}{len(self.inputs) + node_i}',
                self.inputs.values()
            )

        # is output
        if node_name in self.outputs.values():
            node_i = mapping_inv(self.outputs, node_name)
            return self._gen_call_function(
                f'{sxpat_cfg.EXACT_WIRES_PREFIX}{sxpat_cfg.OUT}{node_i}',
                self.inputs.values()
            )

    def _use_approx_var(self, node_name: str) -> str:
        if node_name in self.inputs.values():
            return node_name

        # is constant
        if node_name in self.current_constants.values():
            return sxpat_cfg.Z3_GATES_DICTIONARY[self._current_graph.graph.nodes[node_name][sxpat_cfg.LABEL]]

        # is gate
        if node_name in self.current_gates.values():
            # is subgraph gate
            if self._current_graph.is_subgraph_member(node_name):
                node_i = mapping_inv(self.current_gates, node_name)
                return self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + node_i}',
                    # TODO:marco: update to be recursive, allowing subgraph_inputs to be simpler
                    self.subgraph_inputs.values()
                )

            # is not subgraph gate
            else:
                node_i = mapping_inv(self.current_gates, node_name)
                return self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + node_i}',
                    self.inputs.values()
                )

        # is output
        if node_name in self.outputs.values():
            node_i = mapping_inv(self.outputs, node_name)
            return self._gen_call_function(
                f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{sxpat_cfg.OUT}{node_i}',
                self.inputs.values()
            )

    # utility template methods

    @classmethod
    @abstractmethod
    def _input_parameters(cls, output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        """Returns the pair of parameters for the given indexes. (Literal parameter, State parameter)"""
        raise NotImplementedError(f'{cls.__name__}._input_parameters(...) is abstract.')

    @classmethod
    def _output_parameter(cls, output_i: int) -> str:
        return f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}'

    def _generate_product(self, parameter_pair_gen: Callable[[int], Tuple[str, str]]) -> str:
        multiplexers = []
        for input_i, input_name in enumerate(self.subgraph_inputs):
            p_l, p_s = parameter_pair_gen(input_i)
            multiplexers.append(f'Or(Not({p_s}), {p_l} == {self._use_approx_var(input_name)})')
        return self._gen_call_function('And', multiplexers)

    #

    def _update_builder(self, builder: Builder) -> None:
        # et_encoded
        builder.update(et_encoded=self._encoding.output_value('et'))

        # abs_diff_def
        builder.update(abs_diff_def=self._encoding.abs_diff('a', 'b'))

        # ini_defs
        builder.update(ini_defs='\n'.join(
            self._gen_declare_gate(input_name)
            for input_name in self.inputs.values()
        ))

        # functions: function_exact, function_approximate
        builder.update(
            function_exact=self._encoding.function('fe'),
            function_approximate=self._encoding.function('fa')
        )

        # gen_inputs_arguments
        builder.update(gen_inputs_arguments=', '.join(self.inputs.values()))

        # error
        builder.update(error=self._encoding.output_variable('error'))

        # exact_wires_declaration
        builder.update(exact_wires_declaration='\n'.join(
            self._gen_declare_bool_function(f'{sxpat_cfg.EXACT_WIRES_PREFIX}{len(self.inputs) + gate_i}', len(self.inputs))
            for gate_i in itertools.chain(self.exact_gates.keys(), self.exact_constants.keys())
        ))

        # approximate_declaration
        builder.update(approximate_wires_declaration='\n'.join(
            (
                self._gen_declare_bool_function(f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}', len(self.subgraph_inputs))
                if self._current_graph.is_subgraph_member(gate_name) else
                self._gen_declare_bool_function(f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}', len(self.inputs))
            )
            for gate_i, gate_name in itertools.chain(self.current_gates.items(), self.current_constants.items())
        ))

        # exact_outputs_declaration
        builder.update(exact_outputs_declaration='\n'.join(
            self._gen_declare_enc_function(f'{sxpat_cfg.EXACT_OUTPUT_PREFIX}{sxpat_cfg.OUT}{output_i}')
            for output_i in self.outputs.keys()
        ))

        # approximate_outputs_declaration
        builder.update(approximate_outputs_declaration='\n'.join(
            self._gen_declare_enc_function(f'{sxpat_cfg.APPROXIMATE_OUTPUT_PREFIX}{sxpat_cfg.OUT}{output_i}')
            for output_i in self.outputs.keys()
        ))

        # exact_wires_constraints
        def get_preds(name: str) -> Collection[str]: return tuple(self._exact_graph.graph.predecessors(name))
        def get_func(name: str) -> str: return self._exact_graph.graph.nodes[name][sxpat_cfg.LABEL]
        lines = []
        for gate_i, gate_name in self.exact_gates.items():
            gate_preds = get_preds(gate_name)
            gate_func = get_func(gate_name)
            assert (gate_func, len(gate_preds)) in [
                (sxpat_cfg.NOT, 1),
                (sxpat_cfg.AND, 2),
                (sxpat_cfg.OR, 2),
            ], 'invalid gate function/predecessors combination'

            preds = tuple(self._use_exact_var(gate_pred) for gate_pred in gate_preds)
            name = f'{sxpat_cfg.EXACT_WIRES_PREFIX}{len(self.inputs) + gate_i}'
            lines.append(
                f'{self._gen_call_function(name, self.inputs.values())}'
                f' == {sxpat_cfg.TO_Z3_GATE_DICT[gate_func]}({", ".join(preds)}),'
            )
        builder.update(exact_wires_constraints='\n'.join(lines))

        # exact_output_constraints
        lines = []
        for output_name in self.outputs.values():
            output_preds = get_preds(output_name)
            assert len(output_preds) == 1, 'an output must have exactly one predecessor'

            pred = self._use_exact_var(output_preds[0])
            output = self._use_exact_var(output_name)
            lines.append(f'{output} == {pred},')
        builder.update(exact_output_constraints='\n'.join(lines))

        # exact_aggregated_output
        function_call = self._gen_call_function('fe', self.inputs.values())
        aggregated_output = self._encoding.aggregate_variables(tuple(
            self._use_exact_var(output_name)
            for output_name in self.outputs.values()
        ))
        builder.update(exact_aggregated_output=f'{function_call} == {aggregated_output},')

        # approximate_output_constraints
        lines = []
        for output_name in self.outputs.values():
            output_preds = get_preds(output_name)
            assert len(output_preds) == 1, 'an output must have exactly one predecessor'

            pred = self._use_approx_var(output_preds[0])
            output = self._use_approx_var(output_name)
            lines.append(f'{output} == {pred},')
        builder.update(approximate_output_constraints='\n'.join(lines))

        # approximate_aggregated_output
        function_call = self._gen_call_function('fa', self.inputs.values())
        aggregated_output = self._encoding.aggregate_variables(tuple(
            self._use_approx_var(output_name)
            for output_name in self.outputs.values()
        ))
        builder.update(approximate_aggregated_output=f'{function_call} == {aggregated_output},')

        # solver (both forall and verification)
        builder.update(solver=self._encoding.solver)

        # difference_less_equal_etenc, difference_greater_veret
        builder.update(
            difference_less_equal_etenc=self._encoding.unsigned_less_equal('difference', 'et_encoded'),
            difference_greater_veret=self._encoding.unsigned_greater('difference', self._encoding.output_value('verification_et'))
        )

        # remove_double_constraint
        builder.update(remove_double_constraint='\n'.join(
            ' '.join(
                f'Implies({", ".join(self._input_parameters(output_i, product_i, input_i))}),'
                for input_i in self.subgraph_inputs.keys()
            )
            for output_i in self.subgraph_outputs.keys()
            for product_i in range(self._specs.ppo)
        ))

        # remove_zero_permutations_constraint
        lines = []
        for output_i in self.subgraph_outputs.keys():
            parameters = itertools.chain.from_iterable(
                self._input_parameters(output_i, product_i, input_i)
                for product_i in range(self._specs.ppo)
                for input_i in self.subgraph_inputs.keys()
            )
            lines.append(f'Implies(Not({self._output_parameter(output_i)}), Not(Or({", ".join(parameters)}))),')
        builder.update(remove_zero_permutations_constraint='\n'.join(lines))

        # product_order_constraint
        lines = []
        if self._specs.ppo == 1:
            lines.append('# No order needed for only one product')
        else:
            for output_i in self.subgraph_outputs.keys():
                products = tuple(
                    self._encoding.aggregate_variables(itertools.chain.from_iterable(
                        reversed(self._input_parameters(output_i, product_i, input_i))
                        for input_i in self.subgraph_inputs.keys()
                    ))
                    for product_i in range(self._specs.ppo)
                )
                lines.extend(
                    f'{self._encoding.unsigned_greater_equal(product_a, product_b)},'
                    for product_a, product_b in pairwise_iter(products)
                )
        builder.update(product_order_constraint='\n'.join(lines))

        # output_path
        folder, extension = sxpat_paths.OUTPUT_PATH[sxpat_cfg.JSON]
        file_path = f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'
        builder.update(output_path=file_path)


class SOPManager(ProductTemplateManager):

    @classmethod
    def _input_parameters(cls, output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        partial_parameter = f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}_{sxpat_cfg.TREE_PREFIX}{product_i}_{sxpat_cfg.INPUT_LITERAL_PREFIX}{input_i}'
        return (f'{partial_parameter}_{sxpat_cfg.LITERAL_PREFIX}', f'{partial_parameter}_{sxpat_cfg.SELECT_PREFIX}')

    def _update_builder(self, builder: Builder) -> None:
        # apply superclass updates
        super()._update_builder(builder)

        # params_declaration
        builder.update(params_declaration='\n'.join(itertools.chain(
            (
                self._gen_declare_gate(self._output_parameter(output_i))
                for output_i in self.outputs.keys()
            ),
            itertools.chain.from_iterable(
                (
                    self._gen_declare_gate((pars := self._input_parameters(output_i, product_i, input_i))[0]),
                    self._gen_declare_gate(pars[1])
                )
                for output_i in self.subgraph_outputs.keys()
                for product_i in range(self._specs.ppo)
                for input_i in self.subgraph_inputs.keys()
            ),
        )))

        # approximate_wires_constraints
        def get_preds(name: str) -> Collection[str]: return tuple(self._current_graph.graph.predecessors(name))
        def get_func(name: str) -> str: return self._current_graph.graph.nodes[name][sxpat_cfg.LABEL]
        lines = []
        for gate_i, gate_name in self._current_graph.gate_dict.items():
            if not self._current_graph.is_subgraph_member(gate_name):
                gate_preds = get_preds(gate_name)
                gate_func = get_func(gate_name)
                assert (gate_func, len(gate_preds)) in [
                    (sxpat_cfg.NOT, 1),
                    (sxpat_cfg.AND, 2),
                    (sxpat_cfg.OR, 2),
                ], 'invalid gate function/predecessors combination'

                preds = tuple(self._use_approx_var(gate_pred) for gate_pred in gate_preds)
                name = f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}'
                lines.append(
                    f'{self._gen_call_function(name, self.inputs.values())}'
                    f' == {sxpat_cfg.TO_Z3_GATE_DICT[gate_func]}({", ".join(preds)}),'
                )

            # the gate is an output of the subgraph
            elif self._current_graph.is_subgraph_output(gate_name):
                output_i = mapping_inv(self.subgraph_outputs, gate_name)
                output_use = self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}',
                    self.subgraph_inputs.values()
                )
                products = (
                    self._generate_product(functools.partial(self._input_parameters, output_i, product_i))
                    for product_i in range(self._specs.ppo)
                )

                lines.append(f'{output_use} == And({sxpat_cfg.PRODUCT_PREFIX}{output_i}, Or({", ".join(products)}))')
        builder.update(approximate_wires_constraints='\n'.join(lines))

        # logic_dependant_constraint1
        lines = ['# constrain the number of literals']
        for output_i in self.subgraph_outputs.keys():
            for product_i in range(self._specs.ppo):
                state_parameters = (
                    self._input_parameters(output_i, product_i, input_i)[1]
                    for input_i in self.subgraph_inputs.keys()
                )
                lines.append(f'AtMost({", ".join(state_parameters)}, {self._specs.lpp}),')
        builder.update(logic_dependant_constraint1='\n'.join(lines))

        # general informations: benchmark_name, encoding and cell
        builder.update(
            benchmark_name=self._specs.benchmark_name,
            encoding=self._specs.encoding,
            cell=f'({self._specs.lpp}, {self._specs.ppo})',
        )

    def _generate_script(self) -> None:
        # initialize builder object
        builder = Builder.from_file('./sxpat/template_manager/template.py')

        # update the builder with all required strings
        self._update_builder(builder)

        # save finalized template file
        folder, extension = sxpat_paths.OUTPUT_PATH['z3']
        output_file_path = f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'
        with open(output_file_path, 'w') as ofile:
            ofile.write(builder.finalize())

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
        self._string: str = string
        self._kwargs: Dict[str, str] = dict()

    @ classmethod
    def from_file(cls, filename: str) -> Builder:
        with open(filename, 'r') as ifile:
            return cls(ifile.read())

    def update(self, **kwargs: Dict[str, str]) -> None:
        self._kwargs.update(kwargs)

    def finalize(self) -> str:
        # get normalized template string
        normalized_string = (
            self._string
            .replace(self.LEFT_DELIMITER, self.MAGIC_STRING_1)
            .replace(self.RIGHT_DELIMITER, self.MAGIC_STRING_2)
            .replace('{', '{{')
            .replace('}', '}}')
            .replace(self.MAGIC_STRING_1, '{')
            .replace(self.MAGIC_STRING_2, '}')
        )

        # update kwargs with correctly tabulated values
        for key, value in self._kwargs.items():
            if m := re.search(rf'(?:\r\n|\r|\n)(\s+)\{{{key}\}}', normalized_string):
                tabulation = m.group(1)
                self._kwargs[key] = tabulation.join(value.splitlines(True))

        # apply kwargs to the tamplate
        return normalized_string.format(**self._kwargs)

    def __str__(self) -> str:
        return f'{self._string!r} <- {self._kwargs}'
