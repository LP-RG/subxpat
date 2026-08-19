"""

class Z3NodeEdgeEncoder(Z3Encoder):
    
        Z3 encoder leveraging custom Datatypes (Node, Edge) for subgraph extraction.
        (Variant using explicit 5-loops to demonstrate the three core fixes)
    

    @classmethod
    def encode(cls, graphs: Solver._Graphs,
               destination: IO[str],
               global_task: Union[ForAll, Min, Max, None] = None,
               ) -> None:

        node_mapping = cls.node_mapping
        type_mapping = cls.type_mapping
        solver_construct = cls.solver_construct
        constraint_assertion = cls.constraints_assertion
        
        (graphs, inputs_names, parameters_name, nodes_types, accessories) = cls.simplification_and_accessories(graphs)

        # Initialization
        cls.inject_initialization(destination)

        # Variables
        cls.inject_variables(destination, graphs, accessories)

        # Constants
        cls.inject_constants(destination, graphs, accessories)

        # =====================================================================
        # PHASE 2: VERIFICATION (Circuit Logic)
        # it only runs when I check the error (For All/None); we turn this off at Extraction!
        # =====================================================================
        # why the 'not isinstance(Min, Max)' if statement? Because in Phase 1 
        # (when we cut the graph), we do not want to simulate current. If we did, 
        # Z3 would choke trying to solve logic equations instead of cutting edges.
        if not isinstance(global_task, (Min, Max)):
            # Nodes behavior
            destination.write('\n'.join((
                '# behaviour',
                *(
                    f'{node.name} = {node_mapping[type(node)](node, node.operands, accessories(node))}'
                    for graph in graphs
                    for node in graph.expressions
                ),
                *('',) * 2,
            )))

        # =====================================================================
        # PHASE 1: EXTRACTION (Datatypes + Convexity)
        # runs only on Extraction (Min/Max); no unnecessary overhead in Phase 2!
        # =====================================================================
        # why the 'isinstance(Min, Max)' if statement? this triggers only when 
        # optimizing. we don't want to overhead Phase 2 with graph structure generation.
        if isinstance(global_task, (Min, Max)):
            
            # gather all nodes and edges
            total_unique_names = set()
            for graph in graphs:
                for node in graph.nodes:
                    total_unique_names.add(node.name)
                    if hasattr(node, 'operands'):
                        for op in node.operands:
                            total_unique_names.add(op)
            
            num_bits = max(1, len(total_unique_names).bit_length()) + 1

            # Datatype declarations with BitVecSort 
            destination.write('\n'.join((
                '# --- Custom Datatypes for Subgraph Extraction ---',
                'Node = Datatype("Node")',
                f'Node.declare("mk_node", ("id", BitVecSort({num_bits})), ("weight", BitVecSort({num_bits})), ("in_subgraph", BoolSort()))',
                'Node = Node.create()',
                '',
                'Edge = Datatype("Edge")',
                'Edge.declare("mk_edge", ("source", Node), ("target", Node))',
                'Edge = Edge.create()',
                'nodes = {}',
                'edges = []',
                *('',) * 2,
            )))

            seen_nodes = {}  
            node_counter = 0

            destination.write('\n# 1. Inputs\n')
            for graph in graphs:
                for node in graph.variables:
                    if node.name not in seen_nodes:
                        seen_nodes[node.name] = True
                        weight = getattr(node, 'weight', 1)
                        if weight is None: weight = 1
                        sel_expr = f"Bool('{node.name}_sel')"
                        destination.write(f"nodes['{node.name}'] = Node.mk_node(BitVecVal({node_counter}, {num_bits}), BitVecVal({weight}, {num_bits}), {sel_expr})\n")
                        destination.write(f"solver.add(Node.in_subgraph(nodes['{node.name}']) == BoolVal(False))\n")
                        node_counter += 1

            destination.write('\n# 2. Gates\n')
            for graph in graphs:
                for node in graph.expressions:
                    if node.name not in seen_nodes:
                        seen_nodes[node.name] = True
                        weight = getattr(node, 'weight', 1)
                        if weight is None: weight = 1
                        sel_expr = f"Bool('{node.name}_sel')"
                        destination.write(f"nodes['{node.name}'] = Node.mk_node(BitVecVal({node_counter}, {num_bits}), BitVecVal({weight}, {num_bits}), {sel_expr})\n")
                        # Circuit gates form the actual Translation Bridge
                        if weight == -1:
                            destination.write(f"solver.add(Node.in_subgraph(nodes['{node.name}']) == BoolVal(False))\n")
                        else:
                            destination.write(f"solver.add({node.name} == Node.in_subgraph(nodes['{node.name}']))\n")
                        node_counter += 1
            
            destination.write('\n# 3. Outputs\n')
            for graph in graphs:
                for node in graph.targets:
                    if node.name not in seen_nodes:
                        seen_nodes[node.name] = True
                        weight = getattr(node, 'weight', 1)
                        if weight is None: weight = 1
                        sel_expr = f"Bool('{node.name}_sel')"
                        destination.write(f"nodes['{node.name}'] = Node.mk_node(BitVecVal({node_counter}, {num_bits}), BitVecVal({weight}, {num_bits}), {sel_expr})\n")
                        destination.write(f"solver.add(Node.in_subgraph(nodes['{node.name}']) == BoolVal(False))\n")
                        node_counter += 1
            
            destination.write('\n# 4. Constants\n')
            for graph in graphs:
                for node in graph.constants:
                    if node.name not in seen_nodes:
                        seen_nodes[node.name] = True
                        weight = getattr(node, 'weight', 1)
                        if weight is None: weight = 1
                        sel_expr = f"Bool('{node.name}_sel')"
                        destination.write(f"nodes['{node.name}'] = Node.mk_node(BitVecVal({node_counter}, {num_bits}), BitVecVal({weight}, {num_bits}), {sel_expr})\n")
                        destination.write(f"solver.add(Node.in_subgraph(nodes['{node.name}']) == BoolVal(False))\n")
                        node_counter += 1

            destination.write('\n# 4.5. Constraints & Internal Nodes\n')
            for graph in graphs:
                for node in graph.nodes:
                    if node.name not in seen_nodes:
                        seen_nodes[node.name] = True
                        weight = getattr(node, 'weight', 1)
                        if weight is None: weight = 1
                        sel_expr = f"Bool('{node.name}_sel')"
                        destination.write(f"nodes['{node.name}'] = Node.mk_node(BitVecVal({node_counter}, {num_bits}), BitVecVal({weight}, {num_bits}), {sel_expr})\n")
                        destination.write(f"solver.add(Node.in_subgraph(nodes['{node.name}']) == BoolVal(False))\n")
                        node_counter += 1
                    if hasattr(node, 'operands'):
                        for op in node.operands:
                            if op not in seen_nodes:
                                seen_nodes[op] = True
                                sel_expr = f"Bool('{op}_sel')"
                                destination.write(f"nodes['{op}'] = Node.mk_node(BitVecVal({node_counter}, {num_bits}), BitVecVal(1, {num_bits}), {sel_expr})\n")
                                destination.write(f"solver.add(Node.in_subgraph(nodes['{op}']) == BoolVal(False))\n")
                                node_counter += 1

            destination.write('\n# 5. Edges\n')
            edge_counter = 0
            
            successors: Dict[str, list] = {}
            predecessors: Dict[str, list] = {}
            
            for graph in graphs:
                for node in graph.nodes:
                    if isinstance(node, Operation) and hasattr(node, 'operands'):
                        for op in node.operands:
                            destination.write(f"edge_{edge_counter} = Edge.mk_edge(nodes['{op}'], nodes['{node.name}'])\n")
                            destination.write(f"edges.append(edge_{edge_counter})\n")
                            edge_counter += 1
                            
                            # Populate the dictionaries for the convexity logic
                            successors.setdefault(op, []).append(node.name)
                            predecessors.setdefault(node.name, []).append(op)

            # FIX 3: CONVEXITY CONSTRAINTS
            _desc_cache: Dict[str, list] = {}
            _anc_cache: Dict[str, list] = {}

            def _descendants(name: str) -> list:
                if name in _desc_cache: return _desc_cache[name]
                found, stack, out = set(), list(successors.get(name, [])), []
                while stack:
                    n = stack.pop()
                    if n in found: continue
                    found.add(n)
                    out.append(n)
                    stack.extend(successors.get(n, []))
                _desc_cache[name] = out
                return out

            def _ancestors(name: str) -> list:
                if name in _anc_cache: return _anc_cache[name]
                found, stack, out = set(), list(predecessors.get(name, [])), []
                while stack:
                    n = stack.pop()
                    if n in found: continue
                    found.add(n)
                    out.append(n)
                    stack.extend(predecessors.get(n, []))
                _anc_cache[name] = out
                return out

            convexity_lines = []
            edge_pairs = [(s, t) for s, tgts in successors.items() for t in tgts]
            for src_name, tgt_name in edge_pairs:
                desc = _descendants(tgt_name)
                if desc:
                    not_desc = ", ".join(f"Not(Node.in_subgraph(nodes['{l}']))" for l in desc + [tgt_name])
                    convexity_lines.append(
                        f"    Implies(And(Node.in_subgraph(nodes['{src_name}']), "
                        f"Not(Node.in_subgraph(nodes['{tgt_name}']))), And({not_desc})),"
                    )
                anc = _ancestors(src_name)
                if anc:
                    not_anc = ", ".join(f"Not(Node.in_subgraph(nodes['{l}']))" for l in anc + [src_name])
                    convexity_lines.append(
                        f"    Implies(And(Not(Node.in_subgraph(nodes['{src_name}'])), "
                        f"Node.in_subgraph(nodes['{tgt_name}'])), And({not_anc})),"
                    )

            destination.write('\n'.join((
                '\n# convexity (structural) constraints',
                'convexity = And(',
                *(convexity_lines or ['    True,']),
                ')',
                'solver.add(convexity)',
                *('',) * 2,
            )))

        # Nodes usage 
        destination.write('\n'.join((
            '# usage',
            'usage = And(', *(
                f'    {constraint_node.operand},'
                for graph in graphs
                if isinstance(graph, CGraph)
                for constraint_node in graph.constraints
            ), ')',
            *('',) * 2,
        )))

        # Solver
        destination.write('\n'.join((
            f'# define solver',
            f'solver = {solver_construct[type(global_task)]}',
            *constraint_assertion[type(global_task)]('solver', global_task, ['usage']),
            *('',) * 2,
        )))

        # Results
        cls.inject_solve_and_result_writing(destination, graphs, graphs)

"""