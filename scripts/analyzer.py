import os
import json
import re
import matplotlib.pyplot as plt
import numpy as np

dir_path = os.path.dirname(os.path.realpath(__file__))

def fill_data(p, theory_conc, measured_conc, flow_rate, extrema):
  for file in os.listdir(dir_path + p):
      if file.endswith(".json"):
        with open(os.path.join(dir_path + p, file)) as f:
          data = json.load(f)
          measured_conc.append(data['analysis']['concentration']['sampleVolume']['nonbacteria'])
          x0 = re.findall("2.m[_|\s]([\d|,]+e\d).*", file)
          x1 = re.sub(",", ".", x0[0])
          theory_conc.append(float(x1))
          flow_rate.append(float(data['analysis']['flowRate']))
          extrema.append(data['algResult']['extrema']['count']['hfRe'])




data_dir_new = "/bb2017035_new algorithms/2 µm"
data_dir_old = "/bb2045007_old algorithms/2 µm"

measured_conc_old = []
theory_conc_old = []
measured_conc_new = []
theory_conc_new = []
flow_rate_old = []
flow_rate_new = []

extrema_old = []
extrema_new = []

fill_data(data_dir_old, theory_conc_old, measured_conc_old, flow_rate_old, extrema_old)
fill_data(data_dir_new, theory_conc_new, measured_conc_new, flow_rate_new, extrema_new)

tube_conc = 40000

def make_conc_plot():
  fig, axs = plt.subplots(2)
  fig.suptitle('2 um beads')
  axs[0].plot(theory_conc_old, [a - tube_conc for a in measured_conc_old], 'o', color='blue')
  axs[0].plot(theory_conc_new, [a - tube_conc for a in measured_conc_new], 'o', color='red')
  axs[0].plot(np.linspace(0, max(theory_conc_old),100), np.linspace(0, max(theory_conc_old),100), '-', color='black')
  axs[0].plot(np.linspace(0, max(theory_conc_old),100), np.linspace(0, 1.3 * max(theory_conc_old),100), '--', color='grey')
  axs[0].plot(np.linspace(0, max(theory_conc_old),100), np.linspace(0, 0.7 * max(theory_conc_old),100), '--', color='grey')
  axs[0].set_yscale("log")
  axs[0].set_xscale("log")

  axs[1].plot(theory_conc_old, flow_rate_old, 'o', color='blue')
  axs[1].plot(theory_conc_new, flow_rate_new, 'o', color='red')
  axs[1].set_xscale("log")
  plt.show()

def make_extrema_plot():
  fig, axs = plt.subplots(2)
  fig.suptitle('2 um beads')
  axs[0].plot(theory_conc_old, extrema_old, 'o', color='blue')
  axs[0].plot(theory_conc_new, extrema_new, 'o', color='red')
  
  axs[0].set_yscale("log")
  axs[0].set_xscale("log")
  plt.show()

make_extrema_plot()