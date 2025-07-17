import subprocess
from pathlib import Path
from verilog_generator import npy_verilog

def areafile(file_path):
    #input a npy file
    #extract the area from it
    verilog_path=npy_verilog(file_path)
    filename=Path(verilog_path).stem
    process=subprocess.Popen("yosys -p \"read_verilog "+verilog_path+"; synth -flatten; opt; opt_clean -purge; abc -liberty config/gscl45nm.lib -script config/abc.script; stat -liberty config/gscl45nm.lib;\"", shell=True, stdout=subprocess.PIPE, text=True)
    #subprocess.PIPE tell the program to catch stdout(output), text=True tells that the input is a text,
    area=None
    for line in process.stdout: #line is a string
        if len(line)>=3:
            if line[0]==" " and line[1]==" " and line[2]==" " and line[3]=="C":
                area=line.split()[-1]
                break
    with open(filename+".area", "w") as f:
        f.write(area)

# directory=Path("./matrices/random_no_bug")

# for file in directory.iterdir():
#     if file.is_file():
#         areafile(file)

# subprocess.run("mv *.txt ./random_input_espresso", shell=True)
# subprocess.run("mv *.v ./random_verilog", shell=True)
# subprocess.run("mv *.area ./random_area", shell=True)