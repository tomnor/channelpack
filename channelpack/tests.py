import doctest

of = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

if __name__ == '__main__':

    print '### testing __init__.py'
    f, t = doctest.testfile('__init__.py', package='channelpack', report=True,
                            optionflags=of)
    if f == 0:
        print '--> fail count:', f, 'from', t, 'tests'

    print '### testing pack.py'
    f, t = doctest.testfile('pack.py', package='channelpack', report=True,
                            # verbose=True,
                            optionflags=of)
    if f == 0:
        print '--> fail count:', f, 'from', t, 'tests'

    print '### testing test_examples.rst'
    f, t = doctest.testfile('../docs/test_examples.rst', report=True,
                            # verbose=True,
                            optionflags=of)
    if f == 0:
        print '--> fail count:', f, 'from', t, 'tests'

    print '### testing pullxl.rst'
    f, t = doctest.testfile('pullxl.py', package='channelpack', report=True,
                            # verbose=True,
                            optionflags=of)
    if f == 0:
        print '--> fail count:', f, 'from', t, 'tests'
