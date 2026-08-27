import matplotlib.pyplot as plt
import os

# 1. Raw Data Extraction
# Mode 5 Data (8 circuits tested)
benchmarks = [
    "adder_i16_o9", "abs_diff_i8_o4", "adder_i28_o15", "adder_i32_o17", 
    "abs_diff_i10_o5", "adder_i36_o19", "mul_i8_o8", "mul_i10_o10"
]

m5_z3dint = [
    1.3696229999999936, 
    2.8946889999999996, 
    10.269151000000022, 
    18.276764999999955, 
    61.64154700000004, 
    245.70571799999993, 
    267.53391600000015, 
    1159.1455180000003
]

m5_z3dbvec = [
    1.4432209999999994, 
    3.931713000000002, 
    91.210584, 
    80.76379499999996, 
    99.685563, 
    392.9790430000005, 
    29.439497000000095, 
    1902.9536979999998
]

m5_z3datatype = [
    1.4396439999999995, 
    3.071511000000008, 
    11.729314000000059, 
    35.900001999999745, 
    62.52559400000009, 
    80.76497500000005, 
    68.80189599999994, 
    1095.8414899999996
]

#m5_z3dint = [1.3696229999999936, 10.269151000000022, 18.276764999999955, 245.70571799999993, 267.53391600000015, 1159.1455180000003, 2.8946889999999996, 61.64154700000004]
#m5_z3dbvec = [1.4432209999999994, 91.210584, 80.76379499999996, 392.9790430000005, 29.439497000000095, 1902.9536979999998, 3.931713000000002, 99.685563]
#m5_z3datatype = [1.4396439999999995, 11.729314000000059, 35.900001999999745, 80.76497500000005, 68.80189599999994, 1095.8414899999996, 3.071511000000008, 62.52559400000009]

#m5_z3dint = [2.5124819999999985, 2.5526700000000027, 13.52330000000012, 15.582715000000036, 48.86694599999998, 189.4689489999996, 203.58864200000005, 882.4778560000001]
#m5_z3dbvec = [2.5500760000000007, 2.747993999999977, 21.143208, 63.16720800000002, 73.03686600000003, 100.59911499999994, 324.8175769999991, 1439.1989489999999]
#m5_z3datatype = [2.4466500000000337, 2.541935999999996, 13.46283799999992, 21.533398999999974, 48.68659299999992, 49.365807000000046, 51.75030300000026, 885.4040320000003]

# 2. Cactus Plots require sorting the runtimes in ascending order
#m5_z3dint.sort()
#m5_z3dbvec.sort()
#m5_z3datatype.sort()

# Create X-axis values (number of solved instances)
x_m5 = range(1, len(m5_z3datatype) + 1)

# 3. Plotting Setup
plt.figure(figsize=(16, 8))

# Plot Mode 5 Encodings
plt.plot(x_m5, m5_z3datatype, marker='o', linestyle='-', color='blue', label='z3datatype')
#plt.plot(x_m5, m5_z3dint, marker='s', linestyle='-', color='green', label='z3dint')
plt.plot(x_m5, m5_z3dbvec, marker='^', linestyle='-', color='red', label='z3dbvec')

# 4. Formatting the Graph
plt.yscale('log') 
plt.title('Cactus Plot: Encoding Scalability Comparison', fontsize=14, fontweight='bold')
plt.xlabel('Benchmark Instance', fontsize=12)
plt.ylabel('Cumulative Runtime (Seconds) - Log Scale', fontsize=12)
plt.xticks(x_m5, benchmarks, rotation=45, ha="right", fontsize=11)
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.legend(loc='lower right')

# Save the plot
plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(script_dir, "cactus_plot_encodings.png")
plt.savefig(filename, dpi=300)
plt.show()
print("Plot successfully saved as 'cactus_plot_encodings.png'")