# HPXML to Home Energy Score Translator

This translator script takes an HPXML file or directory of files as an input 
and generates HEScore inputs from it. The HEScore inputs are exported as json. 

Details of the translation assumptions as well instructions for use can be found in [the documentation](http://hescore-hpxml.readthedocs.org/en/latest/).

Instructions on how to run the script are available from the command line by 
typing in:

```
python hpxml_to_hescore.py -h
```

## Software Requirements

It is recommended to run this script with [Python 2.7](https://www.python.org/downloads/). 
It can be run in older versions, but the json output will be out of order. 
Also you will need to install an additional dependency.

The following libraries are needed to run it:

 * [lxml](http://lxml.de/): Handles all the xml processing.
 * [argparse](https://pypi.python.org/pypi/argparse): *Only needed if not using Python 2.7*. Handles the command line argument processing. 

If you have pip installed on top of python you can install these by going to
your terminal and typing in

```
pip install lxml
```

Otherwise, just Google it and you can find distributions for your platform. 

## NREL Assumptions

The `--nrelassumptions` flag activates some assumptions we make to have our files run
that you probably don't want in a production environment.
