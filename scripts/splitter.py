from pathlib import Path

import click

from spat.formats import iqs


def split_iqs_file(source_file: Path) -> None:
    """Split IQS file into separate IQS version 1.0.0 file (one per site)."""
    with source_file.open("rb") as io:
        source_iqs = iqs.from_io(io)
    if source_iqs is None:
        print("No data in IQS file")
        return
    for site_name in source_iqs.ihdr:
        destination_file = source_file.with_stem(f"{source_file.stem}-{site_name}")
        with open(destination_file, "wb") as io:
            iqs.to_io(
                source_iqs, io, version=iqs.IqsVersion.V1_0_0, site_to_keep=site_name
            )


@click.command()
@click.argument("filename", type=click.Path(exists=True, resolve_path=True))
def split_file(filename) -> None:
    split_iqs_file(Path(filename))


if __name__ == "__main__":
    split_file()
