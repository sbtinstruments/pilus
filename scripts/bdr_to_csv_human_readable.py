from pathlib import Path
from math import sqrt
import csv

from pilus.formats.bdr import from_io
from pilus.errors import PilusDeserializeError

root = Path("/mnt/c/Users/mgd/Downloads/peter_bdr_to_csv/measurements/")
files = root.rglob("*.bdr")

for file in files:
    print(file)
    try:
        with file.open("rb") as io:
            bdr_aggregate = from_io(io)
    except PilusDeserializeError as exc:
        print(f"Skipping {file.name}")
        print(f"Reason: {str(exc)}")

    output = {"site": [], "lf_amplitude": [], "hf_amplitude": []}
    for site, bdr_channels in bdr_aggregate.sites.items():
        for name, bdr_channel in bdr_channels.items():
            for fit in bdr_channel.transition_fits:
                if name == "lf":
                    output["site"].append(site)
                output[name + "_amplitude"].append(
                    sqrt(fit.re.scale**2 + fit.im.scale**2)
                )

    OUTPUT_FILE = root / (file.stem + ".amps.csv")
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=output.keys())

        # Write header
        writer.writeheader()

        # Write data
        for i in range(len(output["site"])):
            row = {key: value[i] for key, value in output.items()}
            writer.writerow(row)
