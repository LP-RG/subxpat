import argparse

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--print-hello', help='If active, prints "hello"', action='store_true')
    parser.add_argument('--number', type=int)

    args = parser.parse_args()
    print(args)

    if args.print_hello:
        print('HELLO WORLD')

main()
