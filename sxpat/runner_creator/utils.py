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
