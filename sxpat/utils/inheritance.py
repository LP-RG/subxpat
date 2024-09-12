from typing import List, Type


def get_all_subclasses(cls: Type) -> List[Type]:
    """Returns a collection of all subclasses (itself included)"""

    subclasses = [cls]
    for cls in subclasses:
        subclasses.extend(cls.__subclasses__())

    return subclasses


def get_all_leaves_subclasses(cls: Type) -> List[Type]:
    """
    Returns a collection of all leaf subclasses (possibly included).  
    By leaf subclass we indend a subclass that has no subclasses of its own.
    """

    to_check = [cls]
    leaves = []

    for cls in to_check:
        subclasses = cls.__subclasses__()
        if len(subclasses) == 0:
            leaves.append(cls)
        else:
            to_check.extend(subclasses)

    return leaves