__all__ = [
    'MissingNodeError',
    'UndefinedNodeError',
    'MissingAttributeInNodeError',
]


class MissingNodeError(Exception):
    """Node not found."""


class UndefinedNodeError(Exception):
    """An undefine node is being used."""


class MissingAttributeInNodeError(Exception):
    """A node is missing an attribute."""
