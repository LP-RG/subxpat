from collections import OrderedDict, UserDict
from .node import AnyNode

import networkx as nx


class NodeAttributesDict(UserDict):
    def __init__(self, name: str | None = None, node: AnyNode | None = None): 
        super().__init__() 
        self._name = name
        self._node = node

    @property
    def name(self) -> str | None: 
        return self._name

    @property
    def node(self) -> AnyNode | None: 
        return self._node


class OrderedDiGraph(nx.DiGraph):
    # from-MARCO: during the discussion, we have seen this class to force the ordering of the operands.
    #             this ordering is maintained after creation, which means that it must be given correctly at creation.
    node_dict_factory = dict
    node_attr_dict_factory = dict
    adjlist_outer_dict_factory = OrderedDict
    adjlist_inner_dict_factory = OrderedDict
    edge_attr_dict_factory = dict
    graph_attr_dict_factory = dict
