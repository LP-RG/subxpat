import os
import shutil

def generate_approx_mult_function(input_verilog_path: str, bitwidth: int):
    output_filename = "sub_x_pat_multiplier.py"
    destination_file = open(output_filename, "w")

    function_definition = "def approx_mult(a: int, b: int) -> int:\n"
    destination_file.write(function_definition)

    input_a_vars = ",".join([f"in{i}" for i in range(bitwidth - 1, -1, -1)])
    input_b_vars = ",".join([f"in{i}" for i in range(2 * bitwidth - 1, bitwidth - 1, -1)])
    
    parsing_row_a = f"\t{input_a_vars} = [int(bit) for bit in bin(a)[2:].zfill({bitwidth})]\n"
    parsing_row_b = f"\t{input_b_vars} = [int(bit) for bit in bin(b)[2:].zfill({bitwidth})]\n"
    
    destination_file.write(parsing_row_a)
    destination_file.write(parsing_row_b)

    with open(input_verilog_path, "r") as file:
        for line in file:
            if"//" in line:
                pass
            elif "assign" in line:
                if"po" in line:
                    line_new = "\t" + line[9:].replace("|", "or").replace("&", "and").replace("~", "not ").replace("1'h0", "0").replace("1'h1", "1").replace(";","")
                else:
                    line_new = "\t"+ line[9:].replace("|", "or").replace("&", "and").replace("~", "not ").replace("1'h0", "0").replace("1'h1", "1").replace(";","")
                destination_file.write(line_new)

    output_bits_vars = ",".join([f"int(out{i})" for i in range(2 * bitwidth - 1, -1, -1)])
    destination_file.write(f"\tbits = [{output_bits_vars}]\n")
    
    destination_file.write("\tbit_string = ''.join(str(bit) for bit in bits)\n")
    destination_file.write("\tresult = int(bit_string, 2)\n")
    destination_file.write("\treturn result\n")
    destination_file.close()