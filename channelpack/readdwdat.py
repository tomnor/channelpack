"""
Functions to read Dewesoft data files.
"""
import numpy as np

from dwdat2py import wrappersimport
import channelpack as cp


def dwfullpack(dwfile, channels=None):
    """Return a ChannelPack instance for `dwfile`.

    One time sequence is added to the pack on key 0, with the name
    Time-<channelname>. If a time sequence for another channel is
    different to any time sequence already added, it is added before
    that channel with the name Time-<anotherchannel>.

    Parameters
    ----------
    dwfile : str
        Filename of the .d7d, .dzd or other dewesoft data file.

    channels : seq of int or str
        If given, load only the given channels. Elements is either the
        channel names or the channel indexes.

    """
    packtimekeys = []              # timechannels added to the pack
    pack = cp.ChannelPack()

    def alreadyin(time):
        if not len(packtimekeys) > 0:
            return False

        samelenskeys = [ch for ch in packtimekeys
                        if len(pack(ch)) == len(time)]
        if not samelenskeys:
            return False

        return any([np.all(time == pack(ch)) for ch in samelenskeys])

    with wrappersimport(dwfile) as w:
        for i, ch in enumerate(w.get_channel_list()):
            if (channels is not None and
                not any((ch.index in channels, ch.name in channels))):
                continue
            if ch.array_size > 1:
                continue        # not doing array channels here

            keyoffset = len(packtimekeys)
            count = w.get_scaled_samples_count(ch.index)
            if not count:
                continue

            time, data = w.get_scaled_samples(ch.index, 0, count, array_size=1)
            if not alreadyin(time):
                pack.data[i + keyoffset] = time
                pack.names[i + keyoffset] = 'Time-' + ch.name
                packtimekeys.append(i + keyoffset)
                keyoffset = len(packtimekeys)

            pack.data[i + keyoffset] = data
            pack.names[i + keyoffset] = ch.name

    pack.fn = dwfile
    return pack


def dwreducedpack(dwfile, channels=None, reduction=1):
    """Return a ChannelPack instance for `dwfile`.

    One time sequence is added to the pack on key 0, with the name
    Time-<channelname>. If a time sequence for another channel is
    different to any time sequence already added, it is added before
    that channel with the name Time-<anotherchannel>.

    Parameters
    ----------
    dwfile : str
        Filename of the .d7d, .dzd or other dewesoft data file.

    channels : seq of int or str
        If given, load only the given channels. Elements is either the
        channel names or the channel indexes.

    reduction : int
        The reduction of respective channel, one of:

        | 1 -> average
        | 2 -> min
        | 3 -> max
        | 4 -> rms

    """
    packtimekeys = []              # timechannels added to the pack
    pack = cp.ChannelPack()

    def alreadyin(time):
        if not len(packtimekeys) > 0:
            return False

        samelenskeys = [ch for ch in packtimekeys
                        if len(pack(ch)) == len(time)]
        if not samelenskeys:
            return False

        return any([np.all(time == pack(ch)) for ch in samelenskeys])

    with wrappersimport(dwfile) as w:
        for i, ch in enumerate(w.get_channel_list()):
            if (channels is not None and
                not any((ch.index in channels, ch.name in channels))):
                continue
            if ch.array_size > 1:
                continue        # not doing array channels here

            keyoffset = len(packtimekeys)
            count, _ = w.get_reduced_values_count(ch.index)
            if not count:
                continue

            # datarecs: [(time_stamp, ave, min, max, rms), ..]
            time, ave, minvals, maxvals, rms = \
                zip(*w.get_reduced_values(ch.index, 0, count))

            if not alreadyin(time):
                pack.data[i + keyoffset] = time
                pack.names[i + keyoffset] = 'Time-' + ch.name
                packtimekeys.append(i + keyoffset)
                keyoffset = len(packtimekeys)

            pack.data[i + keyoffset] = (time, ave, minvals,
                                        maxvals, rms)[reduction]
            pack.names[i + keyoffset] = ch.name

    pack.fn = dwfile
    return pack
