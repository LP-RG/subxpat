import sys
from collections import deque
sys.path.append("/home/lorenzospada/Documents/SubXPAT")


from sxpat.annotatedGraph import *

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

def test_equality(a,b):
    global temporary_gates_index
    and1 = TEMPORARY_GATE_PREFIX + str(temporary_gates_index)
    and2 = TEMPORARY_GATE_PREFIX + str(temporary_gates_index+1)
    output.write(f'{and1} = and({a}, {b})\n')
    output.write(f'{and2} = and(-{a}, -{b})\n')
    result_gate_name = TEMPORARY_GATE_PREFIX + str(temporary_gates_index+2)
    output.write(f'{result_gate_name} = or({and1}, {and2})\n')
    temporary_gates_index += 3
    return result_gate_name

#specs_obj: TemplateSpecs
def check_sat(specs_obj: TemplateSpecs):
    annotated = AnnotatedGraph(specs_obj.benchmark_name, is_clean=False, partitioning_percentage=1) 
    annotated.extract_subgraph(specs_obj)
    graph = annotated.graph
    nodes = graph.nodes
    print(annotated.subgraph_input_dict.values())
    print(annotated.subgraph_output_dict.values())
    # print(specs_obj.et)
    # print(specs_obj.max_ppo)
    # print(annotated.subgraph_num_inputs, annotated.subgraph_num_outputs, specs_obj.max_ppo)
    # print(annotated.graph.nodes)
    # print(annotated.graph.nodes['g106'])
    # print(*annotated.graph.neighbors('g20'))
    # print(*annotated.graph.predecessors('out6'))
    # print(*annotated.graph.predecessors('g102'))

    # print(*annotated.graph.predecessors('g101'))
    # print(*annotated.graph.predecessors('g100'))
    # print(*annotated.graph.predecessors('g52'))
    # print(*annotated.graph.predecessors('g98'))

    # print(*annotated.graph.predecessors('g99'))
    # print(*annotated.graph.predecessors('g97'))
    # print(*annotated.graph.predecessors('g60'))
    # print(*annotated.graph.predecessors('g96'))
    # print('\n\n')
    #print(list(annotated.graph.predecessors('g103')))
    
    
    # 1,2,30 is for the input, and, output gates of the exact circuit, 40 for intermidiate and gates of the multiplexer, 41 for the output of the multiplexer,
    # 5 for the and gates, 60 for the or gates, 61 for the and between the or gate and p_o# (the outputs of the parametrical circuit),
    # 62 is for the and gates of the inexact circuit, 7 is for the parameters p_o#_t#_i#_s/l, 31 is for the outputs of the inexact circuit
    # 90 is for the satisfability problem, 91 for false constant, 92 for true constant, 93 for the parameters p_o#, 94 is for temporary gates
    
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
    output.write(')\n\n')
    
    output.write('output(90)\n\n')

    output.write('91 = and()\n92 = or()\n\n')

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
    output.write('\n#outputs of exact circuit\n')
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
    output.write('\n')

    output.write('#parametrical_circuit\n')
    #start with parametrical_template
    deq = deque()
    #pres = set()
    #inverted = {} #key : [gate_referring_to, inverted?]
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
                    predecessors[succ] = [(cur,True)]
            
            elif succ in predecessors:
                deq.append(succ)
                if label == NOT:
                    predecessors[succ].append(predecessors[cur][0])
                else:
                    predecessors[succ].append((cur,False))
            
            else:
                if label == NOT:
                    predecessors[succ] = [predecessors[cur][0]]
                else:
                    predecessors[succ] = [(cur,False)]
   
    output.write('\n#outputs of inexact_circuit\n')
    for x in nodes:
        if x[:len(OUTPUT_GATE_INITIALS)] != OUTPUT_GATE_INITIALS:
            continue
        output.write(make_qcir_variable_inexact(x) + ' = and(' + ('-' if predecessors[x][0][1] else '') + make_qcir_variable_inexact(predecessors[x][0][0]) + ')\n')
    #finished exact_circuit
    output.write('\n')

    i = 0
    remember = []
    for x in nodes:
        if x[0] != 'o':
            continue
        remember.append(test_equality('30'+str(i),'31'+str(i)))
        i+=1
    output.write('\n90 = and(')
    start = True
    for x in remember:
        if not start:
            output.write(', ')
        start = False
        output.write(x)
    output.write(')\n')

    