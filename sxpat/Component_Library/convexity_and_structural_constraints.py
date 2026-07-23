from z3 import And, Not, Implies
import networkx as nx

class ConvexityConstraints:
    @staticmethod
    def add_convexity_constraints(opt, G, gate_literals, gate_edges):
        descendants = {}
        ancestors = {}
        for n in G:
            if n not in descendants:
                descendants[n] = sorted(nx.descendants(G, n))
            if n not in ancestors:
                ancestors[n] = sorted(nx.ancestors(G, n))

        # Generate convexity constraints
        for source in gate_edges:
            for destination in gate_edges[source]:
                if len(descendants[destination]) > 0:  # Constraints on output edges
                    not_descendants = [Not(gate_literals[l]) for l in descendants[destination]]
                    not_descendants.append(Not(gate_literals[destination]))
                    descendat_condition = Implies(And(gate_literals[source], Not(gate_literals[destination])),
                                                  And(not_descendants))
                    opt.add(descendat_condition)
                if len(ancestors[source]) > 0:  # Constraints on input edges
                    not_ancestors = [Not(gate_literals[l]) for l in ancestors[source]]
                    not_ancestors.append(Not(gate_literals[source]))
                    ancestor_condition = Implies(And(Not(gate_literals[source]), gate_literals[destination]),
                                                 And(not_ancestors))
                    opt.add(ancestor_condition)