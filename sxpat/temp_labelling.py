import sys
# sys.path.append("/home/lorenzospada/Documents/Multiple_Instances/1-instance/subxpat")

from sxpat.annotatedGraph import AnnotatedGraph
import networkx as nx
import shutil
import subprocess
import os
import time
from Z3Log.graph import Graph


NOT = 'not'
AND_QCIR = 'and'
AND_SUBXPAT = 'and'
OR_QCIR = 'or'
OR_SUBXPAT = 'or'
INPUT_GATE_INITIALS = 'in'
STANDARD_GATE_INITIALS = 'g'
OUTPUT_GATE_INITIALS = 'out'
TEMPORARY_GATE_PREFIX = '94'
CHANGE = {INPUT_GATE_INITIALS : "1", STANDARD_GATE_INITIALS : "2", OUTPUT_GATE_INITIALS : "30"} #
CHANGE_INEXACT = {INPUT_GATE_INITIALS : "1", STANDARD_GATE_INITIALS : "62", OUTPUT_GATE_INITIALS : "31", '61' : '61'} #
# 1,2,30 is for the input, and, output gates of the exact circuit, 40 for intermidiate and gates of the multiplexer, 41 for the output of the multiplexer,
# 5 for the and gates, 60 for the or gates, 61 for the and between the or gate and p_o# (the outputs of the parametrical circuit),
# 62 is for the and gates of the inexact circuit, 7 is for the parameters p_o#_t#_i#_s/l, 31 is for the outputs of the inexact circuit
# 90 is for the satisfability problem, 91 for true constant, 92 for false constant, 93 for the parameters p_o#, 94 is for temporary gates
output = 1
temporary_gates_index = 0

def make_qcir_variable(var):
    for key,value in CHANGE.items():
        if var[:len(key)] == key:
            return value + var[len(key):] 
    raise TypeError("received a variable that I can't convert, the variable was: " + var)

def make_qcir_variable_inexact(var):
    for key,value in CHANGE_INEXACT.items():
        if var[:len(key)] == key:
            return value + var[len(key):] 
    return var
    # raise TypeError("received a variable that I can't convert, the variable was: " + var)

def next_temporary_variable():
    global temporary_gates_index
    temporary_gates_index += 1
    return TEMPORARY_GATE_PREFIX + str(temporary_gates_index - 1)

def test_equality_bits(a,b):
    and1 = next_temporary_variable()
    and2 = next_temporary_variable()
    output.write(f'{and1} = and({a}, {b})\n')
    output.write(f'{and2} = and(-{a}, -{b})\n')
    result_gate_name = next_temporary_variable()
    output.write(f'{result_gate_name} = or({and1}, {and2})\n')
    return result_gate_name

def test_equality_lists(a : list, b : list):
    output.write('#testing equalilty\n')
    assert len(a) == len(b) , 'lengths of a and b should be the same'
    
    partials = []
    for i in range(len(a)):
        partials.append(test_equality_bits(a[i],b[i]))
    return operation_on_list(partials, 'and')

def and2(a,b):
    res = next_temporary_variable()
    output.write(f'{res} = and({a}, {b})\n')
    return res

def or2(a,b):
    res = next_temporary_variable()
    output.write(f'{res} = or({a}, {b})\n')
    return res

def operation_on_list(a : list, operation : str) -> list:
    res = next_temporary_variable()
    output.write(f'{res} = {operation}(')
    start = True
    for x in a:
        if not start:
            output.write(', ')
        output.write(x)
        start = False
    output.write(')\n#\n')
    return res

def xor(a,b):
    pand1 = next_temporary_variable()
    pand2 = next_temporary_variable()
    output.write(f'{pand1} = and(-{a}, {b})\n')
    output.write(f'{pand2} = and({a}, -{b})\n')
    result_gate_name = next_temporary_variable()
    output.write(f'{result_gate_name} = or({pand1}, {pand2})\n')
    return result_gate_name

def adder_bit3(a,b,c):
    results = []
    partial_xor = xor(a,b)
    results.append(xor(partial_xor,c))
    partial_and1 = and2(a,b)
    partial_and2 = and2(c,partial_xor)
    results.append(or2(partial_and1,partial_and2))
    return results

def xor_bits_with_bit(a : list, b) -> list:
    results = []
    for i in range(len(a)):
        results.append(xor(a[i],b))
    return results

def inverse(a : list) -> list:
    output.write('#inversing every bit\n')
    results = []
    for x in a:
        results.append(next_temporary_variable())
        output.write(f'{results[-1]} = and(-{x})\n')
    output.write('#\n')
    return results

def adder_bits_with_bit(a : list, b) -> list:
    results = []
    last_and = b
    for i in range(len(a)):
        results.append(xor(last_and, a[i]))
        temp = next_temporary_variable()
        output.write(f'{temp} = and({last_and}, {a[i]})\n')
        last_and = temp
    output.write('#\n')
    return results

def absolute_value(a) -> list:
    return adder_bits_with_bit(xor_bits_with_bit(a,a[-1]),a[-1])

def increment(a : list,carry=True) -> list:
    """first element of a should be the least significant digit\n
    add one to a"""
    assert len(a) > 0, "lenght of a should be higher than 0"

    output.write('#incrementing by 1\n')
    if carry:
        a.append(a[-1])
    results = [next_temporary_variable()]
    output.write(f'{results[0]} = and(-{a[0]})\n')
    last_and = a[0]
    for i in range(1,len(a)):
        results.append(xor(last_and, a[i]))
        temp = next_temporary_variable()
        output.write(f'{temp} = and({last_and}, {a[i]})\n')
        last_and = temp
    output.write('#\n')
    return results

def signed_adder(a : list, b : list) -> list:
    """first element of a should be the least significant digit"""

    a.append(a[-1])
    b.append(b[-1])
    while len(a) < len(b):
        a.append(a[-1])
    while len(b) < len(a):
        b.append(b[-1])
    output.write('#adding\n')
    results = [xor(a[0],b[0])]
    carry_in = next_temporary_variable()
    output.write(f'{carry_in} = and({a[0]}, {b[0]})\n')
    for i in range(1,max(len(a),len(b))):
        next,carry_in = adder_bit3(a[i],b[i],carry_in)
        results.append(next)
    output.write('#\n')
    return results

def unsigned_adder(a : list, b : list) -> list:
    assert abs(len(a)-len(b)) <= 1, 'lengths of a and b should differ by maximum 1' 

    if len(a) < len(b):
        a,b = b,a
    results = [xor(a[0],b[0])]
    carry_in = next_temporary_variable()
    output.write(f'{carry_in} = and({a[0]}, {b[0]})\n')
    for i in range(1,max(len(a),len(b))):
        if i < min(len(a),len(b)):
            next,carry_in = adder_bit3(a[i],b[i],carry_in)
        else:
            next = xor(a[i],carry_in)
            carry_in = and2(a[i],carry_in)
        results.append(next)
    output.write('#\n')
    results.append(carry_in)
    return results


def comparator_greater_than(a : list, e : int):
    output.write('#comparing\n')
    if (e >> len(a)) > 0:
        return '92'
    i = len(a) - 1
    partial_and = []
    while i >= 0:
        if (e >> i) & 1 == 0:
            partial_and.append(next_temporary_variable())
            output.write(f'{partial_and[-1]} = and({a[i]}')
            for j in range(len(a) - 1, i, -1):
                output.write(', ' + ('' if (e >> j) & 1 else '-') + f'{a[j]}')
            output.write(')\n')
        i -= 1
    res = next_temporary_variable()
    output.write(f'{res} = or(')
    start = True
    for x in partial_and:
        if not start:
            output.write(', ')
        start = False
        output.write(x)
    output.write(')\n#\n')
    return res

def visit(graph: Graph, node, vis):
    if node in vis:
        return vis[node]
    
    if graph.nodes[node]['label'] == NOT:
        vis[node] = not visit(graph, next(graph.predecessors(node)), vis)
    
    elif graph.nodes[node]['label'] == AND_SUBXPAT:
        childs = list(graph.predecessors(node))
        vis[node] = visit(graph,childs[0], vis) and visit(graph,childs[1], vis)
    
    elif graph.nodes[node]['label'] == 'TRUE':
        vis[node] = True
    
    elif graph.nodes[node]['label'] == 'FALSE':
        vis[node] = False
    
    elif node.startswith(OUTPUT_GATE_INITIALS):
        vis[node] = visit(graph, next(graph.predecessors(node)), vis)
    
    else:
        raise RuntimeError("error here")
    
    return vis[node]

def get_error(exact_graph: AnnotatedGraph, app_graph: Graph, inputs):
    exact_output = 0
    app_output = 0

    vis = {}
    for x in inputs:
        vis[x] = inputs[x]
    
    for out in exact_graph.output_dict.values():
        if visit(exact_graph.graph, out, vis) :
            exact_output += 2 ** int(out[len(OUTPUT_GATE_INITIALS):])
    
    vis = {}
    for x in inputs:
        vis[x] = inputs[x]
    
    for out in exact_graph.output_dict.values():
        if visit(app_graph, out, vis) :
            app_output += 2 ** int(out[len(OUTPUT_GATE_INITIALS):])
    
    return abs(exact_output - app_output)
    

def test(fro, et, needed_inputs, needed_outputs):
    shutil.copy(f'{fro}.txt',f'{fro}_{et}.txt')
    global output
    output = open(f'{fro}_{et}.txt','a')
    outputs_exact = []
    outputs_inexact = []
    for x in range(int(needed_outputs[-1][len(OUTPUT_GATE_INITIALS):]) + 1):
        temp = OUTPUT_GATE_INITIALS + str(x)
        if temp in needed_outputs:
            outputs_exact.append(make_qcir_variable(temp))
            outputs_inexact.append(make_qcir_variable_inexact(temp))
        else:
            outputs_exact.append('92')
            outputs_inexact.append('92')

    outputs_inexact.append('92')
    outputs_exact.append('92')

    outputs_inexact = increment(inverse(outputs_inexact),carry=False)
    subtraction_results = signed_adder(outputs_exact,outputs_inexact)
    absolute_values = absolute_value(subtraction_results)
    output.write(f'90 = and({comparator_greater_than(absolute_values,et)})')

    output.close()
    result = subprocess.run(['../../../../cqesto-master/build/cqesto', f'{fro}_{et}.txt'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout.decode('utf-8')

    os.remove(f'{fro}_{et}.txt')

    return result

def add_predecessors(graph: AnnotatedGraph, cur_node):
    res = []
    for x in graph.graph.predecessors(cur_node):
        res.append(x)
    return res

def labeling(exact_graph_name: str, app_graph_name: str ,et,  already_labeled = {}):
    exact_graph = AnnotatedGraph(exact_graph_name)
    app_graph = AnnotatedGraph(app_graph_name)

    labels = {}
    visited = set()
    K = 2
    exact_nodes = exact_graph.graph.nodes
    app_nodes = app_graph.graph.nodes
    app_graph.graph.add_node('7')
    app_nodes['7']['label'] = 'not'
    global output
    stack = []

    for node in app_graph.output_dict.values():
        value = 2 ** int(node[len(OUTPUT_GATE_INITIALS):])

        
        for x in app_graph.graph.predecessors(node):
            if(value <= K*et):
                stack.append(x)
        
        while len(stack):
            cur_node = stack.pop()
            if cur_node.startswith(INPUT_GATE_INITIALS) or cur_node.startswith(OUTPUT_GATE_INITIALS):
                continue
            if cur_node in visited:
                continue
            visited.add(cur_node)
            if cur_node in already_labeled:
                labels[cur_node] = already_labeled[cur_node]
                for x in add_predecessors(app_graph, cur_node):
                    stack.append(x)
                continue

            output = open(f'./output/labeling_{cur_node}.txt','w')
            output.write('#QCIR-14\nexists(')
            first = True
            for x in exact_graph.input_dict.values():
                if not first:
                    output.write(', ')
                output.write(f'{make_qcir_variable(x)}')
                first = False
            
            
            output.write(')\n#\n')
            output.write('output(90)\n#\n')
            output.write('91 = and()\n92 = or()\n#\n')
            

            output.write('#Exact circuit\n')
            inverted = {} 
            pres = set()
            st = []
            for x in exact_graph.input_dict.values():
                for succ in exact_graph.graph.successors(x):
                    if exact_nodes[succ]['label'] == NOT or succ in pres:
                        st.append(succ)
                    else:
                        pres.add(succ)
            
            while len(st):
                cur = st.pop()
                label = exact_nodes[cur]['label']
                if label == NOT:
                    predecessor = next(exact_graph.graph.predecessors(cur))
                    predecessor_label = exact_nodes[predecessor]['label']
                    if predecessor_label == NOT:
                        inverted[cur] = [inverted[predecessor][0], not inverted[predecessor][1]]
                    else:
                        inverted[cur] = [predecessor, True]
                
                else:
                    output.write(make_qcir_variable(cur) + ' = ' + (AND_QCIR if label == AND_SUBXPAT else OR_QCIR) + '(')
                    for i,x in enumerate(exact_graph.graph.predecessors(cur)):
                        if x in inverted:
                            if inverted[x][1]:
                                output.write('-')
                            output.write(make_qcir_variable(inverted[x][0]))
                        else:
                            output.write(make_qcir_variable(x))
                        output.write(', ' if i < len(list(exact_graph.graph.predecessors(cur))) - 1 else '')
                    output.write(')\n')

                for x in exact_graph.graph.successors(cur):
                    if exact_nodes[x]['label'] == NOT or x in pres:
                        st.append(x)
                    else:
                        pres.add(x)
                
            #add outputs
            output.write('#\n#outputs of exact circuit\n')
            for x in exact_graph.output_dict.values():
                if exact_nodes[next(exact_graph.graph.predecessors(x))]['label'] == 'FALSE' or exact_nodes[next(exact_graph.graph.predecessors(x))]['label'] == 'TRUE':
                    output.write(make_qcir_variable(x) + ' = and(' + ('91' if exact_nodes[next(exact_graph.graph.predecessors(x))]['label'] == 'TRUE' else '92') + ')\n')
                    continue
                predecessor = next(exact_graph.graph.predecessors(x))
                inv = False
                if predecessor in inverted:
                    inv = inverted[predecessor][1]
                    predecessor = inverted[predecessor][0]
                output.write(make_qcir_variable(x) + ' = and(' + ('-' if inv else '') + make_qcir_variable(predecessor) + ')\n')
            #finished exact_circuit
            output.write('#\n')


            inverted = {} 
            pres = set()
            st = [] 
            G_inv = app_graph.graph.copy()
            G_inv.add_edge(cur_node, '7')
            for succ in app_graph.graph.successors(cur_node):
                G_inv.remove_edge(cur_node,succ)
                G_inv.add_edge('7',succ)
            for x in list(app_graph.input_dict.values()) + list(filter(lambda x: app_nodes[x]['label'] == 'FALSE' or app_nodes[x]['label'] == 'TRUE', app_nodes)):
                for succ in G_inv.successors(x):
                    if app_nodes[succ]['label'] == NOT or succ in pres:
                        st.append(succ)
                    else:
                        pres.add(succ)

            while len(st) != 0:
                cur = st.pop()
                label = app_nodes[cur]['label']
                if label == NOT:
                    predecessor = next(G_inv.predecessors(cur))
                    predecessor_label = app_nodes[predecessor]['label']
                    if predecessor_label == NOT:
                        inverted[cur] = [inverted[predecessor][0], not inverted[predecessor][1]]
                    else:
                        inverted[cur] = [predecessor, True]
                
                else:
                    output.write(make_qcir_variable_inexact(cur) + ' = ' + (AND_QCIR if label == AND_SUBXPAT else OR_QCIR) + '(')
                    for i,x in enumerate(G_inv.predecessors(cur)):
                        if x in inverted:
                            if inverted[x][1]:
                                output.write('-')
                            output.write(make_qcir_variable_inexact(inverted[x][0]))
                        else:
                            output.write(make_qcir_variable_inexact(x))
                        output.write(', ' if i < len(list(G_inv.predecessors(cur))) - 1 else '')
                    output.write(')\n')

                for x in G_inv.successors(cur):
                    if app_nodes[x]['label'] == NOT or x in pres:
                        st.append(x)
                    else:
                        pres.add(x)
                
            #add outputs
            output.write('#\n#outputs of app circuit\n')
            for x in app_graph.output_dict.values():
                if app_nodes[next(G_inv.predecessors(x))]['label'] == 'FALSE' or app_nodes[next(G_inv.predecessors(x))]['label'] == 'TRUE':
                    output.write(make_qcir_variable_inexact(x) + ' = and(' + ('91' if app_nodes[next(G_inv.predecessors(x))]['label'] == 'TRUE' else '92') + ')\n')
                    continue
                predecessor = next(G_inv.predecessors(x))
                inv = False
                if predecessor in inverted:
                    inv = inverted[predecessor][1]
                    predecessor = inverted[predecessor][0]
                if app_nodes[predecessor]['label'] == 'TRUE' or app_nodes[predecessor]['label'] == 'FALSE':
                    if app_nodes[predecessor]['label'] == 'FALSE':
                        inv = not inv
                    output.write(make_qcir_variable_inexact(x) + ' = and(' + ('92' if inv else '91') + ')\n')
                    
                else:
                    output.write(make_qcir_variable_inexact(x) + ' = and(' + ('-' if inv else '') + make_qcir_variable_inexact(predecessor) + ')\n')
            #finished exact_circuit
            output.write('#\n')
            output.close()

            l ,r = 0 ,1
            for x in exact_graph.output_dict.values():
                r += 2 ** int(x[len(OUTPUT_GATE_INITIALS):])

            while True:
                start = time.perf_counter()
                res = test(f'./output/labeling_{cur_node}', l, list(exact_graph.input_dict.values()), list(exact_graph.output_dict.values()))
                tot = time.perf_counter() - start
                if res.strip()[-1] == '0':
                    break

                inputsq = res.split('\n')[3].split()[1:-1]
                inputs = {}
                for x in inputsq:
                    inputs['in' + x[2:]] = True if x[0] == '+' else False
                l = max(l+1, get_error(exact_graph, G_inv, inputs))

            labels[cur_node]=l
            for x in add_predecessors(app_graph, cur_node):
                stack.append(x)

            os.remove(f'./output/labeling_{cur_node}.txt')

    return labels
                    


            
           
        
if __name__ == "__main__":
    print(labeling('mul_i4_o4','mul_i4_o4', 1e100))
    print()