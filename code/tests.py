'''
Created on Oct 23, 2014

@author: nmerket
'''
import os
import json
import unittest
from hpxml_to_hescore import HPXMLtoHEScoreTranslator, TranslationError

thisdir = os.path.dirname(os.path.abspath(__file__))
exampledir = os.path.abspath(os.path.join(thisdir,'..','examples'))

class ComparatorBase(object):

    def _convert_hpxml(self,filebase):
        xmlfilepath = os.path.join(exampledir,filebase + '.xml')
        translator = HPXMLtoHEScoreTranslator(xmlfilepath)
        return translator.hpxml_to_hescore_dict()
        
    def _do_compare(self,filebase):
        jsonfilepath = os.path.join(exampledir,filebase + '.json')
        hescore_trans = self._convert_hpxml(filebase)
        with open(os.path.join(exampledir,jsonfilepath)) as f:
            hescore_truth = json.load(f)
        self.assertEqual(hescore_trans, hescore_truth, '{} not equal'.format(filebase))
    

class TestAPIHouses(unittest.TestCase,ComparatorBase):
    
    def test_house1(self):
        self._do_compare('house1')
    
    def test_house1a(self):
        self._do_compare('house1a')
    
    def test_house2(self):
        self._do_compare('house2')
    
    def test_house3(self):
        self._do_compare('house3')
    
    def test_house4(self):
        self._do_compare('house4')
    
    def test_house5(self):
        self._do_compare('house5')
    
    def test_house6(self):
        self._do_compare('house6')

class TestOtherHouses(unittest.TestCase,ComparatorBase):

    def test_hescore_min(self):
        self._do_compare('hescore_min')
    
    def test_townhouse_walls(self):
        self._do_compare('townhouse_walls')
    
    def test_townhouse_wall_fail(self):
        self.assertRaisesRegexp(TranslationError, 
                                r'The house has windows on shared walls\.', 
                                self._convert_hpxml, 'townhouse_walls_fail')
        

if __name__ == "__main__":
    unittest.main()
    