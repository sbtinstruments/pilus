from pathlib import Path

import matplotlib.pyplot as plt

from spat.formats import iqs

from spat.numerics import iqs_to_numpy_array, iqs_timestamp_array

data_file = Path("/home/jonatan/Downloads/test of flowcells with and without filter/bb2017025/1B511-D6Q/measure-20210809-145431-A79.iqs")
with data_file.open("rb") as io:
    data = iqs.from_io(io)

site0 = data.idat.sites['site0']
site0_lf = site0['lf']
site0_lf_re = site0_lf.re

#numbers = [b for b in site0_lf_re]
a = iqs_to_numpy_array(data)
t = iqs_timestamp_array(data)

plt.figure(1)

plt.plot(t, a[0,0,0,:])
plt.show()