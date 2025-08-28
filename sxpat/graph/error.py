__all__ = [
    'MissingNodeError',
    'UndefinedNodeError',
]


class MissingNodeError(Exception):
    """Node not found."""


class UndefinedNodeError(Exception):
    """An undefine node is being used."""
