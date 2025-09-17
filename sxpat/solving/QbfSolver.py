from typing import IO, Any, Callable, Container, Mapping, NoReturn, Optional, Sequence, Tuple, Type, TypeVar, Union, Dict, List
from collections import deque
import subprocess, copy
from bisect import bisect

from .Solver import Solver

from sxpat.graph import *
from sxpat.specifications import Specifications
from sxpat.converting.utils import set_bool_constants, crystallise as crystallize


_Graphs = TypeVar('_Graphs', bound=Sequence[Union[IOGraph, PGraph, SGraph]])

"first elements of list should always be the least significant digit"


TRUE = '91'
FALSE = '92'

"This format uses gates, I used a prefix for every type of gates, all the ones that starts with 4 are the 'free' gates:"
"all those that don't have a specific purpose but are used in all the functions"
"1 is for the inputs"
"4 is for the free gates"
"7 is for the variables/parameters"
"90 is for the satisfability problem"
"91 true constant"
"92 false constant"


def free(a):
    """Return the encoded version of the current gate (simply add the prefix 4 to it)"""
    return f'4{a}'


def next_temporary(a: list):
    """Return the encoded version of the gate inside a, also increment the gate inside"""
    a[0] += 1
    return free(a[0] - 1)

"all the private functions have: next_free which is a list that contains only one element, I use this to keep track of the namings for the gates"
"I add. For example if the element inside next_free is 543 and in a function I add 5 gates I will change the element to 548"

"destination is instead the file where the qbf code needs to be written"

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

def _adder(a : list, b : list, next_free, destination : IO[str], carry = False) -> list:
    if len(a) < len(b):
        a,b = b,a
    while len(b) < len(a):
        b.append(FALSE)
    
    results = [_xor(a[0],b[0],next_free, destination)]
    carry_in = free(next_free[0])
    destination.write(f'{free(next_free[0])} = and({a[0]}, {b[0]})\n')
    next_free[0] += 1
    for i in range(1,len(a)):
        next, carry_in = _adder_bit3(a[i],b[i],carry_in, next_free, destination)
        results.append(next)
    if carry:
        results.append(carry_in)
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

def _test_equality_list(a: list, b: list, next_free, destination : IO[str]):
    while len(a) < len(b):
        a.append(FALSE)
    while len(b) < len(a):
        b.append(FALSE)
    
    equals = []
    for i in range(len(a)):
        equals.append(_test_equality_bits(a[i],b[i],next_free,destination))
    
    res = next_temporary(next_free)
    destination.write(f'{res} = and(')
    first = True
    for x in equals:
        if not first:
            destination.write(', ')
        first = False
        destination.write(x)
    
    return res

# TODO: many other versions of comparator
def _comparator_greater_than(a : list, b : list, next_free, destination : IO[str], or_equal = False):
    while len(a) < len(b):
        a.append(FALSE)
    while len(b) < len(a):
        b.append(FALSE)
    
    equal = []
    one_of = []
    for i in range(len(a)-1, -1, -1):
        one_of.append(next_temporary(next_free))
        if i > 0 or not or_equal:
            destination.write(f'{one_of[-1]} = and({a[i]}, -{b[i]}')
            
        else:
            save = next_temporary(next_free)
            destination.write(f'{save} = and(-{a[i]}, {b[i]})\n')
            destination.write(f'{one_of[-1]} = and(-{save}')
        
        for x in equal:
            destination.write(f', {x}')
        destination.write(')\n')

        equal.append(_test_equality_bits(a[i],b[i], next_free, destination))

    res = next_temporary(next_free)
    destination.write(f'{res} = or(')
    first = True
    for x in one_of:
        if not first:
            destination.write(', ')
        first = False
        destination.write(f'{x}')
    destination.write(')\n')
    return res

def _xor_bits_with_bit(a : list, b, next_free, destination : IO[str]) -> list:
    results = []
    for i in range(len(a)):
        results.append(_xor(a[i],b,next_free,destination))
    return results

def _adder_bits_with_bit(a : list, b, next_free, destination : IO[str]) -> list:
    results = []
    last_and = b
    for i in range(len(a)):
        results.append(_xor(last_and, a[i], next_free, destination))
        temp = next_temporary(next_free)
        destination.write(f'{temp} = and({last_and}, {a[i]})\n')
        last_and = temp
    return results

def _absolute_value(a, next_free, destination : IO[str]) -> list:
    return _adder_bits_with_bit(_xor_bits_with_bit(a,a[-1], next_free, destination),a[-1], next_free, destination)

def process_BoolVariable(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    return next_free

def process_IntVariable(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    raise NotImplementedError(f'this function isn\'t implemented yet')
    return next_free

def process_BoolConstant(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    if n.value:
        first = TRUE
    else:
        first = FALSE
    mapping[n.name] = [first]
    return next_free

def process_IntConstant(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
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

def process_Identity(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    mapping[n.name] = mapping[operands[0]]
    return next_free

def process_Target(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    return next_free

def process_PlaceHolder(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    return next_free

def process_Not(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    destination.write(f'{free(next_free)} = and(-{mapping[operands[0]][0]})\n')
    mapping[n.name] = [free(next_free)]
    return next_free + 1

def _process_f(operands: list, mapping : Dict[str, List[str]], destination: IO[str]):
    first = True
    for x in operands:
        if not first:
            destination.write(', ')
        first = False
        destination.write(f'{mapping[x][0]}')
    destination.write(')\n')

def process_And(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    mapping[n.name] = [free(next_free)]
    destination.write(f'{free(next_free)} = and(')
    _process_f(operands, mapping, destination)
    return next_free + 1

def process_Or(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    mapping[n.name] = [free(next_free)]
    destination.write(f'{free(next_free)} = or(')
    _process_f(operands, mapping, destination)
    return next_free + 1

def process_Xor(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    mapping[n.name] = [_xor(mapping[operands[0]][0], mapping[operands[1]][0], temp, destination)]
    return temp[0]
def process_Implies(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    mapping[n.name] = [free(next_free+1)]
    destination.write(f'{free(next_free)} = and({mapping[operands[0]][0]}, -{mapping[operands[1]][0]})\n')
    destination.write(f'{free(next_free+1)} = and(-{free(next_free)})\n')
    return next_free + 2

def process_Sum(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    if len(operands) == 0:
        mapping[n.name] = [FALSE]
        return next_free
    
    num = mapping[operands[0]]
    for i in range(1,len(operands)):
        temp = [next_free]
        num = _adder(num, mapping[operands[i]], temp, destination, carry=True)
        next_free = temp[0]

    mapping[n.name] = num
    return next_free

# TODO: remove one bit
def process_AbsDiff(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    mapping[operands[0]].append(FALSE)
    mapping[operands[1]].append(FALSE)

    sub = _increment(_inverse(mapping[operands[1]], temp, destination), temp, destination)
    mapping[n.name] = _absolute_value(_adder(mapping[operands[0]], sub, temp, destination),temp,destination)

    mapping[operands[0]].pop()
    mapping[operands[1]].pop()
    return temp[0]

def process_Equals(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    res = _test_equality_list(mapping[operands[0]], mapping[operands[1]], temp, destination)
    mapping[n.name] = [res]

    return temp[0]

def process_NotEquals(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    ans = _test_equality_list(mapping[operands[0]], mapping[operands[1]], temp, destination)
    res = next_temporary(temp)
    destination.write(f'{res} = and(-{ans})\n')
    mapping[n.name] = [res]

    return temp[0]

def process_LessThan(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    ans = _comparator_greater_than(mapping[operands[0]], mapping[operands[1]], temp, destination, or_equal=True)
    res = next_temporary(temp)
    destination.write(f'{res} = and(-{ans})\n')
    mapping[n.name] = [res]

    return temp[0]

def process_LessEqualThan(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    ans = _comparator_greater_than(mapping[operands[0]], mapping[operands[1]], temp, destination)
    res = next_temporary(temp)
    destination.write(f'{res} = and(-{ans})\n')
    mapping[n.name] = [res]
    return temp[0]

def process_GreaterThan(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    ans = _comparator_greater_than(mapping[operands[0]], mapping[operands[1]], temp, destination)
    mapping[n.name] = [ans]
    return temp[0]

def process_GreaterEqualThan(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    ans = _comparator_greater_than(mapping[operands[0]], mapping[operands[1]], temp, destination, or_equal=True)
    mapping[n.name] = [ans]
    return temp[0]

def process_AtLeast(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    remaining = deque()
    for x in operands:
        remaining.append(mapping[x])
    
    while len(remaining) > 1:
        a = remaining.popleft()
        b = remaining.popleft()
        remaining.append(_adder(a,b,temp,destination, True))
    
    sum = remaining.popleft()
    num = []
    rem = n.value
    while rem > 0:
        if rem % 2 == 1:
            num.append(TRUE)
        else:
            num.append(FALSE)
        rem >>= 1

    mapping[n.name] = [_comparator_greater_than(sum, num, temp, destination, True)]

    return temp[0]

# TODO: optimize for various numbers
def process_AtMost(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    remaining = deque()
    for x in operands:
        remaining.append(mapping[x])
    
    while len(remaining) > 1:
        a = remaining.popleft()
        b = remaining.popleft()
        remaining.append(_adder(a,b,temp,destination, True))
    
    sum = remaining.popleft()
    num = []
    rem = n.value
    while rem > 0:
        if rem % 2 == 1:
            num.append(TRUE)
        else:
            num.append(FALSE)
        rem >>= 1

    mapping[n.name] = [_comparator_greater_than(num, sum, temp, destination, True)]

    return temp[0]

def process_Multiplexer(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    monos = []

    monos.append(next_temporary(temp))
    destination.write(f'{monos[-1]} = and(-{mapping[operands[1]][0]}, {mapping[operands[2]][0]})\n')

    monos.append(next_temporary(temp))
    destination.write(f'{monos[-1]} = and({mapping[operands[1]][0]}, {mapping[operands[2]][0]}, {mapping[operands[0]][0]})\n')

    monos.append(next_temporary(temp))
    destination.write(f'{monos[-1]} = and({mapping[operands[1]][0]}, -{mapping[operands[2]][0]}, -{mapping[operands[0]][0]})\n')

    res = next_temporary(temp)
    destination.write(f'{res} = or({monos[0]}, {monos[1]}, {monos[2]})\n')
    mapping[n.name] = [res]

    return temp[0]

def process_If(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    temp = [next_free]
    op1 = copy.copy(mapping[operands[1]])
    op2 = copy.copy(mapping[operands[2]])

    while len(op1) < len(op2):
        op1.append(FALSE)
    while len(op2) < len(op1):
        op2.append(FALSE) 

    ifTrue = []
    for x in op1:
        ifTrue.append(next_temporary(temp))
        destination.write(f'{ifTrue[-1]} = and({mapping[operands[0]][0]}, {x})\n')
    
    ifFalse = []
    for x in op2:
        ifFalse.append(next_temporary(temp))
        destination.write(f'{ifFalse[-1]} = and(-{mapping[operands[0]][0]}, {x})\n')
    
    res = []
    for i in range(len(op1)):
        res.append(next_temporary(temp))
        destination.write(f'{res[-1]} = or({ifTrue[i]}, {ifFalse[i]})\n')
    
    mapping[n.name] = res

    return temp[0]

def process_ToInt(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    res = []
    for x in operands:
        res.append(mapping[x][0])
    mapping[n.name] = res
    return next_free

def process_Constraint(n : Node, operands: list, accs: list, param: list, next_free: int, mapping : Dict[str, List[str]], destination: IO[str]):
    mapping[n.name] = mapping[operands[0]]
    return next_free

Node_Mapping = {
    # variables
    BoolVariable: process_BoolVariable,
    IntVariable: process_IntVariable, #TODO: implement
    # constants
    BoolConstant: process_BoolConstant,
    IntConstant: process_IntConstant,
    # output
    Identity: process_Identity,
    Target: process_Target,
    # placeholder
    PlaceHolder: process_PlaceHolder,
    # boolean operations
    Not: process_Not,
    And: process_And,
    Or: process_Or,
    Xor: process_Xor, #Needs testing
    Implies: process_Implies,
    # integer operations
    Sum: process_Sum,
    AbsDiff: process_AbsDiff,
    # comparison operations
    Equals: process_Equals, # Needs testing
    NotEquals: process_NotEquals, # Needs testing
    LessThan: process_LessThan, # Needs testing
    LessEqualThan: process_LessEqualThan,
    GreaterThan: process_GreaterThan,
    GreaterEqualThan: process_GreaterEqualThan,
    # quantifier operations
    AtLeast: process_AtLeast,
    AtMost: process_AtMost,
    # branching operations
    Multiplexer: process_Multiplexer,
    If: process_If, # Needs testing for Integers
    ToInt: process_ToInt,
    Constraint: process_Constraint,
}

class QbfSolver(Solver):
    @classmethod
    def _solve(cls,
              graphs: _Graphs,
              specifications: Specifications,
              forall = []) -> Tuple[str, Optional[Mapping[str, Any]]]:
        
        script_path = f'output/z3/{specifications.exact_benchmark}_iter{specifications.iteration}.txt'

        mapping = {}
        variables = [node.name for graph in graphs if isinstance(graph, PGraph) for node in graph.nodes if isinstance(node, BoolVariable)]
        variables.sort()
        forall.sort()

        with open(script_path, 'w') as f:

            f.write('#QCIR-14\nexists(')
            first = True
            for i in range(len(variables)):
                if not first:
                    f.write(', ')
                first = False
                f.write(f'7{i}')
                mapping[variables[i]] = [f'7{i}']

            f.write(')\nforall(')
            first = True
            for i in range(len(forall)):
                if not first:
                    f.write(', ')
                first = False
                f.write(f'1{i}')
                mapping[forall[i]] = [f'1{i}']
            f.write(')\noutput(90)\n91 = and()\n92 = or()\n#\n')

            in_the_output = []
            next_free = 0
            targets = []

            for graph in graphs:
                for node in graph.nodes:
                    #TODO : add accessories (accs)
                    next_free = Node_Mapping[type(node)](node, getattr(node, "operands", []),[], variables, next_free, mapping, f)
                    if isinstance(graph,CGraph):
                        if isinstance(node, Constraint):
                            assert(len(mapping[node.name]) == 1)
                            in_the_output.append(node.name)

                        if isinstance(node, Target):
                            targets.append(node.operands[0])

                f.write('#\n')
            
            f.write(f'90 = and(')
            first = True
            for x in in_the_output:
                if not first:
                    f.write(', ')
                first = False
                f.write(f'{mapping[x][0]}')
            f.write(')\n')

        result = subprocess.run(["../../../../cqesto-master/build/cqesto", script_path], capture_output=True, text=True)

        if result.stdout.strip()[-1] == '1':
            answer_vars = {}
            for x in result.stdout.split('\n')[3].split()[1:-1]:
                answer_vars[variables[int(x[2:])]] = True if x[0] == '+' else False

            result = {}
            new_graphs = []
            for graph in graphs:
                new_graphs.append(set_bool_constants(graph, answer_vars, skip_missing=True))

            graphs = crystallize.graphs(new_graphs)
            for graph in graphs:
                for node in graph.nodes:
                    if node.name in targets and not isinstance(node, PlaceHolder):
                        result[node.name] = graph[node.name].value
                
            return ('sat', result)
        
        else:
            return ('unsat', None)
    
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