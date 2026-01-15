import argparse
import csv
import logging
from math import atan2, log10, sqrt
from pathlib import Path

from pilus.errors import PilusDeserializeError
from pilus.sbt import bdr_from_io as from_io

logger = logging.getLogger(__name__)


def process_file(file: Path) -> None:
    logger.info("Processing: %s", file)
    try:
        with file.open("rb") as io:
            bdr_aggregate = from_io(io)
    except PilusDeserializeError as exc:
        logger.warning("Skipping %s", file.name)
        logger.warning("Reason: %s", exc)
        return

    output = {
        "site": [],
        "lf_amplitude": [],
        "hf_amplitude": [],
        "lf_amplitude_dB": [],
        "hf_amplitude_dB": [],
        "lf_phase_rad": [],
        "hf_phase_rad": [],
    }
    for site, bdr_channels in bdr_aggregate.sites.items():
        for name, bdr_channel in bdr_channels.items():
            for fit in bdr_channel.transition_fits:
                if name == "lf":
                    output["site"].append(site)
                output[name + "_amplitude"].append(
                    sqrt(fit.re.scale**2 + fit.im.scale**2)
                )
                output[name + "_amplitude_dB"].append(
                    20 * log10(sqrt(fit.re.scale**2 + fit.im.scale**2))
                )
                output[name + "_phase_rad"].append(atan2(fit.im.scale, fit.re.scale))

    output_file = file.parent / (file.stem + ".csv")
    with output_file.open("w", newline="", encoding="utf-8") as output_handle:
        writer = csv.DictWriter(output_handle, fieldnames=output.keys())

        # Write header
        writer.writeheader()

        # Write data
        for i in range(len(output["site"])):
            row = {key: value[i] for key, value in output.items()}
            writer.writerow(row)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        description="Process .bdr files into amplitude CSVs."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to search for .bdr files (default: current dir)",
    )
    args = parser.parse_args()

    files = []
    for path in args.paths:
        p = Path(path)
        if p.is_file() and p.suffix == ".bdr":
            files.append(p)
        elif p.is_dir():
            files.extend(p.rglob("*.bdr"))

    for file in files:
        process_file(file)


if __name__ == "__main__":
    main()
