Usage Instructions
##################

The HPXML to Home Energy Score (HEScore) translator can be run hosted through the :ref:`HEScore API <hescoreapi>` or :ref:`directly on your local machine <stand-alone>`.
Most users will find that the HEScore API is the preferred method since it easily fits into the API workflow and automates the process.
The stand alone method is mostly for developers needing to debug and track down problems in the translation as well as for those who want to make modifications to the translation assumptions and code.

.. _hescoreapi:

Home Energy Score API
*********************

The HEScore API provides the most generally applicable way use HPXML to generate a Home Energy Score.
Generally in the API is used by doing the following steps, calling each API method in order:

#. ``submit_address`` - Creates a new building and assessment date.
#. ``submit_inputs`` - Submit a detailed house description in a format specific to Home Energy Score.
#. ``calculate_base_building`` - Calculates the energy use of the as-described building.
#. ``commit_results`` - Locks the inputs and marks them as being accurate by the Qualified Assessor.
#. ``calculate_package_building`` - Analyzes a set of retrofit upgrades that are screened against standardized costs, and determines the most cost effective ones.
#. ``generate_label`` - Creates a PDF and PNG Home Energy Score label.

There are other options and reports available, but that is the general gist of it.
The HPXML translator is made available through a separate API method: ``submit_hpxml_inputs``.
It replaces the first two steps above, alleviating the need to translate data elements from your data structure into the HEScore data structure.

``submit_hpxml_inputs`` accepts an HPXML file as a `Base64 <http://en.wikipedia.org/wiki/Base64>`_ encoded payload, so you will need to convert it.
An example of how to do this in Python is:

.. code:: python

    import base64

    with open('path/to/hpxmlfile.xml','r') as f:
        hpxml_as_base64 = base64.standard_b64encode(f.read())

Similar libraries and functionality exist in many languages.

Much more information on how to use the HEScore API including the ``submit_hpxml_inputs`` method is available on the `LBL Home Energy Scoring Tool API Documentation site <https://developers.buildingsapi.lbl.gov/hescore>`_.

.. _stand-alone:

Stand Alone
***********

The HPXML to HEScore translator that is used within the :ref:`hescoreapi` can be used independently as well.
It is a Python script that accepts an HPXML file as input and returns a JSON file with HEScore inputs arranged like the HEScore API call ``submit_inputs`` expects.
It it useful to run it this way for debugging a translation of your particular flavor of HPXML file or for development of the translator.

Set Up
======

First, get a copy of the `source code from GitHub <https://github.com/NREL/hescore-hpxml>`_, using your preferred method.
If you're not sure, just click "Download ZIP".

The program runs using `Python 2.7 <https://www.python.org/>`_. Python 2.6 will work, but the outputs will be all out of order.
It also requires the `lxml <http://lxml.de/>`_ Python library for parsing the xml file, and the argparse module if you're using Python 2.6.
Below are some instructions depending on platform to get the required programs and libraries if you need help.

Windows
-------

#. `Download Python 2.7.10 from python.org <https://www.python.org/downloads/>`_ and Install. 
#. Add ``C:\Python27`` to your path. `Here's how. <http://superuser.com/questions/143119/how-to-add-python-to-the-windows-path>`
#. Figure out whether you have the 32-bit or 64-bit version of python. 
   Open the command line `cmd.exe`.
   Type in `python`. The first line returned should be something like 
   ``Python 2.7.9 (default, Dec 10 2014, 12:24:55) [MSC v.1500 32 bit (Intel)] on win32``.
   Type in ``quit()``. Press Enter.
#. `Download a precompiled lxml binary <http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml>`_.
   Make sure it matches your version of Python and windows architecture 
   (``lxml-x.x.x-cp27-none-win32.whl`` or ``lxml-x.x.x-cp27-none-win_amd64.whl``).
#. Install lxml using pip. Back in your command line window type: 
   ``pip install C:\path\to\lxml-x.x.x-cp27-none-win32.whl``.

Mac OS X
--------

#. Install `Homebrew <http://brew.sh/>`_.
#. Open a terminal.
#. Install Python 2.7 using homebrew: ``brew install python``
#. Install lxml using pip: ``pip install lxml``

Linux
-----

You don't need help.

Running the Translator
======================

The best way to figure out how to run the translator is to call it with the ``-h`` flag.

.. code::

    python hpxml_to_hescore.py -h

It is pretty self-explanatory::

    usage: hpxml_to_hescore.py [-h] [-o OUTPUT] [--bldgid BLDGID]
                               [--nrelassumptions]
                               hpxml_input

    Convert HPXML v1.1.1 or v2.x files to HEScore inputs

    positional arguments:
      hpxml_input           Filename of hpxml file

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTPUT, --output OUTPUT
                            Filename of output file in json format. If not
                            provided, will go to stdout.
      --bldgid BLDGID       HPXML building id to score if there are more than one
                            <Building/> elements. Default: first one.
      --nrelassumptions     Use the NREL assumptions to guess at data elements
                            that are missing.




The ``--nrelassumptions`` flag activates some assumptions we make to have our files run that you probably don't want in a production environment.