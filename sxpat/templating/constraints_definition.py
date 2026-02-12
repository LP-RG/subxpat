import json
from typing import List
from sxpat.graph import *

ERROR_THRESHOLD_ARRAYS_PATH = 'input/error_threshold_arrays.json'

def nine(s_graph: SGraph, t_graph: PGraph, max_error: int, beta: int, alpha: int) -> List[Node]:
        
        return [
            *(PlaceHolder(name) for name in s_graph.inputs_names[:]),
            input_one_value := ToInt('input_one_value', operands=s_graph.inputs_names[:len(s_graph.inputs_names)//2]),
            input_two_value := ToInt('input_two_value', operands=s_graph.inputs_names[len(s_graph.inputs_names)//2:]),

            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=t_graph.outputs_names),
            #Absolute error
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),

            #Int Constant
            zero := IntConstant('zero', value = 0),
            one := IntConstant('one', value = 1),
            alpha := IntConstant('alpha', value = alpha),
            hundred := IntConstant('hundred', value = 100),

            #Relative Error
            condition := Equals('condition', operands = (cur_int, zero)),
            divider := If("divider", operands=(condition, one, cur_int)),
            abs_diff_hundred := Mul('abs_diff_hundred', operands=(abs_diff, hundred)),
            rel_diff := UDiv('rel_diff',operands=(abs_diff_hundred, divider)),    

            #zone parameters
            half := IntConstant('half', value = 127),
            step_divider := IntConstant('step_divider', value = beta),

            #Absolute error_et
            et := IntConstant('et', value=max_error),

            #AE et function
            distance_half := AbsDiff('distance_from_half', operands = (input_two_value, half)),
            x_factor := Mul('x_factor', operands=(distance_half, alpha)),
            numerator := Sum('numerator', operands=(x_factor, input_one_value)),
            low_bound_condition := LessThan('low_bound_condition', operands=(numerator,step_divider)),
            et_function := UDiv('et_function', operands=(numerator,step_divider)),
            low_bounded_et_function := If('low_bounded_et_function', operands=(low_bound_condition, one, et_function)),
            scaled_et := Mul('scaled_et', operands=(low_bounded_et_function,et)),


            #Error constraints
            ae_error := LessEqualThan('ae_error', operands = (abs_diff, scaled_et)),
            re_constraint := LessEqualThan('re_constraint', operands = (rel_diff, hundred)),

            #Half RE
            re_check_condition :=LessEqualThan('re_check_condition', operands = (input_two_value, input_one_value)),
            re_error := Implies("re_error", operands = (re_check_condition, re_constraint)),
            error_check := And('error_check', operands=(ae_error, re_error)),
        ]


def nine_prime(s_graph: SGraph, t_graph: PGraph, max_error: int, beta: int, alpha: int, c_constant: int) -> List[Node]:
        
        return [
            *(PlaceHolder(name) for name in s_graph.inputs_names[:]),
            input_one_value := ToInt('input_one_value', operands=s_graph.inputs_names[:len(s_graph.inputs_names)//2]),
            input_two_value := ToInt('input_two_value', operands=s_graph.inputs_names[len(s_graph.inputs_names)//2:]),

            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=t_graph.outputs_names),
            #Absolute error
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int,)),

            #Int Constant
            zero := IntConstant('zero', value = 0),
            one := IntConstant('one', value = 1),
            alpha := IntConstant('alpha', value = alpha),
            hundred := IntConstant('hundred', value = 100),

            #Relative Error
            condition := Equals('condition', operands = (cur_int, zero)),
            divider := If("divider", operands=(condition, one, cur_int)),
            abs_diff_hundred := Mul('abs_diff_hundred', operands=(abs_diff, hundred)),
            rel_diff := UDiv('rel_diff',operands=(abs_diff_hundred, divider)),    

            #zone parameters
            half := IntConstant('half', value = 127),
            step_divider := IntConstant('step_divider', value = beta),

            #Absolute error_et
            et := IntConstant('et', value=max_error),
            increase_constant := IntConstant('increase_constant', value = c_constant), #flag c
            constraint_validity := IntConstant('constraint_validity', value = 45),

            #AE et function
            distance_half := AbsDiff('distance_from_half', operands = (input_two_value, half)),
            x_factor := Mul('x_factor', operands=(distance_half, alpha)),
            numerator := Sum('numerator', operands=(x_factor, input_one_value)),
            low_bound_condition := LessThan('low_bound_condition', operands=(numerator,step_divider)),
            et_function := UDiv('et_function', operands=(numerator,step_divider)),
            low_bounded_et_function := If('low_bounded_et_function', operands=(low_bound_condition, one, et_function)),
            et_increasing := Mul('et_increasing', operands = (low_bounded_et_function, increase_constant)),
            scaled_et := Sum('scaled_et', operands=(et_increasing,et)),


            #Error constraints
            ae_check_condition := LessEqualThan('ae_check_condition', operands = (low_bounded_et_function, constraint_validity)),
            ae_constraint := LessEqualThan('ae_constraint', operands = (abs_diff, scaled_et)),
            ae_error := Implies('ae_error', operands = (ae_check_condition,ae_constraint)),

            re_check_condition :=LessEqualThan('re_check_condition', operands = (input_two_value, input_one_value)),
            re_constraint := LessEqualThan('re_constraint', operands = (rel_diff, hundred)),
            re_error := Implies("re_error", operands = (re_check_condition, re_constraint)),
            
            error_check := And('error_check', operands=(ae_error, re_error)),
        ]

# beta parameter defines the size of each zone (submatrix)
# For example with beta = 32, we have 8x8 zones for 256x256 input space thus needing array of lenght 64 (8*8).
def explicit_constraints(s_graph: SGraph, t_graph: PGraph, et_array_idx: int, beta: int) -> List[Node]:
        
        try:
            with open(ERROR_THRESHOLD_ARRAYS_PATH, 'r') as f:
                error_threshold_arrays = json.load(f)
            et_array = error_threshold_arrays[et_array_idx]["values"]

            if len(et_array) != (256 // beta) ** 2:
                raise ValueError(f"Error threshold array length {len(et_array)} does not match expected size {(256 // beta) ** 2} for beta={beta}.")

        except FileNotFoundError:
            raise FileNotFoundError(f"Error threshold arrays file not found at path: {ERROR_THRESHOLD_ARRAYS_PATH}")
        except IndexError:
            raise IndexError(f"Threshold array index {et_array_idx} is out of range.")
        except json.JSONDecodeError:
            raise ValueError(f"Error decoding JSON from file: {ERROR_THRESHOLD_ARRAYS_PATH}. Check the file format.")


        num_steps = 256 // beta
        nodes = [

            *(PlaceHolder(name) for name in s_graph.inputs_names[:]),

            input_one_value := ToInt('input_one_value', operands=s_graph.inputs_names[:len(s_graph.inputs_names)//2]),
            input_two_value := ToInt('input_two_value', operands=s_graph.inputs_names[len(s_graph.inputs_names)//2:]),

            
            # --- Output ---
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=t_graph.outputs_names),
            
            # --- Absolute Error ---
            abs_diff := AbsDiff('abs_diff', operands=(cur_int, tem_int)),
            
            # --- Costants ---
            zero := IntConstant('zero', value=0),
            one := IntConstant('one', value=1),
            hundred := IntConstant('hundred', value=100),
            
            # --- Relative Error ---
            condition := Equals('condition', operands=(cur_int, zero)),
            divider := If("divider", operands=(condition, one, cur_int)),
            abs_diff_hundred := Mul('abs_diff_hundred', operands=(abs_diff, hundred)),
            rel_diff := UDiv('rel_diff', operands=(abs_diff_hundred, divider)),
        ]
        
        ae_error_zone_nodes = []

        for zone_i in range(num_steps):
            for zone_j in range(num_steps):
                et_value = IntConstant(f"et_zone_{zone_i}_{zone_j}",
                                    value=et_array[zone_i * num_steps + zone_j])
                nodes.append(et_value)
                
                row_start_val = zone_i * beta
                row_end_val = (zone_i + 1) * beta - 1
                col_start_val = zone_j * beta
                col_end_val = (zone_j + 1) * beta - 1
                
                row_start_const = IntConstant(f"input_one_row_start_{zone_i}_{zone_j}", value = row_start_val)
                row_end_const = IntConstant(f"input_one_row_end_{zone_i}_{zone_j}",value =   row_end_val)
                nodes.extend([row_start_const, row_end_const])
                
                ge_row = GreaterEqualThan(f"ge_input_one_row_{zone_i}_{zone_j}", operands=(input_one_value, row_start_const))
                le_row = LessEqualThan(f"le_input_one_row_{zone_i}_{zone_j}", operands=(input_one_value, row_end_const))
                nodes.extend([ge_row, le_row])
                
                input_one_cond = And(f"input_one_in_zone_{zone_i}_{zone_j}", operands=(ge_row, le_row))
                nodes.append(input_one_cond)
                
                col_start_const = IntConstant(f"input_two_col_start_{zone_i}_{zone_j}",value =  col_start_val)
                col_end_const = IntConstant(f"input_two_col_end_{zone_i}_{zone_j}",value =  col_end_val)
                nodes.extend([col_start_const, col_end_const])
                
                ge_col = GreaterEqualThan(f"ge_input_two_col_{zone_i}_{zone_j}", operands=(input_two_value, col_start_const))
                le_col = LessEqualThan(f"le_input_two_col_{zone_i}_{zone_j}", operands=(input_two_value, col_end_const))
                nodes.extend([ge_col, le_col])
                
                input_two_cond = And(f"input_two_in_zone_{zone_i}_{zone_j}", operands=(ge_col, le_col))
                nodes.append(input_two_cond)
                
                zone_condition = And(f"zone_condition_{zone_i}_{zone_j}", operands=(input_one_cond, input_two_cond))
                nodes.append(zone_condition)
                
                ae_less_equal = LessEqualThan(f"ae_less_equal_{zone_i}_{zone_j}", operands=(abs_diff, et_value))
                nodes.append(ae_less_equal)
                
                ae_error_zone = Implies(f"ae_error_zone_{zone_i}_{zone_j}",
                                operands=(zone_condition, ae_less_equal))
                nodes.append(ae_error_zone)
                
                ae_error_zone_nodes.append(ae_error_zone)
        
        ae_error = And('ae_error', operands=ae_error_zone_nodes)
        nodes.append(ae_error)
        
        re_error = LessEqualThan('re_error', operands=(rel_diff, hundred))
        nodes.append(re_error)
        
        error_check = And('error_check', operands=(ae_error, re_error))
        nodes.append(error_check)
        
        return nodes