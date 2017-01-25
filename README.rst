HPXML to Home Energy Score Translator
=====================================

This translator script takes an HPXML file or directory of files as an input and generates HEScore inputs from it. The HEScore inputs are exported as json.

Details of the translation assumptions as well instructions for use can be found in `the documentation <http://hescore-hpxml.readthedocs.org/en/latest/>`_.

Installation
------------

Use a `virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_. (Good idea, but not strictly required.)

Install using pip::

    pip install hescore-hpxml

To get the latest and greatest, clone this repository, cd into the directory and install as follows::

    pip install -e .


How to use
----------

Use the command line script::

    hpxml2hescore examples/house1.xml

To get some guidance on how to use the script::

    hpxml2hescore -h

