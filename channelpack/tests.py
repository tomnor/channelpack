import doctest

of = doctest.NORMALIZE_WHITESPACE

if __name__ == '__main__':

    print '### testing __init__.py'
    failcnt, testcnt = doctest.testfile('__init__.py',
                                        package='channelpack',
                                        report=True,
                                        optionflags=of)
    if failcnt == 0:
        print '--> fail count:', failcnt, 'from', testcnt, 'tests'

    print '### testing pack.py'
    failcnt, testcnt = doctest.testfile('pack.py',
                                        package='channelpack',
                                        report=True,
                                        optionflags=of)
    if failcnt == 0:
        print '--> fail count:', failcnt, 'from', testcnt, 'tests'
