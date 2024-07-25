import sys
from collections import deque
import subprocess
sys.path.append("/home/lorenzospada/Documents/SubXPAT")


from sxpat.annotatedGraph import *
#test
#I need the labels for how the not,and,or gates are called in subxpat and the labels for the name of the function of and and or in qcir
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

output = open('./Lollo/output.txt','w')
temporary_gates_index = 0

class Result:
    status: str
    model: Dict[str, bool]
    def __init__(self,stri,dicti) -> None:
        self.status = stri
        self.model = dicti

def make_qcir_variable(var):
    for key,value in CHANGE.items():
        if var[:len(key)] == key:
            return value + var[len(key):] 
    raise TypeError("received a variable that I can't convert, the variable was: " + var)

def make_qcir_variable_inexact(var):
    for key,value in CHANGE_INEXACT.items():
        if var[:len(key)] == key:
            return value + var[len(key):] 
    raise TypeError("received a variable that I can't convert, the variable was: " + var)

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

def test_equality_lists(a : List, b : list):
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

def operation_on_list(a : List, operation : str) -> List:
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

def xor_bits_with_bit(a : list, b) -> List:
    results = []
    for i in range(len(a)):
        results.append(xor(a[i],b))
    return results

def inverse(a : List) -> List:
    output.write('#inversing every bit\n')
    results = []
    for x in a:
        results.append(next_temporary_variable())
        output.write(f'{results[-1]} = and(-{x})\n')
    output.write('#\n')
    return results

def adder_bits_with_bit(a : list, b) -> List:
    results = []
    last_and = b
    for i in range(len(a)):
        results.append(xor(last_and, a[i]))
        temp = next_temporary_variable()
        output.write(f'{temp} = and({last_and}, {a[i]})\n')
        last_and = temp
    output.write('#\n')
    return results

def absolute_value(a) -> List:
    return adder_bits_with_bit(xor_bits_with_bit(a,a[-1]),a[-1])

def increment(a : List,carry=True) -> List:
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
    for i in range(1,len(a)):
        next,carry_in = adder_bit3(a[i],b[i],carry_in)
        results.append(next)
    output.write('#\n')
    return results

def unsigned_adder(a : List, b : List) -> List:
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


def comparator_greater_than(a : List, e : int):
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
output.write('variables = 1,2,3,4,5,6,7,8\n92=or()\n')
outputs_inexact = increment(inverse([5,6,7,8,92]),carry=False)
subtraction_results = signed_adder([1,2,3,4,92],outputs_inexact)
absolute_values = absolute_value(subtraction_results)
comparator = comparator_greater_than(absolute_values,128)
output.write(f'90 = and(-{comparator})')
print(outputs_inexact)
print(subtraction_results)
print(absolute_values)
print(comparator)
# output.write('outputs = ')
# start = True
# for x in absolute_values:
#     if not start:
#         output.write(', ')
#     start = False
#     output.write(x)
# output.write('\n')

#specs_obj: TemplateSpecs
def check_sat(specs_obj: TemplateSpecs):
    annotated = AnnotatedGraph(specs_obj.benchmark_name, is_clean=False, partitioning_percentage=1) 
    annotated.extract_subgraph(specs_obj)
    graph = annotated.graph
    nodes = graph.nodes
    print(annotated.subgraph_num_inputs)
    
    # 1,2,30 is for the input, and, output gates of the exact circuit, 40 for intermidiate and gates of the multiplexer, 41 for the output of the multiplexer,
    # 5 for the and gates, 60 for the or gates, 61 for the and between the or gate and p_o# (the outputs of the parametrical circuit),
    # 62 is for the and gates of the inexact circuit, 7 is for the parameters p_o#_t#_i#_s/l, 31 is for the outputs of the inexact circuit
    # 90 is for the satisfability problem, 91 for true constant, 92 for false constant, 93 for the parameters p_o#, 94 is for temporary gates
    
    output.write('#QCIR-14\n')

    #add the exist for parameters
    output.write('exists(')
    start = True
    for a in range(annotated.subgraph_num_outputs):
        for t in range(specs_obj.max_ppo):
            for c in range(annotated.subgraph_num_inputs):
                if not start:
                    output.write(', ')
                var = ((a * specs_obj.max_ppo + t) * annotated.subgraph_num_inputs + c) * 2
                output.write('7' + str(var) + ', 7' + str(var+1))
                start = False
        output.write(', 93' + str(a))

    output.write(')\nforall(')
    deq = deque()
    pres = set() #used to check if and / or gates have all their inputs arrived
    start = True
    for x in nodes:
        if x[:len(INPUT_GATE_INITIALS)] != INPUT_GATE_INITIALS:
            continue
        for succ in graph.successors(x):
            if nodes[succ]['label'] == NOT or succ in pres:
                deq.append(succ)
            else:
                pres.add(succ)
        if not start:
            output.write(', ')
        output.write(make_qcir_variable(x))
        start = False
    output.write(')\n#\n')
    
    output.write('output(90)\n#\n')

    output.write('91 = and()\n92 = or()\n#\n')

    output.write('#exact_circuit\n')
    inverted = {} #key : [gate_referring_to, inverted?]
    while len(deq) != 0:
        cur = deq.popleft()
        label = nodes[cur]['label']
        if label == NOT:
            predecessor = next(graph.predecessors(cur))
            predecessor_label = nodes[predecessor]['label']
            if predecessor_label == NOT:
                inverted[cur] = [inverted[predecessor][0], not inverted[predecessor][1]]
            else:
                inverted[cur] = [predecessor, True]
        
        else:
            output.write(make_qcir_variable(cur) + ' = ' + (AND_QCIR if label == AND_SUBXPAT else OR_QCIR) + '(')
            for i,x in enumerate(graph.predecessors(cur)):
                if x in inverted:
                    if inverted[x][1]:
                        output.write('-')
                    output.write(make_qcir_variable(inverted[x][0]))
                else:
                    output.write(make_qcir_variable(x))
                output.write(', ' if i < len(list(graph.predecessors(cur))) - 1 else '')
            output.write(')\n')

        for x in graph.successors(cur):
            if nodes[x]['label'] == NOT or x in pres:
                deq.append(x)
            else:
                pres.add(x)
        
    #add outputs
    output.write('#\n#outputs of exact circuit\n')
    for x in nodes:
        if x[:len(OUTPUT_GATE_INITIALS)] != OUTPUT_GATE_INITIALS:
            continue
        predecessor = next(graph.predecessors(x))
        inv = False
        if predecessor in inverted:
            inv = inverted[predecessor][1]
            predecessor = inverted[predecessor][0]
        output.write(make_qcir_variable(x) + ' = and(' + ('-' if inv else '') + make_qcir_variable(predecessor) + ')\n')
    #finished exact_circuit
    output.write('#\n')

    output.write('#parametrical_circuit\n')
    #start with parametrical_template
    deq = deque()
    predecessors = {} #key : [(gate_coming_from, inverted?), // ]
    #formula of multiplexer or( and(s,l,in), and(s, !l, !in), !s)
    for a,out in enumerate(annotated.subgraph_output_dict.values()):
        and_list = []

        for t in range(specs_obj.max_ppo):
            multi_list = []

            for c,inp in enumerate(annotated.subgraph_input_dict.values()):
                var = ((a * specs_obj.max_ppo + t) * annotated.subgraph_num_inputs + c) * 2
                and1 = '40' + str(var)
                and2 = '40' + str(var+1)

                #partial and gates of the multiplexer
                output.write(and1 + ' = and(7' + str(var) + ', 7' + str(var+1)  + ', ' + (make_qcir_variable(inp) if nodes[inp]['label'] != NOT else
                                                                                          ('-' if inverted[inp][1] else '') + make_qcir_variable(inverted[inp][0])) + ')\n')

                output.write(and2 + ' = and(7' + str(var) + ', -7' + str(var+1) + ', ' + ('-' + make_qcir_variable(inp) if nodes[inp]['label'] != NOT else
                                                                                          ('' if inverted[inp][1] else '-') + make_qcir_variable(inverted[inp][0])) + ')\n')

                #output of the multiplexer
                multi = '41' + str(var//2)
                output.write(multi + ' = or(' + and1 + ', ' + and2 + ', -7' + str(var) + ')\n')
                multi_list.append(multi)

            #and gates of the parametrical circuit
            var = a * specs_obj.max_ppo + t
            andg = '5' + str(var)
            and_list.append(andg)
            output.write(andg + ' = and(')
            start = True
            for m in multi_list:
                if not start:
                    output.write(', ')
                start = False
                output.write(m)
            output.write(')\n')

        #or gates of the parametrical circuit
        org = '60' + str(a)
        output.write(org + ' = or(')
        start = True
        for x in and_list:
            if not start:
                output.write(', ')
            start = False
            output.write(x)
        output.write(')\n')

        #p_o#
        p_o = '93' + str(a)
        #outputs of the parametrical circuit
        outp = '61' + str(a)
        output.write(outp + ' = and(' + p_o + ', ' + org + ')\n')

        for succ in graph.successors(out):
            if nodes[succ]['label'] == NOT or succ in predecessors:
                deq.append(succ)
                if nodes[succ]['label'] == NOT:
                    predecessors[succ] = [(outp,False)]
                else:
                    predecessors[succ].append((outp,False))
            else:
                predecessors[succ] = [(outp,False)]
    
    for x in nodes:
        if x[:len(INPUT_GATE_INITIALS)] != INPUT_GATE_INITIALS:
            continue
        for succ in graph.successors(x):
            if nodes[succ]['label'] == NOT or succ in predecessors:
                deq.append(succ)
                if nodes[succ]['label'] == NOT:
                    predecessors[succ] = [(x,False)]
                else:
                    predecessors[succ].append((x,False))
            else:
                predecessors[succ] = [(x,False)]
    
    output.write('#\n')
    while len(deq) != 0:
        cur = deq.popleft()
        
        if cur in annotated.subgraph_output_dict.values():
            continue
        label = nodes[cur]['label']
        if label == AND_SUBXPAT or label == OR_SUBXPAT:
            output.write(make_qcir_variable_inexact(cur) + ' = ' + (AND_QCIR if label == AND_SUBXPAT else OR_QCIR) + '(')
            for i,x in enumerate(predecessors[cur]):
                if x[1]:
                    output.write('-')
                output.write(make_qcir_variable_inexact(x[0]))
                output.write(', ' if i < len(predecessors[cur]) - 1 else '')
            output.write(')\n')

        for succ in graph.successors(cur):
            if nodes[succ]['label'] == NOT:
                deq.append(succ)
                if label == NOT:
                    predecessors[succ] = [(predecessors[cur][0][0], not predecessors[cur][0][1])]
                else:
                    predecessors[succ] = [(cur,False)]
            
            elif succ in predecessors:
                deq.append(succ)
                if label == NOT:
                    predecessors[succ].append((predecessors[cur][0][0],not predecessors[cur][0][1]))
                else:
                    predecessors[succ].append((cur,False))
            
            else:
                if label == NOT:
                    predecessors[succ] = [(predecessors[cur][0][0],not predecessors[cur][0][1])]
                else:
                    predecessors[succ] = [(cur,False)]
    
    output.write('#\n#outputs of inexact_circuit\n')
    for x in nodes:
        if x[:len(OUTPUT_GATE_INITIALS)] != OUTPUT_GATE_INITIALS:
            continue
        if x in annotated.subgraph_output_dict.values():
            output.write(f'{make_qcir_variable_inexact(x)} = and(61{x[len(OUTPUT_GATE_INITIALS):]})\n')
        else:
            output.write(make_qcir_variable_inexact(x) + ' = and(' + ('-' if predecessors[x][0][1] else '') + make_qcir_variable_inexact(predecessors[x][0][0]) + ')\n')
    #finished exact_circuit
    output.write('#\n')
    
    # change sign of the outputs of inexact_circuit
    output.write('#change sign of the outputs of inexact_circuit (using two\'s complement)\n')
    outputs_inexact = []
    outputs_exact = []
    i = 0
    while OUTPUT_GATE_INITIALS + str(i) in nodes:
        outputs_inexact.append(CHANGE_INEXACT[OUTPUT_GATE_INITIALS] + str(i))
        outputs_exact.append(CHANGE[OUTPUT_GATE_INITIALS] + str(i))
        i+=1
    outputs_inexact = increment(inverse(outputs_inexact))
    substraction_results = signed_adder(outputs_exact,outputs_inexact)
    absolute_values = absolute_value(substraction_results)
    res = []
    if specs_obj.max_lpp < annotated.subgraph_num_inputs:
        for a in range(annotated.subgraph_num_outputs):
            for t in range(specs_obj.max_ppo):
                deqVar = deque()
                deq = deque()
                for c in range(annotated.subgraph_num_inputs):
                    var = '7' + str(((a * specs_obj.max_ppo + t) * annotated.subgraph_num_inputs + c) * 2)
                    deqVar.append(var)
                while len(deqVar) > 0 or len(deq) > 1:
                    if len(deqVar) > 2:
                        first = deqVar.pop()
                        second = deqVar.pop()
                        third = deqVar.pop()
                        deq.append(adder_bit3(first,second,third))
                    elif len(deqVar) > 0:
                        while len(deqVar) > 0:
                            deq.appendleft([deqVar.pop()])
                    else:
                        first = deq.popleft()
                        second = deq.popleft()
                        deq.append(unsigned_adder(first,second))
                res.append(comparator_greater_than(deq.pop(),specs_obj.max_lpp))

    output.write(f'90 = and(-{comparator_greater_than(absolute_values,specs_obj.et)}')
    for x in res:
        output.write(f', -{x}')
    output.write(')\n')
    output.close()
    #this commands outputs to sdout "c bt_count: #" where # is a number this output is from the QBF solver and I think there's no way to not output it.
    # (I have no idea what its meaning is)
    result = subprocess.run(['../../cqesto-master/build/cqesto', 'Lollo/output.txt'],stdout=subprocess.PIPE).stdout.decode('utf-8')
    
    if result.strip()[-1] == '1':
        print(result.split('\n')[3][2:-2].split())
        print('time taken = ' + result.split('\n')[4].split()[-1])
        res_dict = dict()
        for x in result.split('\n')[3][2:-2].split():
            if x[1] == '7':
                number = int(x[2:])
                res_dict[f'p_o{number // 2 // annotated.subgraph_num_inputs // specs_obj.max_ppo}_t{number // 2 // annotated.subgraph_num_inputs % specs_obj.max_ppo}_i{number // 2 % annotated.subgraph_num_inputs}_' + 's' if int(x) % 2 == 0 else 'l'] = True if x[0] == '+' else False
            else:
                res_dict[f'p_o{x[3:]}'] = True if x[0] == '+' else False
        return Result('solvable',res_dict)
    else:
        print('false')
        print('time taken = ' + result.split('\n')[4].split()[-1])
        return Result('unsolvable',dict())

    # test for equality fast
    # i = 0
    # remember = []
    # for x in nodes:
    #     if x[0] != 'o':
    #         continue
    #     remember.append(test_equality_bits('30'+str(i),'31'+str(i)))
    #     i+=1
    # output.write('#\n90 = and(')
    # start = True
    # for x in remember:
    #     if not start:
    #         output.write(', ')
    #     start = False
    #     output.write(x)
    # output.write(')\n')