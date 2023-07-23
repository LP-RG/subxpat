import shutil
import os
import csv
import json
import re
from sxpat.arguments import Arguments
from sxpat.templateSpecs import TemplateSpecs

def get_json_runtime(json_file_path):
    with open(json_file_path, 'r') as j:
        data = json.load(j)
    for d in data:
        if re.search('unsat', d['result']):
            runtime = float(d['total_time'])
        elif re.search('sat', d['result']):
            runtime = float(d['total_time'])
    return runtime

def get_json_status(json_file_path):
    with open(json_file_path, 'r') as j:
        data = json.load(j)
    for d in data:
        if re.search('unsat', d['result']):
            status = 'unsat'
        elif re.search('sat', d['result']):
            status = 'sat'
    return status


def main():
    args = Arguments.parse()
    print(f'{args = }')

    specs_obj = TemplateSpecs(name='Sop1', literals_per_product=args.lpp, products_per_output=args.ppo,
                              benchmark_name=args.benchmark_name, num_of_models = 1, subxpat=args.subxpat, et=args.et,
                              partitioning_percentage = args.partitioning_percentage)
    print(f'{specs_obj = }')




    # extract subxpat time
    folder = f'experiments/scalability/subxpat/'
    all_json = [f for f in os.listdir(folder)]
    relevant_json = []
    et_array = []

    subxpat_runtime_dict = {}

    for json_file in all_json:
        if re.search(specs_obj.benchmark_name, json_file):
            relevant_json.append(f'{folder}/{json_file}')

    # find all the available ets
    for json_file in relevant_json:
        if re.search('et\d+', json_file):
            et_array.append(int(re.search('et(\d+)', json_file).group(1)))
    et_array = sorted(set(et_array))



    for et in et_array:
        cur_runtime = 0
        cur_status = 'unsat'

        json_file_path = f'{folder}/{specs_obj.benchmark_name}_lpp0_ppo1_{specs_obj.template_name}_et{et}.json'
        print(f'{json_file_path = }')
        if json_file_path in relevant_json:
            cur_runtime += get_json_runtime(json_file_path)
            cur_status = get_json_status(json_file_path)
            print(f'{cur_status = }')
            if not re.search('unsat', cur_status):
                print(f'{et = }')
                subxpat_runtime_dict[et] = (cur_runtime, 0, 1)
                continue
        for ppo in range(1, specs_obj.ppo + 1):
            if cur_status == 'unsat':
                for lpp in range(1, specs_obj.lpp + 1):
                    if cur_status == 'unsat':
                        json_file_path = f'{folder}/{specs_obj.benchmark_name}_lpp{lpp}_ppo{ppo}_{specs_obj.template_name}_et{et}.json'
                        print(f'{json_file_path = }')
                        if json_file_path in relevant_json:

                            cur_runtime += get_json_runtime(json_file_path)
                            cur_status = get_json_status(json_file_path)
                            print(f'{cur_status =}')
                            if cur_status == 'sat':
                                # search the rest of the non-dominated cells
                                cur_lpp = lpp
                                cur_ppo = ppo
                                print(f'{cur_lpp}, {cur_ppo}')
                                print('non-dominated unexplored cells')
                                for this_lpp in range(cur_lpp - 1, 0, -1):
                                    for this_ppo in range(cur_ppo, specs_obj.ppo + 1):
                                        json_file_path = f'{folder}/{specs_obj.benchmark_name}_lpp{lpp}_ppo{ppo}_{specs_obj.template_name}_et{et}.json'
                                        cur_runtime += get_json_runtime(json_file_path)
                                        print(f'{this_lpp}, {this_ppo}')
                                subxpat_runtime_dict[et] = (cur_runtime, cur_lpp, cur_ppo)
                            else:
                                if lpp == specs_obj.lpp and ppo == specs_obj.ppo:
                                    print(f'final file')
                                    subxpat_runtime_dict[et] = (cur_runtime, 'UNSAT')
                    else:
                        break
            else:
                break


    et_list = list(subxpat_runtime_dict.keys())
    print(f'{et_list}')
    et_list.sort()
    print(f'{et_list}')



    for key in subxpat_runtime_dict.keys():
        print(f'{key} = {subxpat_runtime_dict[key]}')

    for et in et_array:
        print(subxpat_runtime_dict[et][0])



    # extract xpat time
    # draw a figure



    pass



if __name__ == "__main__":
    main()