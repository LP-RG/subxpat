from typing import Mapping

from .utils import get_pure_name

# patched:
from Z3Log.graph import Graph as _Graph

__all__ = ['Graph']


class Graph(_Graph):
    def __init__(self, circuit_in_gv_path: str, is_clean: bool = False):
        """
        takes in a circuit and creates a networkx graph out of it
        :param benchmark_name: the input benchmark in gv format
        :param is_clean: leave empty for now
        """

        # reduced
        self.__graph_name = get_pure_name(circuit_in_gv_path)
        self.__graph_out_path = circuit_in_gv_path

        self.__graph = self.import_graph()

        self.__sorted_node_list = None
        self.__is_clean = is_clean

        if not self.is_clean:
            self.clean_graph()
            self.sort_graph()

        self.remove_output_outgoing_edges()

        self.__input_dict = self.sort_dict(self.extract_inputs())
        self.__output_dict = self.sort_dict(self.extract_outputs())
        self.__gate_dict = self.sort_dict(self.extract_gates())
        self.__constant_dict = self.sort_dict(self.extract_constants())

        self.__num_inputs = len(self.__input_dict)
        self.__num_outputs = len(self.__output_dict)
        self.__num_gates = len(self.__gate_dict)
        self.__num_constants = len(self.__constant_dict)

    @property
    def in_path(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def verilog_in_path(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')
    @property
    def dot_in_path(self): raise RuntimeError('[DEPRECATED] talk with Marco if you need this')

    def sort_dict(self, mapping: Mapping) -> dict:
        sorted_keys = sorted(mapping.keys())
        return {k: mapping[k] for k in sorted_keys}

    def __repr__(self):
        return (
            f'An object of class Graph\n'
            f'{self.name = }\n'
            # f'{self.in_path = }\n'
            f'{self.out_path = }\n'
            f'{self.num_inputs = }\n'
            f'{self.num_outputs = }\n'
            f'{self.num_gates = }\n'
        )
