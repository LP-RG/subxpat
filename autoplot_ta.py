import matrix_generation.circuits_analizer
import subprocess

def main(exp_num):
    subprocess.run(
        "mkdir output/mul_i8_o8_exp"+str(exp_num)+"/ta_plots", 
        shell=True)
    subprocess.run(
        "mkdir output/mul_i8_o8_exp"+str(exp_num)+"/npy", 
        shell=True)
    subprocess.run(
        "python3 circuits_analizer.py output/mul_i8_o8_exp"+str(exp_num)+"/ver 4 output/mul_i8_o8_exp"+str(exp_num), 
        shell=True)
    subprocess.run(
        "mv /output/mul_i8_o8_exp"+str(exp_num)+"/*.png /output/mul_i8_o8_exp"+str(exp_num)+"/ta_plots", 
        shell=True)
    subprocess.run(
        "mv /output/mul_i8_o8_exp"+str(exp_num)+"/*.npy /output/mul_i8_o8_exp"+str(exp_num)+"/npy", 
        shell=True)
    
    