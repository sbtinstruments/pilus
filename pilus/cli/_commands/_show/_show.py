from ....forge import FORGE


def show() -> None:
    nodes = FORGE.morph_graph_nodes()
    edges = FORGE.morph_graph_edges()
    print("=== NODES ===")  # noqa: T201
    for node in nodes:
        print(str(node))  # noqa: T201
    print("=== EDGES ===")  # noqa: T201
    for edge in edges:
        print(str(edge))  # noqa: T201
