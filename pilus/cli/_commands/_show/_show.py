
from ....forge import FORGE


def show() -> None:
    nodes = FORGE._morphers._graph.nodes
    edges = FORGE._morphers._graph.edges
    print("=== NODES ===")
    for node in nodes:
        print(str(node))
    print("=== EDGES ===")
    for edge in edges:
        print(str(edge))
