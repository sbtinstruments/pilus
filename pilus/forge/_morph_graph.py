from contextlib import contextmanager
from itertools import pairwise
from os import PathLike
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Iterator

import networkx as nx

from .._magic import MediumSpec
from ..errors import PilusMissingMorpherError
from ._morph import Morpher, MorphFunc, ShapeSpec


class MorphGraph:
    """Graph of available morphs."""

    def __init__(self) -> None:
        # Nodes are of type: `ShapeSpec`
        # Edges are of type: `MorphFunc`
        self._graph = nx.DiGraph()

    def add_morpher(self, morpher: Morpher) -> None:
        """Add nodes and edge that corresponds the given morpher to this graph.

        Removes the existing edge (if any).
        """
        # Remove existing edge (if any)
        try:
            self._graph.remove_edge(morpher.input, morpher.output)
        except nx.NetworkXError:
            pass
        # Add new edge
        self._graph.add_edge(morpher.input, morpher.output, func=morpher.func)
        # Generate edges
        if isinstance(morpher.input, MediumSpec):
            self._generate_edges_to_medium_spec(morpher.input)

    def _generate_edges_to_medium_spec(self, spec: MediumSpec) -> None:
        if spec.raw_type is BinaryIO:
            path_to_io = Morpher(
                input=MediumSpec(raw_type=PathLike, media_type=spec.media_type),
                output=spec,
                func=_file_to_io,
            )
            self._add_morpher_if_not_exists(path_to_io)
        elif spec.raw_type is bytes:
            path_to_io = Morpher(
                input=MediumSpec(raw_type=PathLike, media_type=spec.media_type),
                output=MediumSpec(raw_type=BinaryIO, media_type=spec.media_type),
                func=_file_to_io,
            )
            self._add_morpher_if_not_exists(path_to_io)
            io_to_data = Morpher(
                input=MediumSpec(raw_type=BinaryIO, media_type=spec.media_type),
                output=MediumSpec(raw_type=bytes, media_type=spec.media_type),
                func=_io_to_data,
            )
            self._add_morpher_if_not_exists(io_to_data)

    def _add_morpher_if_not_exists(self, morpher: Morpher) -> None:
        # Early out if the edge already exists
        try:
            self._graph[morpher.input][morpher.output]
        except KeyError:
            pass
        else:
            return
        # Add new edge
        self._graph.add_edge(morpher.input, morpher.output, func=morpher.func)

    def get_morphs(
        self, in_spec: ShapeSpec, out_spec: ShapeSpec
    ) -> Iterator[MorphFunc]:
        """Return morph functions that morphs `in_spec` into `out_spec`."""
        # We find the shortest sequence of morphs that takes
        # us from the source type into the destination type.
        try:
            path: list[Any] = nx.shortest_path(self._graph, in_spec, out_spec)
        except nx.NodeNotFound as exc:
            raise PilusMissingMorpherError(
                f'Can not find morph chain that converts from "{in_spec}" to'
                f' "{out_spec}"'
            ) from exc
        return self._path_to_morph_funcs(path)

    def _path_to_morph_funcs(self, path: Iterable[Any]) -> Iterator[MorphFunc]:
        for edge in pairwise(path):
            yield self._graph[edge[0]][edge[1]]["func"]

    def spec_to_type(self, spec: ShapeSpec) -> type:
        try:
            for edge in nx.dfs_edges(self._graph, spec):
                target_node = edge[1]
                if not isinstance(target_node, MediumSpec):
                    assert isinstance(target_node, type)
                    return target_node
        except KeyError:
            pass
        raise ValueError(
            "Could not find type that corresponds to the given shape specification"
        )


@contextmanager
def _file_to_io(file: Path) -> Iterator[BinaryIO]:
    with file.open("rb") as io:
        yield io


def _io_to_data(io: BinaryIO) -> bytes:
    return io.read()
