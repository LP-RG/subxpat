from typing import IO, Any, Callable, Container, Mapping, NoReturn, Optional, Sequence, Tuple, Type, TypeVar, Union

import subprocess

from sxpat.specifications import Specifications

from .Solver import Solver

from sxpat.graph import *
from bisect import bisect

_Graphs = TypeVar('_Graphs', bound=Sequence[Union[IOGraph, PGraph, SGraph]])

"first elements of list should always be the least significant digit"

"1 is for the inputs"
"4 is for the all the not specified gates in qbf"
"7 is for the variables/parameters"
"90 is for the satisfability problem"
"91 true constant"
"92 false constant"

TRUE = '91'
FALSE = '92'

def free(a):
    return f'4{a}'

def _and(a,b, next_free, destination : IO[str]):
    destination.write(f'{free(next_free)} = and({a}, {b})\n')
    return (free(next_free), next_free + 1)

def _or(a,b, next_free, destination : IO[str]):
    destination.write(f'{free(next_free)} = or({a}, {b})\n')
    return (free(next_free), next_free + 1)

def _xor(a,b, next_free, destination : IO[str]):
    destination.write(f'{free(next_free)} = xor({a}, {b})\n')
    return (free(next_free), next_free + 1)

def _adder_bit3(a,b,c, next_free, destination : IO[str]):
    results = []
    partial_xor, next_free = _xor(a,b,next_free, destination)
    temp, next_free = _xor(partial_xor,c, next_free, destination)
    results.append(temp)
    partial_and1, next_free = _and(a,b,next_free, destination)
    partial_and2, next_free = _and(c,partial_xor, next_free, destination)
    temp, next_free = _or(partial_and1,partial_and2, next_free, destination)
    results.append(temp)
    return (results, next_free)

def _unsigned_adder(a : list, b : list, next_free, destination : IO[str]) -> list:
        if len(a) < len(b):
            a,b = a,a
        while len(b) < len(a):
            b.append(FALSE)
        
        temp, next_free = _xor(a[0],b[0],next_free, destination)
        results = [temp]
        carry_in = free(next_free)
        destination.write(f'{free(next_free)} = and({a[0]}, {b[0]})\n')
        next_free += 1
        for i in range(1,len(a)):
            next_and_carry_in, next_free = _adder_bit3(a[i],b[i],carry_in, next_free, destination)
            next, carry_in = next_and_carry_in
            results.append(next)
        return (results, next_free)

# with open('sxpat/solving/temp.txt', 'w') as f:
#     print(_unsigned_adder([1, 2], [3], 0, f))
# #     # print(_adder_bit3(1,2,3,0,f))

def process_BoolVariable(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    return ('', [f'1{bisect(inputs, n.name)}'], next_free)

def process_IntVariable(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    raise NotImplementedError(f'this function isn\'t yet implemented')

def process_BoolConstant(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    if n.value:
        first = TRUE
    else:
        first = FALSE
    return ('', [first], next_free)

def process_IntConstant(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    temp = n.value
    res = []
    while temp > 0:
        if temp % 2 == 1:
            res.append(TRUE)
        else:
            res.append(FALSE)
        temp >>= 1
    return ('', res, next_free)

def process_Copy(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    return ('', mapping[n.name], next_free)

def process_Target(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    return ('', [], next_free)

def process_PlaceHolder(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    return ('', [], next_free)

def process_Not(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    return (f'{free(next_free)} = and(-{mapping[operands[0]][0]})', [free(next_free)], next_free + 1)

def process_And(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    return (f'{free(next_free)} = and({mapping[operands[0]][0]}, {mapping[operands[1]][0]})', [free(next_free)], next_free + 1)

def process_Or(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    return (f'{free(next_free)} = or({mapping[operands[0]][0]}, {mapping[operands[1]][0]})', [free(next_free)], next_free + 1)

def process_Implies(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    write = f'{free(next_free)} = and({mapping[operands[0]][0]}, -{mapping[operands[1]][0]})\n'
    write += f'{free(next_free+1)} = and(-{free(next_free)})'
    return (write, [free(next_free+1)], next_free + 2)

def process_Sum(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : dict[str, list[str]]):
    if len(operands) == 0:
        return ('', [FALSE], next_free)
    
    num = mapping[operands[0]]
    for i in range(1,len(operands)):
        _
    

Node_Mapping = {
    # variables
    BoolVariable: process_BoolVariable,
    IntVariable: process_IntVariable, #TODO: implement
    # constants
    BoolConstant: process_BoolConstant,
    IntConstant: process_IntConstant,
    # output
    Copy: process_Copy,
    Target: process_Target,
    # placeholder
    PlaceHolder: process_PlaceHolder,
    # boolean operations
    Not: process_Not,
    And: process_And,
    Or: process_Or,
    Implies: process_Implies,
    # integer operations
    Sum: lambda n, operands, accs: f'Sum({", ".join(operands)})',
    AbsDiff: lambda n, operands, accs: f'If({operands[0]} >= {operands[1]}, {operands[0]} - {operands[1]}, {operands[1]} - {operands[0]})',
    # comparison operations
    Equals: lambda n, operands, accs: f'({operands[0]} == {operands[1]})',
    NotEquals: lambda n, operands, accs: f'({operands[0]} != {operands[1]})',
    LessThan: lambda n, operands, accs: f'({operands[0]} < {operands[1]})',
    LessEqualThan: lambda n, operands, accs: f'({operands[0]} <= {operands[1]})',
    GreaterThan: lambda n, operands, accs: f'({operands[0]} > {operands[1]})',
    GreaterEqualThan: lambda n, operands, accs: f'({operands[0]} >= {operands[1]})',
    # quantifier operations
    AtLeast: lambda n, operands, accs: f'AtLeast({", ".join(operands)}, {n.value})',
    AtMost: lambda n, operands, accs: f'AtMost({", ".join(operands)}, {n.value})',
    # branching operations
    Multiplexer: lambda n, operands, accs: f'If({operands[1]}, If({operands[2]}, {operands[0]}, Not({operands[0]})), {operands[2]})',
    If: lambda n, operands, accs: f'If({operands[0]}, {operands[1]}, {operands[2]})',
}

class QbfSolver(Solver):
    @classmethod
    def solve(cls,
              graphs: _Graphs,
              specifications: Specifications) -> Tuple[str, Optional[Mapping[str, Any]]]:
        
        script_path = f'output/z3/{specifications.exact_benchmark}_iter{specifications.iteration}.py'

        inputs = list(set(name for graph in graphs if isinstance(graph, IOGraph) for name in graph.inputs_names))
        variables = [node.name for graph in graphs if isinstance(graph, PGraph) for node in graph.nodes if isinstance(node, BoolVariable) and node.name not in inputs]
        inputs.sort()
        variables.sort()

        with open(script_path, 'w') as f:

            f.write('#QCIR-14\nexists(')
            first = True
            for x in range(len(variables)):
                if not first:
                    f.write(', ')
                first = False
                f.write(f'7{x}')

            f.write(')\nforall(')
            first = True
            for x in range(len(inputs)):
                if not first:
                    f.write(', ')
                first = False
                f.write(f'1{x}')
            f.write(')\noutput(90)#\n')


            




        return ('unsat', None)