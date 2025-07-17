import numpy as np
import matplotlib.pyplot as plt
import sys
import importlib

def multiplier_test(bit_width, filename):
    if 'sub_x_pat_multiplier' in sys.modules:
        sub_x_pat_multiplier = importlib.reload(sys.modules['sub_x_pat_multiplier'])
    else:
        import sub_x_pat_multiplier
    scrumbled_res = np.zeros(((2**bit_width),(2**bit_width)))
    for i in range(0,(2**bit_width)):
        for y in range(0,(2**bit_width)):
            scrumbled_res[i][y] = sub_x_pat_multiplier.approx_mult(i,y)
    np.save(filename,scrumbled_res)


def get_mult_caracteristics(bit_width):
    mean_re = 0
    max_re = 0
    max_error = 0
    mean_ae = 0
    output_exact_array = []
    relative_error_array = []
    for i in range(0,2**bit_width):
        for y in range(0,2**bit_width):
            scrumbled = sub_x_pat.approx_mult(i,y)
            exact = i * y
            diff = abs(scrumbled - exact)
            re = diff / max(1,abs(exact))
            output_exact_array.append(exact)
            relative_error_array.append(re * 100)
            mean_re += re
            mean_ae += diff
            if(re > max_re):
                max_re = re
            if(diff > max_error):
                max_error = diff
    print(f"mean absolute error: {(mean_ae / ((2**bit_width)*(2**bit_width)))}")
    print(f"max absolute error: {max_error}")
    
    mean_re = (mean_re / ((2**bit_width)*(2**bit_width)))
    print(f"mean relative error: {mean_re}")
    print(f"max relative error: {max_re}")

