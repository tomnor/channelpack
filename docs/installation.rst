
Installation
************

channelpack requires `numpy <https://pypi.python.org/pypi/numpy>`_, but does not
attempt to install that for you during installation. It's not a huge deal to
install numpy, but maybe not trivial either, and there might be reasons you
prefer to do that yourself.

Get channelpack
===============

channelpack is on pypi: https://pypi.python.org/pypi/channelpack

And in a repo at Github: https://github.com/tomnor/channelpack

Install
=======

Download from pypi, unpack, and cd to the unpacked directory with setup.py in
it:
    ``python setup.py install``

If you have `pip <https://pypi.python.org/pypi/pip/>`_ or `easy_install
<https://pypi.python.org/pypi/setuptools>`_ and are not restricted by strange IT
environment:

    ``pip install channelpack``
or

    ``easy_install channelpack``

If strange IT environment, the recommended way is the first given, meaning
download the package from pypi and do ``python setup.py install``. A strange IT
environment is a place where you can download things to your computer using
your browser, but trying `pip` or `easy_install` will fail, even if you are some sort
of "admin".
