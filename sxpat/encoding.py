from abc import abstractmethod
from typing import Collection


class Encoding:
    def __init__(self, inputs_count: int, outputs_count: int) -> None:
        self._inputs_count = inputs_count
        self._outputs_count = outputs_count

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

    @abstractmethod
    def function(self, name: str) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.function(...) is abstract.')


class IntegerEncoding(Encoding):
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

    def function(self, name: str) -> str:
        inputs = ', '.join(['BoolSort()'] * self._inputs_count)
        output = f'IntSort()'
        return f"Function('{name}', {inputs}, {output})"


class BitVectorEncoding(Encoding):
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

    def function(self, name: str) -> str:
        inputs = ', '.join(['BoolSort()'] * self._inputs_count)
        output = f'BitVecSort({self._outputs_count})'
        return f"Function('{name}', {inputs}, {output})"
