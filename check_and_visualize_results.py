import csv
import sys
import matplotlib.pyplot as plt

def check_stats(legacy_file_path: str, new_file_path: str) -> None:
    legacy_time = 0.0
    new_time = 0.0
    with open(legacy_file_path) as legacy_obj:
        with open(new_file_path) as new_obj:
        
            legacy_rows = list(csv.reader(legacy_obj))
            new_rows = list(csv.reader(new_obj))
            for legacy_row, new_row in zip(legacy_rows[1:], new_rows[1:]): 
                #legacy_row: ['name', 'generation_time', 'inputs_amount', 'outputs_amount', 'gates_amount', 'const_amount']
                #new_row: ['name', 'generation_time', 'inputs_amount', 'outputs_amount', 'AND_gates_amount', 'NOT_gates_amount', 'const_amount']
                assert(legacy_row[0] == new_row[0])
                if legacy_row[2] != new_row[2] or legacy_row[3] != new_row[3]:
                    print(f"Circuit {legacy_row[0]} has different input/output amount")
                legacy_time += float(legacy_row[1])
                new_time += float(new_row[1])
    print(f"Total amount of time taken by legacy code: {legacy_time}")
    print(f"Total amount of time taken by new code: {new_time}")

def plot_results(legacy_file_path: str, new_file_path: str) -> None:
    with open(legacy_file_path) as legacy_obj:
            with open(new_file_path) as new_obj:
            
                legacy_reader = csv.DictReader(legacy_obj)
                new_reader = csv.DictReader(new_obj)
                
                xpoints = list()
                ypoints_legacy = list()
                ypoints_new = list()
                for legacy_row, new_row in zip(legacy_reader, new_reader):
                    xpoints.append(legacy_row["name"])
                    ypoints_legacy.append(float(legacy_row["generation_time"]))
                    ypoints_new.append(float(new_row["generation_time"]))

                plt.plot(xpoints, ypoints_legacy, color = 'r')
                plt.plot(xpoints, ypoints_new,  color = 'b')
                plt.xticks(rotation=70)
                plt.legend(["legacy", "new"], loc="lower right")
                plt.xlabel("Circuit name")
                plt.ylabel("IoGraph generation time (sec)")
                plt.show()

def main():
    legacy_file_path = ""
    new_file_path = ""
    for arg in sys.argv[1:]:
        if arg.startswith("--legacy-path="):
            legacy_file_path = (arg.split('='))[1]
        elif arg.startswith("--new-path="):
            new_file_path = (arg.split('='))[1]
    check_stats(legacy_file_path, new_file_path)
    plot_results(legacy_file_path, new_file_path)

if __name__ == '__main__':
    main()