from pathlib import Path
import os

import numpy as np
import matplotlib.pyplot as plt

from spat.formats.bdr import Bdr

root = "C:/Users\MGD\Dropbox (SBT Instruments)\SBT R&D\Experiments/2021-10-04 Chr hansen (PLJ)\BB files/bdr\indexed"
paths = [
    "Fusobacterium - Lena - A04.bdr",
    "Pig feed - Lena - A06.bdr",
]

bdrs = []
for path in paths:
    data_file = Path(os.path.join(root, path))
    with data_file.open("rb") as io:
        bdrs.append(Bdr.from_io(io))

fig, ax = plt.subplots(1, 2, figsize=(12, 5))

for bdr in bdrs:
    ax[0].scatter(bdr.data["lf_phase"], bdr.data["hf_phase"], 6)
    ax[1].scatter(bdr.data["lf_amp"], bdr.data["hf_amp"], 6)


ax[0].set_xlabel("LF phase [rad]")
ax[0].set_ylabel("HF phase [rad]")
ax[0].grid(True)

ax[1].set_xlabel("LF amp [dB]")
ax[1].set_ylabel("HF amp [dB]")
ax[1].grid(True)

plt.show()
