import subprocess
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
from autorun_templatesC import auto_run

#here input a verilog file, plot a the relative difference
#the verilog file express the approximated circuit

def logic_analyze(inputs, wires, s):
    #all s starts with ~
    #inside the parenthesis(if exists), there is only & logic gate
    #no parenthesis means there is only one node
    result=True
    if s[0]=="~":
        if s[1]=="(":
            elements=s[2:-1].split()
            for element in elements:
                if element[0]=="i":
                    result=result and inputs[element]
                elif element[0]=="_" or element[0]=="o":
                    result=result and wires[element]
        else:
            element=s[1:]
            if element[0]=="i":
                result=inputs[element]
            elif element[0]=="_" or element[0]=="o":
                result=wires[element]
        return not result
    elif s[0]=="1": return False
    else:
        if s[0]=="(":
            elements=s[1:-1].split()
            for element in elements:
                if element[0]=="i":
                    result=result and inputs[element]
                elif element[0]=="_" or element[0]=="o":
                    result=result and wires[element]
        else:
            element=s
            if element[0]=="i":
                result=inputs[element]
            elif element[0]=="_" or element[0]=="o":
                result=wires[element]
        return result

def bin_trans(dec_num, length):
    #dec_num is an integer
    bin_num=[0]*length
    for i in range(length-1,-1,-1):
        if dec_num>=2**i:
            bin_num[i]=1
            dec_num=dec_num-2**i
    return bin_num 

def dec_trans(bin_num):
    #bin_num is an array
    sum=0
    for i in range(len(bin_num)):
        sum=bin_num[i]*2**i+sum
    return sum 

def approx_matrix(file_path):
    #input a verilog file, output the circuit in array form
    lines=[]
    inputs={}
    outputs={}
    wires={}
    with open(file_path, "r") as file:
        for line in file:
            lines.append(line.strip())
    line_3=lines[2].split("(")
    line_3=line_3[1].split(")")
    line_3=line_3[0].split(",")
    for i in range(len(line_3)):
        line_3[i]=line_3[i].strip()
    for c in line_3:
        if c[0]=="i" and c[1]=="n":
            inputs[c]=0
        elif c[0]=="o" and c[1]=="u":
            outputs[c]=0
    for i in range(3,len(lines)-1,1):
        line=lines[i]
        if line[0]=="a":
            assign=line.split(" = ")
            left=assign[0].split()
            if left[1][0]=="_":
                wires[left[1]]=assign[1][:-1]
            elif left[1][0]=="o":
                wires[left[1]]=assign[1][:-1]
                outputs[left[1]]=assign[1][:-1]
    maxi=2**(len(inputs)//2)
    result = np.full((maxi, maxi), 0)
    for i in range(0, maxi, 1):
        for j in range(0, maxi, 1):
            input_one=bin_trans(i, len(inputs)//2)
            input_two=bin_trans(j, len(inputs)//2)
            input=input_one+input_two
            for k in range(len(inputs)):
                inputs["in"+str(k)]=input[k]
            analyzed_wires={}
            analyzed_outputs={}
            for key in wires.keys():
                analyzed_wires[key]=logic_analyze(inputs, analyzed_wires, wires[key])
            for key in outputs.keys():
                analyzed_outputs[key]=analyzed_wires[key]
            bin_num=[]
            for key in analyzed_outputs.keys():
                bin_num.append(analyzed_outputs[key])
            result[i, j]=dec_trans(bin_num)
    return result

def rel_dif(array):
    #output the relative difference respect to the max
    maxi=(array.shape[0]-1)*(array.shape[1]-1)
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            ex=max(i*j, 1)
            rel_dif_exact=(abs(array[i,j]-i*j)/ex)*100
            rel_dif=min(100, rel_dif_exact)
            array[i,j]=rel_dif
    return array

def plot(array, name):
    #plot the relative difference, the darker the bigger
    fig, ax = plt.subplots(figsize=(6, 6))
    # Turn off axes
    ax.axis('off')
    maxi=array.shape[0]-1
    # Draw the colored squares
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            color = 1-array[i, j]/100
            #colors coordinates (0,0) corresponds to rectangle coordinates(0, 14)
            rect = plt.Rectangle((j, maxi - i), 1, 1, facecolor=(color,0,0))
            ax.add_patch(rect)

    ax.text(
        -1, 16,                         # coordinates in data units; adjust as needed
        "0",
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left'
    )

    ax.text(
        -1, 0.5,                         # coordinates in data units; adjust as needed
        "15",
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left'
    )

    ax.text(
        0, -0.7,                         # coordinates in data units; adjust as needed
        "0",
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left'
    )

    ax.text(
        16, -0.7,                         # coordinates in data units; adjust as needed
        "15",
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left'
    )

    ax.text(
        2, -0.7,                         # coordinates in data units; adjust as needed
        "darker means higher relative error, \nrespecting to the exact value",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white'),
        verticalalignment='top',
        horizontalalignment='left'
    )

    # Set the limits and aspect
    ax.set_xlim(0, array.shape[0])
    ax.set_ylim(0, array.shape[1])
    ax.set_aspect('equal')
    plt.savefig(name+".png")

def satisfying(array, et):
    #array is the array of relative difference in %
    et_0=et
    et_1=int(et+5)
    et_2=int(et+10)
    et_3=int(et+15)
    colors=np.empty((array.shape[0],array.shape[1]), dtype=str)
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            if i<=12 and 2<j<=12:
                if array[i,j]<=et_0:
                    colors[i,j]='blue'
                else:
                    colors[i,j]='red'
            elif i<=2 and (j<=2 or j>12): 
                if array[i,j]<=et_0:
                    colors[i,j]='green'
                elif array[i,j]<=et_1:
                    colors[i,j]='blue'
                else:
                    colors[i,j]='red'
            elif (i>2 and i<=12) and (j<=2 or j>12):
                if array[i,j]<=et_1:
                    colors[i,j]='green'
                elif array[i,j]<=et_2:
                    colors[i,j]='blue'
                else:
                    colors[i,j]='red'
            elif (i>12) and (j<=2 or j>12):
                if array[i,j]<=et_2:
                    colors[i,j]='green'
                elif array[i,j]<=et_3:
                    colors[i,j]='blue'
                else:
                    colors[i,j]='red'
            else:
                colors[i,j]='green'
    return colors

def plot_satisfying(array, name):
    #array is a np array of boolean
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.axis('off')
    maxi=array.shape[0]-1
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            #colors coordinates (0,0) corresponds to rectangle coordinates(0, 14)
            if i==2 and j==14:
                color='red'
            else:
                color=array[i,j]
            rect = plt.Rectangle((j, maxi - i), 1, 1, facecolor=color)
            ax.add_patch(rect)
    ax.text(
        -1, 16,                         # coordinates in data units; adjust as needed
        "0",
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left'
    )

    ax.text(
        -1, 0.5,                         # coordinates in data units; adjust as needed
        "15",
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left'
    )

    ax.text(
        0, -0.7,                         # coordinates in data units; adjust as needed
        "0",
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left'
    )

    ax.text(
        16, -0.7,                         # coordinates in data units; adjust as needed
        "15",
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left'
    )

    ax.text(
        2, -0.7,                         # coordinates in data units; adjust as needed
        "green: rel error <= prev. zone et \nblue: prev. zone et < rel error <= cur. zone et \nred: rel error > cur. et",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white'),
        verticalalignment='top',
        horizontalalignment='left'
    )

    # Set the limits and aspect
    ax.set_xlim(0, array.shape[0])
    ax.set_ylim(0, array.shape[1])
    ax.set_aspect('equal')
    plt.savefig(name+".png")

def graph(file_path, et):
    name=Path(file_path).stem
    rel_dif_matrix=rel_dif(approx_matrix(file_path))
    plot(rel_dif_matrix, name)
    plot_satisfying(satisfying(rel_dif_matrix, et), name+"_sat")

def main(experiment_num, et):
    directory="output/mul_i8_o8_exp"+str(experiment_num)+"/ver/"
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    for file in files:
        graph(directory+file, et)
    subprocess.run("mkdir output/mul_i8_o8_exp"+str(experiment_num)+"/my_plots", shell=True)
    subprocess.run("mv *.png output/mul_i8_o8_exp"+str(experiment_num)+"/my_plots", shell=True)

