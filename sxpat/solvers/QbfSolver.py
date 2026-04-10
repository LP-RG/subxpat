"""
    :author: Lorenzo Spada
"""

from typing import IO, Any, Callable, Iterable, Mapping, Optional, Sequence, Tuple, TypeVar, Union, Dict, List, Protocol
from typing_extensions import TypeAlias, Self

import copy
import subprocess
from itertools import chain, count
from collections import deque
from os.path import join as path_join

from .Solver import Solver

from sxpat.graph.graph import *
from sxpat.graph.node import *
from sxpat.specifications import Specifications
from sxpat.converting.utils import set_bool_constants, crystallise as crystallize


_Graphs = TypeVar('_Graphs', bound=Sequence[Union[IOGraph, PGraph, SGraph]])
NodeID: TypeAlias = str
NodeIDSeq: TypeAlias = Sequence[NodeID]


# first elements of list should always be the least significant digit
# `destination` is instead the file where the qbf code needs to be written

# This format uses gates, I used a prefix for every type of gates, all the ones that starts with 4 are the 'free' gates:
# all those that don't have a specific purpose but are used in all the functions

# 1 is for the inputs
# 4 is for the free gates
# 7 is for the variables/parameters
# 90 is for the satisfability problem
# 91 true constant
# 92 false constant

# TRUE = '91'
# FALSE = '92'

class node_maker_varargs(Protocol):
    def __call__(self, *n: NodeID) -> NodeID: ...


class node_maker_seq(Protocol):
    def __call__(self, ns: NodeIDSeq) -> NodeID: ...


class NodeIdGen:
    def __init__(self): self._id_iter = count()
    def _next(self): return next(self._id_iter)

    def gen_input(self): return f'1{self._next()}'
    def gen_free_gate(self): return f'4{self._next()}'
    def gen_variable(self): return f'7{self._next()}'
    def gen_parameter(self): return f'7{self._next()}'
    def get_sat_problem(self): return '90'
    def get_const_true(self): return '91'
    def get_const_false(self): return '92'
    def get_const(self, v: bool): return self.get_const_true() if v else self.get_const_false()


class Encoder:
    def __init__(self, id_gen: NodeIdGen, file: IO[str]):
        self.id_gen = id_gen
        self.file = file

        self.node_processors = {
            # variables
            BoolVariable: self.process_BoolVariable,
            IntVariable: self.process_IntVariable,  # TODO: implement
            # constants
            BoolConstant: self.process_BoolConstant,
            IntConstant: self.process_IntConstant,
            # output
            Identity: self.process_Identity,
            Target: self.process_Target,
            # placeholder
            PlaceHolder: self.process_PlaceHolder,
            # boolean operations
            Not: self.process_Not,
            And: self.process_And,
            Or: self.process_Or,
            Xor: self.process_Xor,  # Needs testing
            Implies: self.process_Implies,
            # integer operations
            Sum: self.process_Sum,
            AbsDiff: self.process_AbsDiff,
            Mul: self.process_Mul,
            # comparison operations
            Equals: self.process_Equals,  # Needs testing
            NotEquals: self.process_NotEquals,  # Needs testing
            LessThan: self.process_LessThan,  # Needs testing
            LessEqualThan: self.process_LessEqualThan,
            GreaterThan: self.process_GreaterThan,
            GreaterEqualThan: self.process_GreaterEqualThan,
            # quantifier operations
            AtLeast: self.process_AtLeast,
            AtMost: self.process_AtMost,
            # branching operations
            Multiplexer: self.process_Multiplexer,
            If: self.process_If,  # Needs testing for Integers
            ToInt: self.process_ToInt,
            Constraint: self.process_Constraint,
        }

    def __make_gate_func(gate_operator: str) -> Union[node_maker_varargs, node_maker_seq]:
        def write_gate(self: Self, *o) -> NodeID:
            if len(o) == 1 and not isinstance(o[0], str): o = o[0]
            gate = self.id_gen.gen_free_gate()
            self.file.write(f'{gate} = {gate_operator}({", ".join(o)})\n')
            self.file.write(f'#{gate_operator}\n')
            return gate

        return write_gate

    _and = __make_gate_func('and')
    _or = __make_gate_func('or')
    _xor = __make_gate_func('xor')

    def _not(self, o: NodeID) -> NodeID:
        gate = self.id_gen.gen_free_gate()
        self.file.write(f'{gate} = and(-{o})\n')
        return gate

    def _adder_bit3(self, a: NodeID, b: NodeID, c: NodeID) -> NodeIDSeq:
        results = []
        partial_xor = self._xor(a, b)
        results.append(self._xor(partial_xor, c))
        partial_and1 = self._and(a, b)
        partial_and2 = self._and(c, partial_xor)
        results.append(self._or(partial_and1, partial_and2))
        self.file.write('#add3\n')
        return results

    def _adder(self, a: NodeIDSeq, b: NodeIDSeq, carry: bool = False) -> NodeIDSeq:
        if len(a) == 0:
            a.append(self.id_gen.get_const_false())
        if len(a) < len(b):
            a, b = b, a
        while len(b) < len(a):
            b.append(self.id_gen.get_const_false())

        results = [self._xor(a[0], b[0])]
        carry_in = self._and(a[0], b[0])
        for i in range(1, len(a)):
            next, carry_in = self._adder_bit3(a[i], b[i], carry_in)
            results.append(next)

        if carry:
            results.append(carry_in)
        self.file.write('#add\n')

        return results

    def _multiplier(self, a: NodeIDSeq, b: NodeIDSeq) -> NodeIDSeq:
        #
        n = len(a)
        m = len(b)

        #
        result = [self.id_gen.get_const_false()] * (n + m)
        for i, bi in enumerate(b):
            partial = [self.id_gen.get_const_false()] * i + [self._and(aj, bi) for aj in a]
            result = self._adder(result, partial)
        self.file.write('#mul\n')

        return result

    def _inverse(self, a: NodeIDSeq) -> NodeIDSeq:
        return [self._not(x) for x in a]

    def _increment(self, a: NodeIDSeq, carry: bool = False) -> NodeIDSeq:
        assert len(a) > 0, "length of a should be higher than 0"

        if carry:
            a.append(a[-1])

        results = [self._not(a[0])]
        last_and = a[0]
        for i in range(1, len(a)):
            results.append(self._xor(last_and, a[i]))
            last_and = self._and(last_and, a[i])

        return results

    def _test_equality_bits(self, a: NodeID, b: NodeID) -> NodeID:
        and1 = self._and(a, b)
        and2 = self._and(f'-{a}', f'-{b}')
        self.file.write('#testeqbits\n')
        return self._or(and1, and2)

    def _test_equality_list(self, a: NodeIDSeq, b: NodeIDSeq) -> NodeID:
        # normalize
        while len(a) < len(b):
            a.append(self.id_gen.get_const_false())
        while len(b) < len(a):
            b.append(self.id_gen.get_const_false())

        #
        equals = [
            self._test_equality_bits(ai, bi)
            for ai, bi in zip(a, b)
        ]
        self.file.write('#testeqlist\n')
        return self._and(equals)

    def _comparator_greater_than(self, a: NodeIDSeq, b: NodeIDSeq, or_equal: bool = False) -> NodeID:
        # TODO: many other versions of comparator

        while len(a) < len(b):
            a.append(self.id_gen.get_const_false())
        while len(b) < len(a):
            b.append(self.id_gen.get_const_false())

        equal = []
        one_of = []
        for i in range(len(a) - 1, -1, -1):

            to_be_anded: Iterable[str]
            if i > 0 or not or_equal:
                to_be_anded = [a[i], f'-{b[i]}']
            else:
                save = self._and(f'-{a[i]}', b[i])
                to_be_anded = [f'-{save}']

            one_of.append(self._and(chain(to_be_anded, equal)))
            equal.append(self._test_equality_bits(a[i], b[i]))

        return self._or(one_of)

    def _xor_bits_with_bit(self, a: NodeIDSeq, b: NodeID) -> NodeIDSeq:
        return [self._xor(ai, b) for ai in a]

    def _adder_bits_with_bit(self, a: NodeIDSeq, b: NodeID) -> NodeIDSeq:
        results = []
        last_and = b
        for ai in a:
            results.append(self._xor(last_and, ai))
            last_and = self._and(last_and, ai)
        return results

    def _absolute_value(self, a: NodeIDSeq) -> NodeIDSeq:
        return self._adder_bits_with_bit(self._xor_bits_with_bit(a, a[-1]), a[-1])

    def _count_bits(self, a: NodeIDSeq) -> NodeIDSeq:
        # TODO: optimize for various numbers

        remaining = deque(a, len(a))
        while len(remaining) >= 2:
            n0 = remaining.popleft()
            n1 = remaining.popleft()
            remaining.append(self._adder(n0, n1, True))

        return remaining.popleft()

    def _num_to_bits(self, v: int) -> NodeIDSeq:
        return [self.id_gen.get_const((v >> i) & 1) for i in range(v.bit_length())]

    def process_BoolVariable(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        pass

    def process_IntVariable(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        raise NotImplementedError(f'this function isn\'t implemented yet')

    def process_BoolConstant(
        self,
        n: BoolConstant, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        mapping[n.name] = [self.id_gen.get_const(n.value)]

    def process_IntConstant(
        self,
        n: IntConstant, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        mapping[n.name] = self._num_to_bits(n.value)

    def process_Identity(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        mapping[n.name] = mapping[operands[0]]

    def process_Target(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        pass

    def process_PlaceHolder(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        pass

    def process_Not(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        gate = self._not(mapping[operands[0]][0])
        mapping[n.name] = [gate]

    def process_And(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        gate = self._and(mapping[x][0] for x in operands)
        mapping[n.name] = [gate]

    def process_Or(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        gate = self._or(mapping[x][0] for x in operands)
        mapping[n.name] = [gate]

    def process_Xor(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        mapping[n.name] = [self._xor(mapping[operands[0]][0], mapping[operands[1]][0])]

    def process_Implies(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        gate1 = self._and(mapping[operands[0]][0], f'-{mapping[operands[1]][0]}')
        gate2 = self._not(gate1)
        mapping[n.name] = [gate2]

    def process_Sum(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        if len(operands) == 0:
            mapping[n.name] = [self.id_gen.get_const_false()]

        else:
            num = mapping[operands[0]]
            for i in range(1, len(operands)):
                num = self._adder(num, mapping[operands[i]], carry=True)

            mapping[n.name] = num

    def process_Mul(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        if len(operands) == 0:
            mapping[n.name] = [self.id_gen.get_const_false()]

        else:
            num = mapping[operands[0]]
            for i in range(1, len(operands)):
                num = self._multiplier(num, mapping[operands[i]])

            mapping[n.name] = num

    def process_AbsDiff(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        # TODO: remove one bit

        mapping[operands[0]].append(self.id_gen.get_const_false())
        mapping[operands[1]].append(self.id_gen.get_const_false())

        sub = self._increment(self._inverse(mapping[operands[1]]))
        mapping[n.name] = self._absolute_value(self._adder(mapping[operands[0]], sub))

        mapping[operands[0]].pop()
        mapping[operands[1]].pop()

    def process_Equals(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        res = self._test_equality_list(mapping[operands[0]], mapping[operands[1]])
        mapping[n.name] = [res]

    def process_NotEquals(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        ans = self._test_equality_list(mapping[operands[0]], mapping[operands[1]])
        gate = self._not(ans)
        # destination.write(f'{gate} = and(-{ans})\n')
        mapping[n.name] = [gate]

    def process_LessThan(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        ans = self._comparator_greater_than(mapping[operands[0]], mapping[operands[1]], or_equal=True)
        res = self._not(ans)
        # destination.write(f'{res} = and(-{ans})\n')
        mapping[n.name] = [res]

    def process_LessEqualThan(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        ans = self._comparator_greater_than(mapping[operands[0]], mapping[operands[1]])
        res = self._not(ans)
        mapping[n.name] = [res]

    def process_GreaterThan(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        ans = self._comparator_greater_than(mapping[operands[0]], mapping[operands[1]])
        mapping[n.name] = [ans]

    def process_GreaterEqualThan(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        ans = self._comparator_greater_than(mapping[operands[0]], mapping[operands[1]], or_equal=True)
        mapping[n.name] = [ans]

    def process_AtLeast(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        sum = self._count_bits([mapping[x] for x in operands])
        num = self._num_to_bits(n.value)
        mapping[n.name] = [self._comparator_greater_than(sum, num, or_equal=True)]

    def process_AtMost(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        sum = self._count_bits([mapping[x] for x in operands])
        num = self._num_to_bits(n.value)
        mapping[n.name] = [self._comparator_greater_than(num, sum, or_equal=True)]

    def process_Multiplexer(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        monos = []
        monos.append(self._and(f'-{mapping[operands[1]][0]}', mapping[operands[2]][0]))
        monos.append(self._and(mapping[operands[1]][0], mapping[operands[2]][0], mapping[operands[0]][0]))
        monos.append(self._and(mapping[operands[1]][0], f'-{mapping[operands[2]][0]}', f'-{mapping[operands[0]][0]}'))
        res = self._or(monos)
        mapping[n.name] = [res]

    def process_If(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        # normalize
        op1 = copy.copy(mapping[operands[1]])
        op2 = copy.copy(mapping[operands[2]])
        while len(op1) < len(op2):
            op1.append(self.id_gen.get_const_false())
        while len(op2) < len(op1):
            op2.append(self.id_gen.get_const_false())

        res = []
        for op1i, op2i in zip(op1, op2):
            ifTrue = self._and(mapping[operands[0]][0], op1i)
            ifFalse = self._and(f'-{mapping[operands[0]][0]}', op2i)
            res.append(self._or(ifTrue, ifFalse))

        mapping[n.name] = res

    def process_ToInt(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        res = [mapping[x][0] for x in operands]
        mapping[n.name] = res

    def process_Constraint(
        self,
        n: Node, operands: list, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        mapping[n.name] = mapping[operands[0]]

    def process_node(
        self,
        n: Node, accs: list, param: list,
        mapping: Dict[str, List[str]],
    ):
        self.file.write(f'# {n}\n')
        self.node_processors[type(n)](n, getattr(n, "operands", []), accs, param, mapping)

    def write_custom(self, s: str):
        self.file.write(s)


class QbfSolver(Solver):
    @classmethod
    def _solve(cls,
               graphs: _Graphs,
               specifications: Specifications,
               forall=[]) -> Tuple[str, Optional[Mapping[str, Any]]]:

        script_path = path_join(
            specifications.path.run.solver_scripts,
            f'iter{specifications.iteration}_{specifications.sub_iteration}.txt'
        )

        mapping = {}
        forall.sort()
        variables = [node.name for graph in graphs for node in graph.nodes if isinstance(node, BoolVariable) and node.name not in forall]
        variables = list(set(variables))
        variables.sort()

        with open(script_path, 'w') as f:
            id_gen = NodeIdGen()
            encoder = Encoder(id_gen, f)

            encoder.write_custom('#QCIR-14\n')

            #
            _vs = [id_gen.gen_variable() for _ in variables]
            encoder.write_custom(f'exists({", ".join(_vs)})\n')
            mapping.update(zip(variables, map(lambda o: [o], _vs)))

            #
            _fas = [id_gen.gen_input() for _ in forall]
            encoder.write_custom(f'forall({", ".join(_fas)})\n')
            mapping.update(zip(forall, map(lambda o: [o], _fas)))

            #
            encoder.write_custom(f'output({id_gen.get_sat_problem()})\n')
            encoder.write_custom(f'{id_gen.get_const_true()} = and()\n')
            encoder.write_custom(f'{id_gen.get_const_false()} = or()\n')

            in_the_output = []
            targets = []
            for graph in graphs:
                for node in graph.nodes:
                    # TODO : add accessories (accs)
                    encoder.process_node(node, [], variables, mapping)

                    if isinstance(graph, CGraph):
                        if isinstance(node, Constraint):
                            assert len(mapping[node.name]) == 1
                            in_the_output.append(node.name)
                        elif isinstance(node, Target):
                            targets.append(node.operands[0])

                encoder.write_custom('#\n')

            #
            encoder.write_custom(f'{id_gen.get_sat_problem()} = and({", ".join(mapping[x][0] for x in in_the_output)})\n')

        result = subprocess.run([specifications.path.tools.cqesto, script_path], capture_output=True, text=True)

        if result.returncode == 10:
            answer_vars = {
                variables[int(x[2:])]: x[0] == '+'
                for x in result.stdout.split('\n')[3].split()[1:-1]
            }

            graphs = crystallize.graphs([
                set_bool_constants(graph, answer_vars, skip_missing=True)
                for graph in graphs
            ])

            result = {}
            for graph in graphs:
                for node in graph.nodes:
                    if node.name in targets and not isinstance(node, PlaceHolder):
                        result[node.name] = graph[node.name].value

            return ('sat', result)

        elif result.returncode == 20:
            return ('unsat', None)

        else:
            raise RuntimeError(
                f'command `{specifications.path.tools.cqesto} {script_path}` failed with code {result.returncode}\n'
                f'{result.stderr}'
            )

    @classmethod
    def solve_exists(cls,
                     graphs: _Graphs,
                     specifications: Specifications) -> Tuple[str, Optional[Mapping[str, Any]]]:
        status, model = cls._solve(graphs, specifications, [])
        return (status, model)

    @classmethod
    def solve_forall(cls, graphs: _Graphs,
                     specifications: Specifications,
                     forall_target: ForAll,
                     ) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        status, model = cls._solve(graphs, specifications, list(forall_target.operands))
        return (status, model)
