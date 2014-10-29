'''
Created on Oct 23, 2014

@author: nmerket
'''
import os
import json
import unittest
from hpxml_to_hescore import HPXMLtoHEScoreTranslator

thisdir = os.path.dirname(os.path.abspath(__file__))
exampledir = os.path.abspath(os.path.join(thisdir,'..','examples'))

class TestAPIHouses(unittest.TestCase):
    
    def _do_compare(self,filebase):
        xmlfilepath = os.path.join(exampledir,filebase + '.xml')
        jsonfilepath = os.path.join(exampledir,filebase + '.json')
        translator = HPXMLtoHEScoreTranslator(xmlfilepath)
        hescore_trans = translator.hpxml_to_hescore_dict()
        with open(os.path.join(exampledir,jsonfilepath)) as f:
            hescore_truth = json.load(f)
        self.assertEqual(hescore_trans, hescore_truth, '{} not equal'.format(filebase))
        
    def test_house1(self):
        self._do_compare('house1')
    
    def test_house1a(self):
        self._do_compare('house1a')

if __name__ == "__main__":
    unittest.main()
    