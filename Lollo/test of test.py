import itertools

def parse_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    variables = []
    outputs = []
    expressions = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith("variables"):
            variables = [int(x.strip()) for x in line.split('=')[1].split(',')]
        elif line.startswith("outputs"):
            outputs = [int(x.strip()) for x in line.split('=')[1].split(',')]
        else:
            var, expr = line.split('=')
            var = int(var.strip())
            expr = expr.strip()
            expressions[var] = expr
    
    return variables, outputs, expressions

def evaluate_expression(expr, values):
    if expr.startswith('and'):
        args = expr[4:-1].split(',')
        return all(get_value(int(arg.strip()), values) for arg in args)
    elif expr.startswith('or'):
        args = expr[3:-1].split(',')
        return any(get_value(int(arg.strip()), values) for arg in args)
    else:
        return get_value(int(expr.strip()), values)

def get_value(var, values):
    if var < 0:
        return not values[-var]
    return values[var]

def compute_truth_table(variables, outputs, expressions):
    num_vars = len(variables)
    truth_table = []
    
    for values in itertools.product([False, True], repeat=num_vars):
        values = dict(zip(variables, values))
        for var in sorted(expressions.keys()):
            values[var] = evaluate_expression(expressions[var], values)
        truth_table.append([values[var] for var in outputs])
    
    return truth_table

def main():
    file_path = 'Lollo/output.txt'  # Cambia questo con il percorso del tuo file
    variables, outputs, expressions = parse_file(file_path)
    
    truth_table = compute_truth_table(variables, outputs, expressions)
    
    header = ['Input'] + [f'Output {output}' for output in outputs]
    print("\t".join(header))
    
    num_vars = len(variables)
    for idx, row in enumerate(truth_table):
        input_vals = format(idx, f'0{num_vars}b')
        input_vals = " ".join(reversed(input_vals))  # Invertiamo la stringa degli input
        row_vals = " ".join(['1' if val else '0' for val in reversed(row)])  # Invertiamo la stringa degli output
        print(f"{input_vals}\t\t{row_vals}")

    # for idx, row in enumerate(truth_table):
    #     input_vals = format(idx, f'0{num_vars}b')
    #     input_vals = " ".join(input_vals)
    #     row_vals = " ".join(['1' if val else '0' for val in row])
    #     print(f"{input_vals}\t\t{row_vals}")
    
    # for idx, row in enumerate(truth_table):
    #     input_vals = format(idx, f'0{num_vars}b')
    #     input_vals = " ".join(reversed(input_vals))  # Invertiamo la stringa degli input
    #     row_vals = " ".join(['1' if val else '0' for val in row])
    #     row_vals = "".join(reversed(row_vals))  # Invertiamo la stringa degli output
    #     print(f"{input_vals}\t\t{row_vals}")

if __name__ == "__main__":
    main()
