# plotit2.py

import matplotlib.pyplot as pp

import channelpack as cp

tp = cp.txtpack('sampledat.txt')

pp.figure(figsize=(12.5, 6.5))

ax1 = pp.subplot(111)

for n in (0, 3, 4):
    ax1.plot(tp(n), label=tp.name(n))

# Add conditions to the channelpack:
tp.add_conditions('and', 'RPT > AR_BST')
tp.add_conditions('or', 'VG_STOP == 70, VG_STOP == 90')

# Make not true sections be replaced by nan's on calls:
tp.set_mask_on()

ax1.plot(tp(4), label=tp.name(4) + ' relevant', marker='x')

prop = {'size': 12}
ax1.legend(loc='upper left', prop=prop)

pp.show()
