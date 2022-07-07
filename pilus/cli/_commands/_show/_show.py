from pathlib import Path

from ....forge import FORGE


def show() -> None:
    nodes = FORGE._morphers._graph.nodes
    edges = FORGE._morphers._graph.edges
    print(f"=== NODES ===")
    for node in nodes:
        print(str(node))
    print(f"=== EDGES ===")
    for edge in edges:
        print(str(edge))
