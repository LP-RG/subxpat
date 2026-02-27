import networkx as nx


# create dummy graph
graph = nx.digraph.DiGraph()
graph.add_node(0, weight=20, color='red')
graph.add_node(1, weight=10, color='red')
graph.add_node(2, weight=30, color='red')
graph.add_node(3, weight=40, color='red')
graph.add_node(4, weight=50, color='red')
graph.add_edges_from([[0,1], [1,2], [0,2]])


# nodes
print('approach 1')
for node_id in graph.nodes:
    attrs = graph.nodes[node_id]
    print(node_id, attrs)

print('approach 2')
for (node_id, attrs) in graph.nodes(True):
    print(node_id, attrs)

# edges
print('edges')
for (node_source, node_destination) in graph.edges:
    print(node_source, '->', node_destination)

# successors
print('successors from edges')
node_id = 0
print(graph.out_edges(node_id))

print('successors')
node_id = 0
print(list(graph.successors(node_id)))

# predecessors
print('predecessors')
node_id = 2
print(list(graph.predecessors(node_id)))

# degree
print('direct access')
for node_id in graph.nodes:
    print(
        node_id, 
        graph.degree(node_id),
        graph.in_degree(node_id),
        graph.out_degree(node_id),
    )

print('iterable access')
for (node_id, degree) in graph.out_degree:
    print(node_id, degree)
