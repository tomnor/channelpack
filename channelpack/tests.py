import doctest

if __name__ == '__main__':

    doctest.testfile('__init__.py', package='channelpack')
    doctest.testfile('pack.py', package='channelpack')
