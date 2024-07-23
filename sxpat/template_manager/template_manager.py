from __future__ import annotations
from typing import Callable, Collection, Dict, Iterable, Sequence, Tuple
import dataclasses as dc

from abc import abstractmethod

import functools
import itertools

import json
import re
import subprocess

#used in SOP_QBF_Manager (os is used to delete a file that is generated during the run function)
from collections import deque
import os

from sxpat.annotatedGraph import AnnotatedGraph
import sxpat.config.config as sxpat_cfg
import sxpat.config.paths as sxpat_paths
from sxpat.templateSpecs import TemplateSpecs
from .encoding import Encoding
from sxpat.utils.collections import mapping_inv, pairwise_iter


@dc.dataclass
class Result:
    status: str
    model: Dict[str, bool]

class TemplateManager:
    @staticmethod
    def factory(specs: TemplateSpecs,
                exact_graph: AnnotatedGraph,
                current_graph: AnnotatedGraph,
                ) -> TemplateManager:
        # create required Encoding object
        encoding = Encoding.factory(
            specs.encoding,
            exact_graph.num_inputs,
            exact_graph.num_outputs
        )

        # select and return TemplateManager object
        return {
            (False, 1): SOPManager,
            (False, 2): SOPManager,
            (True, 1): SOPSManager,
            (True, 2): SOPSManager,
            (False, 3): SOP_QBF_Manager,
        }[specs.shared, specs.encoding](
            exact_graph,
            current_graph,
            specs,
            encoding
        )

    def __init__(self, exact_graph: AnnotatedGraph,
                 current_graph: AnnotatedGraph,
                 specs: TemplateSpecs,
                 encoding: Encoding,
                 ) -> None:
        self._exact_graph = exact_graph
        self._current_graph = current_graph
        self._specs = specs
        self._encoding = encoding

    def run(self) -> Sequence[Result]:
        raise NotImplementedError(f'{self.__class__.__name__}.run(...) is abstract.')

class SOP_QBF_Manager(TemplateManager):
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

    output = 1
    temporary_gates_index = 0

    def make_qcir_variable(var):
        for key,value in SOP_QBF_Manager.CHANGE.items():
            if var[:len(key)] == key:
                return value + var[len(key):] 
        raise TypeError("received a variable that I can't convert, the variable was: " + var)

    def make_qcir_variable_inexact(var):
        for key,value in SOP_QBF_Manager.CHANGE_INEXACT.items():
            if var[:len(key)] == key:
                return value + var[len(key):] 
        raise TypeError("received a variable that I can't convert, the variable was: " + var)

    def next_temporary_variable():
        SOP_QBF_Manager.temporary_gates_index += 1
        return SOP_QBF_Manager.TEMPORARY_GATE_PREFIX + str(SOP_QBF_Manager.temporary_gates_index - 1)

    def test_equality_bits(a,b):
        and1 = SOP_QBF_Manager.next_temporary_variable()
        and2 = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{and1} = and({a}, {b})\n')
        SOP_QBF_Manager.output.write(f'{and2} = and(-{a}, -{b})\n')
        result_gate_name = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{result_gate_name} = or({and1}, {and2})\n')
        return result_gate_name

    def test_equality_lists(a : list, b : list):
        SOP_QBF_Manager.output.write('#testing equalilty\n')
        assert len(a) == len(b) , 'lengths of a and b should be the same'
        
        partials = []
        for i in range(len(a)):
            partials.append(SOP_QBF_Manager.test_equality_bits(a[i],b[i]))
        return SOP_QBF_Manager.operation_on_list(partials, 'and')

    def and2(a,b):
        res = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{res} = and({a}, {b})\n')
        return res

    def or2(a,b):
        res = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{res} = or({a}, {b})\n')
        return res

    def operation_on_list(a : list, operation : str) -> list:
        res = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{res} = {operation}(')
        start = True
        for x in a:
            if not start:
                SOP_QBF_Manager.output.write(', ')
            SOP_QBF_Manager.output.write(x)
            start = False
        SOP_QBF_Manager.output.write(')\n#\n')
        return res

    def xor(a,b):
        pand1 = SOP_QBF_Manager.next_temporary_variable()
        pand2 = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{pand1} = and(-{a}, {b})\n')
        SOP_QBF_Manager.output.write(f'{pand2} = and({a}, -{b})\n')
        result_gate_name = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{result_gate_name} = or({pand1}, {pand2})\n')
        return result_gate_name

    def adder_bit3(a,b,c):
        results = []
        partial_xor = SOP_QBF_Manager.xor(a,b)
        results.append(SOP_QBF_Manager.xor(partial_xor,c))
        partial_and1 = SOP_QBF_Manager.and2(a,b)
        partial_and2 = SOP_QBF_Manager.and2(c,partial_xor)
        results.append(SOP_QBF_Manager.or2(partial_and1,partial_and2))
        return results

    def xor_bits_with_bit(a : list, b) -> list:
        results = []
        for i in range(len(a)):
            results.append(SOP_QBF_Manager.xor(a[i],b))
        return results

    def inverse(a : list) -> list:
        SOP_QBF_Manager.output.write('#inversing every bit\n')
        results = []
        for x in a:
            results.append(SOP_QBF_Manager.next_temporary_variable())
            SOP_QBF_Manager.output.write(f'{results[-1]} = and(-{x})\n')
        SOP_QBF_Manager.output.write('#\n')
        return results

    def adder_bits_with_bit(a : list, b) -> list:
        results = []
        last_and = b
        for i in range(len(a)):
            results.append(SOP_QBF_Manager.xor(last_and, a[i]))
            temp = SOP_QBF_Manager.next_temporary_variable()
            SOP_QBF_Manager.output.write(f'{temp} = and({last_and}, {a[i]})\n')
            last_and = temp
        SOP_QBF_Manager.output.write('#\n')
        return results

    def absolute_value(a) -> list:
        return SOP_QBF_Manager.adder_bits_with_bit(SOP_QBF_Manager.xor_bits_with_bit(a,a[-1]),a[-1])

    def increment(a : list,carry=True) -> list:
        """first element of a should be the least significant digit\n
        add one to a"""
        assert len(a) > 0, "lenght of a should be higher than 0"

        SOP_QBF_Manager.output.write('#incrementing by 1\n')
        if carry:
            a.append(a[-1])
        results = [SOP_QBF_Manager.next_temporary_variable()]
        SOP_QBF_Manager.output.write(f'{results[0]} = and(-{a[0]})\n')
        last_and = a[0]
        for i in range(1,len(a)):
            results.append(SOP_QBF_Manager.xor(last_and, a[i]))
            temp = SOP_QBF_Manager.next_temporary_variable()
            SOP_QBF_Manager.output.write(f'{temp} = and({last_and}, {a[i]})\n')
            last_and = temp
        SOP_QBF_Manager.output.write('#\n')
        return results

    def signed_adder(a : list, b : list) -> list:
        """first element of a should be the least significant digit"""

        a.append(a[-1])
        b.append(b[-1])
        while len(a) < len(b):
            a.append(a[-1])
        while len(b) < len(a):
            b.append(b[-1])
        SOP_QBF_Manager.output.write('#adding\n')
        results = [SOP_QBF_Manager.xor(a[0],b[0])]
        carry_in = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{carry_in} = and({a[0]}, {b[0]})\n')
        for i in range(1,max(len(a),len(b))):
            next,carry_in = SOP_QBF_Manager.adder_bit3(a[i],b[i],carry_in)
            results.append(next)
        SOP_QBF_Manager.output.write('#\n')
        return results

    def unsigned_adder(a : list, b : list) -> list:
        assert abs(len(a)-len(b)) <= 1, 'lengths of a and b should differ by maximum 1' 

        if len(a) < len(b):
            a,b = b,a
        results = [SOP_QBF_Manager.xor(a[0],b[0])]
        carry_in = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{carry_in} = and({a[0]}, {b[0]})\n')
        for i in range(1,max(len(a),len(b))):
            if i < min(len(a),len(b)):
                next,carry_in = SOP_QBF_Manager.adder_bit3(a[i],b[i],carry_in)
            else:
                next = SOP_QBF_Manager.xor(a[i],carry_in)
                carry_in = SOP_QBF_Manager.and2(a[i],carry_in)
            results.append(next)
        SOP_QBF_Manager.output.write('#\n')
        results.append(carry_in)
        return results


    def comparator_greater_than(a : list, e : int):
        SOP_QBF_Manager.output.write('#comparing\n')
        if (e >> len(a)) > 0:
            return '92'
        i = len(a) - 1
        partial_and = []
        while i >= 0:
            if (e >> i) & 1 == 0:
                partial_and.append(SOP_QBF_Manager.next_temporary_variable())
                SOP_QBF_Manager.output.write(f'{partial_and[-1]} = and({a[i]}')
                for j in range(len(a) - 1, i, -1):
                    SOP_QBF_Manager.output.write(', ' + ('' if (e >> j) & 1 else '-') + f'{a[j]}')
                SOP_QBF_Manager.output.write(')\n')
            i -= 1
        res = SOP_QBF_Manager.next_temporary_variable()
        SOP_QBF_Manager.output.write(f'{res} = or(')
        start = True
        for x in partial_and:
            if not start:
                SOP_QBF_Manager.output.write(', ')
            start = False
            SOP_QBF_Manager.output.write(x)
        SOP_QBF_Manager.output.write(')\n#\n')
        return res
    
    def run(self) -> Sequence[Result]:
        SOP_QBF_Manager.output = open('./Lollo/output.txt','w')
        graph_exact = self._exact_graph.graph
        nodes_exact = graph_exact.nodes
        graph_current = self._current_graph.graph
        nodes_current = graph_current.nodes
        
        # 1,2,30 is for the input, and, output gates of the exact circuit, 40 for intermidiate and gates of the multiplexer, 41 for the output of the multiplexer,
        # 5 for the and gates, 60 for the or gates, 61 for the and between the or gate and p_o# (the outputs of the parametrical circuit),
        # 62 is for the and gates of the inexact circuit, 7 is for the parameters p_o#_t#_i#_s/l, 31 is for the outputs of the inexact circuit
        # 90 is for the satisfability problem, 91 for true constant, 92 for false constant, 93 for the parameters p_o#, 94 is for temporary gates
        
        SOP_QBF_Manager.output.write('#QCIR-14\n')

        #add the exist for parameters
        SOP_QBF_Manager.output.write('exists(')
        start = True
        for a in range(self._current_graph.subgraph_num_outputs):
            for t in range(self._specs.ppo):
                for c in range(self._current_graph.subgraph_num_inputs):
                    if not start:
                        SOP_QBF_Manager.output.write(', ')
                    var = ((a * self._specs.ppo + t) * self._current_graph.subgraph_num_inputs + c) * 2
                    SOP_QBF_Manager.output.write('7' + str(var) + ', 7' + str(var+1))
                    start = False
            SOP_QBF_Manager.output.write(', 93' + str(a))

        SOP_QBF_Manager.output.write(')\nforall(')
        deq = deque()
        pres = set() #used to check if and / or gates have all their inputs arrived
        start = True
        for x in nodes_exact:

            if x[:len(SOP_QBF_Manager.INPUT_GATE_INITIALS)] != SOP_QBF_Manager.INPUT_GATE_INITIALS:
                continue
            for succ in graph_exact.successors(x):
                if nodes_exact[succ]['label'] == SOP_QBF_Manager.NOT or succ in pres:
                    deq.append(succ)
                else:
                    pres.add(succ)
            if not start:
                SOP_QBF_Manager.output.write(', ')
            SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable(x))
            start = False
        SOP_QBF_Manager.output.write(')\n#\n')
        
        SOP_QBF_Manager.output.write('output(90)\n#\n')

        SOP_QBF_Manager.output.write('91 = and()\n92 = or()\n#\n')

        SOP_QBF_Manager.output.write('#exact_circuit\n')
        inverted = {} #key : [gate_referring_to, inverted?]
        while len(deq) != 0:
            cur = deq.popleft()
            label = nodes_exact[cur]['label']
            if label == SOP_QBF_Manager.NOT:
                predecessor = next(graph_exact.predecessors(cur))
                predecessor_label = nodes_exact[predecessor]['label']
                if predecessor_label == SOP_QBF_Manager.NOT:
                    inverted[cur] = [inverted[predecessor][0], not inverted[predecessor][1]]
                else:
                    inverted[cur] = [predecessor, True]
            
            else:
                SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable(cur) + ' = ' + (SOP_QBF_Manager.AND_QCIR if label == SOP_QBF_Manager.AND_SUBXPAT else SOP_QBF_Manager.OR_QCIR) + '(')
                for i,x in enumerate(graph_exact.predecessors(cur)):
                    if x in inverted:
                        if inverted[x][1]:
                            SOP_QBF_Manager.output.write('-')
                        SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable(inverted[x][0]))
                    else:
                        SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable(x))
                    SOP_QBF_Manager.output.write(', ' if i < len(list(graph_exact.predecessors(cur))) - 1 else '')
                SOP_QBF_Manager.output.write(')\n')

            for x in graph_exact.successors(cur):
                if nodes_exact[x]['label'] == SOP_QBF_Manager.NOT or x in pres:
                    deq.append(x)
                else:
                    pres.add(x)
            
        #add outputs
        SOP_QBF_Manager.output.write('#\n#outputs of exact circuit\n')
        for x in nodes_exact:
            if x[:len(SOP_QBF_Manager.OUTPUT_GATE_INITIALS)] != SOP_QBF_Manager.OUTPUT_GATE_INITIALS:
                continue
            predecessor = next(graph_exact.predecessors(x))
            inv = False
            if predecessor in inverted:
                inv = inverted[predecessor][1]
                predecessor = inverted[predecessor][0]
            SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable(x) + ' = and(' + ('-' if inv else '') + SOP_QBF_Manager.make_qcir_variable(predecessor) + ')\n')
        #finished exact_circuit
        SOP_QBF_Manager.output.write('#\n')


        SOP_QBF_Manager.output.write('#parametrical_circuit\n')
        deq = deque()
        predecessors = {} #key : [(gate_coming_from, inverted?), // ]
        for x in nodes_current:
            if x[:len(SOP_QBF_Manager.INPUT_GATE_INITIALS)] != SOP_QBF_Manager.INPUT_GATE_INITIALS:
                continue
            for succ in graph_current.successors(x):
                if nodes_current[succ]['label'] == SOP_QBF_Manager.NOT or succ in predecessors:
                    deq.append(succ)
                    if nodes_current[succ]['label'] == SOP_QBF_Manager.NOT:
                        predecessors[succ] = [(x,False)]
                    else:
                        predecessors[succ].append((x,False))
                else:
                    predecessors[succ] = [(x,False)]
        
        SOP_QBF_Manager.output.write('#\n')
        while len(deq) != 0:
            cur = deq.popleft()
            
            if cur in self._current_graph.subgraph_output_dict.values():
                continue
            label = nodes_current[cur]['label']
            if label == SOP_QBF_Manager.AND_SUBXPAT or label == SOP_QBF_Manager.OR_SUBXPAT:
                SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable_inexact(cur) + ' = ' + (SOP_QBF_Manager.AND_QCIR if label == SOP_QBF_Manager.AND_SUBXPAT else SOP_QBF_Manager.OR_QCIR) + '(')
                for i,x in enumerate(predecessors[cur]):
                    if x[1]:
                        SOP_QBF_Manager.output.write('-')
                    SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable_inexact(x[0]))
                    SOP_QBF_Manager.output.write(', ' if i < len(predecessors[cur]) - 1 else '')
                SOP_QBF_Manager.output.write(')\n')

            for succ in graph_current.successors(cur):
                if nodes_current[succ]['label'] == SOP_QBF_Manager.NOT:
                    deq.append(succ)
                    if label == SOP_QBF_Manager.NOT:
                        predecessors[succ] = [(predecessors[cur][0][0], not predecessors[cur][0][1])]
                    else:
                        predecessors[succ] = [(cur,False)]
                
                elif succ in predecessors:
                    deq.append(succ)
                    if label == SOP_QBF_Manager.NOT:
                        predecessors[succ].append((predecessors[cur][0][0],not predecessors[cur][0][1]))
                    else:
                        predecessors[succ].append((cur,False))
                
                else:
                    if label == SOP_QBF_Manager.NOT:
                        predecessors[succ] = [(predecessors[cur][0][0],not predecessors[cur][0][1])]
                    else:
                        predecessors[succ] = [(cur,False)]

        #formula of multiplexer or( and(s,l,in), and(s, !l, !in), !s)
        for a,out in enumerate(self._current_graph.subgraph_output_dict.values()):
            and_list = []

            for t in range(self._specs.ppo):
                multi_list = []

                for c,inp in enumerate(self._current_graph.subgraph_input_dict.values()):
                    var = ((a * self._specs.ppo + t) * self._current_graph.subgraph_num_inputs + c) * 2
                    and1 = '40' + str(var)
                    and2 = '40' + str(var+1)

                    #partial and gates of the multiplexer
                    SOP_QBF_Manager.output.write(and1 + ' = and(7' + str(var) + ', 7' + str(var+1)  + ', ' + (SOP_QBF_Manager.make_qcir_variable_inexact(inp) if nodes_current[inp]['label'] != SOP_QBF_Manager.NOT else
                                                                                            ('-' if predecessors[inp][0][1] else '') + SOP_QBF_Manager.make_qcir_variable_inexact(predecessors[inp][0][0])) + ')\n')

                    SOP_QBF_Manager.output.write(and2 + ' = and(7' + str(var) + ', -7' + str(var+1) + ', ' + ('-' + SOP_QBF_Manager.make_qcir_variable_inexact(inp) if nodes_current[inp]['label'] != SOP_QBF_Manager.NOT else
                                                                                            ('' if predecessors[inp][0][1] else '-') + SOP_QBF_Manager.make_qcir_variable_inexact(predecessors[inp][0][0])) + ')\n')

                    #output of the multiplexer
                    multi = '41' + str(var//2)
                    SOP_QBF_Manager.output.write(multi + ' = or(' + and1 + ', ' + and2 + ', -7' + str(var) + ')\n')
                    multi_list.append(multi)

                #and gates of the parametrical circuit
                var = a * self._specs.ppo + t
                andg = '5' + str(var)
                and_list.append(andg)
                SOP_QBF_Manager.output.write(andg + ' = and(')
                start = True
                for m in multi_list:
                    if not start:
                        SOP_QBF_Manager.output.write(', ')
                    start = False
                    SOP_QBF_Manager.output.write(m)
                SOP_QBF_Manager.output.write(')\n')

            #or gates of the parametrical circuit
            org = '60' + str(a)
            SOP_QBF_Manager.output.write(org + ' = or(')
            start = True
            for x in and_list:
                if not start:
                    SOP_QBF_Manager.output.write(', ')
                start = False
                SOP_QBF_Manager.output.write(x)
            SOP_QBF_Manager.output.write(')\n')

            #p_o#
            p_o = '93' + str(a)
            #outputs of the parametrical circuit
            outp = '61' + str(a)
            SOP_QBF_Manager.output.write(outp + ' = and(' + p_o + ', ' + org + ')\n')

            for succ in graph_current.successors(out):
                if nodes_current[succ]['label'] == SOP_QBF_Manager.NOT or succ in predecessors:
                    deq.append(succ)
                    if nodes_current[succ]['label'] == SOP_QBF_Manager.NOT:
                        predecessors[succ] = [(outp,False)]
                    else:
                        predecessors[succ].append((outp,False))
                else:
                    predecessors[succ] = [(outp,False)]
        
        SOP_QBF_Manager.output.write('#\n')
        while len(deq) != 0:
            cur = deq.popleft()
            
            if cur in self._current_graph.subgraph_output_dict.values():
                continue
            label = nodes_current[cur]['label']
            if label == SOP_QBF_Manager.AND_SUBXPAT or label == SOP_QBF_Manager.OR_SUBXPAT:
                SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable_inexact(cur) + ' = ' + (SOP_QBF_Manager.AND_QCIR if label == SOP_QBF_Manager.AND_SUBXPAT else SOP_QBF_Manager.OR_QCIR) + '(')
                for i,x in enumerate(predecessors[cur]):
                    if x[1]:
                        SOP_QBF_Manager.output.write('-')
                    SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable_inexact(x[0]))
                    SOP_QBF_Manager.output.write(', ' if i < len(predecessors[cur]) - 1 else '')
                SOP_QBF_Manager.output.write(')\n')

            for succ in graph_current.successors(cur):
                if nodes_current[succ]['label'] == SOP_QBF_Manager.NOT:
                    deq.append(succ)
                    if label == SOP_QBF_Manager.NOT:
                        predecessors[succ] = [(predecessors[cur][0][0], not predecessors[cur][0][1])]
                    else:
                        predecessors[succ] = [(cur,False)]
                
                elif succ in predecessors:
                    deq.append(succ)
                    if label == SOP_QBF_Manager.NOT:
                        predecessors[succ].append((predecessors[cur][0][0],not predecessors[cur][0][1]))
                    else:
                        predecessors[succ].append((cur,False))
                
                else:
                    if label == SOP_QBF_Manager.NOT:
                        predecessors[succ] = [(predecessors[cur][0][0],not predecessors[cur][0][1])]
                    else:
                        predecessors[succ] = [(cur,False)]
        
        SOP_QBF_Manager.output.write('#\n#outputs of inexact_circuit\n')
        for x in nodes_current:
            if x[:len(SOP_QBF_Manager.OUTPUT_GATE_INITIALS)] != SOP_QBF_Manager.OUTPUT_GATE_INITIALS:
                continue
            if x in self._current_graph.subgraph_output_dict.values():
                SOP_QBF_Manager.output.write(f'{SOP_QBF_Manager.make_qcir_variable_inexact(x)} = and(61{x[len(SOP_QBF_Manager.OUTPUT_GATE_INITIALS):]})\n')
            elif len(list(graph_current.predecessors(x))) == 1 and (nodes_current[next(graph_current.predecessors(x))]['label'] == 'FALSE' or nodes_current[next(graph_current.predecessors(x))]['label'] == 'TRUE'):
                SOP_QBF_Manager.output.write(f'{SOP_QBF_Manager.make_qcir_variable_inexact(x)} = and(' + ('91' if nodes_current[next(graph_current.predecessors(x))]['label'] == 'TRUE' else '92') + ')\n')
            else:
                SOP_QBF_Manager.output.write(SOP_QBF_Manager.make_qcir_variable_inexact(x) + ' = and(' + ('-' if predecessors[x][0][1] else '') + SOP_QBF_Manager.make_qcir_variable_inexact(predecessors[x][0][0]) + ')\n')
        #finished exact_circuit
        SOP_QBF_Manager.output.write('#\n')
        
        # change sign of the outputs of inexact_circuit
        SOP_QBF_Manager.output.write('#change sign of the outputs of inexact_circuit (using two\'s complement)\n')
        outputs_inexact = []
        outputs_exact = []
        i = 0
        while SOP_QBF_Manager.OUTPUT_GATE_INITIALS + str(i) in nodes_current:
            outputs_inexact.append(SOP_QBF_Manager.CHANGE_INEXACT[SOP_QBF_Manager.OUTPUT_GATE_INITIALS] + str(i))
            outputs_exact.append(SOP_QBF_Manager.CHANGE[SOP_QBF_Manager.OUTPUT_GATE_INITIALS] + str(i))
            i+=1
        outputs_inexact.append('92')
        outputs_exact.append('92')
        outputs_inexact = SOP_QBF_Manager.increment(SOP_QBF_Manager.inverse(outputs_inexact),carry=False)
        subtraction_results = SOP_QBF_Manager.signed_adder(outputs_exact,outputs_inexact)
        absolute_values = SOP_QBF_Manager.absolute_value(subtraction_results)
        res = []
        if self._specs.lpp < self._current_graph.subgraph_num_inputs:
            for a in range(self._current_graph.subgraph_num_outputs):
                for t in range(self._specs.ppo):
                    deqVar = deque()
                    deq = deque()
                    for c in range(self._current_graph.subgraph_num_inputs):
                        var = '7' + str(((a * self._specs.ppo + t) * self._current_graph.subgraph_num_inputs + c) * 2)
                        deqVar.append(var)
                    while len(deqVar) > 0 or len(deq) > 1:
                        if len(deqVar) > 2:
                            first = deqVar.pop()
                            second = deqVar.pop()
                            third = deqVar.pop()
                            deq.append(SOP_QBF_Manager.adder_bit3(first,second,third))
                        elif len(deqVar) > 0:
                            while len(deqVar) > 0:
                                deq.appendleft([deqVar.pop()])
                        else:
                            first = deq.popleft()
                            second = deq.popleft()
                            deq.append(SOP_QBF_Manager.unsigned_adder(first,second))
                    res.append(SOP_QBF_Manager.comparator_greater_than(deq.pop(),self._specs.lpp))
        SOP_QBF_Manager.output.write(f'90 = and(-{SOP_QBF_Manager.comparator_greater_than(absolute_values,self._specs.et)}')
        for x in res:
            SOP_QBF_Manager.output.write(f', -{x}')
        SOP_QBF_Manager.output.write(')\n')
        SOP_QBF_Manager.output.close()
        result = subprocess.run(['../../cqesto-master/build/cqesto', 'Lollo/output.txt'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout.decode('utf-8')
        # SOP_QBF_Manager.output = open('./Lollo/output.txt','a')
        if result.strip()[-1] == '1':
            res_dict = dict()
            for x in result.split('\n')[3][2:-2].split():
                # SOP_QBF_Manager.output.write(f'{x} = ' + ('and()' if x[0] == '+' else 'or()') + '\n')
                if x[1] == '7':
                    number = int(x[2:])
                    res_dict[f'p_o{number // 2 // self._current_graph.subgraph_num_inputs // self._specs.ppo}_t{number // 2 // self._current_graph.subgraph_num_inputs % self._specs.ppo}_i{number // 2 % self._current_graph.subgraph_num_inputs}_' + ('s' if int(x) % 2 == 0 else 'l')] = True if x[0] == '+' else False
                else:
                    res_dict[f'p_o{x[3:]}'] = True if x[0] == '+' else False
            return [Result(sxpat_cfg.SAT,res_dict)]
        else:
            return [Result(sxpat_cfg.UNSAT,dict())]


class Z3TemplateManager(TemplateManager):
    def generate_script(self) -> None:
        # initialize builder object
        builder = Builder.from_file('./sxpat/template_manager/template.py')

        # update the builder with all required strings
        self._update_builder(builder)

        # save finalized template file
        with open(self.script_path, 'w') as ofile:
            ofile.write(builder.finalize())

    def run_script(self) -> None:
        process = subprocess.run(
            [
                sxpat_cfg.PYTHON3,
                self.script_path,
                f'{self._specs.et}',
                f'{self._specs.num_of_models}',
                f'{self._specs.timeout}'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if process.returncode != 0:
            raise RuntimeError(f'ERROR!!! Cannot run file {self.script_path}')

    def parse_results(self) -> Sequence[Result]:
        with open(self.data_path, 'r') as ifile:
            return [
                Result(d[sxpat_cfg.RESULT], d.get(sxpat_cfg.MODEL, None))
                for d in json.load(ifile)
            ]

    def run(self) -> Sequence[Result]:
        # generate z3 python script
        self.generate_script()

        # run the generated script
        self.run_script()

        # parse the results
        return self.parse_results()

    @abstractmethod
    def _update_builder(self, builder: Builder) -> None:
        raise NotImplementedError(f'{self.__class__.__name__}._update_builder(...) is abstract.')

    # utility file names getters

    @property
    @abstractmethod
    def script_path(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.script_path is abstract.')

    @property
    @abstractmethod
    def data_path(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.data_path is abstract.')

    # utility getters

    @property
    def inputs(self) -> Dict[int, str]:
        """The inputs of the grph. (.exact is equal to .current)"""
        return self._exact_graph.input_dict

    @property
    def outputs(self) -> Dict[int, str]:
        """The outputs of the graph. (.exact is equal to .current)"""
        return self._exact_graph.output_dict

    @functools.cached_property
    def subgraph_inputs(self) -> Dict[int, str]:
        """The inputs of the subgraph, sorted by id (inputs first, gates second)."""

        def is_input(n): return n in self._exact_graph.input_dict.values()
        subpgraph_inputs = list(self._current_graph.subgraph_input_dict.values())

        for i, node in enumerate(subpgraph_inputs):
            if not is_input(node):
                gate_i = mapping_inv(self._current_graph.gate_dict, node)
                subpgraph_inputs[i] = self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{self._exact_graph.num_inputs + gate_i}',
                    self._exact_graph.input_dict.values()
                )
        subpgraph_inputs.sort(key=lambda n: int(re.search(r'\d+', n).group()))

        return dict(enumerate(subpgraph_inputs))

    @property
    def subgraph_outputs(self) -> Dict[int, str]:
        """The outputs of the subgraph."""
        return self._current_graph.subgraph_output_dict

    @property
    def exact_gates(self) -> Dict[int, str]:
        """The gates of the exact graph."""
        return self._exact_graph.gate_dict

    @property
    def exact_constants(self) -> Dict[int, str]:
        """The constants of the exact graph."""
        return self._exact_graph.constant_dict

    @property
    def current_gates(self) -> Dict[int, str]:
        """The gates of the current graph."""
        return self._current_graph.gate_dict

    @property
    def current_constants(self) -> Dict[int, str]:
        """The constants of the current graph."""
        return self._current_graph.constant_dict


class ProductTemplateManager(Z3TemplateManager):

    # utility string methods

    @staticmethod
    def _gen_declare_gate(name: str) -> str:
        return f"{name} = Bool('{name}')"

    @staticmethod
    def _gen_declare_bool_function(name: str, inputs_count: int) -> str:
        return f"{name} = Function('{name}', {', '.join(itertools.repeat('BoolSort()', inputs_count + 1))})"

    @staticmethod
    def _gen_call_function(name: str, inputs: Iterable[str]) -> str:
        return f'{name}({", ".join(inputs)})'

    # utility variable usage methods

    def _use_exact_var(self, node_name: str) -> str:
        # is input
        if node_name in self.inputs.values():
            return node_name

        # is constant
        if node_name in self.exact_constants.values():
            return sxpat_cfg.Z3_GATES_DICTIONARY[self._exact_graph.graph.nodes[node_name][sxpat_cfg.LABEL]]

        # is gate
        if node_name in self.exact_gates.values():
            node_i = mapping_inv(self.exact_gates, node_name)
            return self._gen_call_function(
                f'{sxpat_cfg.EXACT_WIRES_PREFIX}{len(self.inputs) + node_i}',
                self.inputs.values()
            )

        # is output
        if node_name in self.outputs.values():
            node_i = mapping_inv(self.outputs, node_name)
            return self._gen_call_function(
                f'{sxpat_cfg.EXACT_WIRES_PREFIX}{sxpat_cfg.OUT}{node_i}',
                self.inputs.values()
            )

    def _use_approx_var(self, node_name: str) -> str:
        if node_name in self.inputs.values():
            return node_name

        # is constant
        if node_name in self.current_constants.values():
            return sxpat_cfg.Z3_GATES_DICTIONARY[self._current_graph.graph.nodes[node_name][sxpat_cfg.LABEL]]

        # is gate
        if node_name in self.current_gates.values():
            # is subgraph gate
            if self._current_graph.is_subgraph_member(node_name):
                node_i = mapping_inv(self.current_gates, node_name)
                return self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + node_i}',
                    # TODO:marco: update to be recursive, allowing subgraph_inputs to be simpler
                    self.subgraph_inputs.values()
                )

            # is not subgraph gate
            else:
                node_i = mapping_inv(self.current_gates, node_name)
                return self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + node_i}',
                    self.inputs.values()
                )

        # is output
        if node_name in self.outputs.values():
            node_i = mapping_inv(self.outputs, node_name)
            return self._gen_call_function(
                f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{sxpat_cfg.OUT}{node_i}',
                self.inputs.values()
            )

    # utility template methods

    @classmethod
    @abstractmethod
    def _input_parameters(cls, output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        """Returns the pair of parameters for the given indexes. (Literal parameter, State parameter)"""
        raise NotImplementedError(f'{cls.__name__}._input_parameters(...) is abstract.')

    @classmethod
    def _output_parameter(cls, output_i: int) -> str:
        return f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}'

    def _generate_product(self, parameter_pair_gen: Callable[[int], Tuple[str, str]]) -> str:
        multiplexers = []
        for input_i, input_name in self.subgraph_inputs.items():
            p_l, p_s = parameter_pair_gen(input_i)
            # self._use_approx_var
            multiplexers.append(f'Or(Not({p_s}), {p_l} == {(input_name)})')
        return f'And({", ".join(multiplexers)})'

    #

    def _update_builder(self, builder: Builder) -> None:
        # et_encoded
        builder.update(et_encoded=self._encoding.output_value('et'))

        # num_outputs
        builder.update(num_outputs=self._exact_graph.num_outputs)

        # abs_diff_def
        builder.update(abs_diff_def=self._encoding.abs_diff('a', 'b'))

        # ini_defs
        builder.update(ini_defs='\n'.join(
            self._gen_declare_gate(input_name)
            for input_name in self.inputs.values()
        ))

        # functions: function_exact, function_approximate
        builder.update(
            function_exact=self._encoding.function('fe'),
            function_approximate=self._encoding.function('fa')
        )

        # gen_inputs_arguments
        builder.update(gen_inputs_arguments=', '.join(self.inputs.values()))

        # error
        builder.update(error=self._encoding.output_variable('error'))

        # exact_wires_declaration
        builder.update(exact_wires_declaration='\n'.join(
            self._gen_declare_bool_function(f'{sxpat_cfg.EXACT_WIRES_PREFIX}{len(self.inputs) + gate_i}', len(self.inputs))
            for gate_i in itertools.chain(self.exact_gates.keys(), self.exact_constants.keys())
        ))

        # approximate_declaration
        builder.update(approximate_wires_declaration='\n'.join(
            (
                self._gen_declare_bool_function(f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}', len(self.subgraph_inputs))
                if self._current_graph.is_subgraph_member(gate_name) else
                self._gen_declare_bool_function(f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}', len(self.inputs))
            )
            for gate_i, gate_name in itertools.chain(self.current_gates.items(), self.current_constants.items())
        ))

        # exact_outputs_declaration
        builder.update(exact_outputs_declaration='\n'.join(
            self._gen_declare_bool_function(f'{sxpat_cfg.EXACT_OUTPUT_PREFIX}{sxpat_cfg.OUT}{output_i}', len(self.inputs))
            for output_i in self.outputs.keys()
        ))

        # approximate_outputs_declaration
        builder.update(approximate_outputs_declaration='\n'.join(
            self._gen_declare_bool_function(f'{sxpat_cfg.APPROXIMATE_OUTPUT_PREFIX}{sxpat_cfg.OUT}{output_i}', len(self.inputs))
            for output_i in self.outputs.keys()
        ))

        # exact_wires_constraints
        def get_preds(name: str) -> Collection[str]: return tuple(self._exact_graph.graph.predecessors(name))
        def get_func(name: str) -> str: return self._exact_graph.graph.nodes[name][sxpat_cfg.LABEL]
        lines = []
        for gate_i, gate_name in self.exact_gates.items():
            gate_preds = get_preds(gate_name)
            gate_func = get_func(gate_name)
            assert (gate_func, len(gate_preds)) in [
                (sxpat_cfg.NOT, 1),
                (sxpat_cfg.AND, 2),
                (sxpat_cfg.OR, 2),
            ], 'invalid gate function/predecessors combination'

            preds = tuple(self._use_exact_var(gate_pred) for gate_pred in gate_preds)
            name = f'{sxpat_cfg.EXACT_WIRES_PREFIX}{len(self.inputs) + gate_i}'
            lines.append(
                f'{self._gen_call_function(name, self.inputs.values())}'
                f' == {sxpat_cfg.TO_Z3_GATE_DICT[gate_func]}({", ".join(preds)}),'
            )
        builder.update(exact_wires_constraints='\n'.join(lines))

        # exact_output_constraints
        lines = []
        for output_name in self.outputs.values():
            output_preds = get_preds(output_name)
            assert len(output_preds) == 1, 'an output must have exactly one predecessor'

            pred = self._use_exact_var(output_preds[0])
            output = self._use_exact_var(output_name)
            lines.append(f'{output} == {pred},')
        builder.update(exact_output_constraints='\n'.join(lines))

        # exact_aggregated_output
        function_call = self._gen_call_function('fe', self.inputs.values())
        aggregated_output = self._encoding.aggregate_variables(tuple(
            self._use_exact_var(output_name)
            for output_name in self.outputs.values()
        ), True)
        builder.update(exact_aggregated_output=f'{function_call}\n== {aggregated_output},')

        # approximate_output_constraints
        lines = []
        for output_name in self.outputs.values():
            output_preds = get_preds(output_name)
            assert len(output_preds) == 1, 'an output must have exactly one predecessor'

            pred = self._use_approx_var(output_preds[0])
            output = self._use_approx_var(output_name)
            lines.append(f'{output} == {pred},')
        builder.update(approximate_output_constraints='\n'.join(lines))

        # approximate_aggregated_output
        function_call = self._gen_call_function('fa', self.inputs.values())
        aggregated_output = self._encoding.aggregate_variables(tuple(
            self._use_approx_var(output_name)
            for output_name in self.outputs.values()
        ), True)
        builder.update(approximate_aggregated_output=f'{function_call}\n== {aggregated_output},')

        # solver (both forall and verification)
        builder.update(solver=self._encoding.solver)

        # inputs
        builder.update(inputs=', '.join(self.inputs.values()))

        # difference_less_equal_etenc, difference_greater_veret
        builder.update(
            difference_less_equal_etenc=self._encoding.unsigned_less_equal('difference', 'et_encoded'),
            difference_greater_veret=self._encoding.unsigned_greater('difference', self._encoding.output_value('verification_et'))
        )

        # output_path
        builder.update(output_path=self.data_path)


class SOPManager(ProductTemplateManager):

    @property
    def script_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH['z3']
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @property
    def data_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH[sxpat_cfg.JSON]
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @classmethod
    def _input_parameters(cls, output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        partial_parameter = f'{sxpat_cfg.PRODUCT_PREFIX}{output_i}_{sxpat_cfg.TREE_PREFIX}{product_i}_{sxpat_cfg.INPUT_LITERAL_PREFIX}{input_i}'
        return (f'{partial_parameter}_{sxpat_cfg.LITERAL_PREFIX}', f'{partial_parameter}_{sxpat_cfg.SELECT_PREFIX}')

    def _update_builder(self, builder: Builder) -> None:
        # apply superclass updates
        super()._update_builder(builder)

        # params_declaration and params_list
        params = list(itertools.chain(
            (
                self._output_parameter(output_i)
                for output_i in self.subgraph_outputs.keys()
            ),
            itertools.chain.from_iterable(
                self._input_parameters(output_i, product_i, input_i)
                for output_i in self.subgraph_outputs.keys()
                for product_i in range(self._specs.ppo)
                for input_i in self.subgraph_inputs.keys()
            ),
        ))
        builder.update(
            params_declaration='\n'.join(self._gen_declare_gate(p) for p in params),
            params_list=f'[{", ".join(params)}]'
        )

        # approximate_wires_constraints
        def get_preds(name: str) -> Collection[str]:
            return sorted(self._current_graph.graph.predecessors(name), key=lambda n: int(re.search(r'\d+', n).group()))

        def get_func(name: str) -> str: return self._current_graph.graph.nodes[name][sxpat_cfg.LABEL]

        lines = []
        for gate_i, gate_name in self.current_gates.items():
            if not self._current_graph.is_subgraph_member(gate_name):
                gate_preds = get_preds(gate_name)
                gate_func = get_func(gate_name)
                assert (gate_func, len(gate_preds)) in [
                    (sxpat_cfg.NOT, 1),
                    (sxpat_cfg.AND, 2),
                    (sxpat_cfg.OR, 2),
                ], 'invalid gate function/predecessors combination'

                preds = tuple(self._use_approx_var(gate_pred) for gate_pred in gate_preds)
                name = f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}'
                lines.append(
                    f'{self._gen_call_function(name, self.inputs.values())}'
                    f' == {sxpat_cfg.TO_Z3_GATE_DICT[gate_func]}({", ".join(preds)}),'
                )

            # the gate is an output of the subgraph
            elif self._current_graph.is_subgraph_output(gate_name):
                output_i = mapping_inv(self.subgraph_outputs, gate_name)
                output_use = self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}',
                    self.subgraph_inputs.values()
                )
                products = (
                    self._generate_product(functools.partial(self._input_parameters, output_i, product_i))
                    for product_i in range(self._specs.ppo)
                )

                lines.append(f'{output_use} == And({sxpat_cfg.PRODUCT_PREFIX}{output_i}, Or({", ".join(products)})),')
        builder.update(approximate_wires_constraints='\n'.join(lines))

        # remove_zero_permutations_constraint
        lines = []
        for output_i in self.subgraph_outputs.keys():
            parameters = itertools.chain.from_iterable(
                self._input_parameters(output_i, product_i, input_i)
                for product_i in range(self._specs.ppo)
                for input_i in self.subgraph_inputs.keys()
            )
            lines.append(f'Implies(Not({self._output_parameter(output_i)}), Not(Or({", ".join(parameters)}))),')
        builder.update(remove_zero_permutations_constraint='\n'.join(lines))

        # remove_double_constraint
        builder.update(remove_double_constraint='\n'.join(
            ' '.join(
                f'Implies({", ".join(self._input_parameters(output_i, product_i, input_i))}),'
                for input_i in self.subgraph_inputs.keys()
            )
            for output_i in self.subgraph_outputs.keys()
            for product_i in range(self._specs.ppo)
        ))

        # product_order_constraint
        lines = []
        if self._specs.ppo == 1:
            lines.append('# No order needed for only one product')
        else:
            for output_i in self.subgraph_outputs.keys():
                products = tuple(
                    self._encoding.aggregate_variables(
                        tuple(itertools.chain.from_iterable(
                            reversed(self._input_parameters(output_i, product_i, input_i))
                            for input_i in self.subgraph_inputs.keys()
                        ))
                    )
                    for product_i in range(self._specs.ppo)
                )
                lines.extend(
                    f'{self._encoding.unsigned_greater_equal(product_a, product_b)},'
                    for product_a, product_b in pairwise_iter(products)
                )
        builder.update(product_order_constraint='\n'.join(lines))

        # logic_dependant_constraint1
        lines = ['# constrain the number of literals']
        for output_i in self.subgraph_outputs.keys():
            for product_i in range(self._specs.ppo):
                state_parameters = (
                    self._input_parameters(output_i, product_i, input_i)[1]
                    for input_i in self.subgraph_inputs.keys()
                )
                lines.append(f'AtMost({", ".join(state_parameters)}, {self._specs.lpp}),')
        builder.update(logic_dependant_constraint1='\n'.join(lines))

        # general informations: benchmark_name, encoding and cell
        builder.update(
            benchmark_name=self._specs.benchmark_name,
            encoding=self._specs.encoding,
            cell=f'({self._specs.lpp}, {self._specs.ppo})',
        )


class SOPSManager(ProductTemplateManager):

    @property
    def script_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH['z3']
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @property
    def data_path(self) -> str:
        folder, extension = sxpat_paths.OUTPUT_PATH[sxpat_cfg.JSON]
        return f'{folder}/{self._specs.benchmark_name}_{sxpat_cfg.TEMPLATE_SPEC_ET}{self._specs.et}_{self._specs.template_name}_encoding{self._specs.encoding}_{sxpat_cfg.ITER}{self._specs.iterations}.{extension}'

    @classmethod
    def _input_parameters(cls, output_i: int, product_i: int, input_i: int) -> Tuple[str, str]:
        partial_parameter = f'p_pr{product_i}_{sxpat_cfg.INPUT_LITERAL_PREFIX}{input_i}'
        return (f'{partial_parameter}_{sxpat_cfg.LITERAL_PREFIX}', f'{partial_parameter}_{sxpat_cfg.SELECT_PREFIX}')

    @classmethod
    def _product_parameter(cls, output_i: int, product_i: int) -> str:
        return f'p_pr{product_i}_o{output_i}'

    def _update_builder(self, builder: Builder) -> None:
        # apply superclass updates
        super()._update_builder(builder)

        # params_declaration and params_list
        params = list(itertools.chain(
            (  # p_o#
                self._output_parameter(output_i)
                for output_i in self.subgraph_outputs.keys()
            ),
            itertools.chain.from_iterable(  # p_pr#_i#
                self._input_parameters(None, product_i, input_i)
                for product_i in range(self._specs.pit)
                for input_i in self.subgraph_inputs.keys()
            ),
            (  # p_pr#_o#
                self._product_parameter(output_i, product_i)
                for output_i in self.subgraph_outputs.keys()
                for product_i in range(self._specs.pit)
            ),
        ))
        builder.update(
            params_declaration='\n'.join(self._gen_declare_gate(p) for p in params),
            params_list=f'[{", ".join(params)}]'
        )

        # approximate_wires_constraints
        def get_preds(name: str) -> Collection[str]: return sorted(self._current_graph.graph.predecessors(name), key=lambda n: int(re.search(r'\d+', n).group()))
        def get_func(name: str) -> str: return self._current_graph.graph.nodes[name][sxpat_cfg.LABEL]
        lines = []
        for gate_i, gate_name in self.current_gates.items():
            if not self._current_graph.is_subgraph_member(gate_name):
                gate_preds = get_preds(gate_name)
                gate_func = get_func(gate_name)
                assert (gate_func, len(gate_preds)) in [
                    (sxpat_cfg.NOT, 1),
                    (sxpat_cfg.AND, 2),
                    (sxpat_cfg.OR, 2),
                ], 'invalid gate function/predecessors combination'

                preds = tuple(self._use_approx_var(gate_pred) for gate_pred in gate_preds)
                name = f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}'
                lines.append(
                    f'{self._gen_call_function(name, self.inputs.values())}'
                    f' == {sxpat_cfg.TO_Z3_GATE_DICT[gate_func]}({", ".join(preds)}),'
                )

            # the gate is an output of the subgraph
            elif self._current_graph.is_subgraph_output(gate_name):
                output_i = mapping_inv(self.subgraph_outputs, gate_name)
                output_use = self._gen_call_function(
                    f'{sxpat_cfg.APPROXIMATE_WIRE_PREFIX}{len(self.inputs) + gate_i}',
                    self.subgraph_inputs.values()
                )
                products = (
                    f'And({self._product_parameter(output_i, product_i)}, {self._generate_product(functools.partial(self._input_parameters, None, product_i))})'
                    for product_i in range(self._specs.pit)
                )

                lines.append(f'{output_use} == And({sxpat_cfg.PRODUCT_PREFIX}{output_i}, Or({", ".join(products)})),')
        builder.update(approximate_wires_constraints='\n'.join(lines))

        # remove_double_constraint
        builder.update(remove_double_constraint='\n'.join(
            ' '.join(
                f'Implies({", ".join(self._input_parameters(output_i, product_i, input_i))}),'
                for input_i in self.subgraph_inputs.keys()
            )
            for product_i in range(self._specs.ppo)
        ))

        # product_order_constraint
        lines = []
        if self._specs.pit == 1:
            lines.append('# No order needed for only one product')
        else:
            products = tuple(
                self._encoding.aggregate_variables(
                    tuple(itertools.chain.from_iterable(
                        reversed(self._input_parameters(output_i, product_i, input_i))
                        for input_i in self.subgraph_inputs.keys()
                    ))
                )
                for product_i in range(self._specs.pit)
            )
            lines.extend(
                f'{self._encoding.unsigned_greater_equal(product_a, product_b)},'
                for product_a, product_b in pairwise_iter(products)
            )
        builder.update(product_order_constraint='\n'.join(lines))

        # remove_zero_permutations_constraint
        lines = []
        for output_i in self.subgraph_outputs.keys():
            parameters = (
                self._product_parameter(output_i, product_i)
                for product_i in range(self._specs.ppo)
            )
            lines.append(f'Implies(Not({self._output_parameter(output_i)}), Not(Or({", ".join(parameters)}))),')
        builder.update(remove_zero_permutations_constraint='\n'.join(lines))

        # logic_dependant_constraint1
        parameters = (
            self._product_parameter(output_i, product_i)
            for output_i in self.subgraph_outputs.keys()
            for product_i in range(self._specs.pit)
        )
        builder.update(logic_dependant_constraint1='\n'.join([
            '# Force the number of inputs to sum to be at most `its`',
            f'AtMost({", ".join(parameters)}, {self._specs.lpp}),'
        ]))

        # general informations: benchmark_name, encoding and cell
        builder.update(
            benchmark_name=self._specs.benchmark_name,
            encoding=self._specs.encoding,
            cell=f'({self._specs.lpp}, {self._specs.pit})',
        )


class Builder:
    LEFT_DELIMITER = '{{{{'
    RIGHT_DELIMITER = '}}}}'
    MAGIC_STRING_1 = 'zqwezrtyzuiozpaszdfgzhjkzlzxzcvbznm1z234z567z890z'
    MAGIC_STRING_2 = 'zmnbzvcxzzlkzjhgzfdszapoziuyztrezwq0z987z654z321z'

    def __init__(self, string: str) -> 'Builder':
        self._string: str = string
        self._kwargs: Dict[str, str] = dict()

    @ classmethod
    def from_file(cls, filename: str) -> Builder:
        with open(filename, 'r') as ifile:
            return cls(ifile.read())

    def update(self, **kwargs: Dict[str, str]) -> None:
        self._kwargs.update(kwargs)

    def finalize(self) -> str:
        # get normalized template string
        normalized_string = (
            self._string
            .replace(self.LEFT_DELIMITER, self.MAGIC_STRING_1)
            .replace(self.RIGHT_DELIMITER, self.MAGIC_STRING_2)
            .replace('{', '{{')
            .replace('}', '}}')
            .replace(self.MAGIC_STRING_1, '{')
            .replace(self.MAGIC_STRING_2, '}')
        )

        # update kwargs with correctly tabulated values
        for key, value in self._kwargs.items():
            if m := re.search(rf'(?:\r\n|\r|\n)([\t ]+)\{{{key}\}}', normalized_string):
                tabulation = m.group(1)
                self._kwargs[key] = tabulation.join(value.splitlines(True))

        # apply kwargs to the tamplate
        return normalized_string.format(**self._kwargs)

    def __str__(self) -> str:
        return f'{self._string!r} <- {self._kwargs}'
