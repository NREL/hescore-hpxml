'''
Created on Oct 23, 2014

@author: nmerket
'''
import os
import json
import unittest
from lxml import etree
from copy import deepcopy
from hpxml_to_hescore import HPXMLtoHEScoreTranslator, TranslationError

thisdir = os.path.dirname(os.path.abspath(__file__))
exampledir = os.path.abspath(os.path.join(thisdir,'..','examples'))

class ComparatorBase(object):
    
    def _load_xmlfile(self,filebase):
        xmlfilepath = os.path.join(exampledir,filebase + '.xml')
        self.translator = HPXMLtoHEScoreTranslator(xmlfilepath)
        return self.translator
    
    def _do_compare(self,filebase):
        hescore_trans = self.translator.hpxml_to_hescore_dict()
        jsonfilepath = os.path.join(exampledir,filebase + '.json')
        with open(os.path.join(exampledir,jsonfilepath)) as f:
            hescore_truth = json.load(f)
        self.assertEqual(hescore_trans, hescore_truth, '{} not equal'.format(filebase))

    def _do_full_compare(self,filebase):
        self._load_xmlfile(filebase)
        self._do_compare(filebase)
    
    

class TestAPIHouses(unittest.TestCase,ComparatorBase):
    
    def test_house1(self):
        self._do_full_compare('house1')
    
    def test_house1a(self):
        self._do_full_compare('house1a')
    
    def test_house2(self):
        self._do_full_compare('house2')
    
    def test_house3(self):
        self._do_full_compare('house3')
    
    def test_house4(self):
        self._do_full_compare('house4')
    
    def test_house5(self):
        self._do_full_compare('house5')
    
    def test_house6(self):
        self._do_full_compare('house6')

class TestOtherHouses(unittest.TestCase,ComparatorBase):

    def test_hescore_min(self):
        self._do_full_compare('hescore_min')
    
    def test_townhouse_walls(self):
        self._do_full_compare('townhouse_walls')
    
    def test_townhouse_wall_fail(self):
        tr = self._load_xmlfile('townhouse_walls')
        el = tr.doxpath(tr.hpxmldoc, '//h:Window/h:Orientation[text()="south"]')
        el.text = 'east'
        self.assertRaisesRegexp(TranslationError, 
                                r'The house has windows on shared walls\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_siding(self):
        tr = self._load_xmlfile('hescore_min')
        siding = tr.doxpath(tr.hpxmldoc,'//h:Wall[1]/h:Siding')
        siding.getparent().remove(siding)
        self.assertRaisesRegexp(TranslationError, 
                                r'Exterior finish information is missing',
                                tr.hpxml_to_hescore_dict)
        
        
    def test_siding_fail2(self):
        tr = self._load_xmlfile('hescore_min')
        siding = tr.doxpath(tr.hpxmldoc, '//h:Wall[1]/h:Siding')
        siding.text = 'other'
        self.assertRaisesRegexp(TranslationError, 
                                r'There is no HEScore wall siding equivalent for the HPXML option: other',
                                tr.hpxml_to_hescore_dict)
    
    def test_siding_cmu_fail(self):
        tr = self._load_xmlfile('hescore_min')
        walltype = tr.doxpath(tr.hpxmldoc, '//h:Wall[1]/h:WallType')
        walltype.clear()
        etree.SubElement(walltype, tr.addns('h:ConcreteMasonryUnit'))
        siding = tr.doxpath(tr.hpxmldoc, '//h:Wall[1]/h:Siding')
        siding.text = 'vinyl siding'
        self.assertRaisesRegexp(TranslationError, 
                                r'is a CMU and needs a siding of stucco, brick, or none to translate to HEScore. It has a siding type of vinyl siding', 
                                tr.hpxml_to_hescore_dict)
    
    def test_log_wall_fail(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:Wall[1]/h:WallType')
        el.clear()
        etree.SubElement(el, tr.addns('h:LogWall'))
        self.assertRaisesRegexp(TranslationError, 
                                r'Wall type LogWall not supported',
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_residential_facility_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:ResidentialFacilityType')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError,
                                r'ResidentialFacilityType is required in the HPXML document',
                                tr.hpxml_to_hescore_dict)
    
    def test_invalid_residential_faciliy_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:ResidentialFacilityType')
        el.text = 'manufactured home'
        self.assertRaisesRegexp(TranslationError,
                                r'Cannot translate HPXML ResidentialFacilityType of .+ into HEScore building shape',
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_surroundings(self):
        tr = self._load_xmlfile('townhouse_walls')
        el = tr.doxpath(tr.hpxmldoc, '//h:Surroundings')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                r'Site/Surroundings element is required in the HPXML document for town houses', 
                                tr.hpxml_to_hescore_dict)
    
    def test_invalid_surroundings(self):
        tr = self._load_xmlfile('townhouse_walls')
        el = tr.doxpath(tr.hpxmldoc, '//h:Surroundings')
        el.text = 'attached on three sides'
        self.assertRaisesRegexp(TranslationError, 
                                r'Cannot translate HPXML Site/Surroundings element value of .+ into HEScore town_house_walls', 
                                tr.hpxml_to_hescore_dict)
    
    def test_attic_roof_assoc(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:Attic[1]/h:AttachedToRoof')
        el.getparent().remove(el)
    
    def test_invalid_attic_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:Attic[1]/h:AtticType')
        el.text = 'other'
        self.assertRaisesRegexp(TranslationError, 
                                'Attic .+ Cannot translate HPXML AtticType .+ to HEScore rooftype.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_roof_color(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:Roof[1]/h:RoofColor')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'Attic .+ Invalid or missing RoofColor', 
                                tr.hpxml_to_hescore_dict)
    
    def test_invalid_roof_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:Roof[1]/h:RoofType')
        el.text = 'no one major type'
        self.assertRaisesRegexp(TranslationError, 
                                'Attic .+ HEScore does not have an analogy to the HPXML roof type: .+', 
                                tr.hpxml_to_hescore_dict)
        
    def test_missing_roof_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:Roof[1]/h:RoofType')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'Attic .+ HEScore does not have an analogy to the HPXML roof type: .+', 
                                tr.hpxml_to_hescore_dict)

    def test_missing_skylight_area(self):
        tr = self._load_xmlfile('hescore_min')
        area = tr.doxpath(tr.hpxmldoc, '//h:Skylight[1]/h:Area')
        area.getparent().remove(area)
        self.assertRaisesRegexp(TranslationError, 
                                'Every skylight needs an area\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_foundation_walls_on_slab(self):
        tr = self._load_xmlfile('house6')
        fnd = tr.doxpath(tr.hpxmldoc, '//h:Foundation[name(h:FoundationType/*) = "SlabOnGrade"]')
        for i,el in enumerate(fnd):
            if el.tag.endswith('Slab'):
                break
        fndwall = etree.Element(tr.addns('h:FoundationWall'))
        etree.SubElement(fndwall, tr.addns('h:SystemIdentifier'), attrib={'id': 'asdfjkl12345'})
        fnd.insert(i,fndwall)
        self.assertRaisesRegexp(TranslationError, 
                                'The house is a slab on grade foundation, but has foundation walls\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_window_area(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:Window[1]/h:Area')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'All windows need an area\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_window_orientation(self):
        tr = self._load_xmlfile('hescore_min')
        el = tr.doxpath(tr.hpxmldoc, '//h:Window[1]/h:Orientation')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'All windows need to have either an AttachedToWall, Orientation, or Azimuth sub element\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_window_attached_to_wall(self):
        filebase = 'house5'
        tr = self._load_xmlfile(filebase)
        # Get the first wall id
        wallid = tr.doxpath(tr.hpxmldoc, '//h:Wall[1]/h:Orientation/parent::node()/h:SystemIdentifier/@id')
        # get the orientation of the wall
        orientation = tr.doxpath(tr.hpxmldoc, '//h:Wall[h:SystemIdentifier/@id=$wallid]/h:Orientation/text()',wallid=wallid)
        # get the window orientation element of a window that is facing the same direction as the wall
        window_orientation = tr.doxpath(tr.hpxmldoc, '//h:Window[h:Orientation=$orientation][1]/h:Orientation',orientation=orientation)
        # remove the window orientation
        window = window_orientation.getparent()
        window.remove(window_orientation)
        # attach that window to the wall
        etree.SubElement(window, tr.addns('h:AttachedToWall'), attrib={'idref': wallid})
        self._do_compare(filebase)
        
        
        
        

if __name__ == "__main__":
    unittest.main()
    