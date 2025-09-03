from pathlib import Path
from math import sqrt, log10, atan2
import csv
import argparse

from pilus.sbt import bdr_from_io as from_io
from pilus.errors import PilusDeserializeError


def process_file(file: Path):
    print("Processing: ", file)
    try:
        with file.open("rb") as io:
            bdr_aggregate = from_io(io)
    except PilusDeserializeError as exc:
        print(f"Skipping {file.name}")
        print(f"Reason: {str(exc)}")

    output = {"site": [], "lf_amplitude": [], "hf_amplitude": [], "lf_amplitude_dB": [], "hf_amplitude_dB": [], "lf_phase_rad": [], "hf_phase_rad": [] }
    for site, bdr_channels in bdr_aggregate.sites.items():
        for name, bdr_channel in bdr_channels.items():
            for fit in bdr_channel.transition_fits:
                if name == "lf":
                    output["site"].append(site)
                output[name + "_amplitude"].append(
                    sqrt(fit.re.scale**2 + fit.im.scale**2)
                )
                output[name + "_amplitude_dB"].append(
                    20*log10(sqrt(fit.re.scale**2 + fit.im.scale**2))
                )
                output[name + "_phase_rad"].append(
                    atan2(fit.im.scale, fit.re.scale)
                )

    OUTPUT_FILE = file.parent / (file.stem + ".csv")
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=output.keys())

        # Write header
        writer.writeheader()

        # Write data
        for i in range(len(output["site"])):
            row = {key: value[i] for key, value in output.items()}
            writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description="Process .bdr files into amplitude CSVs.")
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