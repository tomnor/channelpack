from setuptools import setup, find_packages
import codecs
import os
import re

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()

def find_version(*parts):
    version_file = read(*parts)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

long_description = read('README.rst')

setup(
    name='channelpack',
    version=find_version('channelpack', '__init__.py'),
    description='Package for loading, analyzing and slicing acqusition data',
    long_description=long_description,
    url='https://github.com/tomnor/channelpack',
    author='Tomas Nordin',
    author_email='tomasn@kth.se',
    license='GPLv3+',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2',
        ],
    keywords='data-mining datafile daq masking conditions evaluation ad-hoc',
    packages=['channelpack'],
    # Requires numpy but channelpack choose not to provide
    install_requires=['xlrd'],
)
