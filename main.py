import Z3Log
from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import *
from Z3Log.argument import Arguments
from sxpat.templateCreator import TemplateCreator
from sxpat.templateCreator import Template_SOP1
from sxpat.templateSpecs import TemplateSpecs
from sxpat.config.paths import *

def main():
    setup_folder_structure()
    for key in OUTPUT_PATH.keys():
        directory = OUTPUT_PATH[key][0]
        if ~os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    args = Arguments.parse()
    print(f'{args = }')

    specs_obj = TemplateSpecs(name='Sop1', literals_per_product=3, products_per_output=2, benchmark_name=args.benchmark_name)
    print(f'{specs_obj = }')

    template_obj = Template_SOP1(specs_obj)
    print(f'{template_obj = }')
    template_obj.z3_generate_z3pyscript()

if __name__ == "__main__":
    main()
