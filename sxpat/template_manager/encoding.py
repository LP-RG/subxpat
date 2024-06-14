from __future__ import annotations
from abc import abstractmethod
from typing import Collection


class Encoding:
    """
    Encoding interface
    """

    def __init__(self,
                 inputs_count: int, outputs_count: int,
                 # full_inputs: Collection[str], sub_inputs: Collection[str],
                 # full_outputs: Collection[str], sub_outputs: Collection[str]
                 ) -> None:
        self._inputs_count = inputs_count
        self._outputs_count = outputs_count
        # self._full_inputs = full_inputs
        # self._sub_inputs = sub_inputs
        # self._full_outputs = full_outputs
        # self._sub_outputs = sub_outputs

    @staticmethod
    def factory(encoding_id: int,
                inputs_count: int, outputs_count: int,
                # full_inputs: Collection[str], sub_inputs: Collection[str],
                # full_outputs: Collection[str], sub_outputs: Collection[str]
                ) -> Encoding:
        # select and return Encoding object
        return {
            1: IntegerEncoding,
            2: BitVectorEncoding,
        }[encoding_id](inputs_count, outputs_count)

    @property
    @abstractmethod
    def solver(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.solver(...) is abstract.')

    @property
    @abstractmethod
    def sort(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.sort(...) is abstract.')

    @abstractmethod
    def unsigned_greater_equal(self, a: str, b: str) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.unsigned_greater_equal(...) is abstract.')

    @abstractmethod
    def unsigned_less_equal(self, a: str, b: str) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.unsigned_less_equal(...) is abstract.')

    def abs_diff(self, a: str, b: str) -> str:
        return f'If({self.unsigned_greater_equal(a, b)}, {a} - {b}, {b} - {a})'

    @abstractmethod
    def output_value(self, value: str) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.output_value(...) is abstract.')

    @abstractmethod
    def output_variable(self, name: str) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.output_variable(...) is abstract.')

    @abstractmethod
    def aggregate_variables(self, vars: Collection[str]) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.aggregate_variables(...) is abstract.')

    def function(self, name: str) -> str:
        inputs = ', '.join(['BoolSort()'] * self._inputs_count)
        return f"Function('{name}', {inputs}, {self.sort})"

    # @abstractmethod
    # def declare_gate_step1(self, name: str) -> str:
    #     raise NotImplementedError(f'{self.__class__.__name__}.declare_gate_step1(...) is abstract.')

    # @abstractmethod
    # def declare_gate_step2(self, name: str) -> str:
    #     raise NotImplementedError(f'{self.__class__.__name__}.declare_gate_step1(...) is abstract.')


class IntegerEncoding(Encoding):
    """
    Concrete Encoding

    defines:
     - data type operations
    """

    @property
    def solver(self) -> str:
        return 'Solver()'

    @property
    def sort(self) -> str:
        return 'IntSort()'

    def unsigned_greater_equal(self, a: str, b: str) -> str:
        return f'{a} >= {b}'

    def unsigned_less_equal(self, a: str, b: str) -> str:
        return f'{a} <= {b}'

    def output_value(self, value: str) -> str:
        return f'IntVal({value})'

    def output_variable(self, name: str) -> str:
        return f'Int({name})'

    def aggregate_variables(self, vars: Collection[str]) -> str:
        return ' + '.join(
            f'If({var}, {2**i}, 0)'
            for i, var in enumerate(vars)
        )


class BitVectorEncoding(Encoding):
    """
    Concrete Encoding

    defines:
        - data type operations
    """

    @property
    def solver(self) -> str:
        return "SolverFor('BV')"

    @property
    def sort(self) -> str:
        return f'BitVecSort({self._outputs_count})'

    def unsigned_greater_equal(self, a: str, b: str) -> str:
        return f'UGE({a}, {b})'

    def unsigned_less_equal(self, a: str, b: str) -> str:
        return f'ULE({a}, {b})'

    def _value(self, value: str, length: int) -> str:
        return f'BitVecVal({value}, {length})'

    def output_value(self, value: str) -> str:
        return self._value(value, self._outputs_count)

    def _variable(self, name: str, length: int) -> str:
        return f"BitVec('{name}', {length})"

    def output_variable(self, name: str) -> str:
        return self._variable(name, self._outputs_count)

    def aggregate_variables(self, vars: Collection[str]) -> str:
        bits_count = len(vars)
        return ' + '.join(
            f'If({var}, {self._value(2 ** i, bits_count)}, {self._value(0, bits_count)})'
            for i, var in enumerate(vars)
        )


# class FunctionEncoding(Encoding):
#     """
#     Abstract Encoding: defining behavioural operations
#     """

#     def _use(self, name: str) -> str:
#         if name in self._full_inputs:
#             return name

#         inputs = self._sub_inputs if name in self._sub_outputs else self._full_inputs
#         args = ', '.join(self._use(g) for g in inputs)
#         return f'{name}({args})'

#     def declare_gate_step1(self, name: str) -> str:
#         count = 1 + len(self._sub_inputs if name in self._sub_outputs else self._full_inputs)
#         bool_refs = ', '.join(['BoolSort()'] * count)
#         return f"{name} = Function('name', {bool_refs})"

#     @abstractmethod
#     def declare_gate_step2(self, name: str) -> str:
#         return f'{self._use(name)} == '
#         raise NotImplementedError(f'{self.__class__.__name__}.declare_gate_step1(...) is abstract.')


# class DirectEncoding(Encoding):
#     """
#     Abstract Encoding: defining behavioural operations
#     """

#     def declare_gate_step1(self, name: str) -> str:
#         # count = 1 + len(self._sub_inputs if name in self._sub_outputs else self._full_inputs)
#         # bool_refs = ', '.join(['BoolSort()'] * count)
#         return f"{name} = Function('name', {bool_refs})"

#     @abstractmethod
#     def declare_gate_step2(self, name: str) -> str:
#         raise NotImplementedError(f'{self.__class__.__name__}.declare_gate_step1(...) is abstract.')