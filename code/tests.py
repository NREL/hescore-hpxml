'''
Created on Oct 23, 2014

@author: nmerket
'''
import os
import json
import unittest
import datetime as dt
from lxml import etree
from hpxml_to_hescore import HPXMLtoHEScoreTranslator, TranslationError, InputOutOfBounds

thisdir = os.path.dirname(os.path.abspath(__file__))
exampledir = os.path.abspath(os.path.join(thisdir,'..','examples'))

class ComparatorBase(object):
    
    def _load_xmlfile(self,filebase):
        xmlfilepath = os.path.join(exampledir,filebase + '.xml')
        self.translator = HPXMLtoHEScoreTranslator(xmlfilepath)
        return self.translator
    
    def _do_compare(self,filebase,jsonfilebase=None):
        if not jsonfilebase:
            jsonfilebase = filebase
        hescore_trans = self.translator.hpxml_to_hescore_dict()
        jsonfilepath = os.path.join(exampledir,jsonfilebase + '.json')
        with open(os.path.join(exampledir,jsonfilepath)) as f:
            hescore_truth = json.load(f)
        self.assertEqual(hescore_trans, hescore_truth, '{} not equal'.format(filebase))

    def _do_full_compare(self,filebase,jsonfilebase=None):
        self._load_xmlfile(filebase)
        self._do_compare(filebase,jsonfilebase)
    
    def _write_xml_file(self,filename):
        self.translator.hpxmldoc.write(os.path.join(exampledir,filename))
    
    def xpath(self,xpathexpr,*args,**kwargs):
        return self.translator.xpath(self.translator.hpxmldoc, xpathexpr, *args, **kwargs)

class TestAPIHouses(unittest.TestCase,ComparatorBase):
    
    def test_house1(self):
        self._do_full_compare('house1')
    
    def test_house1_v1_1(self):
        self._do_full_compare('house1-v1-1','house1')
    
    def test_house1_v2(self):
        self._do_full_compare('house1-v2','house1')
    
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
    
    def test_house7(self):
        self._do_full_compare('house7')

    def test_house8(self):
        self._do_full_compare('house8')

class TestOtherHouses(unittest.TestCase,ComparatorBase):

    def test_hescore_min(self):
        self._do_full_compare('hescore_min')
    
    def test_townhouse_walls(self):
        self._do_full_compare('townhouse_walls')
    
    def test_townhouse_wall_fail(self):
        tr = self._load_xmlfile('townhouse_walls')
        el = self.xpath( '//h:Window/h:Orientation[text()="south"]')
        el.text = 'east'
        self.assertRaisesRegexp(TranslationError, 
                                r'The house has windows on shared walls\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_siding(self):
        tr = self._load_xmlfile('hescore_min')
        siding = self.xpath('//h:Wall[1]/h:Siding')
        siding.getparent().remove(siding)
        self.assertRaisesRegexp(TranslationError, 
                                r'Exterior finish information is missing',
                                tr.hpxml_to_hescore_dict)
        
        
    def test_siding_fail2(self):
        tr = self._load_xmlfile('hescore_min')
        siding = self.xpath('//h:Wall[1]/h:Siding')
        siding.text = 'other'
        self.assertRaisesRegexp(TranslationError, 
                                r'There is no HEScore wall siding equivalent for the HPXML option: other',
                                tr.hpxml_to_hescore_dict)
    
    def test_siding_cmu_fail(self):
        tr = self._load_xmlfile('hescore_min')
        walltype = self.xpath('//h:Wall[1]/h:WallType')
        walltype.clear()
        etree.SubElement(walltype, tr.addns('h:ConcreteMasonryUnit'))
        siding = self.xpath('//h:Wall[1]/h:Siding')
        siding.text = 'vinyl siding'
        self.assertRaisesRegexp(TranslationError, 
                                r'is a CMU and needs a siding of stucco, brick, or none to translate to HEScore. It has a siding type of vinyl siding', 
                                tr.hpxml_to_hescore_dict)
    
    def test_log_wall_fail(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Wall[1]/h:WallType')
        el.clear()
        etree.SubElement(el, tr.addns('h:LogWall'))
        self.assertRaisesRegexp(TranslationError, 
                                r'Wall type LogWall not supported',
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_residential_facility_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:ResidentialFacilityType')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError,
                                r'ResidentialFacilityType is required in the HPXML document',
                                tr.hpxml_to_hescore_dict)
    
    def test_invalid_residential_faciliy_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:ResidentialFacilityType')
        el.text = 'manufactured home'
        self.assertRaisesRegexp(TranslationError,
                                r'Cannot translate HPXML ResidentialFacilityType of .+ into HEScore building shape',
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_surroundings(self):
        tr = self._load_xmlfile('townhouse_walls')
        el = self.xpath('//h:Surroundings')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                r'Site/Surroundings element is required in the HPXML document for town houses', 
                                tr.hpxml_to_hescore_dict)
    
    def test_invalid_surroundings(self):
        tr = self._load_xmlfile('townhouse_walls')
        el = self.xpath('//h:Surroundings')
        el.text = 'attached on three sides'
        self.assertRaisesRegexp(TranslationError, 
                                r'Cannot translate HPXML Site/Surroundings element value of .+ into HEScore town_house_walls', 
                                tr.hpxml_to_hescore_dict)
    
    def test_attic_roof_assoc(self):
        tr = self._load_xmlfile('house6')
        el = self.xpath('//h:Attic[1]/h:AttachedToRoof')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                r'Attic .+ does not have a roof associated with it\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_invalid_attic_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Attic[1]/h:AtticType')
        el.text = 'other'
        self.assertRaisesRegexp(TranslationError, 
                                'Attic .+ Cannot translate HPXML AtticType .+ to HEScore rooftype.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_roof_color(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Roof[1]/h:RoofColor')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'Attic .+ Invalid or missing RoofColor', 
                                tr.hpxml_to_hescore_dict)
    
    def test_invalid_roof_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Roof[1]/h:RoofType')
        el.text = 'no one major type'
        self.assertRaisesRegexp(TranslationError, 
                                'Attic .+ HEScore does not have an analogy to the HPXML roof type: .+', 
                                tr.hpxml_to_hescore_dict)
        
    def test_missing_roof_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Roof[1]/h:RoofType')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'Attic .+ HEScore does not have an analogy to the HPXML roof type: .+', 
                                tr.hpxml_to_hescore_dict)

    def test_missing_skylight_area(self):
        tr = self._load_xmlfile('hescore_min')
        area = self.xpath('//h:Skylight[1]/h:Area')
        area.getparent().remove(area)
        self.assertRaisesRegexp(TranslationError, 
                                'Every skylight needs an area\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_foundation_walls_on_slab(self):
        tr = self._load_xmlfile('house7')
        fnd = self.xpath('//h:Foundation[name(h:FoundationType/*) = "SlabOnGrade"]')
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
        el = self.xpath('//h:Window[1]/h:Area')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'All windows need an area\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_window_orientation(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Window[1]/h:Orientation')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'All windows need to have either an AttachedToWall, Orientation, or Azimuth sub element\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_window_attached_to_wall(self):
        filebase = 'house6'
        tr = self._load_xmlfile(filebase)
        # Get the first wall id
        wallid = self.xpath('//h:Wall[1]/h:Orientation/parent::node()/h:SystemIdentifier/@id')
        # get the orientation of the wall
        orientation = self.xpath('//h:Wall[h:SystemIdentifier/@id=$wallid]/h:Orientation/text()',wallid=wallid)
        # get the window orientation element of a window that is facing the same direction as the wall
        window_orientation = self.xpath('//h:Window[h:Orientation=$orientation][1]/h:Orientation',orientation=orientation)
        # remove the window orientation
        window = window_orientation.getparent()
        window.remove(window_orientation)
        # attach that window to the wall
        etree.SubElement(window, tr.addns('h:AttachedToWall'), attrib={'idref': wallid})
        self._do_compare(filebase)
        
    def test_impossible_window(self):
        tr = self._load_xmlfile('house1')
        el = self.xpath('//h:Window[h:GlassLayers="single-pane"]/h:FrameType/h:Aluminum')
        etree.SubElement(el, tr.addns('h:ThermalBreak')).text = "true"
        self.assertRaisesRegexp(TranslationError, 
                                'Cannot translate window type\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_impossible_heating_system_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:HeatingSystem[1]/h:HeatingSystemType')
        el.clear()
        etree.SubElement(el, tr.addns('h:PortableHeater'))
        self.assertRaisesRegexp(TranslationError, 
                                'HEScore does not support the HPXML HeatingSystemType', 
                                tr.hpxml_to_hescore_dict)
        
    def test_missing_heating_capacity(self):
        tr = self._load_xmlfile('house4')
        el = self.xpath('(//h:HeatingSystem|//h:HeatPump)[1]/h:HeatingCapacity')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'If a primary heating system is not defined, each heating system must have a capacity', 
                                tr.hpxml_to_hescore_dict)
    
    def test_primary_heating_system(self):
        filebase = 'house4'
        tr = self._load_xmlfile(filebase)
        hvacplant = self.xpath('//h:HVACPlant')
        el = etree.Element(tr.addns('h:PrimarySystems'))
        etree.SubElement(el, tr.addns('h:PrimaryHeatingSystem'), attrib={'idref': 'boiler1'})
        hvacplant.insert(0,el)
        for el in self.xpath('(//h:HeatingSystem|//h:HeatPump)/h:HeatingCapacity'):
            el.getparent().remove(el)
        self._do_compare(filebase)
        
    def test_missing_cooling_capacity(self):
        tr = self._load_xmlfile('house5')
        for el in self.xpath('(//h:HVACPlant/h:CoolingSystem|//h:HVACPlant/h:HeatPump)/h:CoolingCapacity'):
            el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'If a primary cooling system is not defined, each cooling system must have a capacity', 
                                tr.hpxml_to_hescore_dict)
    
    def test_primary_cooling_system(self):
        filebase = 'house4'
        tr = self._load_xmlfile(filebase)
        hvacplant = self.xpath('//h:HVACPlant')
        el = etree.Element(tr.addns('h:PrimarySystems'))
        etree.SubElement(el, tr.addns('h:PrimaryCoolingSystem'), attrib={'idref': 'centralair1'})
        hvacplant.insert(0,el)
        for el in self.xpath('(//h:HeatingSystem|//h:HeatPump)/h:CoolingCapacity'):
            el.getparent().remove(el)
        self._do_compare(filebase)
    
    def test_bad_duct_location(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:DuctLocation[1]')
        el.text = 'outside'
        self.assertRaisesRegexp(TranslationError, 
                                'No comparable duct location in HEScore', 
                                tr.hpxml_to_hescore_dict)
    
    def test_duct_cfa_requirement(self):
        tr = self._load_xmlfile('house5')
        el = self.xpath('//h:HVACDistribution[1]/h:ConditionedFloorAreaServed')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'All HVACDistribution elements need to have or NOT have the ConditionFloorAreaServed subelement\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_missing_water_heater(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:WaterHeating')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError, 
                                'No water heating systems found\.', 
                                tr.hpxml_to_hescore_dict)
    
    def test_indirect_dhw_error(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:WaterHeatingSystem[1]/h:WaterHeaterType')
        el.text = 'space-heating boiler with storage tank'
        self.assertRaisesRegexp(TranslationError, 
                                'Cannot have an indirect water heater if the primary heating system is not a boiler\.', 
                                tr.hpxml_to_hescore_dict)
        
    def test_tankless_coil_dhw_error(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:WaterHeatingSystem[1]/h:WaterHeaterType')
        el.text = 'space-heating boiler with tankless coil'
        self.assertRaisesRegexp(TranslationError, 
                                'Cannot have a tankless coil water heater if the primary heating system is not a boiler\.', 
                                tr.hpxml_to_hescore_dict)
        
    def test_missing_attached_to_roof(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:AttachedToRoof')
        el.getparent().remove(el)
        self._do_compare('hescore_min')
        
class TestInputOutOfBounds(unittest.TestCase,ComparatorBase):
    
    def test_assessment_date1(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Building/h:ProjectStatus/h:Date')
        el.text = '2009-12-31'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'assessment_date is out of bounds',
                                tr.hpxml_to_hescore_dict)

    def test_assessment_date2(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Building/h:ProjectStatus/h:Date')
        el.text = (dt.datetime.today().date() + dt.timedelta(1)).isoformat()
        self.assertRaisesRegexp(InputOutOfBounds,
                                'assessment_date is out of bounds',
                                tr.hpxml_to_hescore_dict)

    def test_year_built1(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:YearBuilt')
        el.text = '1599'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'year_built is out of bounds',
                                tr.hpxml_to_hescore_dict)

    def test_year_built2(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:YearBuilt')
        el.text = str(dt.datetime.today().year + 1)
        self.assertRaisesRegexp(InputOutOfBounds,
                                'year_built is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_num_floor_above_grade(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:NumberofConditionedFloorsAboveGrade')
        el.text = '5'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'num_floor_above_grade is out of bounds',
                                tr.hpxml_to_hescore_dict)
        
    def test_floor_to_ceiling_height1(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:AverageCeilingHeight')
        el.text = '5'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'floor_to_ceiling_height is out of bounds',
                                tr.hpxml_to_hescore_dict)

    def test_floor_to_ceiling_height2(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:AverageCeilingHeight')
        el.text = '13'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'floor_to_ceiling_height is out of bounds',
                                tr.hpxml_to_hescore_dict)
        
    def test_conditioned_floor_area1(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:ConditionedFloorArea')
        el.text = '249'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'conditioned_floor_area is out of bounds',
                                tr.hpxml_to_hescore_dict)

    def test_conditioned_floor_area2(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:ConditionedFloorArea')
        el.text = '25001'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'conditioned_floor_area is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_envelope_leakage(self):
        tr = self._load_xmlfile('hescore_min')
        units_el = self.xpath('//h:BuildingAirLeakage/h:UnitofMeasure')
        leak_el = self.xpath('//h:BuildingAirLeakage/h:AirLeakage')
        units_el.text = 'CFM'
        leak_el.text = '25001'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'envelope_leakage is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_skylight_area(self):
        tr = self._load_xmlfile('house4')
        el = self.xpath('//h:Skylight/h:Area')
        el.text = '301'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'skylight_area is out of bounds',
                                tr.hpxml_to_hescore_dict)
        
    def test_skylight_u_value(self):
        tr = self._load_xmlfile('house4')
        skylight = self.xpath('//h:Skylight')
        etree.SubElement(skylight, tr.addns('h:UFactor')).text = '0.001'
        etree.SubElement(skylight, tr.addns('h:SHGC')).text = '0.7'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'skylight_u_value is out of bounds',
                                tr.hpxml_to_hescore_dict)

    def test_window_area(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:Window[1]/h:Area')
        el.text = '1000'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'window_area is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_window_u_value(self):
        tr = self._load_xmlfile('house2')
        el = self.xpath('//h:Window[1]/h:UFactor')
        el.text = '5.00001'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'window_u_value is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_heating_efficiency(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:HeatingSystem/h:AnnualHeatingEfficiency/h:Value')
        el.text = '20.1'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'heating_efficiency is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_heating_year(self):
        tr = self._load_xmlfile('house3')
        el = self.xpath('//h:HeatPump/h:YearInstalled')
        el.text = str(dt.datetime.today().year + 1)
        self.assertRaisesRegexp(InputOutOfBounds,
                                'heating_year is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_cooling_efficiency(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:CoolingSystem/h:AnnualCoolingEfficiency/h:Value')
        el.text = '30.1'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'cooling_efficiency is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_cooling_year(self):
        tr = self._load_xmlfile('house1')
        eff_el = self.xpath('//h:CoolingSystem/h:AnnualCoolingEfficiency')
        eff_el.getparent().remove(eff_el)
        year_el = self.xpath('//h:CoolingSystem/h:YearInstalled')
        year_el.text = str(dt.datetime.today().year + 1)
        self.assertRaisesRegexp(InputOutOfBounds,
                                'cooling_year is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_dhw_efficiency(self):
        tr = self._load_xmlfile('house1')
        el = self.xpath('//h:WaterHeatingSystem/h:EnergyFactor')
        el.text = '4'
        self.assertRaisesRegexp(InputOutOfBounds,
                                'domestic_hot_water_energy_factor is out of bounds',
                                tr.hpxml_to_hescore_dict)
    
    def test_dhw_year(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:WaterHeatingSystem/h:YearInstalled')
        el.text = str(dt.datetime.today().year + 1)
        self.assertRaisesRegexp(InputOutOfBounds,
                                'domestic_hot_water_year is out of bounds',
                                tr.hpxml_to_hescore_dict)
        
        
        
        
if __name__ == "__main__":
    unittest.main()
