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
