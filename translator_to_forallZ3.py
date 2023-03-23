# two arguments: 1) name of file, 2) number of gates to be approximated
from z3 import *
import sys
import os
from typing import Iterable, List, Callable, Any, Union, Tuple
from itertools import repeat, islice


# FUNCTION DECLARATIONS

class Builder:
    LEFT_DELIMITER = "{{{{"
    RIGHT_DELIMITER = "}}}}"
    MAGIC_STRING_1 = "zqwezrtyzuiozpaszdfgzhjkzlzxzcvbznm1z234z567z890z"
    MAGIC_STRING_2 = "zmnbzvcxzzlkzjhgzfdszapoziuyztrezwq0z987z654z321z"

    def __init__(self, string: str) -> 'Builder':
        self._string = string
        self._kwargs = dict()

    def __call__(self, **kwargs: Any) -> Union[str, None]:
        if kwargs:
            self._kwargs.update(kwargs)
        else:
            return (self._string
                    .replace(self.LEFT_DELIMITER, self.MAGIC_STRING_1)
                    .replace(self.RIGHT_DELIMITER, self.MAGIC_STRING_2)
                    .replace("{", "{{")
                    .replace("}", "}}")
                    .replace(self.MAGIC_STRING_1, "{")
                    .replace(self.MAGIC_STRING_2, "}")
                    .format(**self._kwargs))

    def __str__(self) -> str:
        return f"{self._string!r} <- {self._kwargs}"


def is_output(gate_id: int):
    return (len(C[gate_id]) == 0
            and gate_names[gate_id] not in "TUF")


def is_input(gate_id: int):
    return len(P[gate_id]) == 0


def generate_and_join(function: Callable[..., Iterable[str]],
                      ranges: List[Union[int, Iterable]],
                      joiner: str,
                      __internal: List[int] = []) -> str:
    """
    Args:
        function (Callable[..., str]): it must take in one argument per element in ranges.\
            If 'ranges' contains iterables then the function needs 2 arguments for that (index, value).
    """

    strings = []

    if len(ranges) == 1:
        # end case
        if type(ranges[0]) is int:
            for i in range(ranges[0]):
                strings.extend(function(*__internal, i))
        else:
            for i, v in enumerate(ranges[0]):
                strings.extend(function(*__internal, i, v))

    else:
        # middle case
        if type(ranges[0]) is int:
            for i in range(ranges[0]):
                strings.append(generate_and_join(function, ranges[1:], joiner, __internal + [i]))
        else:
            for i, v in enumerate(ranges[0]):
                strings.append(generate_and_join(function, ranges[1:], joiner, __internal + [i, v]))

    return joiner.join(strings)


def generate_function(name: str, in_types: Iterable[str], out_type: str) -> str:
    return f"{name} = Function('{name}', {', '.join(in_types)}, {out_type})"


def inputs_line(inputs_count: int) -> str:
    def generator(i_id):
        return [f"i{i_id}"]
    return generate_and_join(generator, [inputs_count], ",")


def generate_inputs(inputs_count: int) -> str:
    def generator(i_id):
        inp = f"i{i_id}"
        return [f"{inp} = Bool('{inp}')"]
    return generate_and_join(generator, [inputs_count], "\n")


def generate_wires(inputs_count, middles_count):
    def generator(_, m_id):
        return [generate_function(f"e{m_id}", repeat("BoolSort()", inputs_count), "BoolSort()")]
    return generate_and_join(generator, [range(inputs_count, inputs_count + middles_count)], "\n")


def generate_outputs(inputs_count, outputs_count):
    def generator(o_id):
        return [generate_function(f"eout{o_id}", repeat("BoolSort()", inputs_count), "BoolSort()")]
    return generate_and_join(generator, [outputs_count], "\n")


def implicit_parameters(trees_per_output: int,
                        inputs_count: int, outputs_count: int) -> str:
    # create all OTI parameters
    def generator_oti(o_id, t_id, i_id):
        p_s = f"p_o{o_id}_t{t_id}_i{i_id}_s"
        p_l = f"p_o{o_id}_t{t_id}_i{i_id}_l"
        return [f"{p_s} = Bool('{p_s}')",
                f"{p_l} = Bool('{p_l}')"]
    oti_parameters = generate_and_join(generator_oti, [outputs_count, trees_per_output, inputs_count], "\n")

    # create all O parameters
    def generator_o(o_id):
        p_o = f"p_o{o_id}"
        return [f"{p_o} = Bool('{p_o}')"]
    o_parameters = generate_and_join(generator_o, [outputs_count], "\n")

    return f"{o_parameters}\n{oti_parameters}"


def approximate_implicit_circuit(trees_per_output: int,
                                 inputs_count: int, outputs_count: int) -> str:

    # create all outputs
    outputs: 'list[str]' = []
    for output_id in range(outputs_count):
        # create all trees
        trees = []
        for tree_id in range(trees_per_output):
            tree = generate_implicit_tree(output_id, tree_id, inputs_count)
            trees.append(tree)

        outputs.append(f"Or({', '.join(trees)})")

    # create integer output
    return generate_implicit_int_output(outputs)


def generate_implicit_tree(output_id: int, tree_id: int,
                           inputs_count: int) -> str:
    def generator(_0, o_id, _1, t_id, i):
        p_s = f"p_o{o_id}_t{t_id}_i{i}_s"
        p_l = f"p_o{o_id}_t{t_id}_i{i}_l"
        inp = f"i{i}"
        return [f"Or(Not({p_s}), {p_l} == {inp})"]

    string = generate_and_join(generator, [[output_id], [tree_id], inputs_count], ", ")
    return f"And({string})"


def generate_parameters_constraints_for_redundancy(inputs_count: int,
                                                   trees_per_output: int,
                                                   outputs_count: int) -> str:
    def generator(_0, o_id, t_id, i_id):
        p_s = f"p_o{o_id}_t{t_id}_i{i_id}_s"
        p_l = f"p_o{o_id}_t{t_id}_i{i_id}_l"
        # state and literal must not be both False
        return [f"Implies({p_l}, {p_s})"]

    strings = []
    for o_id in range(outputs_count):
        strings.append(generate_and_join(generator, [[o_id], trees_per_output, inputs_count], ", "))

    return ",\n".join(strings)


def generate_output_constants_constraints_for_redundancy(inputs_count: int,
                                                         trees_per_output: int,
                                                         outputs_count: int) -> str:
    def generator(_0, o_id, t_id, i_id):
        p_s = f"p_o{o_id}_t{t_id}_i{i_id}_s"
        p_l = f"p_o{o_id}_t{t_id}_i{i_id}_l"
        return [p_s, p_l]

    strings = []
    for o_id in range(outputs_count):
        strings.append(f"Implies(Not(p_o{o_id}), Not(Or({generate_and_join(generator, [[o_id], trees_per_output, inputs_count], ', ')})))")

    return ",\n".join(strings)


def generate_tree_order_constraints_for_redundancy(inputs_count: int,
                                                   trees_per_output: int,
                                                   outputs_count: int) -> str:
    if trees_per_output == 1:
        return "True"

    def generator(_0, o_id, _1, t_id, i_id):
        n = i_id * 2
        p_s = f"IntVal({2 ** n}) * p_o{o_id}_t{t_id}_i{i_id}_s"
        p_l = f"IntVal({2 ** (n+1)}) * p_o{o_id}_t{t_id}_i{i_id}_l"
        return [p_s, p_l]

    constraints = []
    for o_id in range(outputs_count):
        trees = []
        for t_id in range(trees_per_output):
            trees.append(generate_and_join(generator, [[o_id], [t_id], inputs_count], ' + '))

        for tree1, tree2 in zip(trees, islice(trees, 1, None)):
            # every tree must be greater or equal than the next one (per output)
            constraints.append(f"({tree1}) >= ({tree2})")

    return ",\n".join(constraints)


def generate_implicit_int_output(outputs: List[str]) -> str:
    def generator(o_id, o_gates):
        return [f"IntVal({2 ** o_id}) * And(p_o{o_id}, {o_gates})"]

    string = generate_and_join(generator, [outputs], ',\n    ')
    return f"Sum({string})"


def generate_atmost_constraints(trees_per_output: int,
                                literal_per_tree: int,
                                inputs_count: int, outputs_count: int) -> str:
    # create all constraints
    constraints: 'list[str]' = []
    for output_id in range(outputs_count):
        for tree_id in range(trees_per_output):
            def generator(_0, o_id, _1, t_id, i_id):
                return [f"If(p_o{o_id}_t{t_id}_i{i_id}_s, 1, 0)"]
                # return [f"p_o{o_id}_t{t_id}_i{i_id}_s"]

            # string = generate_and_join(generator, [[output_id], [tree_id], inputs_count], ", ")
            # atmost = f"AtMost({string}, {literal_per_tree})"
            string = generate_and_join(generator, [[output_id], [tree_id], inputs_count], " + ")
            atmost = f"({string}) <= {literal_per_tree}"
            constraints.append(atmost)

    return ",\n".join(constraints)


def indent(lines: str, indent_size: int) -> str:
    spaces = " " * indent_size
    return spaces + lines.replace("\n", f"\n{spaces}")


file_name = str(sys.argv[1])
trees_per_output = int(sys.argv[2])
literals_per_tree = int(sys.argv[3])

circuit_name = file_name.split("/")[-1].split(".")[0]
out_directory = f"runners/{circuit_name}"
out_path = f"{out_directory}/run_tpo{trees_per_output}_lpt{literals_per_tree}.py"
os.makedirs(out_directory, exist_ok=True)

infile = open(file_name, "r")
reader = infile.readlines()

dictino = {'and': 'And', 'or': 'Or', 'not': 'Not', 'xor': 'Xor', 'nand': 'Not(And', 'nor': 'Not(Or'}
rand_funs = {1: 'True', 2: 'False', 3: 'And', 4: 'Or', 5: 'Xor', 6: 'Not(And', 7: 'Not(Or', 8: 'Not(Xor'}


# read the circuit
flag = 0
C = []
P = []
gate_names = []
gates_count = 0
for line in reader:
    if line[0] == '}':
        flag = 3
    if flag == 2:
        # fai le cose degli edges
        line = line[1:]
        line = line.split(' ')
        conn = line[0]
        conn = conn.split("->")
        a = int(conn[0][1:])
        b = int(conn[1][1:])
        # set b as child of a and a as parent of b
        C[a].append(b)
        P[b].append(a)
    if line[0:5] == "\tedge":
        flag = 2
        C = [[] for _ in range(gates_count)]
        P = [[] for _ in range(gates_count)]
    if flag == 1:
        v = line.split(' ')
        i = 0
        for part in v:
            if part[0:4] == "[lab":
                piece = i
            i = i+1
        toks = v[piece].split(',')
        st = toks[0].split('=')
        roughlab = st[1]
        roughlab = roughlab.replace("\"", "")
        roughlab = roughlab.split("\\n")
        gatename = roughlab[0]
        gate_names.append(gatename)
        gates_count = gates_count+1
    if line[0:5] == "\tnode":
        flag = 1

# now find number of inputs and outputs
inputs_count = 0
for g in range(gates_count):
    inputs_count += is_input(g)

outputs_count = 0
for g in range(gates_count):
    outputs_count += is_output(g)

middles_count = gates_count - inputs_count - outputs_count


with open("translator/template.py", "r") as template_file:
    template_string = template_file.read()
    template_builder = Builder(template_string)


template_builder(circuit_name=file_name,
                 inputs_count=inputs_count,
                 outputs_count=outputs_count)


# inputs declaration
template_builder(inputs_declaration=generate_inputs(inputs_count))

# wires declaration
template_builder(middles_declaration=generate_wires(inputs_count, middles_count))

# outputs declaration
template_builder(outputs_declaration=generate_outputs(inputs_count, outputs_count))

# parameters declaration
template_builder(parameters_declaration=implicit_parameters(trees_per_output, inputs_count, outputs_count))


# functions declaration
template_builder(exact_function_declaration=generate_function("fe", repeat("BoolSort()", inputs_count), "IntSort()"))
template_builder(approx_function_declaration=generate_function("fa", repeat("BoolSort()", inputs_count), "IntSort()"))


template_builder(inputs=inputs_line(inputs_count))
template_builder(exact_function=f"fe({inputs_line(inputs_count)})")
template_builder(approx_function=f"fa({inputs_line(inputs_count)})")


# write gate functionality
exact_circuit = ""
for i in range(inputs_count, len(gate_names)-outputs_count):
    if gate_names[i] == 'U' or gate_names[i] == 'F':
        exact_circuit += f"g{i} = False\n"
    elif gate_names[i] == 'T':
        exact_circuit += f"g{i} = True\n"
    else:
        exact_circuit += f"    e{i}({inputs_line(inputs_count)}) == {dictino[gate_names[i]]}("
        parz = P[i]
        if len(parz) == 1:
            # single parent (this is an unary operator)
            if parz[0] < inputs_count:
                # parent is input
                exact_circuit += f"i{parz[0]})"
            else:
                # parent is middle
                exact_circuit += f"e{parz[0]}({inputs_line(inputs_count)}))"

        else:
            # two parents (this is an binary operator)
            if parz[0] < inputs_count:
                # parent is input
                exact_circuit += f"i{parz[0]},"
            else:
                # parent is middle
                exact_circuit += f"e{parz[0]}({inputs_line(inputs_count)}),"

            if parz[1] < inputs_count:
                # parent is input
                exact_circuit += f"i{parz[1]})"
            else:
                # parent is middle
                exact_circuit += f"e{parz[1]}({inputs_line(inputs_count)}))"

            if gate_names[i] == 'nand' or gate_names[i] == 'nor':
                exact_circuit += ")"
        exact_circuit += ",\n"

exact_circuit = exact_circuit[4:-2]
template_builder(middles_definition=exact_circuit)


# write vector with output gates
out_vector = []
for i in range(0, outputs_count):
    out_vector.append(P[len(gate_names)-outputs_count+i][0])
outputs_definition = ""
for i in range(0, len(out_vector)):

    in_l = inputs_line(inputs_count)
    # LP and here the inputoutput correct number of  BoolSort() )
    outputs_definition += f"    eout{i}({in_l}) == e{out_vector[i]}({in_l}),\n"
outputs_definition = outputs_definition[4:-2]

template_builder(outputs_definition=outputs_definition)


exact_function_definition = f"fe({inputs_line(inputs_count)}) ==\n"
for i in range(0, outputs_count):
    exact_function_definition += f"    {pow(2, i)} * eout{i}({inputs_line(inputs_count)})"
    if i < outputs_count-1:
        exact_function_definition += " +\n"

template_builder(exact_function_definition=exact_function_definition)


approximate_circuit = f"fa({inputs_line(inputs_count)}) ==\n"
approximate_circuit += indent(approximate_implicit_circuit(trees_per_output, inputs_count, outputs_count), 4)
template_builder(approximate_circuit=approximate_circuit)


redundancy_constraints = indent(generate_parameters_constraints_for_redundancy(inputs_count, trees_per_output, outputs_count), 8)[8:]
template_builder(redundancy_constraints_multiplexer_constant=redundancy_constraints)

redundancy_constraints = indent(generate_output_constants_constraints_for_redundancy(inputs_count, trees_per_output, outputs_count), 8)[8:]
template_builder(redundancy_constraints_output_constant=redundancy_constraints)

redundancy_constraints = indent(generate_tree_order_constraints_for_redundancy(inputs_count, trees_per_output, outputs_count), 8)[8:]
template_builder(redundancy_constraints_tree_order=redundancy_constraints)


atmost_constraints = generate_atmost_constraints(trees_per_output, literals_per_tree, inputs_count, outputs_count)
atmost_constraints = indent(atmost_constraints, 8)[8:]
template_builder(trees_contraints=atmost_constraints)


# write to file
with open(out_path, "w") as ofile:
    ofile.write(template_builder())
print("ok")
