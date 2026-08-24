import matplotlib.pyplot as plt
import os

# 1. Raw Data Extraction
# Mode 5 Data (8 circuits tested)
m5_z3dint = [0.652787, 3.8745069999999995, 10.4320460000001, 12.119720999999998, 50.10040500000001, 165.15697100000034, 1018.1783460000001, 8920.390728]
m5_z3dbvec = [0.5485569999999846, 4.16224899999999, 54.63632599999997, 89.71668199999999, 76.61809999999997, 297.07430200000067, 1575.4752940000008, 8962.082373000005]
m5_z3datatype = [0.48982400000001647, 3.895863000000003, 10.435973000000047, 12.161224999999945, 51.009985999999984, 164.49849100000006, 901.2620770000002, 8697.295145999991]

# 2. Cactus Plots require sorting the runtimes in ascending order
#m5_z3dint.sort()
#m5_z3dbvec.sort()
#m5_z3datatype.sort()

# Create X-axis values (number of solved instances)
x_m5 = range(1, len(m5_z3dint) + 1)

# 3. Plotting Setup
plt.figure(figsize=(10, 6))

# Plot Mode 5 Encodings
plt.plot(x_m5, m5_z3datatype, marker='o', linestyle='-', color='blue', label='z3datatype')
#plt.plot(x_m5, m5_z3dint, marker='s', linestyle='-', color='green', label='z3dint')
plt.plot(x_m5, m5_z3dbvec, marker='^', linestyle='-', color='red', label='z3dbvec')

# 4. Formatting the Graph
plt.yscale('log') 
plt.title('Cactus Plot: Encoding Scalability Comparison', fontsize=14, fontweight='bold')
plt.xlabel('Number of Solved Benchmark Instances', fontsize=12)
plt.ylabel('Cumulative Runtime (Seconds) - Log Scale', fontsize=12)
plt.xticks(range(1, 9))
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.legend(loc='lower right')

# Save the plot
plt.tight_layout()
script_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(script_dir, "cactus_plot_encodings.png")
plt.savefig(filename, dpi=300)
plt.show()
print("Plot successfully saved as 'cactus_plot_encodings.png'")