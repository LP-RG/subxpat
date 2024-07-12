from z3 import *

# Define the Node datatype
Node = Datatype('Node')
Node.declare('mk_node', ('id', BitVecSort(32)), ('name', StringSort()), ('weight', BitVecSort(32)), ('node_type', IntSort()))
Node = Node.create()
print(f'{Node.num_constructors() = }')
print(f'{Node.constructor(0).arity() = }')
print(f'{Node.accessor(0, 0) = }')


# Define the Edge datatype
Edge = Datatype('Edge')
Edge.declare('mk_edge', ('source', Node), ('target', Node))
Edge = Edge.create()

# Create some nodes
in0 = Node.mk_node(BitVecVal(0, 32), StringVal("in0"), BitVecVal(4294967295, 32), IntVal(0))
in1 = Node.mk_node(BitVecVal(1, 32), StringVal("in1"), BitVecVal(4294967295, 32), IntVal(0))
g0 = Node.mk_node(BitVecVal(0, 32), StringVal("g0"), BitVecVal(1, 32), IntVal(1))

print(f'{Node.accessor(0,3)(g0) = }')
print(f'{Node.node_type(g0) = }')

if Node.accessor(0,3)(g0) == Node.node_type(g0):
    print(f'True')
if Node.node_type(g0) == IntVal(1):
    print(f'True')
else:
    print(f'False')


opt = Optimize()

opt.add(Node.accessor(0,3)(g0) == IntVal(1))

res = opt.check()

if res == sat:
    print(f'sat')
    model = opt.model()
    print(f'{model = }')
else:
    print(f'unsat')
print(f'{type(Node.node_type(g0)) = }')
print(f'{type(IntVal(1)) = }')
print(f'{type(IntVal(1).as_long()) = }')
print(f'{type(IntSort()) = }')





# Create an edge
edge = Edge.mk_edge(in0, g0)

# Print the nodes and edge
# print(in0)
# print(in1)
# print(g0)
# print(edge)
