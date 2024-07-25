from __future__ import annotations
from typing import Any, Mapping, Optional
from os import PathLike
import dataclasses as dc

import re

from Z3Log.config import path as z3logpath
from sxpat.config.config import NameParameters


def runner_name(main_name: str,
                literals_per_product: int = None,
                products_per_output: int = None,
                partitioning_percentage: str = None,
                distance_function_name: str = None,
                iteration: int = None,
                implementation: str = None
                ) -> str:
    # define name parts
    parts = [
        ("", main_name),
        (NameParameters.LPP.value, literals_per_product),
        (NameParameters.PPO.value, products_per_output),
        (NameParameters.PAP.value, partitioning_percentage),
        (NameParameters.DST.value, distance_function_name),
        (NameParameters.ITER.value, iteration),
        ("", implementation),
    ]

    # construct name
    name = "_".join(
        f"{prefix}{string}"
        for prefix, string in parts
        if string is not None
    )

    # get folder and extension
    folder, extension = z3logpath.OUTPUT_PATH['z3']

    return f"{folder}/{name}.{extension}"


@dc.dataclass(repr=True)
class NameData(PathLike):
    """Class representing the data of a benchmark file name.

    @implements: PathLike
    """

    root: str
    source_id: Optional[str] = None
    id: Optional[str] = None

    NAME_PATTERN = re.compile(r'(.+)_si(\d+)m(\d+)_i(\d+)m(\d+)')

    def __post_init__(self):
        self.id = self.id or 'E'

    @classmethod
    def from_filename(cls, filename: str) -> NameData:
        if (match := cls.NAME_PATTERN.match(filename)) is None:
            return NameData(filename)
        return NameData(match[1],cls.gen_id(match[2], match[3]), cls.gen_id(match[4], match[5]))

    @ staticmethod
    def gen_id(iteration_number: int, model_number: int) -> str:
        return f'i{iteration_number}m{model_number}'

    @ property
    def is_origin(self) -> bool:
        return self.source_id is None

    def get_successor(self, iteration_number: int, model_number: int) -> NameData:
        return NameData(self.root, self.id, self.gen_id(iteration_number, model_number))

    def __fspath__(self) -> str:
        if self.source_id is None:
            return self.root
        return f'{self.root}_s{self.source_id}_{self.id}'

    def __str__(self) -> str:
        return self.__fspath__()
