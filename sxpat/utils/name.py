from __future__ import annotations
from typing import Optional
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


@dc.dataclass(frozen=True)
class NameData(PathLike):
    root: str
    source_id: Optional[str]
    id: Optional[str]

    NAME_PATTERN = re.compile(r'([a-zA-Z_]+_i\d+_o\d+)(?:_src(E|\d+-\d+)_(\d+-\d+)|)\.v')

    def __post_init__(self):
        object.__setattr__(self, 'id', self.id or 'E')

    @classmethod
    def from_filename(cls, filename: str) -> NameData:
        match = cls.NAME_PATTERN.match(filename)  # todo:wip: maybe .search ?
        return NameData(match[1], match[2], match[3])

    def get_successor(self, iteration_number: int, model_number: int) -> NameData:
        return NameData(self.root, self.id, f'{iteration_number}-{model_number}')

    def __fspath__(self) -> str:
        if self.source_id is None:
            return self.root
        return f'{self.root}_src{self.source_id}_{self.id}'
