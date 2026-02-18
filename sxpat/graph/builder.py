from __future__ import annotations
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Type, Union, final, overload
from typing_extensions import Self, Protocol

import functools

from .graph import T_Graph
from .node import AnyNode, Node, PlaceHolder


@final
class GraphBuilder:
    # error classes
    class AlreadyBuiltError(Exception): pass
    class DuplicateNodeError(Exception): pass
    class ReassigningOperandsError(Exception): pass
    class InvalidNodeError(Exception): pass
    class NoRecordingError(Exception): pass

    def __init__(self):
        # utility state
        self.__is_built: bool = False
        self.__last_name: str = None
        self.__names_record: List[List[str]] = list()
        self.__nodes_with_operands: Set[str] = set()
        # graph data
        self.__partial_nodes: Dict[str, functools.partial] = dict()
        self.__extras: Dict[str, Any] = dict()

    def push_recording(self) -> None:
        """
            Push a new recording of names to the stack, which will record future node additions.

            The buffer can be retrieved using `.pop_recording()`.
        """
        self.__names_record.append(list())

    def pop_recording(self) -> List[str]:
        """
            Pop the most recent buffer of names (created using `.push_recording()`) from the stack and return it.
            If no buffer is present, raises a `NoRecordingError`.

            Future node additions will be recorded on the new topmost buffer, or discarded if none is present.

            :return: The list of names recorded from the most recent call to `.start_recording()`.
        """
        # guard
        if len(self.__names_record) == 0: raise self.NoRecordingError()

        return self.__names_record.pop()

    def build(
            self,
            graph_type: Type[T_Graph],
    ) -> T_Graph:
        """
            Build the graph using the given type.

            :param graph_type: The class to use to build the graph, the nodes and all accessories will be passed to it.
            :return graph:     The built graph.
        """
        # prevent rebuilding
        if self.__is_built: raise self.AlreadyBuiltError()
        self.__is_built = True

        # finalize the nodes
        nodes = (partial_node() for partial_node in self.__partial_nodes.values())
        # construct the graph
        return graph_type(nodes, **self.__extras)

    def add_node(
            self,
            name: str,
            constructor: Union[Type[AnyNode], Callable[..., Node]],
            **kwargs,
    ) -> Self:
        """
            Add a node to the graph.

            :param name:          The name of the node.
            :param constructor:   The type of the node or a function that will return the node.
            :param **kwargs:      Keyword arguments to pass to the node constructor.
            :return self:         The builder object.
        """
        # guards
        if self.__is_built: raise self.AlreadyBuiltError()
        if name in self.__partial_nodes: raise self.DuplicateNodeError(name)

        # call inner
        self._add_node(name, constructor, **kwargs)

        # return the builder for chaining
        return self

    def _add_node(
            self,
            name: str,
            constructor: Union[Type[AnyNode], Callable[..., Node]],
            **kwargs,
    ):
        """
            :param name:          The name of the node.
            :param constructor:   The type of the node or a function that will return the node.
            :param **kwargs:      Keyword arguments to pass to the node constructor.
        """

        # prepare partial node
        self.__partial_nodes[name] = functools.partial(constructor, name, **kwargs)
        # update utility state
        self.__last_name = name
        if 'operands' in kwargs: self.__nodes_with_operands.add(name)
        # store the node name if recording
        if len(self.__names_record) != 0: self.__names_record[-1].append(name)

    @property
    def last_name(self) -> str:
        """The name of the last added node."""
        return self.__last_name

    @property
    def name(self) -> str:
        """Alias of `.last_name`."""
        return self.__last_name

    @overload
    def add_operands(
            self,
            operation: str,
            operands: Iterable[str],
    ) -> Self:
        """
            Add the operands to the node.

            :param operation: The name of the node to add the operands to.
            :param operands:  The iterable of names of the nodes to be added as operands, the order is preserved.
            :return self:     The builder object.
        """
    @overload
    def add_operands(
            self,
            operands: Iterable[str],
    ) -> Self:
        """
            Add the operands to the last added node.

            :param operands: Iterable of names of the nodes to be added as operands, the order is preserved.
            :return self:    The builder object.
        """

    def add_operands(
            self,
            operation_or_operands: Union[str, Iterable[str]],
            operands: Optional[Iterable[str]] = None,
    ) -> Self:
        # organize args
        if isinstance(operation_or_operands, str):
            operation = operation_or_operands
            operands = tuple(operands)
        else:
            operation = self.__last_name
            operands = tuple(operation_or_operands)

        # guards
        if self.__is_built: raise self.AlreadyBuiltError()
        if operation not in self.__partial_nodes: raise self.InvalidNodeError(operation)
        if any((n not in self.__partial_nodes) for n in operands):
            raise self.InvalidNodeError(list(filter(lambda n: n not in self.__partial_nodes, operands)))
        if operation in self.__nodes_with_operands: raise self.ReassigningOperandsError(operation)

        # call inner
        self._add_operands(operation, operands)

        # return the builder for chaining
        return self

    def _add_operands(
            self,
            operation: str,
            operands: Iterable[str]
    ):
        """
            :param operation: The name of the node to add the operands to.
            :param operands:  The iterable of names of the nodes to be added as operands, the order is preserved.
        """
        # add operands
        self.__partial_nodes[operation] = functools.partial(self.__partial_nodes[operation], operands=operands)
        # update utility state
        self.__nodes_with_operands.add(operation)

    def add_placeholders(
            self,
            nodes_name: Iterable[str],
    ) -> Self:
        """
        Add all the given names as placeholders.

        :param nodes_name: The names of the placeholders to be.
        :return self:      The builder object.
        """
        # guards
        if self.__is_built: raise self.AlreadyBuiltError()
        if any(name in self.__partial_nodes for name in nodes_name):
            raise self.DuplicateNodeError(list(filter(lambda n: n in self.__partial_nodes, nodes_name)))

        # call inner
        for name in nodes_name: self._add_node(name, PlaceHolder)

        # return the builder for chaining
        return self

    def mark_inputs(
            self,
            inputs_names: Iterable[str],
    ) -> Self:
        """
            Marks the wanted nodes as inputs.

            :param inputs_names: The names of the nodes to be marked as inputs.
            :return self:        The builder object.
        """
        # freeze
        inputs_names = tuple(inputs_names)

        # guards
        if any((n not in self.__partial_nodes) for n in inputs_names):
            raise self.InvalidNodeError(list(filter(lambda n: n not in self.__partial_nodes, inputs_names)))

        # elaborate
        self.__extras['inputs_names'] = tuple(inputs_names)

        # return the builder for chaining
        return self

    def mark_outputs(
            self,
            outputs_names: Iterable[str],
    ) -> Self:
        """
            Marks the wanted nodes as outputs.

            :param outputs_names: The names of the nodes to be marked as outputs.
            :return self:         The builder object.
        """
        # freeze
        outputs_names = tuple(outputs_names)

        # guards
        if any((n not in self.__partial_nodes) for n in outputs_names):
            raise self.InvalidNodeError(list(filter(lambda n: n not in self.__partial_nodes, outputs_names)))

        # elaborate
        self.__extras['outputs_names'] = tuple(outputs_names)

        # return the builder for chaining
        return self

    def mark_parameters(
            self,
            parameters_names: Iterable[str],
    ) -> Self:
        """
            Marks the wanted nodes as parameters.

            :param parameters_names: The names of the nodes to be marked as parameters.
            :return self:            The builder object.
        """
        # freeze
        parameters_names = tuple(parameters_names)

        # guards
        if any((n not in self.__partial_nodes) for n in parameters_names):
            raise self.InvalidNodeError(list(filter(lambda n: n not in self.__partial_nodes, parameters_names)))

        # elaborate
        self.__extras['parameters_names'] = tuple(parameters_names)

        # return the builder for chaining
        return self

    def mark_subgraph(
            self,
            nodes_names: Iterable[str],
    ) -> Self:
        """
            Marks the wanted nodes as being in the subgraph.

            :param nodes_names: The names of the nodes to be marked as being in the subgraph.
            :return self:       The builder object.
        """
        # freeze
        nodes_names = tuple(nodes_names)

        # guards
        if any((n not in self.__partial_nodes) for n in nodes_names):
            raise self.InvalidNodeError(list(filter(lambda n: n not in self.__partial_nodes, nodes_names)))

        # elaborate
        for n in nodes_names:
            self.__partial_nodes[n] = functools.partial(self.__partial_nodes[n], in_subgraph=True)

        # return the builder for chaining
        return self

    class PipableCallable(Protocol):
        def __call__(self, builder: Self, *args: Any, **kwargs: Any) -> None: ...

    def update_with(
            self,
            func: PipableCallable, *args: Any, **kwargs: Any,
    ) -> Self:
        """
            Updates the builder by passing it to a function.

            :param func:  Function to apply to the builder. `args`, and `kwargs` are passed into `func`.
            :return self: The builder object.
        """
        func(self, *args, **kwargs)
        return self
