import os
import json
import unittest
import datetime as dt
from lxml import etree
from hpxml_to_hescore import HPXMLtoHEScoreTranslator, TranslationError, InputOutOfBounds
import StringIO
import json
from copy import deepcopy

thisdir = os.path.dirname(os.path.abspath(__file__))
exampledir = os.path.abspath(os.path.join(thisdir, '..', 'examples'))


class ComparatorBase(object):
    def _load_xmlfile(self, filebase):
        xmlfilepath = os.path.join(exampledir, filebase + '.xml')
        self.translator = HPXMLtoHEScoreTranslator(xmlfilepath)
        return self.translator

    def _do_compare(self, filebase, jsonfilebase=None):
        if not jsonfilebase:
            jsonfilebase = filebase
        hescore_trans = self.translator.hpxml_to_hescore_dict()
        jsonfilepath = os.path.join(exampledir, jsonfilebase + '.json')
        with open(os.path.join(exampledir, jsonfilepath)) as f:
            hescore_truth = json.load(f)
        self.assertEqual(hescore_trans, hescore_truth, '{} not equal'.format(filebase))

    def _do_full_compare(self, filebase, jsonfilebase=None):
        self._load_xmlfile(filebase)
        self._do_compare(filebase, jsonfilebase)

    def _write_xml_file(self, filename):
        self.translator.hpxmldoc.write(os.path.join(exampledir, filename))

    def xpath(self, xpathexpr, *args, **kwargs):
        return self.translator.xpath(self.translator.hpxmldoc, xpathexpr, *args, **kwargs)


class TestAPIHouses(unittest.TestCase, ComparatorBase):
    def test_house1(self):
        self._do_full_compare('house1')

    def test_house1_v1_1(self):
        self._do_full_compare('house1-v1-1', 'house1')

    def test_house1_v2(self):
        self._do_full_compare('house1-v2', 'house1')

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


class TestOtherHouses(unittest.TestCase, ComparatorBase):
    def test_hescore_min(self):
        self._do_full_compare('hescore_min')

    def test_townhouse_walls(self):
        self._do_full_compare('townhouse_walls')

    def test_townhouse_window_fail(self):
        tr = self._load_xmlfile('townhouse_walls')
        el = self.xpath('//h:Window/h:Orientation[text()="south"]')
        el.text = 'west'
        self.assertRaisesRegexp(TranslationError,
                                r'The house has windows on shared walls\.',
                                tr.hpxml_to_hescore_dict)

    def test_townhouse_walls_all_same(self):
        tr = self._load_xmlfile('townhouse_walls')
        # Remove other walls
        for el in self.xpath('//h:Wall[h:SystemIdentifier/@id!="wall1"]'):
            el.getparent().remove(el)
        # Remove the orientation of the first one
        wall1_orientation = self.xpath('//h:Wall[h:SystemIdentifier/@id="wall1"]/h:Orientation')
        wall1_orientation.getparent().remove(wall1_orientation)
        # This means that the interpreter should assume all walls are like the first wall.
        d = tr.hpxml_to_hescore_dict()
        # Check to make sure we're not getting any walls facing directions that are attached to adjacent to other units.
        for wall in d['building']['zone']['zone_wall']:
            self.assertIn(wall['side'], ['front', 'back', 'left'])

    def test_townhouse_window_wall_all_same_fail(self):
        tr = self._load_xmlfile('townhouse_walls')
        # Remove other walls
        for el in self.xpath('//h:Wall[h:SystemIdentifier/@id!="wall1"]'):
            el.getparent().remove(el)
        # Remove the orientation of the first one
        wall1_orientation = self.xpath('//h:Wall[h:SystemIdentifier/@id="wall1"]/h:Orientation')
        wall1_orientation.getparent().remove(wall1_orientation)
        # This means that the interpreter should assume all walls are like the first wall.
        el = self.xpath('//h:Window/h:Orientation[text()="south"]')
        el.text = 'west'
        self.assertRaisesRegexp(TranslationError,
                                r'The house has windows on shared walls\.',
                                tr.hpxml_to_hescore_dict)

    def test_townhouse_walls_conflict(self):
        tr = self._load_xmlfile('townhouse_walls')
        # move a wall to the west (attached) side
        el = self.xpath('//h:Wall[1]/h:Orientation')
        el.text = 'west'
        self.assertRaisesRegexp(
            TranslationError,
            r'The house has walls defined for sides ((front|right|left|back)(, )?)+ and shared walls on sides ((front|right|left|back)(, )?)+',
            tr.hpxml_to_hescore_dict
        )

    def test_townhouse_windows_area_wrong(self):
        tr = self._load_xmlfile('townhouse_walls')
        el = self.xpath('//h:OrientationOfFrontOfHome')
        el.text = 'west'
        for wall in self.xpath('//h:Wall/h:Orientation'):
            if wall.text == 'north':
                wall.text = 'west'
        for i, window in enumerate(self.xpath('//h:Window')):
            if i == 0:
                window.xpath('h:Area', namespaces=tr.ns)[0].text = '20'
                window.xpath('h:Orientation', namespaces=tr.ns)[0].text = 'west'
            elif i == 1:
                window.xpath('h:Area', namespaces=tr.ns)[0].text = '4'
                window.xpath('h:Orientation', namespaces=tr.ns)[0].text = 'south'
            else:
                window.getparent().remove(window)
        hesd = tr.hpxml_to_hescore_dict()
        walls_found = set()
        for wall in hesd['building']['zone']['zone_wall']:
            walls_found.add(wall['side'])
            if wall['side'] == 'front':
                self.assertEqual(wall['zone_window']['window_area'], 20)
            elif wall['side'] == 'right':
                self.assertEqual(wall['zone_window']['window_area'], 4)
            elif wall['side'] == 'back':
                self.assertEqual(wall['zone_window']['window_area'], 0)
        self.assertEqual(set(['front', 'right', 'back']), walls_found)

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
        rvalue = self.xpath('//h:Wall[1]/h:Insulation/h:Layer[1]/h:NominalRValue')
        rvalue.text = '3'
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
        for i, el in enumerate(fnd):
            if el.tag.endswith('Slab'):
                break
        fndwall = etree.Element(tr.addns('h:FoundationWall'))
        etree.SubElement(fndwall, tr.addns('h:SystemIdentifier'), attrib={'id': 'asdfjkl12345'})
        fnd.insert(i, fndwall)
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
        orientation = self.xpath('//h:Wall[h:SystemIdentifier/@id=$wallid]/h:Orientation/text()', wallid=wallid)
        # get the window orientation element of a window that is facing the same direction as the wall
        window_orientation = self.xpath('//h:Window[h:Orientation=$orientation][1]/h:Orientation',
                                        orientation=orientation)
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

    def test_impossible_cooling_system_type(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:CoolingSystem[1]/h:CoolingSystemType')
        el.text = 'other'
        self.assertRaisesRegexp(TranslationError,
                                'HEScore does not support the HPXML CoolingSystemType',
                                tr.hpxml_to_hescore_dict)

    def test_evap_cooling_system_type(self):
        tr = self._load_xmlfile('hescore_min')
        clgsystype = self.xpath('//h:CoolingSystem[1]/h:CoolingSystemType')
        clgsystype.text = 'evaporative cooler'
        for el in self.xpath('//h:CoolingSystem[1]/h:AnnualCoolingEfficiency', aslist=True):
            el.getparent().remove(el)
        res = tr.hpxml_to_hescore_dict()
        self.assertEqual(res['building']['systems']['hvac'][0]['cooling']['type'], 'dec')
        self.assertNotIn('efficiency_method', res['building']['systems']['hvac'][0]['cooling'])
        self.assertNotIn('efficiency', res['building']['systems']['hvac'][0]['cooling'])

    def test_missing_heating_weighting_factor(self):
        tr = self._load_xmlfile('house4')
        el = self.xpath('//h:HeatingSystem[1]/h:HeatingCapacity')
        el.getparent().remove(el)
        el = self.xpath('//h:HeatPump[1]/h:FloorAreaServed')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError,
                                'Every heating/cooling system needs to have either FloorAreaServed or FracLoadServed',
                                tr.hpxml_to_hescore_dict)

    def test_missing_cooling_weighting_factor(self):
        tr = self._load_xmlfile('house5')
        el = self.xpath('//h:CoolingSystem[1]/h:CoolingCapacity')
        el.getparent().remove(el)
        el = self.xpath('//h:CoolingSystem[2]/h:FloorAreaServed')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError,
                                'Every heating/cooling system needs to have either FloorAreaServed or FracLoadServed',
                                tr.hpxml_to_hescore_dict)

    def test_bad_duct_location(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:DuctLocation[1]')
        el.text = 'outside'
        self.assertRaisesRegexp(TranslationError,
                                'No comparable duct location in HEScore',
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
                                'Cannot have water heater type indirect if there is no boiler heating system',
                                tr.hpxml_to_hescore_dict)

    def test_tankless_coil_dhw_error(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:WaterHeatingSystem[1]/h:WaterHeaterType')
        el.text = 'space-heating boiler with tankless coil'
        self.assertRaisesRegexp(TranslationError,
                                'Cannot have water heater type tankless_coil if there is no boiler heating system',
                                tr.hpxml_to_hescore_dict)

    def test_missing_attached_to_roof(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:AttachedToRoof')
        el.getparent().remove(el)
        self._do_compare('hescore_min')

    def _wood_stove_setup(self):
        tr = self._load_xmlfile('hescore_min')
        htgsys = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="furnace1"]')
        htgsys.remove(htgsys.find(tr.addns('h:DistributionSystem')))
        htgsystype = htgsys.find(tr.addns('h:HeatingSystemType'))
        htgsystype.clear()
        etree.SubElement(htgsystype, tr.addns('h:Stove'))
        htgsys.find(tr.addns('h:HeatingSystemFuel')).text = 'wood'
        htgsys.remove(htgsys.find(tr.addns('h:AnnualHeatingEfficiency')))
        return htgsys

    def test_wood_stove(self):
        self._wood_stove_setup()
        result_dict = self.translator.hpxml_to_hescore_dict()
        htg_sys = result_dict['building']['systems']['hvac'][0]['heating']
        self.assertEqual(htg_sys['type'], 'wood_stove')
        self.assertEqual(htg_sys['fuel_primary'], 'cord_wood')

    def test_wood_stove_invalid_fuel_type(self):
        htgsys = self._wood_stove_setup()
        htgsys.find(self.translator.addns('h:HeatingSystemFuel')).text = 'natural gas'
        self.assertRaisesRegexp(TranslationError,
                                r'Heating system wood_stove cannot be used with fuel natural_gas',
                                self.translator.hpxml_to_hescore_dict)

    def test_too_many_duct_systems(self):
        tr = self._load_xmlfile('house5')
        dist_sys_el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="backfurnace"]/h:DistributionSystem')
        htg_sys = dist_sys_el.getparent()
        idx = htg_sys.index(dist_sys_el)
        htg_sys.insert(idx, etree.Element(tr.addns('h:DistributionSystem'), idref='frontducts'))
        self.assertRaisesRegexp(TranslationError,
                                r'Each HVAC plant is only allowed to specify one duct system\. .+ references more than one',
                                tr.hpxml_to_hescore_dict)

    def test_only_duct_system_per_heating_sys(self):
        tr = self._load_xmlfile('house5')
        dist_sys_el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="backfurnace"]/h:DistributionSystem')
        dist_sys_el.set('idref', 'frontducts')
        self.assertRaisesRegexp(TranslationError,
                                r'Each duct system is only allowed to serve one heating and one cooling system',
                                tr.hpxml_to_hescore_dict)

    def test_dist_sys_idref(self):
        tr = self._load_xmlfile('house5')
        dist_sys_el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="backfurnace"]/h:DistributionSystem')
        dist_sys_el.set('idref', 'backwindows1')
        self.assertRaisesRegexp(TranslationError,
                                r'HVAC plant .+ specifies an HPXML distribution system of .+, which does not exist.',
                                tr.hpxml_to_hescore_dict)

    def test_htg_sys_has_air_dist(self):
        tr = self._load_xmlfile('hescore_min')
        dist_sys_el = self.xpath('//h:HeatingSystem[1]/h:DistributionSystem')
        dist_sys_el.getparent().remove(dist_sys_el)
        self.assertRaisesRegexp(TranslationError,
                                r'Heating system .+ is not associated with an air distribution system\.',
                                tr.hpxml_to_hescore_dict)

    def test_clg_sys_has_air_dist(self):
        tr = self._load_xmlfile('hescore_min')
        dist_sys_el = self.xpath('//h:CoolingSystem[1]/h:DistributionSystem')
        dist_sys_el.getparent().remove(dist_sys_el)
        self.assertRaisesRegexp(TranslationError,
                                r'Cooling system .+ is not associated with an air distribution system\.',
                                tr.hpxml_to_hescore_dict)

    def test_floor_no_area(self):
        tr = self._load_xmlfile('house8')
        el = self.xpath('//h:Foundation[1]/*/h:Area')
        el.getparent().remove(el)
        self.assertRaisesRegexp(TranslationError,
                                r'If there is more than one foundation, each needs an area specified on either the Slab or FrameFloor',
                                tr.hpxml_to_hescore_dict)

    def test_bldgid_not_found(self):
        tr = self._load_xmlfile('house1')
        self.assertRaisesRegexp(TranslationError,
                                r'HPXML BuildingID not found',
                                tr.hpxml_to_hescore_dict,
                                hpxml_bldg_id='bldgnothere')

    def test_missing_cooling_system(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:CoolingSystem[h:SystemIdentifier/@id="centralair1"]')
        el.getparent().remove(el)
        res = tr.hpxml_to_hescore_dict()
        self.assertEqual(res['building']['systems']['hvac'][0]['cooling']['type'], 'none')

    def test_missing_heating_system(self):
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="furnace1"]')
        el.getparent().remove(el)
        res = tr.hpxml_to_hescore_dict()
        self.assertEqual(res['building']['systems']['hvac'][0]['heating']['type'], 'none')

    def test_wall_same_area_same_side_different_construction(self):
        '''
        Unit test for #37
        '''
        tr = self._load_xmlfile('house6')
        el = self.xpath('//h:Wall[h:SystemIdentifier/@id="wallleft2"]/h:Area')
        el.text = '240' # making it the same area as wallleft1
        tr.hpxml_to_hescore_dict()

    def test_cooling_system_wrong_efficiency_type(self):
        '''
        Unit test for #39
        '''
        tr = self._load_xmlfile('house7')
        el = self.xpath('//h:CoolingSystem[h:SystemIdentifier/@id="roomac"]/h:AnnualCoolingEfficiency/h:Units')
        el.text = 'SEER'
        self.assertRaisesRegexp(
            TranslationError,
            r'Cooling efficiency could not be determined',
            tr.hpxml_to_hescore_dict
        )

    def test_heating_system_wrong_efficiency_type(self):
        '''
        Another unit test for #39
        '''
        tr = self._load_xmlfile('hescore_min')
        el = self.xpath('//h:HeatingSystem/h:AnnualHeatingEfficiency/h:Units')
        el.text = 'Percent'
        self.assertRaisesRegexp(
            TranslationError,
            r'Heating efficiency could not be determined',
            tr.hpxml_to_hescore_dict
        )

    def test_hvac_fractions_sum_to_one(self):
        tr = self._load_xmlfile('house6')
        el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="furnace"]')
        el.remove(el[-1])
        etree.SubElement(el, tr.addns('h:FractionHeatLoadServed')).text = '0.94'
        el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="baseboard"]')
        el.remove(el[-1])
        etree.SubElement(el, tr.addns('h:FractionHeatLoadServed')).text = '0.06'
        el = self.xpath('//h:CoolingSystem[h:SystemIdentifier/@id="centralair"]')
        el.getparent().remove(el)
        f = StringIO.StringIO()
        tr.hpxml_to_hescore_json(f)
        f.seek(0)
        hesinp = json.load(f)
        self.assertEqual(sum([x['hvac_fraction'] for x in hesinp['building']['systems']['hvac']]), 1)

    def test_extra_roof_sheathing_insulation(self):
        '''
        Unit test for #44
        '''
        tr = self._load_xmlfile('house3')
        attic = self.xpath('//h:Attic[h:SystemIdentifier/@id="attic1"]/h:AtticRoofInsulation')
        lyr = etree.SubElement(attic, tr.addns('h:Layer'))
        etree.SubElement(lyr, tr.addns('h:InstallationType')).text = 'continuous'
        insmat = etree.SubElement(lyr, tr.addns('h:InsulationMaterial'))
        etree.SubElement(insmat, tr.addns('h:Rigid')).text = 'xps'
        etree.SubElement(lyr, tr.addns('h:NominalRValue')).text = '20'
        hesinp = tr.hpxml_to_hescore_dict()
        self.assertEqual(hesinp['building']['zone']['zone_roof'][0]['roof_assembly_code'], 'rfps21lc')

    def test_extra_wall_sheathing_insulation(self):
        '''
        Unit test for #44
        '''
        tr = self._load_xmlfile('house3')
        el = self.xpath('//h:Wall[h:SystemIdentifier/@id="wall1"]/h:Insulation/h:Layer[h:InstallationType="continuous"]/h:NominalRValue')
        el.text = '15'
        hesinp = tr.hpxml_to_hescore_dict()
        self.assertEqual(hesinp['building']['zone']['zone_wall'][0]['wall_assembly_code'], 'ewps21al')

    def test_wall_insulation_layer_missing_rvalue(self):
        tr = self._load_xmlfile('house3')
        el = self.xpath('//h:Wall[1]/h:Insulation/h:Layer[1]/h:NominalRValue')
        el.getparent().remove(el)
        self.assertRaisesRegexp(
            TranslationError,
            r'Every wall insulation layer needs a NominalRValue',
            tr.hpxml_to_hescore_dict
        )

    def test_attic_knee_wall(self):
        """
        Unit test for #48
        """
        tr = self._load_xmlfile('hescore_min')
        # make a copy of the first wall
        wall1 = self.xpath('//h:Wall[1]')
        wall2 = deepcopy(wall1)
        # change the system id
        sysid = wall2.find(tr.addns('h:SystemIdentifier'))
        sysid.attrib['id'] = 'wall2'
        # and the insulation id
        ins_sysid = wall2.xpath('h:Insulation/h:SystemIdentifier', namespaces=tr.ns)[0]
        ins_sysid.attrib['id'] = 'wall2ins'
        # remove the siding
        siding = wall2.find(tr.addns('h:Siding'))
        wall2.remove(siding)
        # add an ExteriorAdjacentTo = attic
        ext_adj_to = etree.Element(tr.addns('h:ExteriorAdjacentTo'))
        ext_adj_to.text = 'attic'
        wall2.insert(1, ext_adj_to)
        # insert new wall
        walls = self.xpath('//h:Walls')
        walls.append(wall2)
        # run translation
        tr.hpxml_to_hescore_dict()

    def test_wall_construction_ps_low_r(self):
        """
        Unit test for #47
        """
        tr = self._load_xmlfile('hescore_min')
        wallins = self.xpath('//h:Wall[1]/h:Insulation')
        wallins.xpath('h:Layer[1]/h:NominalRValue[1]', namespaces=tr.ns)[0].text = '8'
        newlayer = etree.SubElement(wallins, tr.addns('h:Layer'))
        etree.SubElement(newlayer, tr.addns('h:InstallationType')).text = 'continuous'
        insmat = etree.SubElement(newlayer, tr.addns('h:InsulationMaterial'))
        etree.SubElement(insmat, tr.addns('h:Rigid')).text = 'eps'
        etree.SubElement(newlayer, tr.addns('h:NominalRValue')).text = '5'
        b = tr.hpxml_to_hescore_dict()
        self.assertEquals(b['building']['zone']['zone_wall'][0]['wall_assembly_code'], 'ewps07br')

    def test_ove_low_r(self):
        """
        Make sure we pick the lowest construction code for walls
        """
        tr = self._load_xmlfile('hescore_min')
        wood_stud_wall_type = self.xpath('//h:Wall[1]/h:WallType/h:WoodStud')
        etree.SubElement(wood_stud_wall_type, tr.addns('h:OptimumValueEngineering')).text = 'true'
        self.xpath('//h:Wall[1]/h:Insulation/h:Layer[h:InstallationType="cavity"]/h:NominalRValue').text = '0'
        self.assertRaisesRegexp(
            TranslationError,
            r'Envelope construction not supported',
            tr.hpxml_to_hescore_dict
        )

    def test_heating_system_no_efficiency(self):
        """
        #50
        Some heating systems should ignore the efficiency value.
        Make sure that's happening.
        """
        tr = self._load_xmlfile('hescore_min')
        htgsys_fuel = self.xpath('//h:HeatingSystem[1]/h:HeatingSystemFuel')
        htgsys_fuel.text = 'electricity'
        annual_heating_eff = self.xpath('//h:HeatingSystem[1]/h:AnnualHeatingEfficiency')
        d = tr.hpxml_to_hescore_dict()
        self.assertNotIn(
            'efficiency',
            d['building']['systems']['hvac'][0]['heating'],
            'Electric furnace should not have an efficiency.'
        )
        annual_heating_eff.getparent().remove(annual_heating_eff)
        d = tr.hpxml_to_hescore_dict()
        self.assertNotIn(
            'efficiency',
            d['building']['systems']['hvac'][0]['heating'],
            'Electric furnace should not have an efficiency.'
        )
        htgsys_fuel.text = 'wood'
        htgsys_type = self.xpath('//h:HeatingSystem[1]/h:HeatingSystemType')
        htgsys_type.clear()
        etree.SubElement(htgsys_type, tr.addns('h:Stove'))
        d = tr.hpxml_to_hescore_dict()
        self.assertNotIn(
            'efficiency',
            d['building']['systems']['hvac'][0]['heating'],
            'Wood stove should not have an efficiency.'
        )
        htgsys = self.xpath('//h:HeatingSystem[1]')
        htgsys.append(annual_heating_eff)
        d = tr.hpxml_to_hescore_dict()
        self.assertNotIn(
            'efficiency',
            d['building']['systems']['hvac'][0]['heating'],
            'Wood stove should not have an efficiency.'
        )

    def test_zipcode_missing(self):
        """
        #51 Should error out when zipcode is missing.
        :return:
        """
        tr = self._load_xmlfile('hescore_min')
        zipcode_el = self.xpath('//h:Building/h:Site/h:Address[h:AddressType="street"]/h:ZipCode')
        zipcode_el.getparent().remove(zipcode_el)
        self.assertRaisesRegexp(
            TranslationError,
            r'ZipCode missing',
            tr.hpxml_to_hescore_dict
        )

    def test_air_source_heat_pump_has_no_ducts(self):
        tr = self._load_xmlfile('house4')
        el = self.xpath('//h:HeatPump[h:SystemIdentifier/@id="heatpump1"]/h:HeatPumpType')
        el.text = 'air-to-air'
        self.assertRaisesRegexp(
            TranslationError,
            r'(Cooling|Heating) system heatpump1 is not associated with an air distribution system',
            tr.hpxml_to_hescore_dict
        )


class TestInputOutOfBounds(unittest.TestCase, ComparatorBase):

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

class TestHVACFractions(unittest.TestCase, ComparatorBase):
    '''
    These are tests for weird HVAC configurations, see issue #45
    '''

    def test_boiler_roomac(self):
        '''
        Whole house heating by boiler, room AC added for one section (30%).
        '''
        tr = self._load_xmlfile('house4')

        # get rid of the heat pump
        el = self.xpath('//h:HeatPump[h:SystemIdentifier/@id="heatpump1"]')
        el.getparent().remove(el)

        # Remove floor areas served
        for el in self.xpath('//h:HVACPlant/*/h:FloorAreaServed'):
            el.getparent().remove(el)

        # Set the boiler to 100 of heating load
        boiler = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="boiler1"]')
        etree.SubElement(boiler, tr.addns('h:FractionHeatLoadServed')).text = '1'

        # Convert the central air to a room a/c and set the fraction to 0.3
        aircond = self.xpath('//h:CoolingSystem[h:SystemIdentifier/@id="centralair1"]')
        el = aircond.xpath('h:CoolingSystemType', namespaces=tr.ns)[0]
        el.text = 'room air conditioner'
        # remove distribution systems
        el = aircond.xpath('h:DistributionSystem', namespaces=tr.ns)[0]
        el.getparent().remove(el)
        el = self.xpath('//h:HVACDistribution[h:SystemIdentifier/@id="aircondducts"]')
        el.getparent().remove(el)
        el = aircond.xpath('h:AnnualCoolingEfficiency/h:Units', namespaces=tr.ns)[0]
        el.text = 'EER'
        el = aircond.xpath('h:AnnualCoolingEfficiency/h:Value', namespaces=tr.ns)[0]
        el.text = '8'
        el = etree.Element(tr.addns('h:FractionCoolLoadServed'))
        el.text = '0.3'
        aircond.insert(-1, el)

        b = self.xpath('h:Building[1]')
        hvac_systems = tr._get_hvac(b)
        hvac_systems.sort(key=lambda x: x['hvac_fraction'])

        hvac1 = hvac_systems[0]
        self.assertAlmostEqual(hvac1['hvac_fraction'], 0.3, 3)
        self.assertEqual(hvac1['heating']['type'], 'boiler')
        self.assertEqual(hvac1['cooling']['type'], 'packaged_dx')

        hvac2 = hvac_systems[1]
        self.assertAlmostEqual(hvac2['hvac_fraction'], 0.7, 3)
        self.assertEqual(hvac2['heating']['type'], 'boiler')
        self.assertEqual(hvac2['cooling']['type'], 'none')

    def test_furnace_baseboard_centralac(self):
        '''
        Furnace and baseboard each heat a fraction of the house.
        2 identical Central air cools corresponding fractions.
        '''
        tr = self._load_xmlfile('house6')

        # Get total floor area
        total_floor_area = 0
        for htgsys_floor_area in self.xpath('//h:HeatingSystem/h:FloorAreaServed/text()'):
            total_floor_area += float(htgsys_floor_area)

        # Set each equipment to the proper fractions
        furnace_floor_area_el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="furnace"]/h:FloorAreaServed')
        furnace_floor_area_el.text = str(0.6 * total_floor_area)
        baseboard_floor_area_el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="baseboard"]/h:FloorAreaServed')
        baseboard_floor_area_el.text = str(0.4 * total_floor_area)

        # Set 1st central air unit
        clgsys_floor_area_el = self.xpath('//h:CoolingSystem[h:SystemIdentifier/@id="centralair"]/h:FloorAreaServed')
        clgsys_floor_area_el.text = str(0.6 * total_floor_area)

        # Copy central air unit
        clgsys = self.xpath('//h:CoolingSystem[h:SystemIdentifier/@id="centralair"]')
        clgsys2 = deepcopy(clgsys)
        clgsys.getparent().append(clgsys2)
        tr.xpath(clgsys2, 'h:SystemIdentifier').attrib['id'] = 'centralair2'
        tr.xpath(clgsys2, 'h:FloorAreaServed').text = str(0.4 * total_floor_area)
        tr.xpath(clgsys2, 'h:DistributionSystem').attrib['idref'] = 'ducts2'

        # Copy the ducts
        ducts = self.xpath('//h:HVACDistribution[h:SystemIdentifier/@id="ducts"]')
        ducts2 = deepcopy(ducts)
        ducts.getparent().append(ducts2)
        tr.xpath(ducts2, 'h:SystemIdentifier').attrib['id'] = 'ducts2'

        b = self.xpath('h:Building[1]')
        hvac_systems = tr._get_hvac(b)
        hvac_systems.sort(key=lambda x: x['hvac_fraction'])

        hvac1 = hvac_systems[0]
        self.assertAlmostEqual(hvac1['hvac_fraction'], 0.4, 3)
        self.assertEqual(hvac1['heating']['type'], 'baseboard')
        self.assertEqual(hvac1['cooling']['type'], 'split_dx')

        hvac2 = hvac_systems[1]
        self.assertAlmostEqual(hvac2['hvac_fraction'], 0.6, 3)
        self.assertEqual(hvac2['heating']['type'], 'central_furnace')
        self.assertEqual(hvac2['cooling']['type'], 'split_dx')

    def test_wall_furnace_baseboard_centralac(self):
        '''
        60% wall furnace
        40% baseboard
        100% central air
        '''
        tr = self._load_xmlfile('house6')

        # Get total floor area
        total_floor_area = 0
        for htgsys_floor_area in self.xpath('//h:HeatingSystem/h:FloorAreaServed/text()'):
            total_floor_area += float(htgsys_floor_area)

        # Set each equipment to the proper fractions
        furnace_floor_area_el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="furnace"]/h:FloorAreaServed')
        furnace_floor_area_el.text = str(0.6 * total_floor_area)
        baseboard_floor_area_el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="baseboard"]/h:FloorAreaServed')
        baseboard_floor_area_el.text = str(0.4 * total_floor_area)

        # Change to natural gas wall furnace (no ducts)
        htgsys_type = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="furnace"]/h:HeatingSystemType')
        htgsys_type.clear()
        etree.SubElement(htgsys_type, tr.addns('h:WallFurnace'))
        distsys = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="furnace"]/h:DistributionSystem')
        distsys.getparent().remove(distsys)
        htgsys_fuel = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="furnace"]/h:HeatingSystemFuel')
        htgsys_fuel.text = 'natural gas'

        # Set central air unit
        clgsys_floor_area_el = self.xpath('//h:CoolingSystem[h:SystemIdentifier/@id="centralair"]/h:FloorAreaServed')
        clgsys_floor_area_el.text = str(total_floor_area)

        b = self.xpath('h:Building[1]')
        hvac_systems = tr._get_hvac(b)
        hvac_systems.sort(key=lambda x: x['hvac_fraction'])

        hvac1 = hvac_systems[0]
        self.assertAlmostEqual(hvac1['hvac_fraction'], 0.4, 3)
        self.assertEqual(hvac1['heating']['type'], 'baseboard')
        self.assertEqual(hvac1['cooling']['type'], 'split_dx')

        hvac2 = hvac_systems[1]
        self.assertAlmostEqual(hvac2['hvac_fraction'], 0.6, 3)
        self.assertEqual(hvac2['heating']['type'], 'wall_furnace')
        self.assertEqual(hvac2['cooling']['type'], 'split_dx')

    def test_furnace_heat_pump(self):
        '''
        Original house heated by central furnace 70%
        Addition heated and cooled by heat pump
        '''
        tr = self._load_xmlfile('house4')

        # Get total floor area
        total_floor_area = 0
        for htgsys_floor_area in self.xpath('//h:HeatingSystem/h:FloorAreaServed/text()|//h:HeatPump/h:FloorAreaServed/text()'):
            total_floor_area += float(htgsys_floor_area)

        # Turn the boiler into central furnace
        furnace_el = self.xpath('//h:HeatingSystem[h:SystemIdentifier/@id="boiler1"]')
        sys_type = tr.xpath(furnace_el, 'h:HeatingSystemType')
        sys_type.clear()
        etree.SubElement(sys_type, tr.addns('h:Furnace'))

        # Attach the furnace to the air conditioning ducts
        el = tr.xpath(furnace_el, 'h:DistributionSystem')
        el.attrib['idref'] = 'aircondducts'

        # Set the furnace to be 70% of the area
        furnace_floor_area_el = tr.xpath(furnace_el, 'h:FloorAreaServed')
        furnace_floor_area_el.text = str(0.7 * total_floor_area)

        # Remove the air conditioner
        el = self.xpath('//h:CoolingSystem')
        el.getparent().remove(el)

        # Set the heat pump to 30% of the area
        heat_pump_floor_area_el = self.xpath('//h:HeatPump/h:FloorAreaServed')
        heat_pump_floor_area_el.text = str(0.3 * total_floor_area)

        # Get HEScore inputs and sort by fraction
        b = self.xpath('h:Building[1]')
        hvac_systems = tr._get_hvac(b)
        hvac_systems.sort(key=lambda x: x['hvac_fraction'])

        hvac1 = hvac_systems[0]
        self.assertAlmostEqual(hvac1['hvac_fraction'], 0.3, 3)
        self.assertEqual(hvac1['heating']['type'], 'mini_split')
        self.assertEqual(hvac1['cooling']['type'], 'mini_split')

        hvac2 = hvac_systems[1]
        self.assertAlmostEqual(hvac2['hvac_fraction'], 0.7, 3)
        self.assertEqual(hvac2['heating']['type'], 'central_furnace')
        self.assertEqual(hvac2['cooling']['type'], 'none')


class TestPhotovoltaics(unittest.TestCase, ComparatorBase):

    def _add_pv(self, sysid='pv1', orientation='south', azimuth=180, capacity=5, inverter_year=2015, module_year=2013):
        addns = self.translator.addns

        def add_elem(parent, subname, text=None):
            el = etree.SubElement(parent, addns('h:' + subname))
            if text:
                el.text = str(text)
            return el

        pv_container = self.xpath('//h:Photovoltaics')
        if pv_container is None:
            systems_el = self.xpath('//h:Systems')
            pv_container = add_elem(systems_el, 'Photovoltaics')
        pv_system = add_elem(pv_container, 'PVSystem')
        sys_id = add_elem(pv_system, 'SystemIdentifier')
        sys_id.attrib['id'] = sysid
        if orientation is not None:
            add_elem(pv_system, 'ArrayOrientation', orientation)
        if azimuth is not None:
            add_elem(pv_system, 'ArrayAzimuth', azimuth)
        if capacity is not None:
            add_elem(pv_system, 'MaxPowerOutput', capacity * 1000)
        if inverter_year is not None:
            add_elem(pv_system, 'YearInverterManufactured', inverter_year)
        if module_year is not None:
            add_elem(pv_system, 'YearModulesManufactured', module_year)

    def test_pv(self):
        tr = self._load_xmlfile('hescore_min')
        self._add_pv()
        hesd = tr.hpxml_to_hescore_dict()
        pv = hesd['building']['systems']['generation']['solar_electric']
        self.assertTrue(pv['capacity_known'])
        self.assertEqual(pv['system_capacity'], 5)
        self.assertEqual(pv['year'], 2015)
        self.assertEqual(pv['array_azimuth'], 'south')

    def test_capacity_missing(self):
        tr = self._load_xmlfile('hescore_min')
        self._add_pv(capacity=None)
        self.assertRaisesRegexp(
            TranslationError,
            r'MaxPowerOutput is required',
            tr.hpxml_to_hescore_dict
        )

    def test_orientation(self):
        tr = self._load_xmlfile('hescore_min')
        self._add_pv(orientation='east', azimuth=None)
        hesd = tr.hpxml_to_hescore_dict()
        pv = hesd['building']['systems']['generation']['solar_electric']
        self.assertEqual(pv['array_azimuth'], 'east')

    def test_azimuth_orientation_missing(self):
        tr = self._load_xmlfile('hescore_min')
        self._add_pv(azimuth=None, orientation=None)
        self.assertRaisesRegexp(
            TranslationError,
            r'ArrayAzimuth or ArrayOrientation is required for every PVSystem',
            tr.hpxml_to_hescore_dict
        )

    def test_years_missing(self):
        tr = self._load_xmlfile('hescore_min')
        self._add_pv(module_year=None, inverter_year=None)
        self.assertRaisesRegexp(
            TranslationError,
            r'Either YearInverterManufactured or YearModulesManufactured is required foe every PVSystem',
            tr.hpxml_to_hescore_dict
        )

    def test_two_sys_avg(self):
        tr = self._load_xmlfile('hescore_min')
        self._add_pv('pv1', azimuth=None, orientation='south', inverter_year=None, module_year=2015)
        self._add_pv('pv2', azimuth=None, orientation='west', inverter_year=None, module_year=2013)
        hesd = tr.hpxml_to_hescore_dict()
        pv = hesd['building']['systems']['generation']['solar_electric']
        self.assertEqual(pv['system_capacity'], 10)
        self.assertEqual(pv['array_azimuth'], 'southwest')
        self.assertEqual(pv['year'], 2014)






if __name__ == "__main__":
    unittest.main()
