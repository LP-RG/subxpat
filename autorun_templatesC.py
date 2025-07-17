import subprocess
import os

# here input a range of max_errors, auto-run the experiment iterating through the values
# save the .png and .v outputs, create a txt. file that save the sh lines and runtime
def auto_run(experiment_num):
    command="python3 main.py mul_i8_o8 --metric wre --min-labeling --extraction-mode 0 --zone-constraint 7 --subxpat --encoding z3bvec --max-error 35 --imax 4 --omax 2 --template nonshared --max-lpp 8 --max-ppo 8"
    process1=subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True)
    codes=None
    with open("sxpat/templating/NonSharedTemplate.py", "r") as file: 
        lines=file.read().splitlines()
        start=0
        end=0
        for i in range(len(lines)):
            if lines[i].strip()=="def relative_error_zone_constraint(cls, s_graph: SGraph, t_graph: PGraph, error_threshold: int,":
                start=i
                break
        for i in range(start, len(lines),1):
            if lines[i].strip()=="]":
                end=i
                break
        codes=lines[start:end+1]
    with open("description.txt", "w") as file:
        file.write(command+"\n")
        file.write(process1.stdout+"\n")
        file.write("Code: \n")
        for i in codes:
            file.write(i+"\n")
    subprocess.run("mkdir output/mul_i8_o8_exp"+str(experiment_num),shell=True)
    subprocess.run("mv description.txt output/gv output/ver output/z3 output/report output/mul_i8_o8_exp"+str(experiment_num),shell=True)
