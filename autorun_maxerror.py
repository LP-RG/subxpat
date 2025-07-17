import subprocess

# here input a range of max_errors, auto-run the experiment iterating through the values
# save the .png and .v outputs, create a txt. file that save the sh lines and runtime
def auto_run(max_errors):
    for max_error in max_errors:
        process1=subprocess.run(
            "python3 main.py mul_i8_o8 --metric wre --min-labeling --extraction-mode 55 --subxpat --encoding z3bvec --max-error "+str(max_error)+" --imax 4 --omax 4 --template nonshared --max-lpp 4 --max-ppo 2",
            shell=True,
            capture_output=True,
            text=True)
        runtime=process1.stdout[-25:]
        for i in range(len(runtime)):
            c=runtime[i]
            if c!="R":
                continue
            else:
                runtime=runtime[i:]
                break
        with open("description.txt", "w") as file:
            file.write("python3 main.py mul_i8_o8 \n")
            file.write("--metric wre --min-labeling --extraction-mode 55 --subxpat --encoding z3bvec \n")
            file.write("--max-error "+str(max_error)+" --imax 4 --omax 4 --template nonshared --max-lpp 4 --max-ppo 2\n\n")
            file.write("runtime: "+runtime)
        subprocess.run("mkdir output/mul_i8_o8_maxerror"+str(max_error),shell=True)
        subprocess.run("mv description.txt output/gv/*.png output/ver/*.v output/mul_i8_o8_maxerror"+str(max_error),shell=True)
        subprocess.run("rm -r output/gv output/ver output/report output/z3", shell=True)

max_errors=range(20, 36, 5)
auto_run(max_errors)

    

