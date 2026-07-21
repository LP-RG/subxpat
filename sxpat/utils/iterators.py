from typing import Callable, Iterator


def while_predicate(predicate: Callable[[], bool]) -> Iterator:
    while predicate(): yield
