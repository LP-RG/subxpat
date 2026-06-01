from io import TextIOWrapper
from sxpat.graph import IOGraph
from sxpat.graph.node import Node, And, Not, Identity, BoolVariable
from sxpat.annotatedGraph import AnnotatedGraph
from collections import defaultdict, deque
from typing import Union
import subprocess

def check_node(count: dict, que: deque, current: IOGraph, node: str):
    for succ in current.successors(node):
        count[succ] += 1
        if count[succ] == len(current.predecessors(succ)) and succ.name not in current.outputs_names:
            que.append(succ)

def pred_to_str(current: IOGraph, node: Node, appr=False):
    ans = ''
    n_first = False
    for pred in current.predecessors(node):
        if n_first:
            ans += ', '
        n_first = True
        if appr and not isinstance(pred, BoolVariable):
            ans += 'a_'
        ans += pred.name
    return ans

def to_int(graph: IOGraph, out: TextIOWrapper, appr=False):
    names = []
    for i, outp in enumerate(graph.outputs_names):
        if appr:
            outp = 'a_' + outp
        name = f'if_{outp}'
        names.append(name)
        out.write(f'{name} = If({outp}, const{i}, constf)\n')
    out.write(f'{"a_sum" if appr else "sum"} = Sum(')
    n_first = False
    for name in names:
        if n_first:
            out.write(', ')
        n_first = True
        out.write(name)
    out.write(')\n')

def label_node(exact: IOGraph, current: IOGraph, target: str, path: str):
    num_outputs = len(current.outputs_names)

    with open(path, mode='w') as out:
        out.write('from z3 import *\n\n')

        count = defaultdict(int)
        que = deque()

        out.write('# variables (inputs, parameters)\n')
        for inp in exact.inputs_names:
            out.write(f'{inp} = Bool(\'{inp}\')\n')
            check_node(count, que, exact, inp)
        out.write('\n')

        out.write(f'constf = BitVecVal(0, {num_outputs})\n')
        for i in range(num_outputs):
            out.write(f'const{i} = BitVecVal({2**i}, {num_outputs})\n')

        # doing first exact
        out.write('# behaviour\n')
        while len(que):
            node: Union[Not, And]  = que.popleft()
            out.write(f'{node.name} = {"And" if isinstance(node, And) else "Not"}({pred_to_str(current, node)})\n')
            check_node(count, que, current, node.name)
        
        for outp in exact.outputs_names:
            out.write(f'{outp} = {list(exact.predecessors(outp))[0].name}\n')

        count = defaultdict(int)
        que = deque()

        for inp in current.inputs_names:
            check_node(count, que, current, inp)

        for const in current.constants:
            out.write(f'a_{const.name} = BoolVal({const.value})\n')
            check_node(count, que, current, const.name)
        
        while len(que):
            node: Union[Not, And]  = que.popleft()
            if node.name == target:
                out.write(f'target = {"And" if isinstance(node, And) else "Not"}({pred_to_str(current, node, appr=True)})\n')
                out.write(f'a_{node.name} = Not(target)\n')
            else:
                out.write(f'a_{node.name} = {"And" if isinstance(node, And) else "Not"}({pred_to_str(current, node, appr=True)})\n')
            check_node(count, que, current, node.name)
        
        for outp in current.outputs_names:
            out.write(f'a_{outp} = a_{list(exact.predecessors(outp))[0].name}\n')
        
        to_int(exact, out)
        to_int(current, out, True)
        out.write(f'error = If(UGE(sum, a_sum), sum - a_sum, a_sum - sum)\n\n')

        out.write(f'solver = Optimize()\nsolver.maximize(error)\n\n')

        out.write('# check\n')
        out.write('solver.check()\n')
        # out.write('print(status)\n\n')

        out.write('# model\n')
        # out.write('if status == sat:\n')
        out.write('model = solver.model()\n')
        out.write('print(model.eval(error, model_completion=True))\n')

    result = subprocess.run(
        ["python3", "test.py"],
        capture_output=True,
        text=True
    )

    return int(result.stdout)






        


        


        






        