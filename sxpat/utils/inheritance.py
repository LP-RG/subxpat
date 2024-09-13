from typing import Set, Type


__all__ = ['get_all_subclasses', 'get_all_leaves_subclasses']


def get_all_subclasses(cls: Type) -> Set[Type]:
    """Returns a collection of all subclasses (itself included)"""

    subclasses = [cls]
    for cls in subclasses:
        subclasses.extend(cls.__subclasses__())

    return set(subclasses)


def get_all_leaves_subclasses(cls: Type) -> Set[Type]:
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

    return set(leaves)
