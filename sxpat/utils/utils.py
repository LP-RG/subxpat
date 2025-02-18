# typing
from __future__ import annotations
from typing import Iterable, Callable, Any

import time
import colorama


# Z3Log libs
from Z3Log.config.config import TAB


def indent_lines(lines: Iterable[str], indent_amount: int = 1) -> Iterable[str]:
    """Indent the lines by the wanted amound."""
    return (TAB * indent_amount + line for line in lines)


def format_lines(lines: Iterable[str], indent_amount: int = 0, extra_newlines: int = 0) -> str:
    """Join lines into a single string, indenting each line by the wanted amount and adding extra newlines at the end if needed."""
    return "\n".join(indent_lines(lines, indent_amount)) + "\n" * (1 + extra_newlines)


def unzip(it: Iterable) -> Iterable:
    return zip(*it)


# > Z3 functions
def declare_z3_function(name: str, input_count: int, input_type: str, output_type: str) -> str:
    """NOTE: If the input count is 0, then the result will be a variable and not a function"""
    if input_count == 0:
        # remove the sort-ref part, keep the pure type
        output_type = output_type.replace("Sort()", "")
        return f"{name} = {output_type}('{name}')"
    else:
        return f"{name} = z3.Function('{name}', {', '.join([input_type]*input_count)}, {output_type})"


def declare_z3_gate(name: str) -> str:
    return f"{name} = z3.Bool('{name}')"


def call_z3_function(name: str, arguments: Iterable[str]) -> str:
    """NOTE: If the arguments count is 0, then the result will be a variable use and not a function call"""
    if len(arguments) == 0:
        return name
    else:
        return f"{name}({', '.join(arguments)})"


class color:
    def factory(color: str) -> Callable[[str], str]:
        return lambda s: color + s + colorama.Fore.RESET

    with_color = staticmethod(factory)

    s = success = green = staticmethod(factory(colorama.Fore.GREEN))
    w = warning = yellow = staticmethod(factory(colorama.Fore.YELLOW))
    e = error = red = staticmethod(factory(colorama.Fore.RED))
    i1 = info1 = cyan = staticmethod(factory(colorama.Fore.CYAN))
    i2 = info2 = blue = staticmethod(factory(colorama.Fore.BLUE))
    i3 = info3 = magenta = staticmethod(factory(colorama.Fore.MAGENTA))
    black = staticmethod(factory(colorama.Fore.BLACK))
    white = staticmethod(factory(colorama.Fore.WHITE))


class pprint:
    def factory(color: str):
        def p(title: Any, *args: Any, **kwargs: Any) -> None:
            print(color + str(title) + colorama.Fore.RESET, *args, **kwargs)
        return p

    with_color = staticmethod(factory)

    s = success = green = staticmethod(factory(colorama.Fore.GREEN))
    w = warning = yellow = staticmethod(factory(colorama.Fore.YELLOW))
    e = error = red = staticmethod(factory(colorama.Fore.RED))
    i1 = info1 = cyan = staticmethod(factory(colorama.Fore.CYAN))
    i2 = info2 = blue = staticmethod(factory(colorama.Fore.BLUE))
    i3 = info3 = magenta = staticmethod(factory(colorama.Fore.MAGENTA))
    black = staticmethod(factory(colorama.Fore.BLACK))
    white = staticmethod(factory(colorama.Fore.WHITE))


def augment(extra_parameters: Iterable[str]):
    """Applies augmentations to the function. \ 
        The augmented function will return a tuple containing the original function result, followed by the wanted augmentations in the passed order.

        Available augmentations:
            - "timed": measure the elapsed time from the start to the end of the function.
    """

    def do_timed(function):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = function(*args, **kwargs)
            total_time = time.time() - start_time
            return result, total_time
        return wrapper

    def unpacker(function, depth: int):
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            other_results = []
            for _ in range(depth):
                result, other = result
                other_results.append(other)
            return result, *reversed(other_results)
        return wrapper

    decorators = {
        "timed": do_timed
    }

    def decorator(function):
        wrapper = function
        for key in extra_parameters:
            wrapper = decorators[key](wrapper)

        return unpacker(wrapper, len(extra_parameters))

    return decorator


def static(**vars):
    def decorate(func):
        for k, v in vars.items():
            setattr(func, k, v)
        return func

    return decorate


if __name__ == "__main__":
    pprint.e("ERROR", "some other", "message", [1, True, dict()])
    pprint.w("WARNING", "some other", "message", [1, True, dict()])
    pprint.s("SUCCESS", "some other", "message", [1, True, dict()])
    pprint.i1("INFO 1", "some other", "message", [1, True, dict()])
    pprint.i2("INFO 2", "some other", "message", [1, True, dict()])
    pprint.i3("INFO 3", "some other", "message", [1, True, dict()])

    print(color.e("ERROR"), "some other", "message", [1, True, dict()])
    print(color.w("WARNING"), "some other", "message", [1, True, dict()])
    print(color.s("SUCCESS"), "some other", "message", [1, True, dict()])
    print(color.i1("INFO 1"), "some other", "message", [1, True, dict()])
    print(color.i2("INFO 2"), "some other", "message", [1, True, dict()])
    print(color.i3("INFO 3"), "some other", "message", [1, True, dict()])
