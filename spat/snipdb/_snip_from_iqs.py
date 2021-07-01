from typing import Any, Iterable

from immutables import Map

from ..basic import Wave
from ..formats import iqs
from ..formats.snip import (
    SnipAttributeDeclaration,
    SnipAttributeDeclarationMap,
    SnipAttributeMap,
    SnipEnumDeclaration,
    SnipPart,
    SnipPartMetadata,
    create_attribute_map,
)


def iqs_to_attribute_declaration(
    iqs_chunks: iqs.IqsChunks,
) -> SnipAttributeDeclarationMap:
    # Go through the site-channel hierarchy and record the names along the way
    site_enum_values: set[str] = set()
    channel_enum_values: set[str] = set()
    for site_name, site in iqs_chunks.idat.sites.items():
        site_enum_values.add(site_name)
        for channel_name in site:
            channel_enum_values.add(channel_name)
    # Convert all site and channel names into enum attributes
    root: dict[str, SnipAttributeDeclaration] = {
        "site": SnipEnumDeclaration.from_args(values=site_enum_values),
        "channel": SnipEnumDeclaration.from_args(values=channel_enum_values),
        "part": SnipEnumDeclaration.from_args(values=("re", "im")),
    }
    return SnipAttributeDeclarationMap(__root__=root)


def iqs_to_snip_parts(
    iqs_chunks: iqs.IqsChunks, attribute_declarations: SnipAttributeDeclarationMap
) -> Iterable[SnipPart[Any]]:
    """Convert IQS chunks to snip parts."""
    name = "chunk"
    for site_name, site in iqs_chunks.idat.sites.items():
        site_header = iqs_chunks.ihdr[site_name]
        for channel_name, channel in site.items():
            channel_header = site_header[channel_name]
            for part_name in ("re", "im"):
                wave = Wave(
                    channel_header.byte_depth,
                    channel_header.time_step_ns,
                    getattr(channel, part_name),
                    iqs_chunks.idat.start_time,
                )
                attributes = create_attribute_map(
                    attribute_declarations,
                    site=site_name,
                    channel=channel_name,
                    part=part_name,
                )
                metadata = SnipPartMetadata(name=name, attributes=attributes)
                yield SnipPart(value=wave, metadata=metadata)
