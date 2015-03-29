import doctest
import sys
import os

of = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

if __name__ == '__main__':

    suit = sys.argv[-1].split()

    if '0' in suit:
        print '### README.rst (0)'
        f, t = doctest.testfile('../README.rst', report=True,
                                # verbose=True,
                                optionflags=of)
        if f == 0:
            print '--> fail count:', f, 'from', t, 'tests'

    if '1' in suit:
        print '### testing __init__.py (1)'
        f, t = doctest.testfile('__init__.py', package='channelpack', report=True,
                                optionflags=of)
        if f == 0:
            print '--> fail count:', f, 'from', t, 'tests'

    if '2' in suit:
        print '### testing pack.py (2)'
        f, t = doctest.testfile('pack.py', package='channelpack', report=True,
                                # verbose=True,
                                optionflags=of)
        if f == 0:
            print '--> fail count:', f, 'from', t, 'tests'

    if '3' in suit:
        print '### testing test_examples.rst (3)'
        f, t = doctest.testfile('../docs/test_examples.rst', report=True,
                                # verbose=True,
                                optionflags=of)
        if f == 0:
            print '--> fail count:', f, 'from', t, 'tests'

    if '4' in suit:
        print '### testing pullxl.py (4)'
        f, t = doctest.testfile('pullxl.py', package='channelpack', report=True,
                                # verbose=True,
                                optionflags=of)
        if f == 0:
            print '--> fail count:', f, 'from', t, 'tests'

    if '5' in suit:
        print '### overview_examples.rst (5)'
        f, t = doctest.testfile('../docs/overview_examples.rst', report=True,
                                # verbose=True,
                                optionflags=of)
        if f == 0:
            print '--> fail count:', f, 'from', t, 'tests'

    sys.path.insert(0, 'testdata')

    if '6' in suit:
        print '### testing plotit1.py (6)'
        f, t = 0, 1
        try:
            import plotit1
        except Exception as e:
            print e
            f = 1

        if f == 0:
            print '--> fail count:', f, 'from', t, 'module import'

    if '7' in suit:
        print '### testing plotit2.py (7)'
        f, t = 0, 1
        try:
            import plotit2
        except Exception as e:
            print e
            f = 1

        if f == 0:
            print '--> fail count:', f, 'from', t, 'module import'
