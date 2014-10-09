# HPXML to Home Energy Score Translator

This translator script takes an HPXML file or directory of files as an input 
and generates HEScore inputs from it. The HEScore inputs are exported as json. 

Details of the translation assumptions can be found in [the documentation](http://hescore-hpxml.readthedocs.org/en/latest/).

To run this script you will need the following python library:

 * [lxml](http://lxml.de/): handles all the xml processing.

If you have pip installed on top of python you can install these by going to
your terminal and typing in

```
pip install lxml
```

Otherwise, just Google it and you can find distributions for your platform. 

Instructions on how to run the script are available from the command line by 
typing in:

```
python hpxml_to_hescore.py -h
```

The `--nrelassumptions` flag activates some assumptions we make to have our files run
that you probably don't want in a production environment.
