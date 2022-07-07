from __future__ import annotations

from io import SEEK_CUR, BytesIO
from typing import Any, BinaryIO, Iterable, Optional, Type, Union

from ...errors import PilusDeserializeError, PilusMissingDataError, PilusSerializeError
from .._io import read_exactly, read_int, seek, write_exactly, write_int
from ._chunk import ReadableChunk, UnidentifiedAncilliaryChunk, WritableChunk
from ._crc import crc32

# When we get variadic generics in Python 3.11, we can use `TypeVarTuple` for
# proper mapping between the type of `chunk_models` and the return type.
# Similar to: https://github.com/python/typing/issues/193#issuecomment-406801158
#
# Something like:
#
#     Ts = TypeVarTuple("Ts", bind=Chunk)
#     def require_single_chunk(
#         io: BinaryIO, *, chunk_models: tuple[Type[*Ts]], **kwargs: Any
#     ) -> Union[*Ts]:
#         ...
#


def require_single_chunk(
    io: BinaryIO, *, chunk_models: tuple[Type[ReadableChunk], ...], **kwargs: Any
) -> ReadableChunk:
    """Return the first chunk of the required type.

    May raise `PilusDeserializeError` or one of its derivatives.
    """
    for chunk in stream_chunks(io, chunk_models=chunk_models, **kwargs):
        return chunk
    raise PilusDeserializeError(
        f"Could not find a required chunk of type: {chunk_models}"
    )


def stream_chunks(
    io: BinaryIO, *, chunk_models: tuple[Type[ReadableChunk], ...], **kwargs: Any
) -> Iterable[ReadableChunk]:
    """Return stream of chunks.

    Automatically skips unidentified ancilliary (non-critical) chunks.

    May raise `PilusDeserializeError` or one of its derivatives.
    """
    while chunk := read_chunk(io, chunk_models=chunk_models, **kwargs):
        # Discard all unidentified ancilliary (non-critical) chunks
        if isinstance(chunk, UnidentifiedAncilliaryChunk):
            continue
        yield chunk


def read_chunk(
    io: BinaryIO, *, chunk_models: tuple[Type[ReadableChunk], ...], **kwargs: Any
) -> Union[Optional[ReadableChunk], UnidentifiedAncilliaryChunk]:
    """Read single chunk.

    This is a low-level function. Prefer `stream_chunks` or similar.

    May raise `PilusDeserializeError` or one of its derivatives.
    """
    # Early out if there is no more data in the IO stream
    chunk_length = _read_chunk_length(io)
    if chunk_length is None:
        return None
    # Read chunk type
    chunk_type = read_exactly(io, 4)
    # Get chunk model from the chunk type
    chunk_model = _chunk_type_to_model(chunk_type, chunk_models=chunk_models)
    # Early out if this is an unidentified ancilliary chunk
    if isinstance(chunk_model, UnidentifiedAncilliaryChunk):
        seek(io, chunk_length + 4, SEEK_CUR)  # Skip data and CRC
        return chunk_model
    # Read chunk data.
    # TODO: Do not read all data into memory at once. Split it into smaller parts.
    chunk_data = read_exactly(io, chunk_length)
    chunk = _deserialize_chunk_data(chunk_model, chunk_data, **kwargs)
    # CRC check
    actual_crc = _chunk_crc(chunk_type, chunk_data)
    expected_crc = read_int(io, 4)
    if actual_crc != expected_crc:
        raise PilusDeserializeError("CRC mismatch")
    return chunk


def _chunk_type_to_model(
    chunk_type: bytes, *, chunk_models: tuple[Type[ReadableChunk], ...]
) -> Union[Type[ReadableChunk], UnidentifiedAncilliaryChunk]:
    try:
        return next(model for model in chunk_models if model.type_ == chunk_type)
    except StopIteration as exc:
        chunk_type_name = _chunk_type_to_string(chunk_type)
        # We don't reckognize the chunk type.
        # Check the so-called "ancilliary bit" to see if it's an:
        #   1. Ancilliary chunk (optional)
        #   2. Critical chunk (required)
        chunk_is_ancilliary = chunk_type_name[0].islower()
        if not chunk_is_ancilliary:
            # Raise an error if we can't deserialize a critical chunk
            raise PilusDeserializeError(
                f'Encountered unknown critical chunk: "{chunk_type_name}"'
            ) from exc
        return UnidentifiedAncilliaryChunk()


def _chunk_type_to_string(chunk_type: bytes) -> str:
    try:
        # All chunk types are in ASCII
        return chunk_type.decode("ascii")
    # Note that pytohn raises `UnicodeDecodeError` even though we try to decode
    # from ASCII.
    except UnicodeDecodeError as exc:
        raise PilusDeserializeError("Invalid chunk type") from exc


def _read_chunk_length(io: BinaryIO) -> Optional[int]:
    """Read chunk length.

    May raise `IqsError` or one of its derivatives.
    """
    try:
        return read_int(io, 4)
    except PilusMissingDataError as exc:
        # There is no more data so return `None`
        if exc.number_of_bytes_read == 0:
            return None
        # There is some data but not enough to become a chunk length
        raise PilusDeserializeError(f'Could not read chunk length: "{exc}"') from exc


def _deserialize_chunk_data(
    chunk_model: Type[ReadableChunk],
    chunk_data: bytes,
    **kwargs: Any,
) -> ReadableChunk:
    """Read and parse chunk data of the given type and length.

    May raise `PilusDeserializeError` or one of its derivatives.
    """
    if "data_length" not in kwargs:
        kwargs["data_length"] = len(chunk_data)
    # It may seem a bit strange that we convert `chunk_data` back into an IO
    # stream here. The reasoning is three-fold:
    #   1. We already read all the data into memory to compute the CRC. It doesn't
    #      make sense to read it again just to satisfy the `from_io` interface.
    #   2. The various deserializers only requires a single pass over the data. In
    #      other words, the deserializers only require a `BinaryIO` stream and not
    #      the full `bytes` interface.
    #   3. The deserializers require the notion of "position within the data" that
    #      you get from `BinaryIO` but not from `bytes`. if we only got `bytes`,
    #      we would have to keep track of this "position" anyway.
    chunk_data_io = BytesIO(chunk_data)
    # Parse chunk data
    return chunk_model.from_io(chunk_data_io, **kwargs)


def write_chunk(io: BinaryIO, chunk: WritableChunk) -> None:
    """Serialize chunk into the IO stream.

    May raise `PilusSerializeError` or one of its derivatives.
    """
    # Serialize the chunk data itself
    chunk_data_io = BytesIO()
    # We know the data length up front so we can reserve (pre-allocate)
    # memory for it.
    chunk_data_length = chunk.data_length()
    _reserve(chunk_data_io, chunk_data_length)  # [1]
    chunk.to_io(chunk_data_io)
    # Our `chunk.data_length` function is exact. We neither reserve too much
    # or too little data at [1].
    assert chunk_data_length == len(chunk_data_io.getbuffer())
    # Write chunk length and type
    write_int(io, len(chunk_data_io.getbuffer()), 4)
    write_exactly(io, chunk.type_)
    # Then the data itself
    write_exactly(io, chunk_data_io.getbuffer())
    # Finally, write the CRC checksum of the data and type
    crc = _chunk_crc(chunk.type_, chunk_data_io.getbuffer())
    write_int(io, crc, 4)


def _reserve(io: BinaryIO, size: int) -> None:
    """Pre-allocate data in the IO stream."""
    if size < 0:
        raise PilusSerializeError("Can't reserve a negative number of bytes")
    if size == 0:
        return
    # Theory of operation:
    #
    #   1. Seek ahead
    #   2. Write a single byte
    #   3. Seek back to where we start
    #
    # If we only do (1) and (3) alone, we only move a position but we won't
    # cause any data allocation. Because we also do (2), we force the
    # stream to allocate the data.
    if size != 1:
        seek(io, size - 1, SEEK_CUR)
    write_exactly(io, bytes(1))
    seek(io, -size, SEEK_CUR)


def _chunk_crc(chunk_type: bytes, chunk_data: bytes) -> int:
    crc = 0xFFFFFFFF
    crc = crc32(chunk_type, crc)
    crc = crc32(chunk_data, crc)
    return crc
