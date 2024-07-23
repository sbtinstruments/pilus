from typing import Any, Iterable

from ..basic import IqsAggregate, Lpcm, Wave, WaveMeta
from ..forge import FORGE, Morpher
from ..snipdb import (
    SnipAttrDecl,
    SnipAttrDeclMap,
    SnipDb,
    SnipEnumDecl,
    SnipRow,
    SnipRowMetadata,
    create_attribute_map,
)


def iqs_to_attr_decls(aggregate: IqsAggregate) -> SnipAttrDeclMap:
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
    return SnipAttrDeclMap(root=root)


def iqs_to_snip_parts(
    aggregate: IqsAggregate, attr_decls: SnipAttrDeclMap
) -> Iterable[SnipRow[Any]]:
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
                metadata = SnipRowMetadata(name=name, attributes=attributes)
                yield SnipRow(content=wave, metadata=metadata)


def iqs_aggregate_to_snipdb(iqs_aggregate: IqsAggregate) -> SnipDb:
    """Convert IQS aggregate to snip DB."""
    attr_decls = iqs_to_attr_decls(iqs_aggregate)
    snip_parts = iqs_to_snip_parts(iqs_aggregate, attr_decls)
    return SnipDb(snip_parts, attr_decls)


FORGE.add_morpher(
    Morpher(
        input=IqsAggregate,
        output=SnipDb,
        func=iqs_aggregate_to_snipdb,
    )
)
