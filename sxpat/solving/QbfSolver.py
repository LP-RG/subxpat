from typing import IO, Any, Callable, Container, Mapping, NoReturn, Optional, Sequence, Tuple, Type, TypeVar, Union, Dict, List

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

def next_temporary(a):
    a[0] += 1
    return free(a[0] - 1)

def _and(a,b, next_free, destination : IO[str]):
    destination.write(f'{free(next_free[0])} = and({a}, {b})\n')
    next_free[0] += 1
    return free(next_free[0]-1)

def _or(a,b, next_free, destination : IO[str]):
    destination.write(f'{free(next_free[0])} = or({a}, {b})\n')
    next_free[0] += 1
    return free(next_free[0]-1)

def _xor(a,b, next_free, destination : IO[str]):
    destination.write(f'{free(next_free[0])} = xor({a}, {b})\n')
    next_free[0] += 1
    return free(next_free[0]-1)

def _adder_bit3(a,b,c, next_free, destination : IO[str]):
    results = []
    partial_xor = _xor(a,b,next_free, destination)
    results.append(_xor(partial_xor,c, next_free, destination))
    partial_and1 = _and(a,b,next_free, destination)
    partial_and2 = _and(c,partial_xor, next_free, destination)
    results.append( _or(partial_and1,partial_and2, next_free, destination))
    return results

def _adder(a : list, b : list, next_free, destination : IO[str]) -> list:
    if len(a) < len(b):
        a,b = a,a
    while len(b) < len(a):
        b.append(FALSE)
    
    results = [_xor(a[0],b[0],next_free, destination)]
    carry_in = free(next_free[0])
    destination.write(f'{free(next_free[0])} = and({a[0]}, {b[0]})\n')
    next_free[0] += 1
    for i in range(1,len(a)):
        next, carry_in = _adder_bit3(a[i],b[i],carry_in, next_free, destination)
        results.append(next)
    return results

def _inverse(a : list, next_free, destination : IO[str]) -> list:
    results = []
    for x in a:
        results.append(next_temporary(next_free))
        destination.write(f'{results[-1]} = and(-{x})\n')
    return results


def _increment(a : list,next_free, destination : IO[str], carry=False) -> list:
    assert len(a) > 0, "lenght of a should be higher than 0"

    if carry:
        a.append(a[-1])
    results = [next_temporary(next_free)]
    destination.write(f'{results[0]} = and(-{a[0]})\n')
    last_and = a[0]
    for i in range(1,len(a)):
        results.append(_xor(last_and, a[i], next_free, destination))
        temp = next_temporary(next_free)
        destination.write(f'{temp} = and({last_and}, {a[i]})\n')
        last_and = temp
    return results

def _test_equality_bits(a,b, next_free, destination: IO[str]):
    and1 = next_temporary(next_free)
    and2 = next_temporary(next_free)
    destination.write(f'{and1} = and({a}, {b})\n')
    destination.write(f'{and2} = and(-{a}, -{b})\n')
    result_gate_name = next_temporary(next_free)
    destination.write(f'{result_gate_name} = or({and1}, {and2})\n')
    return result_gate_name




# with open("sxpat/solving/temp.txt", 'w') as f:
#     print(_comparator_greater_then([1,2],[3,4], [0], f))

def process_BoolVariable(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    return next_free

def process_IntVariable(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    raise NotImplementedError(f'this function isn\'t yet implemented')

def process_BoolConstant(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    if n.value:
        first = TRUE
    else:
        first = FALSE
    mapping[n.name] = [first]
    return next_free

def process_IntConstant(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = n.value
    res = []
    while temp > 0:
        if temp % 2 == 1:
            res.append(TRUE)
        else:
            res.append(FALSE)
        temp >>= 1
    mapping[n.name] = res
    return next_free

def process_Copy(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    mapping[n.name] = mapping[operands[0]]
    return next_free

def process_Target(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    return next_free

def process_PlaceHolder(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    return next_free

def process_Not(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    destination.write(f'{free(next_free)} = and(-{mapping[operands[0]][0]})\n')
    mapping[n.name] = [free(next_free)]
    return next_free

def _process_f(operands: list, mapping : Dict[str, List[str]], destination: IO[str]):
    first = True
    for x in operands:
        if not first:
            destination.write(', ')
        first = False
        destination.write(f'{mapping[x][0]}')
    destination.write(')\n')

def process_And(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    mapping[n.name] = [free(next_free)]
    destination.write(f'{free(next_free)} = and(')
    _process_f(operands, mapping, destination)
    return next_free + 1

def process_Or(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    mapping[n.name] = [free(next_free)]
    destination.write(f'{free(next_free)} = or(')
    _process_f(operands, mapping, destination)
    return next_free + 1

def process_Implies(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    write = f'{free(next_free)} = and({mapping[operands[0]][0]}, -{mapping[operands[1]][0]})\n'
    write += f'{free(next_free+1)} = and(-{free(next_free)})\n'
    return next_free + 2

def process_Sum(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    if len(operands) == 0:
        mapping[n.name] = [FALSE]
        return next_free
    
    num = mapping[operands[0]]
    for i in range(1,len(operands)):
        temp = [next_free]
        num = _adder(num, operands[i], temp, destination)
        next_free = temp[0]

    mapping[n.name] = num
    return next_free
    
def process_AbsDiff(n : Node, operands: list, accs: list, inputs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    sub = _increment(_inverse(mapping[operands[1]], temp, destination), temp, destination)
    mapping[n.name] = _adder(mapping[operands[0]], mapping[operands[1]], temp, destination)
    return temp[0]


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
    Sum: process_Sum,
    AbsDiff: process_AbsDiff,
}

class QbfSolver(Solver):
    @classmethod
    def solve(cls,
              graphs: _Graphs,
              specifications: Specifications) -> Tuple[str, Optional[Mapping[str, Any]]]:
        
        script_path = f'output/z3/{specifications.exact_benchmark}_iter{specifications.iteration}.py'

        mapping = {}
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
            f.write(')\noutput(90)\n#\n')

            next_free = 0
            for graph in graphs:
                for node in graph.nodes:
                    #TODO : add accessories (accs)
                    next_free = Node_Mapping[type(node)](node, node.operands,[] , inputs, variables, next_free, mapping, f)
            exit()




        return ('unsat', None)