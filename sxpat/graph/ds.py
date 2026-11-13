from typing import TypedDict


class AttributeMonoDict: #(UserDict)
    __slots__ = ['_name'] # ...
    def __init__(self, name: str | None = None): self._name = name
    @property
    def name(self) -> str | None: return self._name


class OrderedDiGraph(nx.DiGraph):
    # from-MARCO: during the discussion, we have seen this class to force the ordering of the operands.
    #             this ordering is maintained after creation, which means that it must be given correctly at creation.
    node_dict_factory = dict
    node_attr_dict_factory = AttributeMonoDict
    adjlist_outer_dict_factory = dict
    adjlist_inner_dict_factory = dict
    edge_attr_dict_factory = dict
    graph_attr_dict_factory = dict
