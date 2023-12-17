import dataclasses as dc
from typing import Dict, List, Tuple


@dc.dataclass
class Group:
    comment: str
    elements: List[str]


class Builder:
    def __init__(self) -> None:
        self.__variables: List[Group] = []
        self.__constraints: List[Group] = []
        self.__aliases: Dict[str, str] = dict()

    def add_variables(self, comment: str, variables: List[str]):
        self.__variables.append(Group(comment, variables))
    
    def add_function_gates(self, comment:str, a: List[Tuple[str,str]])
