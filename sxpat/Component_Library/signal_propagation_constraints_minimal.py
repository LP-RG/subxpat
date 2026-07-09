from z3 import (
    And, Not, Or
    )

class SignalPropagationConstraintsMinimal:
    """
    Extracts edge definition logic (input/output/gate)
    from AnnotatedGraph to maintain separation of responsibilities.
    """
    
    @staticmethod
    def define_constraints(input_edges, gate_edges, output_edges, 
                           input_literals, gate_literals, output_literals):
        
        partition_input_edges = []
        partition_output_edges = []

        # Define input edges
        for source in input_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in input_edges[source]:
                e_in = And(Not(input_literals[source]), gate_literals[destination])

                edge_in_holder.append(e_in)

            partition_input_edges.append(Or(edge_in_holder))

        # Define gate edges
        for source in gate_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in gate_edges[source]:
                e_in = And(Not(gate_literals[source]), gate_literals[destination])
                e_out = And(gate_literals[source], Not(gate_literals[destination]))

                edge_in_holder.append(e_in)
                edge_out_holder.append(e_out)

            partition_input_edges.append(Or(edge_in_holder))
            partition_output_edges.append(Or(edge_out_holder))

        # Define output edges
        for output_id in output_edges:
            predecessor = output_edges[output_id][
                0]  # Output nodes have only one predecessor  (it could be a gate or it could be an input)
            if predecessor not in gate_literals:  # This handle cases where input and output are directly connected
                continue
            e_out = And(gate_literals[predecessor], Not(output_literals[output_id]))

            partition_output_edges.append(e_out)


        return partition_input_edges, partition_output_edges
