from __future__ import annotations
from abc import abstractmethod
import itertools
from typing import Callable, Collection, Dict, Tuple, Union

from sxpat.annotatedGraph import AnnotatedGraph
import sxpat.config.config as sxpat_cfg
from sxpat.templateSpecs import TemplateSpecs
from .encoding import Encoding


class TemplateManager:
    def __init__(self, exact_graph: AnnotatedGraph, current_graph: AnnotatedGraph,
                 specs: TemplateSpecs, encoding: Encoding) -> None:
        self._exact_graph = exact_graph
        self._current_graph = current_graph
        self._specs = specs
        self._encoding = encoding

    @staticmethod
    def factory(graph: AnnotatedGraph, specs: TemplateSpecs):
        # create required Encoding object
        encoding = Encoding.factory(
            specs.encoding, graph.num_inputs, graph.num_outputs)

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

    @classmethod
    def run(cls, graph: AnnotatedGraph, specs: TemplateSpecs) -> Dict:
        # create manager instance
        instance = cls(graph, specs)

        # generate z3 python script
        instance._generate_script()

        # run the generated script
        instance._run_script()

        # parse the results
        results = instance._parse_result()

        return results


class ProductTemplateManager(TemplateManager):
    @staticmethod
    def _gen_declare_gate(name: str) -> str:
        return f"{name} = Bool('{name}')"

    @staticmethod
    def _gen_declare_function(name: str, inputs_count: int) -> str:
        return f"{name} = Function('{name}', {', '.join(itertools.repeat('BoolSort()', inputs_count + 1))})"

    def _gen_inputs_as_arguments(self) -> str:
        return ', '.join(self._exact_graph.input_dict.values())

    def _use_var(self, name: str) -> str:
        if name in self._exact_graph.input_dict.values():
            return name

        inputs = self._current_graph.subgraph_input_dict.values() if name in self._current_graph.subgraph_input_dict.values() else self._exact_graph.input_dict.values()
        args = ', '.join(self._use_var(g) for g in inputs)
        return f'{name}({args})'

    def _generate_product(self, parameter_pair_gen: Callable[[int], Tuple[str, str]]) -> str:
        multiplexers = []
        for input_i, input_name in self._current_graph.subgraph_input_dict.items():
            p_l, p_s = parameter_pair_gen(input_i)
            multiplexers.append(f'Or(Not({p_s}), {p_l} == {self._use_var(input_name)})')

        return f'And({", ".join(multiplexers)})'


class SOPManager(ProductTemplateManager):
    @staticmethod
    def _input_parameters(output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        partial_parameter = f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}_{sxpat_cfg.TREE_PREFIX}{product_i}_{sxpat_cfg.INPUT_LITERAL_PREFIX}{input_i}'
        return (f'{partial_parameter}_{sxpat_cfg.LITERAL_PREFIX}', f'{partial_parameter}_{sxpat_cfg.SELECT_PREFIX}')

    def _output_parameter(output_i: int) -> str:
        return f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}'

    def _generate_script(self) -> None:
        builder = Builder.from_file('./template.py')

        #
        builder.update(ET_BV=f"ET_BV = {self._encoding.output_value('ET')}")

        #
        builder.update(abs_diff_def=self._encoding.abs_diff('a', 'b'))

        #
        builder.update(ini_defs='\n'.join(
            self._gen_declare_gate(input_name)
            for input_name in self._exact_graph.input_dict.values()
        ))

        #
        builder.update(function_exact=self._encoding.function('fe'))
        builder.update(function_approximate=self._encoding.function('fa'))

        #
        builder.update(gen_inputs_arguments=self._gen_inputs_as_arguments())

        #
        builder.update(error=self._encoding.output_variable('error'))

        #
        builder.update(params_declaration='\n'.join(itertools.chain(
            (
                self._gen_declare_gate(self._output_parameter(output_i))
                for output_i in self._exact_graph.output_dict.keys()
            ),
            itertools.chain.from_iterable(
                (
                    self._gen_declare_gate((pars := self._input_parameters(output_i, product_i, input_i))[0]),
                    self._gen_declare_gate(pars[1])
                )
                for output_i in self._exact_graph.output_dict.keys()
                for product_i in self._specs.ppo
                for input_i in self._exact_graph.input_dict.keys()
            ),
        )))

        #
        builder.update(wires_exact_declaration='\n'.join(
            self._gen_declare_function(f'{sxpat_cfg.EXACT_WIRES_PREFIX}{len(self._exact_graph.input_dict) + gate_i}', len(self._exact_graph.input_dict))
            for gate_i in itertools.chain(self._exact_graph.gate_dict.keys(), self._exact_graph.constant_dict.keys())
        ))

        wires_approximate_declaration
        outputs_exact_declaration
        outputs_approximate_declaration
        exact_constraints
        approximate_constraints
        boolean_outputs
        approximate_outputs
        forall_solver
        verification_solver
        difference_constraint
        data_object
        output_path
        circuit_name
        encoding
        cell

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

    @classmethod
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
