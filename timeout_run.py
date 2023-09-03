
from colorama import Fore, Style
from sxpat.arguments import Arguments
import subprocess
from subprocess import PIPE
from subprocess import TimeoutExpired
def timeout_run():
    args = Arguments.parse()

    if args.multiple:
        command = ['python3', 'main.py',
                   f'input/ver/{args.benchmark_name}.v', f'-app=input/ver/{args.approximate_benchmark}.v',
                   f'-lpp={args.lpp}', f'-ppo={args.ppo}',
                   f'-iterations={args.iterations}', f'-imax={args.imax}', f'-omax={args.omax}',
                   f'--grid', f'--subxpat', f'--multiple']
    else:
        command = ['python3', 'main.py',
                  f'input/ver/{args.benchmark_name}.v', f'-app=input/ver/{args.approximate_benchmark}.v',
                  f'-lpp={args.lpp}', f'-ppo={args.ppo}', f'-et={args.et}',
                  f'-iterations={args.iterations}', f'-imax={args.imax}', f'-omax={args.omax}',
                  f'--grid', f'--subxpat']

    try:
        process = subprocess.run(command, timeout=100, stderr=PIPE)
        if process.stderr:
            print(Fore.RED + f'ERROR!!! while running {command}' + Style.RESET_ALL)

    except subprocess.TimeoutExpired as e:
        print(Fore.MAGENTA + f'TIMEOUT {e}' + Style.RESET_ALL)
if __name__ == "__main__":
    timeout_run()


