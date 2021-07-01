from pandas.core import series
import altair as alt
import pandas as pd
import numpy as np
import scipy.stats as stats
import os
import re


alt.renderers.enable('altair_viewer')
alt.data_transformers.disable_max_rows()

ges_data = False
lower_min = True

# Build up a pandas dataframe with the data we want. Traverse the directory, looking for 'transitions.csv'-files, extracting, transforming and loading as we go.

def iam(data: pd.Series, quantile=0.25):
    q = data.quantile([quantile, 1-quantile])  # calculate lower and upper bounds
    masked = data[~data.clip(*q).isin(q)]
    return masked.mean()

get_ps_ges = re.compile(r'PS\s([0-9]{2})')

get_id_p = re.compile(r'(C93|C94|C95|C96|C97|C98|C99|D00)\/')
id2ps = {'C93': 8,
        'C94': 14,
        'C95': 20,
        'C96': 26,
        'C97': 26,
        'C98': 20,
        'C99': 14,
        'D00': 8}

pumpspeeds = []
i = 0

transition_times = None


if ges_data == True:
    root_dir = "/media/jonatan/20BCC727BCC6F5F6/FromUbuntu/pump_speeds/2021-06-03 Underestimation investigation with beads/processed"
else:
    root_dir = "/media/jonatan/20BCC727BCC6F5F6/FromUbuntu/pump_speeds/2021-06-04 Pump speed listeria coli 1;10 PBS/processed"

if lower_min == True:
    root_dir = root_dir + "_lower_min"

# Traverse tree
for root, dirs, files in os.walk(root_dir, topdown=False):
    for name in files:
        if name.endswith('transitions.csv'):
            # Open csv file
            filename = os.path.join(root, name)
            print(filename)
            tt = pd.read_csv(filename)
            # Add measurement ID
            short_filename = '/'.join(filename.split('/')[-3:-1])
            tt['measurement'] = short_filename

            # Add pumpspeed
            if ges_data == True:
                ps_re = get_ps_ges.search(filename)
                ps = float(ps_re.group(1))
                pumpspeeds.append(ps)
            else:
                id_re = get_id_p.search(filename)
                if id_re is not None:
                    id = id_re.group(1)
                    ps = id2ps[id]
                else:
                    ps = 20
            tt['pumpspeed'] = ps
            
            # Add flow rate estimate
            tt['iam'] = iam(tt['high_real.transition.offset'], quantile=0.25)
            # Append
            if transition_times is None:
                transition_times = tt
            else:
                transition_times = transition_times.append(tt, ignore_index=True)
            
            

# Take care of annoying naming
transition_times = transition_times.rename(columns={'high_real.transition.offset': 'high_real_transition_offset'})

selector = alt.selection_single(empty='all', fields=['measurement'])
highlight = alt.selection_single(on='mouseover', fields=['measurement'], empty='none')

color_scale = alt.Scale(domain=[6, 40],
                        range=['#1FC3AA', '#8624F5'])


base = alt.Chart(transition_times).properties(
    width=500,
    height=500
)

points = base.add_selection(selector).mark_point(filled=True, size=200).encode(
    x=alt.X('pumpspeed:Q'),
    y=alt.Y('measurement:N'),
    color=alt.condition(selector,
                        'pumpspeed:Q',
                        alt.value('lightgray'),
                        scale=color_scale),
    tooltip=['measurement', 'pumpspeed', 'count():Q']                    
).interactive()

hists_data= base.transform_filter(
    selector
).transform_joinaggregate(
    total='count(*)',
    groupby=['measurement']
).transform_calculate(
    pct='1 / datum.total'
).mark_bar(opacity=0.5, thickness=100).encode(
    alt.X('high_real_transition_offset:Q', bin=alt.Bin(step=20000), scale=alt.Scale(domain=[160000, 800000])),
    alt.Y('sum(pct):Q', axis=alt.Axis(format='%')),
    color=alt.Color('pumpspeed:Q',
                    scale=color_scale)
)

line_min = alt.Chart(pd.DataFrame({'x': [250000]})).mark_rule().encode(x='x')
line_max = alt.Chart(pd.DataFrame({'x': [750000]})).mark_rule().encode(x='x')


# hists_text = base.transform_filter(
#     selector
# ).transform_calculate(
#     num_transitions='datum.total'
# ).mark_text(align='right', dx=5, dy=-5).encode(
#     text="num_transitions:N"
# )

hists = alt.layer(hists_data, line_min, line_max)

concentrations = base.add_selection(selector).transform_joinaggregate(
    total='count(*)',
    groupby=['measurement']
).transform_calculate(
    #yval='datum.total / datum.pumpspeed'
    yval = 'datum.total * datum.iam'
).mark_point(filled=True, size=150).encode(
    x=alt.X('pumpspeed:Q'),
    y=alt.Y('yval:Q'),   ## = count() / pumpspeed                  
    color=alt.condition(selector,
                        'pumpspeed:Q',
                        alt.value('lightgray'),
                        scale=color_scale),
    tooltip=['measurement', 'pumpspeed', 'count():Q']
).interactive()

final_chart = (points | concentrations | hists).properties(title=f'GES data: {ges_data} & lower_min: {lower_min}')
final_chart.save('chart.html')
final_chart.show()
