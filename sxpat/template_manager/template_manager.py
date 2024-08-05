from __future__ import annotations
from typing import Callable, Collection, Dict, Iterable, Sequence, Tuple
import dataclasses as dc

from abc import abstractmethod

import functools
import itertools

import json
import re
import subprocess

from sxpat.annotatedGraph import AnnotatedGraph
import sxpat.config.config as sxpat_cfg
import sxpat.config.paths as sxpat_paths
from sxpat.templateSpecs import TemplateSpecs
from .encoding import Encoding
from sxpat.utils.collections import mapping_inv, pairwise_iter


@dc.dataclass
class Result:
    status: str
    model: Dict[str, bool]


class TemplateManager:
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
            (False, 1): SOPManager,
            (False, 2): SOPManager,
            (True, 1): MultilevelManager if specs.multilevel else SOPSManager,
            (True, 2): MultilevelManager if specs.multilevel else SOPSManager,
            (False, 3): SOP_QBF_Manager,
        }[specs.shared, specs.encoding](
            exact_graph,
            current_graph,
            specs,
            encoding
        )


    def __init__(self, exact_graph: AnnotatedGraph,
                 current_graph: AnnotatedGraph,
                 specs: TemplateSpecs,
                 encoding: Encoding,
                 ) -> None:
        self._exact_graph = exact_graph
        self._current_graph = current_graph
        self._specs = specs
        self._encoding = encoding

    def run(self) -> Sequence[Result]:
        raise NotImplementedError(f'{self.__class__.__name__}.run(...) is abstract.')


class SOP_QBF_Manager(TemplateManager):
    def run(self) -> Sequence[Result]:
        # todo:lorenzo: here
        pass


class Z3TemplateManager(TemplateManager):
    def generate_script(self) -> None:
        # initialize builder object
        builder = Builder.from_file('./sxpat/template_manager/template.py')

        # update the builder with all required strings
        self._update_builder(builder)

        # save finalized template file
        with open(self.script_path, 'w') as ofile:
            ofile.write(builder.finalize())

    def run_script(self) -> None:
        process = subprocess.run(
            [
                sxpat_cfg.PYTHON3,
                self.script_path,
                f'{self._specs.et}',
                f'{self._specs.num_of_models}',
                f'{self._specs.timeout}'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if process.returncode != 0:
            raise RuntimeError(f'ERROR!!! Cannot run file {self.script_path}')

    def parse_results(self) -> Sequence[Result]:
        with open(self.data_path, 'r') as ifile:
            return [
                Result(d[sxpat_cfg.RESULT], d.get(sxpat_cfg.MODEL, None))
                for d in json.load(ifile)
            ]

    def run(self) -> Sequence[Result]:
        # generate z3 python script
        self.generate_script()

        # run the generated script
        self.run_script()

        # parse the results
        return self.parse_results()

    @abstractmethod
    def _update_builder(self, builder: Builder) -> None:
        raise NotImplementedError(f'{self.__class__.__name__}._update_builder(...) is abstract.')

    # utility file names getters

    @property
    @abstractmethod
    def script_path(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.script_path is abstract.')

    @property
    @abstractmethod
    def data_path(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.data_path is abstract.')

    # utility getters

    @property
    def inputs(self) -> Dict[int, str]:
        """The inputs of the grph. (.exact is equal to .current)"""
        return self._exact_graph.input_dict

    @property
    def outputs(self) -> Dict[int, str]:
        """The outputs of the graph. (.exact is equal to .current)"""
        return self._exact_graph.output_dict
    
    @property
    def lv(self):
        return self._specs.lv
    
    @property
    def pit(self):
        return self._specs.pit

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


class ProductTemplateManager(Z3TemplateManager):

    # utility string methods

    @staticmethod
    def _gen_declare_gate(name: str) -> str:
        return f"{name} = Bool('{name}')"

    @staticmethod
    def _gen_declare_bool_function(name: str, inputs_count: int) -> str:
        return f"{name} = Function('{name}', {', '.join(itertools.repeat('BoolSort()', inputs_count + 1))})"

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
        for input_i, input_name in self.subgraph_inputs.items():
            p_l, p_s = parameter_pair_gen(input_i)
            # self._use_approx_var
            multiplexers.append(f'Or(Not({p_s}), {p_l} == {(input_name)})')
        return f'And({", ".join(multiplexers)})'

    def _update_builder(self, builder: Builder) -> None:
        # et_encoded
        builder.update(et_encoded=self._encoding.output_value('et'))

        # num_outputs
        builder.update(num_outputs=self._exact_graph.num_outputs)

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
            self._gen_declare_bool_function(f'{sxpat_cfg.EXACT_OUTPUT_PREFIX}{sxpat_cfg.OUT}{output_i}', len(self.inputs))
            for output_i in self.outputs.keys()
        ))

        # approximate_outputs_declaration
        builder.update(approximate_outputs_declaration='\n'.join(
            self._gen_declare_bool_function(f'{sxpat_cfg.APPROXIMATE_OUTPUT_PREFIX}{sxpat_cfg.OUT}{output_i}', len(self.inputs))
            for output_i in self.outputs.keys()
        ))

        # exact_wires_constraints
        def get_preds(name: str) -> Collection[str]: return tuple(self._exact_graph.graph.predecessors(name))
        def get_preds_approx(name: str) -> Collection[str]: return tuple(self._current_graph.graph.predecessors(name))
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
        ), True)
        builder.update(exact_aggregated_output=f'{function_call}\n== {aggregated_output},')

        # approximate_output_constraints
        lines = []
        for output_name in self.outputs.values():
            output_preds = get_preds_approx(output_name)
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
        ), True)
        builder.update(approximate_aggregated_output=f'{function_call}\n== {aggregated_output},')

        # solver (both forall and verification)
        builder.update(solver=self._encoding.solver)

        # inputs
        builder.update(inputs=', '.join(self.inputs.values()))

        # difference_less_equal_etenc, difference_greater_veret
        builder.update(
            difference_less_equal_etenc=self._encoding.unsigned_less_equal('difference', 'et_encoded'),
            difference_greater_veret=self._encoding.unsigned_greater('difference', self._encoding.output_value('verification_et'))
        )

        # output_path
        builder.update(output_path=self.data_path)


class SOPManager(ProductTemplateManager):

    @property
    def script_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH['z3']
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @property
    def data_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH[sxpat_cfg.JSON]
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @classmethod
    def _input_parameters(cls, output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        partial_parameter = f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}_{sxpat_cfg.TREE_PREFIX}{product_i}_{sxpat_cfg.INPUT_LITERAL_PREFIX}{input_i}'
        return (f'{partial_parameter}_{sxpat_cfg.LITERAL_PREFIX}', f'{partial_parameter}_{sxpat_cfg.SELECT_PREFIX}')

    def _update_builder(self, builder: Builder) -> None:
        # apply superclass updates
        super()._update_builder(builder)

        # params_declaration and params_list
        params = list(itertools.chain(
            (
                self._output_parameter(output_i)
                for output_i in self.subgraph_outputs.keys()
            ),
            itertools.chain.from_iterable(
                self._input_parameters(output_i, product_i, input_i)
                for output_i in self.subgraph_outputs.keys()
                for product_i in range(self._specs.ppo)
                for input_i in self.subgraph_inputs.keys()
            ),
        ))
        builder.update(
            params_declaration='\n'.join(self._gen_declare_gate(p) for p in params),
            params_list=f'[{", ".join(params)}]'
        )

        # approximate_wires_constraints
        def get_preds(name: str) -> Collection[str]:
            return sorted(self._current_graph.graph.predecessors(name), key=lambda n: int(re.search(r'\d+', n).group()))

        def get_func(name: str) -> str: return self._current_graph.graph.nodes[name][sxpat_cfg.LABEL]

        lines = []
        for gate_i, gate_name in self.current_gates.items():
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

                lines.append(f'{output_use} == And({sxpat_cfg.PRODUCT_PREFIX}{output_i}, Or({", ".join(products)})),')
        builder.update(approximate_wires_constraints='\n'.join(lines))

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

        # remove_double_constraint
        builder.update(remove_double_constraint='\n'.join(
            ' '.join(
                f'Implies({", ".join(self._input_parameters(output_i, product_i, input_i))}),'
                for input_i in self.subgraph_inputs.keys()
            )
            for output_i in self.subgraph_outputs.keys()
            for product_i in range(self._specs.ppo)
        ))

        # product_order_constraint
        lines = []
        if self._specs.ppo == 1:
            lines.append('# No order needed for only one product')
        else:
            for output_i in self.subgraph_outputs.keys():
                products = tuple(
                    self._encoding.aggregate_variables(
                        tuple(itertools.chain.from_iterable(
                            reversed(self._input_parameters(output_i, product_i, input_i))
                            for input_i in self.subgraph_inputs.keys()
                        ))
                    )
                    for product_i in range(self._specs.ppo)
                )
                lines.extend(
                    f'{self._encoding.unsigned_greater_equal(product_a, product_b)},'
                    for product_a, product_b in pairwise_iter(products)
                )
        builder.update(product_order_constraint='\n'.join(lines))

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

        builder.update(connection_constraint="")


class SOPSManager(ProductTemplateManager):

    @property
    def script_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH['z3']
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @property
    def data_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH[sxpat_cfg.JSON]
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @classmethod
    def _input_parameters(cls, output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        partial_parameter = f'p_pr{product_i}_{sxpat_cfg.INPUT_LITERAL_PREFIX}{input_i}'
        return (f'{partial_parameter}_{sxpat_cfg.LITERAL_PREFIX}', f'{partial_parameter}_{sxpat_cfg.SELECT_PREFIX}')

    @classmethod
    def _product_parameter(cls, output_i: int, product_i: int) -> str:
        return f'p_pr{product_i}_o{output_i}'

    def _update_builder(self, builder: Builder) -> None:
        # apply superclass updates
        super()._update_builder(builder)

        # params_declaration and params_list
        params = list(itertools.chain(
            (  # p_o#
                self._output_parameter(output_i)
                for output_i in self.subgraph_outputs.keys()
            ),
            itertools.chain.from_iterable(  # p_pr#_i#
                self._input_parameters(None, product_i, input_i)
                for product_i in range(self._specs.pit)
                for input_i in self.subgraph_inputs.keys()
            ),
            (  # p_pr#_o#
                self._product_parameter(output_i, product_i)
                for output_i in self.subgraph_outputs.keys()
                for product_i in range(self._specs.pit)
            ),
        ))
        builder.update(
            params_declaration='\n'.join(self._gen_declare_gate(p) for p in params),
            params_list=f'[{", ".join(params)}]'
        )

        # approximate_wires_constraints
        def get_preds(name: str) -> Collection[str]: return sorted(self._current_graph.graph.predecessors(name), key=lambda n: int(re.search(r'\d+', n).group()))
        def get_func(name: str) -> str: return self._current_graph.graph.nodes[name][sxpat_cfg.LABEL]
        
        lines = []
        for gate_i, gate_name in self.current_gates.items():
            if not self._current_graph.is_subgraph_member(gate_name): #check wheter the node belongs to the subgraph
                gate_preds = get_preds(gate_name) #get all the predecesson of a gate
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
                    f'And({self._product_parameter(output_i, product_i)}, {self._generate_product(functools.partial(self._input_parameters, None, product_i))})'
                    for product_i in range(self._specs.pit)
                )

                lines.append(f'{output_use} == And({sxpat_cfg.PRODUCT_PREFIX}{output_i}, Or({", ".join(products)})),')
        builder.update(approximate_wires_constraints='\n'.join(lines))

        # remove_double_constraint
        builder.update(remove_double_constraint='\n'.join(
            ' '.join(
                f'Implies({", ".join(self._input_parameters(output_i, product_i, input_i))}),'
                for input_i in self.subgraph_inputs.keys()
            )
            for product_i in range(self._specs.ppo)
        ))

        # product_order_constraint
        lines = []
        if self._specs.pit == 1:
            lines.append('# No order needed for only one product')
        else:
            products = tuple(
                self._encoding.aggregate_variables(
                    tuple(itertools.chain.from_iterable(
                        reversed(self._input_parameters(output_i, product_i, input_i))
                        for input_i in self.subgraph_inputs.keys()
                    ))
                )
                for product_i in range(self._specs.pit)
            )
            lines.extend(
                f'{self._encoding.unsigned_greater_equal(product_a, product_b)},'
                for product_a, product_b in pairwise_iter(products)
            )
        builder.update(product_order_constraint='\n'.join(lines))

        # remove_zero_permutations_constraint
        lines = []
        for output_i in self.subgraph_outputs.keys():
            parameters = (
                self._product_parameter(output_i, product_i)
                for product_i in range(self._specs.ppo)
            )
            lines.append(f'Implies(Not({self._output_parameter(output_i)}), Not(Or({", ".join(parameters)}))),')
        builder.update(remove_zero_permutations_constraint='\n'.join(lines))

        # logic_dependant_constraint1
        parameters = (
            self._product_parameter(output_i, product_i)
            for output_i in self.subgraph_outputs.keys()
            for product_i in range(self._specs.pit)
        )
        builder.update(logic_dependant_constraint1='\n'.join([
            '# Force the number of inputs to sum to be at most `its`',
            f'AtMost({", ".join(parameters)}, {self._specs.lpp}),'
        ]))

        builder.update(connection_constraint='')

        # general informations: benchmark_name, encoding and cell
        builder.update(
            benchmark_name=self._specs.benchmark_name,
            encoding=self._specs.encoding,
            cell=f'({self._specs.lpp}, {self._specs.pit})',
        )

class MultilevelManager(ProductTemplateManager):

    @property
    def script_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH['z3']
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @property
    def data_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH[sxpat_cfg.JSON]
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'
    
    @staticmethod
    def _input_parameters(input_i: int, node_i: int) -> Tuple[str, str]:
        partial_parameter = f'p_{sxpat_cfg.INPUT_LITERAL_PREFIX}{input_i}_n{node_i}'
        return (f'{partial_parameter}_{sxpat_cfg.LITERAL_PREFIX}', f'{partial_parameter}_{sxpat_cfg.SELECT_PREFIX}')
    
    @staticmethod
    def _node_connection_levels(from_n: int, from_lv: int, to_n: int, to_lv:int) -> str:
        return f'p_con_fn{from_n}_lv{from_lv}_tn{to_n}_lv{to_lv}'
    
    @staticmethod
    def _node_connection_output(from_n: int, output_i: int) -> str:
        return f'p_con_fn{from_n}_to{output_i}'
    
    @staticmethod
    def _switch_parameter_levels(from_n: int, from_lv: int, to_n: int, to_lv:int):
        return f'p_sw_fn{from_n}_lv{from_lv}_tn{to_n}_lv{to_lv}'
    
    @staticmethod
    def _switch_parameter_output(from_n: int, to_out_i: int):
        return f'p_sw_fn{from_n}_to{to_out_i}'

    @staticmethod
    def _level_parameter(node_i: int,level_i: int):
        return f'n{node_i}_lv{level_i}'
    
    @staticmethod
    def _output_negation(output_i: int):
        return f'neg_o{output_i}'
    
    @staticmethod
    def _output_identifier(output_i :int):
        return f'out_id{output_i}'

    # ----------------------------- # ----------------------------- # ----------------------------- # ----------------------------- #

    def _multiplexer_multilevel(self,input_i,input_i__name,node_i):
        return f'\n     {sxpat_cfg.Z3_OR}({self._input_parameters(input_i,node_i)[0]} == {input_i__name},{sxpat_cfg.Z3_NOT}({self._input_parameters(input_i,node_i)[1]}))'
    
    # ----------------------------- # ----------------------------- # ----------------------------- # ----------------------------- #
    def _edge_constraint(self, vars: Collection[str]) -> str:
        return ' + '.join(
            f'If({var}, {1}, 0)'
            for var in vars
        )
    
    # ----------------------------- # ----------------------------- # ----------------------------- # ----------------------------- #
    def _generate_input(self,node_i):
        multiplexers = []
        for input_i, input_name in self.subgraph_inputs.items():
            # self._use_approx_var
            multiplexers.append(self._multiplexer_multilevel(input_i,input_name,node_i))
        return f'{", ".join(multiplexers)},'
    
    # ----------------------------- # ----------------------------- # ----------------------------- # ----------------------------- #
    def _generate_output(self, node_i,output_i):
        return f'\n{sxpat_cfg.IF}({self._node_connection_output(node_i,output_i)}, {sxpat_cfg.IF}({self._switch_parameter_output(node_i, output_i)}, {self._gen_call_function(self._level_parameter(node_i,self._specs.lv - 1),self.subgraph_inputs.values())}, {sxpat_cfg.Z3_NOT}({self._gen_call_function(self._level_parameter(node_i, self._specs.lv - 1),self.subgraph_inputs.values())})), {sxpat_cfg.IF}({self._switch_parameter_output(node_i, output_i)}, True, False))'

    # ----------------------------- # ----------------------------- # ----------------------------- # ----------------------------- #
    def _connection_constraints(self, npl, level_i, gate, output_i = None):
        gates_per_level = ""
        #base case
        if level_i == len(npl):
            return self._generate_output(gate,output_i)
        elif level_i == 0:
            return self._generate_input(gate)
        
        for node in range(npl[level_i-1]): #param connection from node# to node#s
            gates_per_level += f'\n{sxpat_cfg.IF}({self._node_connection_levels(node,level_i-1,gate,level_i)}, {sxpat_cfg.IF}({self._switch_parameter_levels(node,level_i-1,gate,level_i)}, {self._gen_call_function(self._level_parameter(node,level_i-1),self.subgraph_inputs.values())}, {sxpat_cfg.Z3_NOT}({self._gen_call_function(self._level_parameter(node,level_i-1),self.subgraph_inputs.values())})), True),'
        return gates_per_level

    # ----------------------------- # ----------------------------- # ----------------------------- # ----------------------------- #
    def _generate_levels(self,npl):
        gates_per_level = []
        for level_i in range(len(npl)):
            for gate in range( npl[level_i]):
                gates_per_level.append(f'\n#level: {level_i}\n{self._gen_call_function(self._level_parameter(gate,level_i),self.subgraph_inputs.values())} == {sxpat_cfg.Z3_AND}({self._connection_constraints(npl, level_i, gate)}),')
        return gates_per_level
    
    # ----------------------------- # ----------------------------- # ----------------------------- # ----------------------------- #
    def _update_builder(self, builder: Builder) -> None:
        # apply superclass updates
        super()._update_builder(builder)
        print("Multilevel")
        print(f'number of sub_outputs in template gen = {self.subgraph_outputs.__len__()}')
        print(f'number of sub_inputs in template gen = {self.subgraph_inputs.__len__()}')
        print(f'number of levels = {self._specs.lv}')
        print(f'actual level(lpp) = {self._specs.lpp}')
        print(f'actual node per level (pit) = {self._specs.pit}')
        # Node Per Level
        # initialization gpl
        # Amedeo: note that this could be parametrized with different number of gates for each level
        npl = [self.pit]*self.lv
        # npl = [self._specs.pit]*self._specs.lpp
        # npl[0] = self.subgraph_inputs.__len__()
        npl[len(npl)-1] = self.subgraph_outputs.__len__()
        # npl[self.lv - 1] = self.subgraph_outputs.__len__()
        print(f'npl = {npl}')
        

        # params_declaration
        # ----------------------------- # ----------------------------- #
        builder.update(params_declaration='\n'.join(
                itertools.chain(                                            
                    itertools.chain.from_iterable
                    (
                        (
                            self._gen_declare_gate(self._switch_parameter_levels(f_nd,lv-1,t_nd,lv)),   # p_sw_fn#_lv#_tn#_lv#
                            self._gen_declare_gate(self._node_connection_levels(f_nd,lv-1,t_nd,lv)),    # p_con_fn#_lv#_tn#_lv#
                        )
                        for lv in range(len(npl)-1,0,-1)
                        for t_nd in range(npl[lv])
                        for f_nd in range(npl[lv-1])
                    ),
                    itertools.chain.from_iterable
                    (
                        (
                            self._gen_declare_gate((pars := self._input_parameters(input_i,nd))[0]),   # p_i#_n#_l
                            self._gen_declare_gate(pars[1])                                            # p_i#_n#_s 
                        )
                        for input_i in range(self.subgraph_inputs.__len__())
                        for nd in range(npl[0]) 
                    ),
                    itertools.chain.from_iterable
                    (   
                        (
                            self._gen_declare_gate(self._node_connection_output(nd,output_i)),  # p_con_fn#_to#
                            self._gen_declare_gate(self._switch_parameter_output(nd,output_i))  # p_sw_fn#_to#                
                        )
                        for output_i in range(self.subgraph_outputs.__len__())
                        for nd in range(npl[len(npl)-1])
                    ),  
                    itertools.chain
                    ( 
                        self._gen_declare_bool_function(self._level_parameter(nd,lv),len(self.subgraph_inputs))    # function n#_lv# 
                        # for lv in range(self._specs.lpp)
                        for lv in range(self._specs.lv)
                        for nd in range(npl[lv])
                    ),
                ),
            )
        )

        builder.update(params_list = '[{}]'.format(','.join(
                itertools.chain(                                            
                    itertools.chain.from_iterable
                    (
                        (
                            self._switch_parameter_levels(f_nd,lv-1,t_nd,lv),   # p_sw_fn#_lv#_tn#_lv#
                            self._node_connection_levels(f_nd,lv-1,t_nd,lv),    # p_con_fn#_lv#_tn#_lv#
                        )
                        for lv in range(len(npl)-1,0,-1)
                        for t_nd in range(npl[lv])
                        for f_nd in range(npl[lv-1])
                    ),
                    itertools.chain.from_iterable
                    (
                        (
                            self._input_parameters(input_i,nd)[0],   # p_i#_n#_l
                            self._input_parameters(input_i,nd)[1]    # p_i#_n#_s 
                        )
                        for input_i in range(self.subgraph_inputs.__len__())
                        for nd in range(npl[0]) 
                    ),
                    itertools.chain.from_iterable
                    (   
                        (
                            self._node_connection_output(nd,output_i),  # p_con_fn#_to#
                            self._switch_parameter_output(nd,output_i)  # p_sw_fn#_to#                
                        )
                        for output_i in range(self.subgraph_outputs.__len__())
                        for nd in range(npl[len(npl)-1])
                    ), 
                )
            )))
        # approximate_wires_constraints
        # ----------------------------- # ----------------------------- #
        def get_preds(name: str) -> Collection[str]: return sorted(self._current_graph.graph.predecessors(name), key=lambda n: int(re.search(r'\d+', n).group()))
        def get_func(name: str) -> str: return self._current_graph.graph.nodes[name][sxpat_cfg.LABEL]

        lines = []
        multilevel_structure = '\n'.join(self._generate_levels(npl)) + '\n'
        lines.append(multilevel_structure)
        for gate_i, gate_name in self.current_gates.items():
            if not self._current_graph.is_subgraph_member(gate_name): #check wheter the node belongs to the subgraph
                gate_preds = get_preds(gate_name) #get all the predecesson of a gate
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
            
            elif self._current_graph.is_subgraph_output(gate_name):
                
                output_i = mapping_inv(self.subgraph_outputs, gate_name)

                output_use = self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}', #that's why we have plus 8 or something in a#
                    self.subgraph_inputs.values()
                )

                #TODO: constraint at least one connection to the output
                output_selection = ', '.join(
                                itertools.chain(
                                    f'{self._connection_constraints(npl,len(npl),gate,output_i)}'
                                    for gate in range(npl[len(npl)-1])
                                )
                            )
                #lines.append(f'{self._gen_call_function(self._output_identifier(output_i),self.subgraph_inputs.values())} == {output_selection},')
                #lines.append(f'{output_use} == {sxpat_cfg.IF}({self._output_negation(output_i)},\n{sxpat_cfg.Z3_AND}({self._gen_call_function(self._output_identifier(output_i),self.subgraph_inputs.values())}),\n{sxpat_cfg.Z3_NOT}({self._gen_call_function(self._output_identifier(output_i), self.subgraph_inputs.values())})),') 
                lines.append(f'{output_use} == {sxpat_cfg.Z3_OR}({output_selection}),') 
        builder.update(approximate_wires_constraints='\n'.join(lines))

        # ----------------------------- # ----------------------------- #

        # remove_double_constraint -> # remove double no-care
        builder.update(remove_double_constraint= '\n'.join(
            itertools.chain(
                f'Implies({",".join(self._input_parameters(input_i,nd))}),'
                for input_i in self.subgraph_inputs.keys()
                for nd in range(npl[0])
            )
        ))
        # ----------------------------- # ----------------------------- #
        #logic dependant constraint

        # ode connection constraint
        # lines = []
        # lines.append('# node connection constraint')
        # for lv in range(len(npl)-1):
        #     lines.append(
        #         ' + '.join(
        #             itertools.chain
        #             (
        #                 (
        #                     f'If({self._node_connection_levels(f_nd,lv,t_nd,lv+1)},1,0)'    # p_con_fn#_lv#_tn#_lv#
        #                 )
        #                 for t_nd in range(npl[lv+1])
        #                 for f_nd in range(npl[lv])
        #             ),
        #         ) + ' >= 1,' 
        #     )
        # connect at least one node to the output
        # lines.append('\n# At least one node connect to the output')
        # for output_i in self.subgraph_outputs.keys():
        #     lines.append(f'# Constraint for output {output_i}')
        #     output_i_constraint = 'Or({}),'.format(', '.join(
        #         itertools.chain
        #         (
        #             self._node_connection_output(nd,output_i)  # p_con_fn#_to#               
        #             for nd in range(npl[len(npl)-1])
        #         )
        #     ))
        #     lines.append(output_i_constraint) 
        builder.update(logic_dependant_constraint1 = '\n'.join(lines))


        # product_order_constraint
        # list_of_constraint = []
        # for lv in range(len(npl)):
        #     if npl[lv] == 1:
        #         lines.append(f'# No order needed for only one node at - level: {lv}')
        #     else:
        #         if lv == len(npl) - 1:
        #             list_of_constraint.append(

        #             )
        #             continue
        #         else:
        #             continue

        builder.update(product_order_constraint='')
        # ----------------------------- # ----------------------------- #
    
        #TODO: impement the following constraint
        #at least one node between each level
        #at least one node connected to the output

        # remove_zero_permutations_constraint
        # TODO: add it for all outpus
        lines = [""]
        """ lines.append('\n# At least one node connect to the output')
        for output_i in self.subgraph_outputs.keys():
            lines.append(f'# Constraint for output {output_i}')
            output_i_constraint = 'Or({}),'.format(', '.join(
                itertools.chain
                (
                    self._node_connection_output(nd,output_i)  # p_con_fn#_to#               
                    for nd in range(npl[len(npl)-1])
                )
            ))
            lines.append(output_i_constraint)"""
        builder.update(remove_zero_permutations_constraint='\n'.join(lines))
        # builder.update(remove_zero_permutations_constraint='\n{}\nOr({}),'.format(
        #     '# At least one node connect to the output',
        #     ','.join(
        #         itertools.chain
        #         (
        #             self._node_connection_output(nd,output_i)  # p_con_fn#_to#               
        #             for output_i in self.subgraph_outputs.keys()
        #             for nd in range(npl[len(npl)-1])
        #         )
        #     )
        # ))

        # ----------------------------- # ----------------------------- #
        # general informations: benchmark_name, encoding and cell
        builder.update(
            benchmark_name=self._specs.benchmark_name,
            encoding=self._specs.encoding,
            cell=f'({self._specs.lpp}, {self._specs.pit})',
        )

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
            if m := re.search(rf'(?:\r\n|\r|\n)([\t ]+)\{{{key}\}}', normalized_string):
                tabulation = m.group(1)
                self._kwargs[key] = tabulation.join(value.splitlines(True))

        return normalized_string.format(**self._kwargs)

    def __str__(self) -> str:
        return f'{self._string!r} <- {self._kwargs}'
