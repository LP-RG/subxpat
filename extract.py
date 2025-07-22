import subprocess
from pathlib import Path
import re
    
def extract_area_power_delay(file_path):
    #input a verilog file
    #extract the area, power, delay from it
    filename=Path(file_path).stem
    area_pattern=r"Chip area for module .*\: (\d+.\d+)"
    delay_pattern=r"(\d+.\d+)\s+data arrival time"
    power_pattern=r"Total\s+\S+\s+\S+\s+\S+\s+(\S+)\s+\d+.\d+%"
    area=""
    delay=""
    power=""
    yosys_command="yosys -p \"read_verilog "+file_path+"; synth -flatten; opt; opt_clean -purge; abc -liberty config/gscl45nm.lib -script config/abc.script; stat -liberty config/gscl45nm.lib; write_verilog "+filename+"_netlist.v\""
    in_sta_command="read_liberty \"config/gscl45nm.lib\"; read_verilog \""+filename+"_netlist.v\"; link_design \"graph\"; create_clock -name clk -period 1; set_input_delay -clock clk 0 [all_inputs]; set_output_delay -clock clk 0 [all_outputs]; report_checks -digits 12; report_power -digits 12; exit"

    process_yosys=subprocess.run(yosys_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #subprocess.PIPE tell the program to catch stdout(output), text=True tells that the input is a text, not byte

    if process_yosys.stderr!="":
        print("Yosys error")
        return
    
    yosys_output=process_yosys.stdout
    area_match=re.search(area_pattern, yosys_output)
    if area_match:
        area=area_match.group(1)
    else:
        return "no area found"
    with open(filename+".area", "w") as f:
        f.write(area)

    process_sta=subprocess.run(['sta'], input=in_sta_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if process_sta.stderr!="":
        print("Opensta error")
        return
    
    sta_output=process_sta.stdout
    delay_match=re.search(delay_pattern, sta_output)
    if delay_match:
        delay=delay_match.group(1)
    else:
        return "no delay found"
    with open(filename+".delay", "w") as f:
        f.write(delay)

    power_match=re.search(power_pattern, sta_output)
    if power_match:
        power=power_match.group(1)
    else:
        return "no power found"
    with open(filename+".power", "w") as f:
        f.write(power)