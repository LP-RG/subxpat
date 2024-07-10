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
CHANGE = {INPUT_GATE_INITIALS : "1", STANDARD_GATE_INITIALS : "2", OUTPUT_GATE_INITIALS : "30"} #

def make_qcir_variable(var):
    for key,value in CHANGE.items():
        if var[:len(key)] == key:
            return value + var[len(key):] 
    raise TypeError("received a variable that I can't convert, the variable was: " + var)

#specs_obj: TemplateSpecs
def check_sat(specs_obj: TemplateSpecs):
    annotated = AnnotatedGraph('adder_i16_o9', is_clean=False, partitioning_percentage=1) 
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
    print(*annotated.graph.predecessors('g18'))
    print(*annotated.graph.predecessors('g35'))
    #print(list(annotated.graph.predecessors('g103')))
    
    # 1,2,30 is for the input, and, output gates of the exact circuit, 40 for intermidiate and gates of the multiplexer, 41 for the output of the multiplexer,
    # 5 for the and gates, 60 for the or gates, 61 for the and between the or gate and p_o# (the outputs of the parametrical circuit),
    # 62 is for the and gates of the inexact circuit, 7 is for the parameters p_o#_t#_i#_s/l,
    # 90 is for the satisfability problem, 91 for false constant, 92 for true constant, 93 for the parameters p_o#
    output = open('./Lollo/output.txt','w')
    
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
    pres = {}  # qcir_gate_name : qcir_gate_you_come_from
    inverted = {} #key : [qcir_gate_referring_to, inverted?]
    for x in nodes:
        if x[:len(INPUT_GATE_INITIALS)] != INPUT_GATE_INITIALS:
            continue
        for succ in graph.successors(x):
            if nodes[succ]['label'] == NOT or make_qcir_variable(succ) in pres:
                deq.append(succ)
            else:
                pres[make_qcir_variable(succ)] = make_qcir_variable(x)
    
    #quasi uguale a sopra, sistemare
    while len(deq) != 0:
        cur = deq.popleft()
        if cur in annotated.subgraph_output_dict.values():
            continue
        label = nodes[cur]['label']
        if label == NOT:
            predecessor = next(graph.predecessors(cur))
            predecessor_label = nodes[predecessor]['label']
            if predecessor_label == NOT:
                inverted[make_qcir_variable(cur)] = [inverted[make_qcir_variable(predecessor)][0], not inverted[make_qcir_variable(predecessor)][1]]
            else:
                inverted[make_qcir_variable(cur)] = [predecessor, True]
        
        
        for x in graph.successors(cur):
            if nodes[x]['label'] == NOT or make_qcir_variable(x) in pres:
                deq.append(x)
            else:
                pres[make_qcir_variable(x)] = make_qcir_variable(cur)
    
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
                                                                                          ('-' if inverted[make_qcir_variable(inp)][1] else '') + make_qcir_variable(inverted[make_qcir_variable(inp)][0])) + ')\n')

                output.write(and2 + ' = and(7' + str(var) + ', -7' + str(var+1) + ', ' + ('-' + make_qcir_variable(inp) if nodes[inp]['label'] != NOT else
                                                                                          ('' if inverted[make_qcir_variable(inp)][1] else '-') + make_qcir_variable(inverted[make_qcir_variable(inp)][0])) + ')\n')

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

    output.write('\n#continuing exploration of inexact_circuit\n')
    #continuing exploration of inexact_circuit
    for a,out in enumerate(annotated.subgraph_output_dict.values()):
        for succ in graph.successors(out):
            label = nodes[succ]['label']
            qcir_out = '61' + str(a)
            # print(succ,pres[make_qcir_variable(succ)])
            if label == NOT:
                inverted[succ] = [qcir_out,True]
                deq.append(succ)
            
            
            elif make_qcir_variable(succ) in pres:
                deq.append(succ)
                output.write('62' + succ[len(STANDARD_GATE_INITIALS):] + ' = and(' + pres[make_qcir_variable(succ)] + ', ' + qcir_out + ')\n')

            else:
                pres[make_qcir_variable(succ)] = qcir_out
    

            

            
            
            

        



#check_sat()