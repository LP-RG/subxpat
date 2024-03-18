# typing
from __future__ import annotations
from typing import Iterable


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
