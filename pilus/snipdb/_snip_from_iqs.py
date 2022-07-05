from typing import Any, Iterable

from ..basic import Wave, WaveMeta
from ..formats import iqs
from ..formats.snip import (
    SnipAttrDecl,
    SnipAttrDeclMap,
    SnipEnumDecl,
    SnipPart,
    SnipPartMetadata,
    create_attribute_map,
)
from ..formats.wave import Lpcm


def iqs_to_attr_decls(aggregate: iqs.IqsAggregate) -> SnipAttrDeclMap:
    """Extract attribute declarations from an IQS aggregate."""
    # Go through the site-channel hierarchy and record the names along the way
    site_enum_values: set[str] = set()
    channel_enum_values: set[str] = set()
    for site_name, site in aggregate.sites.items():
        site_enum_values.add(site_name)
        for channel_name in site:
            channel_enum_values.add(channel_name)
    # Convert all site and channel names into enum attributes
    root: dict[str, SnipAttrDecl] = {
        "site": SnipEnumDecl.from_args(values=site_enum_values),
        "channel": SnipEnumDecl.from_args(values=channel_enum_values),
        "part": SnipEnumDecl.from_args(values=("re", "im")),
    }
    return SnipAttrDeclMap(__root__=root)


def iqs_to_snip_parts(
    aggregate: iqs.IqsAggregate, attr_decls: SnipAttrDeclMap
) -> Iterable[SnipPart[Any]]:
    """Convert IQS aggregate to snip parts."""
    name = "diff"
    for site_name, site in aggregate.sites.items():
        for channel_name, channel in site.items():
            for part_name in ("re", "im"):
                lpcm = Lpcm(
                    channel.byte_depth,
                    channel.time_step_ns,
                    getattr(channel, part_name),
                )
                wave_metadata = WaveMeta(
                    start_time=aggregate.start_time, max_amplitude=channel.max_amplitude
                )
                wave = Wave(lpcm, wave_metadata)
                attributes = create_attribute_map(
                    attr_decls,
                    site=site_name,
                    channel=channel_name,
                    part=part_name,
                )
                metadata = SnipPartMetadata(name=name, attributes=attributes)
                yield SnipPart(value=wave, metadata=metadata)
