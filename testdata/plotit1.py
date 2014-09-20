# plotit1.py

import matplotlib.pyplot as pp

import channelpack as cp

tp = cp.txtpack('sampledat.txt')

pp.figure(figsize=(12.5, 6.5))

ax1 = pp.subplot(111)

for n in (0, 3, 4):
    ax1.plot(tp(n), label=tp.name(n))

prop = {'size': 12}
ax1.legend(loc='upper left', prop=prop)

pp.show()
