# plotit5.py

import matplotlib.pyplot as pp

import channelpack as cp

tp = cp.txtpack('sampledat2.txt')

pp.figure(figsize=(12.5, 6.5))

ax1 = pp.subplot(111)

for n in (0, 3, 4):
    ax1.plot(tp(n), label=tp.name(n))

# Eat a conf_file sitting in the same directory as the data file:
tp.eat_config()

# Make not true sections be replaced by nan's on calls:
tp.set_mask_on()

ax1.plot(tp(3), label=tp.name(3) + ' relevant', marker='o')

prop = {'size': 12}
ax1.legend(loc='upper left', prop=prop)

pp.show()
