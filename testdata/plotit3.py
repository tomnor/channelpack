# plotit3.py

import matplotlib.pyplot as pp

import channelpack as cp

tp = cp.txtpack('sampledat.txt')

pp.figure(figsize=(12.5, 6.5))

ax1 = pp.subplot(111)

for n in (0, 3, 4):
    ax1.plot(tp(n), label=tp.name(n))

# Add conditions to the channelpack, using start and stop:
tp.add_conditions('start_and', 'AR_BST >= 200')
tp.add_conditions('stop_and', 'VG_STOP == 90, RPT > VG_STOP')

# Make not true sections be replaced by nan's on calls:
tp.set_mask_on()

ax1.plot(tp(3), label=tp.name(3) + ' relevant', marker='o')

prop = {'size': 12}
ax1.legend(loc='upper left', prop=prop)

pp.show()
