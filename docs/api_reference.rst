channelpack API Reference
*************************

All objects and functions documented below are available by::

    import channelpack

in the `channelpack` namespace.

ChannelPack object
==================

.. autoclass:: channelpack.ChannelPack

    .. automethod:: __init__
    .. automethod:: __call__
    .. automethod:: append_pack
    .. automethod:: mask_reset
    .. automethod:: duration
    .. automethod:: startstop
    .. automethod:: parts
    .. automethod:: records
    .. automethod:: name


Functions to get a pack from data files
=======================================

Text
----

Data stored in readable text files in the form of delimited data
fields, (csv, txt). Fields might be numbers or text:

.. autofunction:: channelpack.textpack

If data is numeric only, a lazy variant is available:

.. autofunction:: channelpack.lazy_textpack

Spread sheet
------------

Code from the library `xlrd` is used, xls and xlsx types of spread
sheets are supported:

.. autofunction:: channelpack.sheetpack


About code from the xlrd project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

channelpack include code from the xlrd project copied from a checkout
of commit d470bc9374ee3a1cf149c2bab0684e63c1dcc575 and is thereby not
dependent on the xlrd project.

With the release of version 2.0.0 of xlrd, support for the xlsx format
was removed. A main reason it seems was nobody was willing to maintain
it (the xlrd project do not discourage using xlrd for xls files).
Concerns about possible vulnerabilities with the xml parsing was also
raised and since channelpack now include the code that was removed
from xlrd, some sort of re-iteration of those concerns is given here
so a potential user of channelpack can make an informed choice.

The announcement about xlrd 2.x series and the deprecation of xlsx
support can be read here

https://groups.google.com/g/python-excel/c/IRa8IWq_4zk/m/Af8-hrRnAgAJ

One issue alleged was that `defusedxml`__ and xlrd as a combination
don't work well with python 3.9. The linked defusedxml project readme
discuss the vulnerabilities with xml files it addresses. Those
vulnerabilities are also discussed in the Python docs `here`__ and in
a thread on the python bug tracker, "`XML vulnerabilities in
Python`__", discussing if it should be addressed by Python xml
libraries.

__ https://pypi.org/project/defusedxml
__ https://docs.python.org/3/library/xml.html#xml-vulnerabilities
__ https://bugs.python.org/issue17239

In short, it is possible to craft xml files so they might cause harm
or disturbance when parsing them with a parser not taking precautions
for the risk. The code from the xlrd project included in channelpack
uses defusedxml if available.

Early xlrd includes software developed by David Giffin
<david@giffin.org>.

Xbase DBF format
----------------

Legacy kind of data base format:

.. autofunction:: channelpack.dbfpack


Dewesoft data files
-------------------

Optional support for reading Dewesoft data files. Requires `dwdat2py`__
which must be installed separately.

.. autofunction:: channelpack.dwfullpack

.. autofunction:: channelpack.dwreducedpack

__ http://github.com/tomnor/dwdat2py
