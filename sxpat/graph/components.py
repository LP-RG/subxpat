from typing import Any, final
from collections.abc import Callable
import networkx as nx

__all__ = [
    'Subgraph', 'Topology', 'Weight', 'Type', 'Component',
]


# COMMENT:from-MARCO: all this looks good.
# i think you can simplify a few things, specifically:
# - given that different components may behave vary different behaviours, you can keep each one in its own unique hierarchy, meaning that, if you want to inherit from Component, Component can be only a very coincise interface, maybe specifying the requirements all components should follow (like as immutability and such).
# - given the above, the .perform_action could be removed, and instead of passing thorugh self.action, each component directly defines its methods (e.g. .nodes_names, .get, ...).
# these could simplify the effort required for a new developer to understand the component

# COMMENT:from-MARCO: (this can be left for later)
# if you want to simplify further your structure (as it will get there eventually anyway) you can use integers as "ids" for nodes, instead than strings.
# NOTE THAT if you do this many other things will break, so you would require a middle-step on the accesses of the graphs to map from an outside string to an inside integer, and viceversa


class Component:
    """Generic component"""
    object: Any
    action: Callable[..., Any]
    inheritable: bool

    # COMMENT:from-MARCO: i think the auto-inherit-on-copy is a very good idea
    def __init__(self,
                 object: Any,
                 action: Callable[..., Any],
                 inheritable: bool = True) -> None:
        """The component stores an object (could also be a list of objects) onto which an action is applied 
           when the component is accessed/used. A component can be inheritable, meaning that a graph resulting
           from a copy of a graph having a the component will automatically inherit it, instead an uninheritable 
           component will not be passed to the graph's copies.
        """
        self.object = object
        self.action = action
        self.inheritable = inheritable

    @final
    def perform_action(self, *optionalArgs) -> Any:
        return self.action(self.object, *optionalArgs)


class Subgraph(Component):
    """Concrete and 'static' component
        - object: mapping from node id to boolean representing whether node is present in the current subgraph
        - action: return list of node ids in the current subgraph 
    """

    def __init__(self, map: dict[str, bool]) -> None:
        action = lambda map: [k for k in map.keys() if map[k] == 1]
        super().__init__(map, action)

    def nodes_names(self) -> list[str]:
        return self.perform_action()


class Topology(Component):
    """Concrete and 'static' component
        - object: DiGraph representing the topology
        - action: return the DiGraph
    """

    def __init__(self, digraph: nx.DiGraph) -> None:
        action = lambda digraph: digraph
        super().__init__(digraph, action)

    def get(self) -> nx.DiGraph:
        # COMMENT:from-MARCO: values produced by components should not allow to change the graph
        return self.perform_action()


class Weight(Component):
    """Concrete and 'static' component
        - object: mapping from node id to its weight
        - action: return the weight corresponding to the given node id
    """

    def __init__(self, map: dict[str, int]) -> None:
        action = lambda map, node_id: map[node_id]
        super().__init__(map, action)

    def get(self, node_id: str) -> int:
        return self.perform_action(node_id)


class Type(Component):
    """Concrete and 'static' component
        - object: mapping from node id to its type
        - action: return the type corresponding to the given node id
    """

    # COMMENT:from-MARCO: types here should be specific Node types (Sum, And, ...)
    def __init__(self, map: dict[str, str]) -> None:
        action = lambda map, node_id: map[node_id]
        super().__init__(map, action)

    def get(self, node_id: str) -> str:
        return self.perform_action(node_id)


# def test_classes():
#     M1 = {'a': True, 'b': False, 'c': False, 'd': True}
#     C1 = Subgraph(M1)
#     assert(C1.perform_action() == ['a', 'd'])

#     M3 = {'a': 5, 'b': 45, 'c': 12, 'd': 0}
#     C2 = Weight(M3)
#     assert(C2.perform_action('a') == 5)
#     assert(C2.perform_action('b') == 45)
#     assert(C2.perform_action('c') == 12)
#     assert(C2.perform_action('d') == 0)

#     M5 = {'a': 'nodeA', 'b': 'nodeB', 'c': 'nodeC', 'd': 'nodeD'}
#     C3 = Type(M5)
#     assert(C3.perform_action('a') == 'nodeA')
#     assert(C3.perform_action('b') == 'nodeB')
#     assert(C3.perform_action('c') == 'nodeC')
#     assert(C3.perform_action('d') == 'nodeD')

#     G1 = nx.DiGraph()
#     C4 = Topology(G1)
#     assert(C4.perform_action() == G1)

#     print("All tests passed!")

# if __name__ == '__main__': test_classes()
