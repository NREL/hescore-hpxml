'''
Created on Mar 4, 2014

@author: nmerket
'''
# Python standard library imports
import os
import sys
import argparse
import datetime as dt
import logging
import traceback
import re
import json
import math
from lxml import etree

logging.basicConfig(filename='hpxml_to_hescore.log', level=logging.DEBUG, filemode='w')

# My imports
thisdir = os.path.dirname(os.path.abspath(__file__))

ns = {'h': 'http://hpxml.org/hpxml/2011/1',
      'xs': 'http://www.w3.org/2001/XMLSchema'}
nsre = re.compile(r'([a-zA-Z][a-zA-Z0-9]*):')
schemapath = os.path.join(thisdir,'schemas','hpxml-1.1.1','HPXML.xsd')
schematree = etree.parse(schemapath)
schema = etree.XMLSchema(schematree)
hpxmlparser = etree.XMLParser(schema = schema)

hpxml_base_elements = etree.parse(os.path.join(os.path.dirname(schemapath),'BaseElements.xsd'))
site_element_order = hpxml_base_elements.xpath('//xs:element[@name="Site"][ancestor::xs:complexType[@name="BuildingDetailsType"]]/xs:complexType/xs:sequence/xs:element/@name',namespaces=ns)
site_element_order = ['h:' + x for x in site_element_order]
wall_element_order = hpxml_base_elements.xpath('//xs:element[@name="Siding"]/parent::node()/xs:element/@name',namespaces=ns)
wall_element_order = ['h:' + x for x in wall_element_order]

hpxml_orientation_to_azimuth = {'north': 0,
                                'northeast': 45,
                                'east': 90,
                                'southeast': 135,
                                'south': 180,
                                'southwest': 225,
                                'west': 270,
                                'northwest': 315}  

fuel_type_mapping = {'electricity': 'electric', 
                     'renewable electricity': 'electric', 
                     'natural gas': 'natural_gas', 
                     'renewable natural gas': 'natural_gas', 
                     'fuel oil': 'fuel_oil', 
                     'fuel oil 1': 'fuel_oil', 
                     'fuel oil 2': 'fuel_oil', 
                     'fuel oil 4': 'fuel_oil', 
                     'fuel oil 5/6': 'fuel_oil', 
                     'propane': 'lpg'}

def doxpath(el,xpathquery,**kwargs):
    res = el.xpath(xpathquery,namespaces=ns,**kwargs)
    if isinstance(res,list):
        if len(res) == 0:
            return None
        elif len(res) == 1:
            return res[0]
        else:
            return res
    else:
        return res

def tobool(x):
    if x is None:
        return None
    elif x.lower() == 'true':
        return True
    else:
        assert x.lower() == 'false'
        return False

def convert_to_type(type_,value):
    if value is None:
        return value
    else:
        return type_(value)

class TranslationError(Exception):
    pass

def unspin_azimuth(azimuth):
    while azimuth >= 360:
        azimuth -= 360
    while azimuth < 0:
        azimuth += 360
    return azimuth

def get_nearest_azimuth(azimuth=None,orientation=None):
    if azimuth is not None:
        return int(round(float(azimuth) / 45.)) % 8 * 45
    else:
        assert orientation is not None
        return hpxml_orientation_to_azimuth[orientation]

def find_largest_hpxml_wall(walls):
    assert len(walls) >= 1
    if len(walls) == 1:
        return walls[0]
    else:
        return max(walls, key=lambda x: float(doxpath(x,'h:Area/text()')))

def round_to_nearest(x,vals):
    return min(vals, key=lambda y: abs(x-y))

def get_wall_assembly_code(hpxmlwall):
    # siding
    # TODO: determine what to assume for other siding types.
    sidingmap = {'wood siding': 'wo',
                 'stucco': 'st',
                 'synthetic stucco': 'st',
                 'vinyl siding': 'vi',
                 'aluminum siding': 'al',
                 'brick veneer': 'br',
                 'asbestos siding': None,
                 'fiber cement siding': None,
                 'composite shingle siding': None,
                 'masonite siding': None,
                 'other': None}
    
    # construction type
    wall_type = doxpath(hpxmlwall,'name(h:WallType/*)')
    if wall_type == 'WoodStud':
        has_rigid_ins = False
        cavity_rvalue = 0
        for lyr in hpxmlwall.xpath('h:Insulation/h:Layer',namespaces=ns):
            installation_type = doxpath(lyr,'h:InstallationType/text()')
            if doxpath(lyr,'h:InsulationMaterial/h:Rigid') is not None and \
               installation_type == 'continuous':
                has_rigid_ins = True
            else:
                cavity_rvalue += float(doxpath(lyr,'h:NominalRValue/text()'))
        if tobool(doxpath(hpxmlwall,'h:WallType/h:WoodStud/h:ExpandedPolystyreneSheathing/text()')) or has_rigid_ins:
            wallconstype = 'ps'
            rvalue = round_to_nearest(cavity_rvalue,(0,3,7,11,13,15,19,21))
        elif tobool(doxpath(hpxmlwall,'h:WallType/h:WoodStud/h:OptimumValueEngineering/text()')):
            wallconstype = 'ov'
            rvalue = round_to_nearest(cavity_rvalue,(19,21,27,33,38))
        else:
            wallconstype = 'wf'
            rvalue = round_to_nearest(cavity_rvalue,(0,3,7,11,13,15,19,21))
        sidingtype = sidingmap[doxpath(hpxmlwall,'h:Siding/text()')]
        assert sidingtype is not None
    elif wall_type == 'StructuralBrick':
        wallconstype = 'br'
        sidingtype = 'nn'
        rvalue = 0
        for lyr in hpxmlwall.xpath('h:Insulation/h:Layer',namespaces=ns):
            rvalue += float(doxpath(lyr,'h:NominalRValue/text()'))
        rvalue = round_to_nearest(rvalue,(0,5,10))
    elif wall_type in ('ConcreteMasonryUnit','Stone'):
        wallconstype = 'cb'
        rvalue = 0
        for lyr in hpxmlwall.xpath('h:Insulation/h:Layer',namespaces=ns):
            rvalue += float(doxpath(lyr,'h:NominalRValue/text()'))
        rvalue = round_to_nearest(rvalue,(0,3,6))
        if doxpath(hpxmlwall,'h:Siding/text()') is None:
            sidingtype = 'nn'
        else:
            sidingtype = sidingmap[doxpath(hpxmlwall,'h:Siding/text()')]
            assert sidingtype in ('st','br')
    elif wall_type == 'StrawBale':
        wallconstype = 'sb'
        rvalue = 0
        sidingtype = 'st'
    else:
        raise TranslationError('Wall type %s not supported' % wall_type)
    
    return 'ew%s%02d%s' % (wallconstype,rvalue,sidingtype)

def get_window_code(window):
    window_code = None
    frame_type = doxpath(window,'name(h:FrameType/*)')
    glass_layers = doxpath(window,'h:GlassLayers/text()')
    glass_type = doxpath(window,'h:GlassType/text()')
    gas_fill = doxpath(window,'h:GasFill/text()')
    if frame_type in ('Aluminum','Metal'):
        thermal_break = tobool(doxpath(window,'h:FrameType/*/h:ThermalBreak/text()'))
        if thermal_break:
            # Aluminum with Thermal Break
            if glass_layers in ('double-pane','single-paned with storms','single-paned with low-e storms'):
                if glass_layers == 'double-pane' and glass_type == 'low-e' and gas_fill == 'argon':
                    window_code = 'dpeaab'
                elif glass_type is not None and glass_type == 'reflective':
                    # TODO: figure out if 'reflective' is close enough to 'solar-control' low-e
                    window_code = 'dseab'
                elif glass_type is not None and glass_type.startswith('tinted'):
                    window_code = 'dtab'
                else:
                    window_code = 'dcab'
        else:
            # Aluminum
            if glass_layers == 'single-pane':
                if glass_type is not None and glass_type.startswith('tinted'):
                    window_code = 'stna'
                else:
                    window_code = 'scna'
            elif glass_layers in ('double-pane','single-paned with storms','single-paned with low-e storms'):
                if glass_type is not None and glass_type == 'reflective':
                    # TODO: figure out if 'reflective' is close enough to 'solar-control' low-e
                    window_code = 'dseaa'
                elif glass_type is not None and glass_type.startswith('tinted'):
                    window_code = 'dtaa'
                else:
                    window_code = 'dcaa'
    elif frame_type in ('Vinyl','Wood','Fiberglass','Composite'):
        # Wood or Vinyl
        if glass_layers == 'single-pane':
            if glass_type is not None and glass_type.startswith('tinted'):
                window_code = 'stnw'
            else:
                window_code = 'scnw'
        elif glass_layers in ('double-pane','single-paned with storms','single-paned with low-e storms'):
            if (glass_layers == 'double-pane' and glass_type == 'low-e') or \
                glass_layers == 'single-paned with low-e storms':
                if gas_fill == 'argon' and glass_layers == 'double-pane':
                    window_code = 'dpeaaw'
                else:
                    window_code = 'dpeaw'
            elif glass_type == 'reflective':
                # TODO: figure out if 'reflective' is close enough to 'solar-control' low-e
                if gas_fill == 'argon' and glass_layers == 'double-pane':
                    window_code = 'dseaaw'
                else:
                    window_code = 'dseaw'
            elif glass_type is not None and glass_type.startswith('tinted'):
                window_code = 'dtaw'
            else:
                window_code = 'dcaw'                        
        elif glass_layers == 'triple-paned':
            window_code = 'thmabw'

    if window_code is None:
        TranslationError('Cannot translate window type')
    return window_code

heat_pump_type_map = {'water-to-air': 'heat_pump', 
                      'water-to-water': 'heat_pump', 
                      'air-to-air': 'heat_pump', 
                      'mini-split': 'heat_pump', 
                      'ground-to-air': 'gchp'}

def get_heating_system_type(htgsys):
    sys_heating = {}
    if htgsys.tag.endswith('HeatPump'):
        sys_heating['fuel_primary'] = 'electric'
        heat_pump_type = doxpath(htgsys,'h:HeatPumpType/text()')
        if heat_pump_type is None:
            sys_heating['type'] = 'heat_pump'
        else:
            sys_heating['type'] = heat_pump_type_map[heat_pump_type]
    else:
        assert htgsys.tag.endswith('HeatingSystem')
        sys_heating['fuel_primary'] = fuel_type_mapping[doxpath(htgsys,'h:HeatingSystemFuel/text()')]
        hpxml_heating_type = doxpath(htgsys,'name(h:HeatingSystemType/*)')
        try:
            sys_heating['type'] = {'Furnace': 'central_furnace',
                                 'WallFurnace': 'wall_furnace',
                                 'Boiler': 'boiler',
                                 'ElectricResistance': 'baseboard'}[hpxml_heating_type]
        except KeyError:
            raise TranslationError('HEScore does not support the HPXML HeatingSystemType %s' % hpxml_heating_type)
        
    if not (sys_heating['type'] in ('furnace','baseboard') and sys_heating['fuel_primary'] == 'electric'):
        eff_units = {'heat_pump': 'HSPF',
                     'central_furnace': 'AFUE',
                     'wall_furnace': 'AFUE',
                     'boiler': 'AFUE',
                     'gchp': 'COP'}[sys_heating['type']]
        getefficiencyxpathexpr = '(h:AnnualHeatingEfficiency|h:AnnualHeatEfficiency)[h:Units=$effunits]/h:Value/text()'
        eff_els = htgsys.xpath(getefficiencyxpathexpr,namespaces=ns,
                               effunits=eff_units)
        if len(eff_els) == 0:
            # Use the year instead
            sys_heating['efficiency_method'] = 'shipment_weighted'
            sys_heating['year'] = int(htgsys.xpath('(h:YearInstalled|h:ModelYear)/text()',namespaces=ns)[0])
        else:
            # Use the efficiency of the first element found.
            sys_heating['efficiency_method'] = 'user'
            sys_heating['efficiency'] = float(eff_els[0])
    sys_heating['capacity'] = convert_to_type(float,doxpath(htgsys,'h:HeatingCapacity/text()'))
    return sys_heating

def get_cooling_system_type(clgsys):
    sys_cooling = {}
    if clgsys.tag.endswith('HeatPump'):
        heat_pump_type = doxpath(clgsys,'h:HeatPumpType/text()')
        if heat_pump_type is None:
            sys_cooling['type'] = 'heat_pump'
        else:
            sys_cooling['type'] = heat_pump_type_map[heat_pump_type]
    else:
        assert clgsys.tag.endswith('CoolingSystem')
        hpxml_cooling_type = doxpath(clgsys,'h:CoolingSystemType/text()')
        sys_cooling['type'] = {'central air conditioning': 'split_dx',
                               'room air conditioner': 'packaged_dx',
                               'mini-split': 'split_dx',
                               'evaporative cooler': 'dec'}[hpxml_cooling_type]
        # TODO: Figure out how to specify indirect and direct/indirect evap coolers
        
    
    # cooling efficiency
    eff_units = {'split_dx': 'SEER',
                 'packaged_dx': 'EER',
                 'heat_pump': 'SEER',
                 'gchp': 'SEER',
                 'dec': None,
                 'iec': None,
                 'idec': None}[sys_cooling['type']]
    if eff_units is not None:
        clgeffxpathexpr = '(h:AnnualCoolingEfficiency|h:AnnualCoolEfficiency)[h:Units=$effunits]/h:Value/text()'
        eff_els = clgsys.xpath(clgeffxpathexpr,namespaces=ns,
                               effunits=eff_units)
    else:
        eff_els = []
    if len(eff_els) == 0:
        # Use the year instead
        sys_cooling['efficiency_method'] = 'shipment_weighted'
        sys_cooling['year'] = int(clgsys.xpath('(h:YearInstalled|h:ModelYear)/text()',namespaces=ns)[0])
    else:
        # Use the efficiency of the first element found.
        sys_cooling['efficiency_method'] = 'user'
        sys_cooling['efficiency'] = float(eff_els[0])
    sys_cooling['capacity'] = convert_to_type(float,doxpath(clgsys,'h:CoolingCapacity/text()'))
    return sys_cooling
        

def get_or_create_child(parent,childname,insertpos=-1):
    child = parent.find(childname)
    if child is None:
        child = etree.Element(childname)
        parent.insert(insertpos,child)
    return child

def addns(x):
    repl = lambda m: ('{%(' + m.group(1) + ')s}') % ns
    return nsre.sub(repl,x)

def insert_element_in_order(parent,child,elorder):
    fullelorder = map(addns,elorder)
    childidx = fullelorder.index(child.tag)
    if len(parent) == 0:
        parent.append(child)
    else:
        for i,el in enumerate(parent):
            try:
                idx = fullelorder.index(el.tag)
            except ValueError:
                continue
            if idx > childidx:
                parent.insert(i,child)
                return

def apply_nrel_assumptions(b):
    
    # Assume the back of the house has the largest window area
    site = get_or_create_child(doxpath(b,'h:BuildingDetails/h:BuildingSummary'),addns('h:Site'),0)
    doxpath(site,'h:OrientationOfFrontOfHome/text()')
    if doxpath(site,'h:AzimuthOfFrontOfHome/text()') is None and \
       doxpath(site,'h:OrientationOfFrontOfHome/text()') is None:
        window_areas = {}
        for window in doxpath(b,'h:BuildingDetails/h:Enclosure/h:Windows/h:Window'):
            azimuth = get_nearest_azimuth(doxpath(window,'h:Azimuth/text()'), 
                                          doxpath(window,'h:Orientation/text()'))
            window_area = float(doxpath(window,'h:Area/text()'))
            try:
                window_areas[azimuth] += window_area
            except KeyError:
                window_areas[azimuth] = window_area
        back_azimuth = max(window_areas.items(),key=lambda x: x[1])[0]
        front_azimuth = (back_azimuth + 180) % 360
        azimuth_el = etree.Element(addns('h:AzimuthOfFrontOfHome'))
        azimuth_el.text = str(front_azimuth)
        insert_element_in_order(site,azimuth_el,site_element_order)
        logging.debug('Assuming the house faces %d',front_azimuth)
    
    # Assume stucco if none specified
    if doxpath(b,'h:BuildingDetails/h:Enclosure/h:Walls/h:Wall/h:Siding') is None:
        logging.debug('Assuming stucco siding')
        for wall in b.xpath('h:BuildingDetails/h:Enclosure/h:Walls/h:Wall',namespaces=ns):
            siding_el = etree.Element(addns('h:Siding'))
            siding_el.text = 'stucco'
            insert_element_in_order(wall,siding_el,wall_element_order)
                
def hpxml_to_hescore_json(hpxmlfilename,outfile,hpxml_bldg_id=None,nrel_assumptions=False):
    hescore_bldg = hpxml_to_hescore_dict(hpxmlfilename,hpxml_bldg_id,nrel_assumptions)
    json.dump(hescore_bldg,outfile,indent=2)
    
def hpxml_to_hescore_dict(hpxmlfilename,hpxml_bldg_id=None,nrel_assumptions=False):
    '''
    Convert a HPXML building file to a python dict with the same structure as the HEScore API
    
    hpxmlfilename - location of HPXML file
    hpxml_bldg_id (optional) - If there is more than one <Building> element in an HPXML file,
        use this one. Otherwise just use the first one.
    nrel_assumptions - Apply the NREL assumptions for files that don't explicitly have certain fields.
    '''
    # Load the xml document into lxml etree
    hpxmldoc = etree.parse(hpxmlfilename, parser=hpxmlparser)
    if hpxml_bldg_id is not None:
        b = doxpath(hpxmldoc,'h:Building[h:BuildingID/@id=$bldgid]',bldgid=hpxml_bldg_id)
    else:
        b = doxpath(hpxmldoc,'h:Building[1]')
    
    # Apply NREL assumptions, if requested
    if nrel_assumptions:
        apply_nrel_assumptions(b)
    schema.assertValid(hpxmldoc)
    
    # Create return dict
    hescore_inputs = {}
    
    # building_address
    bldgaddr = {}
    hescore_inputs['building_address'] = bldgaddr
    hpxmladdress = doxpath(b,'h:Site/h:Address[h:AddressType="street"]')
    if hpxmladdress is None:
        raise TranslationError('The house address must be a street address.')
    bldgaddr['address'] = ' '.join(hpxmladdress.xpath('h:Address1/text() | h:Address2/text()',namespaces=ns))
    bldgaddr['city'] = doxpath(b,'h:Site/h:Address/h:CityMunicipality/text()')
    bldgaddr['state'] = doxpath(b,'h:Site/h:Address/h:StateCode/text()')
    bldgaddr['zip_code'] = doxpath(b,'h:Site/h:Address/h:ZipCode/text()')
    # TODO: verify this mapping with Glenn
    bldgaddr['assessment_type'] = {'audit': 'initial',
                                   'proposed workscope': 'alternative',
                                   'approved workscope': 'alternative',
                                   'construction-period testing/daily test out': 'corrected',
                                   'job completion testing/final inspection': 'final',
                                   'quality assurance/monitoring': 'qa'}[doxpath(b,'h:ProjectStatus/h:EventType/text()')]
    
    # building-----------------------------------------------------------------
    bldg = {}
    hescore_inputs['building'] = bldg
    
    # building.about-----------------------------------------------------------
    bldg['about'] = {}
    bldg_about = bldg['about']
    projstatdateel = b.find('h:ProjectStatus/h:Date',namespaces=ns)
    if projstatdateel is None:
        bldg_about['assessment_date'] = dt.date.today()
    else:
        bldg_about['assessment_date'] = dt.datetime.strptime(projstatdateel.text,'%Y-%m-%d').date()
    bldg_about['assessment_date'] = bldg_about['assessment_date'].isoformat()

    # TODO: See if we can map more of these facility types
    bldg_about['shape'] = {'single-family detached': 'rectangle',
                           'single-family attached': 'town_house',
                           'manufactured home': None,
                           '2-4 unit building': None,
                           '5+ unit building': None,
                           'multi-family - uncategorized': None,
                           'multi-family - town homes': 'town_house',
                           'multi-family - condos': None,
                           'apartment unit': None,
                           'studio unit': None,
                           'other': None,
                           'unknown': None
                           }[doxpath(b,'h:BuildingDetails/h:BuildingSummary/h:BuildingConstruction/h:ResidentialFacilityType/text()')]
    assert bldg_about['shape'] is not None
    if bldg_about['shape'] == 'town_house':
        # TODO: what to do with a house that is attached on three sides?
        # TODO: pull this info from the geometry
        bldg_about['town_house_walls'] = {'stand-alone': None,
                                          'attached on one side': 'back_right_front',
                                          'attached on two sides': 'back_front',
                                          'attached on three sides': None
                                          }[doxpath('h:BuildingDetails/h:BuildingSummary/h:Site/h:Surroundings/text()')]
        assert bldg_about['town_house_walls'] is not None
    
    bldg_cons_el = b.find('h:BuildingDetails/h:BuildingSummary/h:BuildingConstruction',namespaces=ns)
    bldg_about['year_built'] = int(doxpath(bldg_cons_el,'h:YearBuilt/text()'))
    nbedrooms = int(doxpath(bldg_cons_el,'h:NumberofBedrooms/text()'))
    if nbedrooms > 10:
        nbedrooms = 10
    bldg_about['number_bedrooms'] = nbedrooms
    bldg_about['num_floor_above_grade'] = int(math.ceil(float(doxpath(bldg_cons_el,'h:NumberofConditionedFloorsAboveGrade/text()'))))
    avg_ceiling_ht = doxpath(bldg_cons_el,'h:AverageCeilingHeight/text()')
    if avg_ceiling_ht is None:
        avg_ceiling_ht = float(doxpath(bldg_cons_el,'h:ConditionedBuildingVolume/text()')) / \
                                       float(doxpath(bldg_cons_el,'h:ConditionedFloorArea/text()'))
    else:
        avg_ceiling_ht = float(avg_ceiling_ht)
    bldg_about['floor_to_ceiling_height'] = int(round(avg_ceiling_ht))
    bldg_about['conditioned_floor_area'] = float(doxpath(b,'h:BuildingDetails/h:BuildingSummary/h:BuildingConstruction/h:ConditionedFloorArea/text()'))
    
    site_el = doxpath(b,'h:BuildingDetails/h:BuildingSummary/h:Site')
    house_azimuth = get_nearest_azimuth(doxpath(site_el,'h:AzimuthOfFrontOfHome/text()'),
                                        doxpath(site_el,'h:OrientationOfFrontOfHome/text()'))
    bldg_about['orientation'] = {0:   'north',
                        45:  'north_east',
                        90:  'east',
                        135: 'south_east',
                        180: 'south',
                        225: 'south_west',
                        270: 'west',
                        315: 'north_west'}[house_azimuth]
    
    blower_door_test = None
    air_infilt_est = None
    for air_infilt_meas in b.xpath('h:BuildingDetails/h:Enclosure/h:AirInfiltration/h:AirInfiltrationMeasurement',namespaces=ns):
        # Take the last blower door test that is in CFM50 or ACH50
        if doxpath(air_infilt_meas,'h:TypeOfInfiltrationMeasurement/text()') == 'blower door':
            house_pressure = doxpath(air_infilt_meas,'h:HousePressure/text()')
            if house_pressure is not None:
                house_pressure = int(house_pressure)
            if doxpath(air_infilt_meas,'h:BuildingAirLeakage/h:UnitofMeasure/text()') in ('CFM','ACH') and \
               house_pressure == 50:
                blower_door_test = air_infilt_meas
        elif doxpath(air_infilt_meas,'h:TypeOfInfiltrationMeasurement/text()') == 'estimate':
            air_infilt_est = air_infilt_meas
    if blower_door_test is not None:
        bldg_about['blower_door_test'] = True
        if doxpath(blower_door_test,'h:BuildingAirLeakage/h:UnitofMeasure/text()') == 'CFM':
            bldg_about['envelope_leakage'] = float(doxpath(blower_door_test,'h:BuildingAirLeakage/h:AirLeakage/text()'))
        else:
            assert doxpath(blower_door_test,'h:BuildingAirLeakage/h:UnitofMeasure/text()') == 'ACH'
            bldg_about['envelope_leakage'] = bldg_about['floor_to_ceiling_height'] * bldg_about['conditioned_floor_area'] * \
                float(doxpath(blower_door_test,'h:BuildingAirLeakage/h:AirLeakage/text()')) / 60.
    else:
        bldg_about['blower_door_test'] = False
        if len(doxpath(b,'h:BuildingDetails/h:Enclosure/h:AirInfiltration/h:AirSealing')) > 0 or \
           doxpath(air_infilt_est,'h:LeakinessDescription/text()') in ('tight','very tight'):
            bldg_about['air_sealing_present'] = True
        else:
            bldg_about['air_sealing_present'] = False
    
    # building.zone------------------------------------------------------------
    bldg_zone = {}
    bldg['zone'] = bldg_zone
    sidemap = {house_azimuth: 'front',
               (house_azimuth + 90) % 360: 'right',
               (house_azimuth + 180) % 360: 'back',
               (house_azimuth + 270) % 360: 'left'}
    
    # building.zone.zone_roof--------------------------------------------------
    attics = b.xpath('//h:Attic',namespaces=ns)
    rooftypemap = {'cape cod': 'cath_ceiling', 
                   'cathedral ceiling': 'cath_ceiling', 
                   'flat roof': 'cath_ceiling', 
                   'unvented attic': 'cond_attic', 
                   'vented attic': 'vented_attic', 
                   'venting unknown attic': None, 
                   'other': None}
    roof_center_of_cavity_rvalues = \
        {'wf': {'co': dict(zip((0,11,13,15,19,21),(2.7,13.6,15.6,17.6,21.6,23.6))),
                'wo': dict(zip((0,11,13,15,19,21,27),(3.2,14.1,16.1,18.1,22.1,24.1,30.1))),
                'rc': dict(zip((0,11,13,15,19,21,27),(2.2,13.2,15.2,17.2,21.2,23.2,29.2))),
                'lc': dict(zip((0,11,13,15,19,21,27),(2.3,13.2,15.2,17.2,21.2,23.2,29.2))),
                'tg': dict(zip((0,11,13,15,19,21,27),(2.3,13.2,15.2,17.2,21.2,23.2,29.2)))},
         'rb': {'co': {0: 5},
                'wo': {0: 5.5},
                'rc': {0: 4.5},
                'lc': {0: 4.6},
                'tg': {0: 4.6}},
         'ps': {'co': dict(zip((0,11,13,15),(6.8,17.8,19.8,21.8))),
                'wo': dict(zip((0,11,13,15,19,21),(7.3,18.3,20.3,22.3,26.3,28.3))),
                'rc': dict(zip((0,11,13,15,19,21),(6.4,17.4,19.4,21.4,25.4,27.4))),
                'lc': dict(zip((0,11,13,15,19,21),(6.4,17.4,19.4,21.4,25.4,27.4))),
                'tg': dict(zip((0,11,13,15,19,21),(6.4,17.4,19.4,21.4,25.4,27.4)))}}
    hescore_attic_info = {}
    atticds = []
    for attic in attics:
        atticd = {}
        atticds.append(atticd)
        roof = doxpath(b,'//h:Roof[h:SystemIdentifier/@id=$roofid]',roofid=doxpath(attic,'h:AttachedToRoof/@idref'))
        
        # Roof type
        atticd['rooftype'] = rooftypemap[doxpath(attic,'h:AtticType/text()')]
        assert atticd['rooftype'] is not None
        
        # Roof color
        atticd['roofcolor'] = {'light': 'light', 'medium': 'medium', 'dark': 'dark', 'reflective': 'white'}[doxpath(roof,'h:RoofColor/text()')]

        # Exterior finish
        hpxml_roof_type = doxpath(roof,'h:RoofType/text()')
        atticd['extfinish'] = {'shingles': 'co', 
                               'slate or tile shingles': 'lc', 
                               'wood shingles or shakes': 'wo', 
                               'asphalt or fiberglass shingles': 'tg', 
                               'metal surfacing': None, 
                               'expanded polystyrene sheathing': None, 
                               'plastic/rubber/synthetic sheeting': None, 
                               'concrete': 'lc', 
                               'cool roof': None, 
                               'green roof': None, 
                               'no one major type': None, 
                               'other': None}[hpxml_roof_type]
        if atticd['extfinish'] is None:
            raise TranslationError('HEScore does not have an analogy to the HPXML roof type: %s' % hpxml_roof_type)
        
        # construction type
        has_rigid_sheathing = doxpath(attic,'boolean(h:AtticRoofInsulation/h:Layer[h:NominalRValue > 0][h:InstallationType="continuous"][boolean(h:InsulationMaterial/h:Rigid)])')
        has_radiant_barrier = doxpath(roof,'h:RadiantBarrier="true"')
        if has_radiant_barrier:
            atticd['roofconstype'] = 'rb'
        elif has_rigid_sheathing:
            atticd['roofconstype'] = 'ps'
        else:
            atticd['roofconstype'] = 'wf'
        
        # roof R-value
        roof_rvalue = doxpath(attic,'sum(h:AtticRoofInsulation/h:Layer[not(boolean(h:InsulationMaterial/h:Rigid) and h:InstallationType="continuous")]/h:NominalRValue)')
        roof_rvalue, atticd['roof_coc_rvalue'] = \
            min(roof_center_of_cavity_rvalues[atticd['roofconstype']][atticd['extfinish']].items(),
                key=lambda x: abs(x[0] - roof_rvalue))
        
        # attic floor R-value
        atticd['attic_floor_rvalue'] = doxpath(attic,'sum(h:AtticFloorInsulation/h:Layer/h:NominalRValue)')
        
        # Attic area
        atticd['attic_area'] = convert_to_type(float,doxpath(attic,'h:Area/text()'))
    
    def select_attic_category_with_most_total_area(key):
        attic_area_by_cat = {}
        for atticd in atticds:
            try:
                attic_area_by_cat[atticd[key]] += atticd['attic_area']
            except:
                attic_area_by_cat[atticd[key]] = atticd['attic_area']
        return max(attic_area_by_cat,key=lambda x: attic_area_by_cat[x])

    if len(atticds) == 0:
        raise TranslationError('There are no Attic elements in this building.')

    # Get the roof type
    rooftype = select_attic_category_with_most_total_area('rooftype')
    
    # Make sure we're either dealing with all cathedral ceilings or not
    if rooftype == 'cath_ceiling':
        for atticd in atticds:
            if atticd['rooftype'] != 'cath_ceiling':
                atticds.remove(atticd)
    else:
        for atticd in atticds:
            if atticd['rooftype'] == 'cath_ceiling':
                atticds.remove(atticd)

    # Determine predominant roof characteristics
    roofconstype, extfinish, roofcolor, rooftype = \
        map(select_attic_category_with_most_total_area,
            ('roofconstype','extfinish','roofcolor','rooftype'))
        
    # Calculate roof area weighted average effective center-of-cavity R-value
    total_attic_area = sum([atticd['attic_area'] for atticd in atticds])
    if len(atticds) == 1:
        area_wt_coc_roof_rvalue = atticds[0]['roof_coc_rvalue']
    else:
        area_wt_coc_roof_rvalue = \
            sum([atticd['roof_coc_rvalue'] * atticd['attic_area'] for atticd in atticds]) / \
            total_attic_area
    
    # Get Roof R-value
    roffset = roof_center_of_cavity_rvalues[roofconstype][extfinish][0]
    roof_rvalue = min(roof_center_of_cavity_rvalues[roofconstype][extfinish].keys(),
                      key=lambda x: abs(area_wt_coc_roof_rvalue - roffset - x))
        
    # Get Attic Floor R-value
    attic_floor_rvalues = (0,3,6,9,11,19,21,25,30,38,44,49,60)
    attic_floor_rvalue = sum([(min(attic_floor_rvalues,
                                  key=lambda x: abs(atticd['attic_floor_rvalue']-x)) + 0.5) * atticd['attic_area']
                              for atticd in atticds]) / total_attic_area - 0.5
    attic_floor_rvalue = min(attic_floor_rvalues,key=lambda x: abs(attic_floor_rvalue - x))
    
    # store it all
    zone_roof = {}
    bldg['zone']['zone_roof'] = zone_roof
    zone_roof['roof_assembly_code'] = 'rf%s%02d%s' % (roofconstype,roof_rvalue,extfinish)
    zone_roof['roof_color'] = roofcolor
    zone_roof['roof_type'] = rooftype
    if rooftype != 'cath_ceiling':
        zone_roof['ceiling_assembly_code'] = 'ecwf%02d' % attic_floor_rvalue

    # building.zone.zone_roof.zone_skylight -----------------------------------
    zone_skylight = {}
    zone_roof['zone_skylight'] = zone_skylight
    skylights = b.xpath('//h:Skylight',namespaces=ns)
    if len(skylights) > 0:
        uvalues, shgcs, areas = map(list,zip(*[[doxpath(skylight,'h:%s/text()' % x) for x in ('UFactor','SHGC','Area')] for skylight in skylights]))
        assert None not in areas
        areas = map(float,areas)
        zone_skylight['skylight_area'] = sum(areas)
        
        # Remove skylights from the calculation where a uvalue or shgc isn't set.
        idxstoremove = set()
        for i,uvalue in enumerate(uvalues):
            if uvalue is None:
                idxstoremove.add(i)
        for i,shgc in enumerate(shgcs):
            if shgc is None:
                idxstoremove.add(i)
        for i in sorted(idxstoremove,reverse=True):
            uvalues.pop(i)
            shgcs.pop(i)
            areas.pop(i)
        assert len(uvalues) == len(shgcs)
        uvalues = map(float,uvalues)
        shgcs = map(float,shgcs)
        
        if len(uvalues) > 0:
            # Use an area weighted average of the uvalues, shgcs
            zone_skylight['skylight_method'] = 'custom'
            zone_skylight['skylight_u_value'] = sum([uvalue * area for (uvalue,area) in zip(uvalues,areas)]) / sum(areas)
            zone_skylight['skylight_shgc'] = sum([shgc * area for (shgc,area) in zip(shgcs,areas)]) / sum(areas)
        else:
            # use a construction code
            skylight_type_areas = {}
            for skylight in skylights:
                area = convert_to_type(float,doxpath(skylight,'h:Area/text()'))
                if area is None:
                    if len(skylights) == 1:
                        area = 1.0
                    else:
                        raise TranslationError('If there are more than one Skylight elements, each needs to have an area.')
                skylight_code = get_window_code(skylight)
                try:
                    skylight_type_areas[skylight_code] += area
                except KeyError:
                    skylight_type_areas[skylight_code] = area
            zone_skylight['skylight_method'] = 'code'
            zone_skylight['skylight_code'] = max(skylight_type_areas.items(), key=lambda x: x[1])[0]
    
    
    # building.zone.zone_floor-------------------------------------------------
    zone_floor = {}
    bldg_zone['zone_floor'] = zone_floor
    
    foundations = b.xpath('//h:Foundations/h:Foundation',namespaces=ns)
    # get the Foundation element that covers the largest square footage of the house
    foundation = max(foundations, 
                     key=lambda fnd: max([doxpath(fnd,'sum(h:%s/h:Area)' % x) for x in ('Slab','FrameFloor')]))
    
    # Foundation type
    hpxml_foundation_type = doxpath(foundation,'name(h:FoundationType/*)')
    if hpxml_foundation_type == 'Basement':
        bsmtcond = doxpath(foundation,'h:FoundationType/h:Basement/h:Conditioned="true"')
        if bsmtcond:
            zone_floor['foundation_type'] = 'cond_basement'
        else:
            # assumed unconditioned basement if h:Conditioned is missing
            zone_floor['foundation_type'] = 'uncond_basement'
    elif hpxml_foundation_type == 'Crawlspace':
        crawlvented = doxpath(foundation,'h:FoundationType/h:Crawlspace/h:Vented="true"')
        if crawlvented:
            zone_floor['foundation_type'] = 'vented_crawl'
        else:
            # assumes unvented crawlspace if h:Vented is missing. 
            zone_floor['foundation_type'] = 'unvented_crawl'
    elif hpxml_foundation_type == 'SlabOnGrade':
        zone_floor['foundation_type'] = 'slab_on_grade'
    elif hpxml_foundation_type == 'Ambient':
        zone_floor['foundation_type'] = 'vented_crawl'
    else:
        raise TranslationError('HEScore does not have a foundation type analogous to: %s' % hpxml_foundation_type)
    
    # Foundation Wall insulation R-value
    fwra = 0
    fwtotalarea = 0
    foundationwalls = foundation.xpath('h:FoundationWall',namespaces=ns)
    fw_eff_rvalues = dict(zip((0,5,11,19),(4,7.9,11.6,19.6)))
    if len(foundationwalls) > 0:
        assert zone_floor['foundation_type'] != 'slab_on_grade'
        del fw_eff_rvalues[5] # remove the value for slab insulation
        for fwall in foundationwalls:
            fwarea, fwlength, fwheight = \
                map(lambda x: convert_to_type(float,doxpath(fwall,'h:%s/text()' % x)),
                    ('Area','Length','Height'))
            if fwarea is None:
                try:
                    fwarea = fwlength * fwheight
                except TypeError:
                    if len(foundationwalls) == 1:
                        fwarea = 1.0
                    else:
                        raise TranslationError('If there is more than one FoundationWall, an Area is required for each.')
            fwrvalue = doxpath(fwall,'sum(h:Insulation/h:Layer/h:NominalRValue)')
            fweffrvalue = fw_eff_rvalues[min(fw_eff_rvalues.keys(), key=lambda x: abs(fwrvalue - x))]
            fwra += fweffrvalue * fwarea
            fwtotalarea += fwarea
        zone_floor['foundation_insulation_level'] = fwra / fwtotalarea - 4.0
    elif zone_floor['foundation_type'] == 'slab_on_grade':
        del fw_eff_rvalues[11] # remove unused values 
        del fw_eff_rvalues[19] 
        slabs = foundation.xpath('h:Slab',namespaces=ns)
        slabra = 0
        slabtotalperimeter = 0
        for slab in slabs:
            exp_perimeter = convert_to_type(float,doxpath(slab,'h:ExposedPerimeter/text()'))
            if exp_perimeter is None:
                if len(slabs) == 1:
                    exp_perimeter = 1.0
                else:
                    raise TranslationError('If there is more than one Slab, an ExposedPerimeter is required for each.')
            slabrvalue = doxpath(slab,'sum(h:PerimeterInsulation/h:Layer/h:NominalRValue)')
            slabeffrvalue = fw_eff_rvalues[min(fw_eff_rvalues.keys(), key=lambda x: abs(slabrvalue - x))]
            slabra += slabeffrvalue * exp_perimeter
            slabtotalperimeter += exp_perimeter
        zone_floor['foundation_insulation_level'] = slabra / slabtotalperimeter - 4.0
    else:
        zone_floor['foundation_insulation_level'] = 0
    zone_floor['foundation_insulation_level'] = min(fw_eff_rvalues.keys(), key=lambda x: abs(zone_floor['foundation_insulation_level'] - x))
    
    # floor above foundation insulation
    ffra = 0
    fftotalarea = 0
    framefloors = foundation.xpath('h:FrameFloor',namespaces=ns)
    floor_eff_rvalues = dict(zip((0,11,13,15,19,21,25,30,38),(4.0,15.8,17.8,19.8,23.8,25.8,31.8,37.8,42.8)))
    if len(framefloors) > 0:
        for framefloor in framefloors:
            ffarea = convert_to_type(float,doxpath(framefloor,'h:Area/text()'))
            if ffarea is None:
                if len(framefloors) == 1:
                    ffarea = 1.0
                else:
                    raise TranslationError('If there is more than one FrameFloor, an Area is required for each.')
            ffrvalue = doxpath(framefloor,'sum(h:Insulation/h:Layer/h:NominalRValue)')
            ffeffrvalue = floor_eff_rvalues[min(floor_eff_rvalues.keys(), key=lambda x: abs(ffrvalue - x))]
            ffra += ffarea * ffeffrvalue
            fftotalarea += ffarea
        ffrvalue = ffra / fftotalarea - 4.0
        zone_floor['floor_assembly_code'] = 'efwf%02dca' % min(floor_eff_rvalues.keys(), key=lambda x: abs(ffrvalue - x))
    else:
        zone_floor['floor_assembly_code'] = 'efwf00ca'

    # building.zone.zone_wall--------------------------------------------------
    bldg_zone['zone_wall'] = []
    
    hpxmlwalls = dict([(side,[]) for side in sidemap.values()])
    hpxmlwalls['noside'] = []
    for wall in b.xpath('h:BuildingDetails/h:Enclosure/h:Walls/h:Wall',namespaces=ns):
        walld = {'assembly_code': get_wall_assembly_code(wall),
                 'area': convert_to_type(float,doxpath(wall,'h:Area/text()')),
                 'id': doxpath(wall,'h:SystemIdentifier/@id')}
        
        try:
            wall_azimuth = get_nearest_azimuth(doxpath(wall,'h:Azimuth/text()'),
                                               doxpath(wall,'h:Orientation/text()'))
        except AssertionError:
            # There is no directional information in the HPXML wall
            wall_side = 'noside'
            hpxmlwalls[wall_side].append(walld)
        else:
            try:
                wall_side = sidemap[wall_azimuth]
            except KeyError:
                # The direction of the wall is in between sides
                # split the area between sides
                walld['area'] /= 2.0
                hpxmlwalls[sidemap[unspin_azimuth(wall_azimuth+45)]].append(dict(walld))
                hpxmlwalls[sidemap[unspin_azimuth(wall_azimuth-45)]].append(dict(walld))                
            else:
                hpxmlwalls[wall_side].append(walld)

    if len(hpxmlwalls['noside']) > 0 and map(len,[hpxmlwalls[key] for key in sidemap.values()]) == ([0] * 4):
        # if none of the walls have orientation information
        # copy the walls to all sides
        bldg_zone['wall_construction_same'] = False
        for side in sidemap.values():
            hpxmlwalls[side] = hpxmlwalls['noside']
        del hpxmlwalls['noside']
    else:
        # make sure all of the walls have an orientation
        if len(hpxmlwalls['noside']) > 0:
            raise TranslationError('Some of the HPXML walls have orientation information and others do not.')
        bldg_zone['wall_construction_same'] = False
    
    # Wall effective R-value map
    wall_const_types = ('wf','ps','ov','br','cb','sb')
    wall_ext_finish_types = ('wo','st','vi','al','br','nn')
    wall_eff_rvalues = {}
    wall_eff_rvalues['wf'] = dict(zip(wall_ext_finish_types[:-1],[dict(zip((0,3,7,11,13,15,19,21),x)) 
                                                             for x in [(3.6, 5.7, 9.7, 13.7, 15.7, 17.7, 21.7, 23.7), 
                                                                       (2.3, 4.4, 8.4, 12.4, 14.4, 16.4, 20.4, 22.4), 
                                                                       (2.2, 4.3, 8.3, 12.3, 14.3, 16.3, 20.3, 22.3), 
                                                                       (2.1, 4.2, 8.2, 12.2, 14.2, 16.2, 20.2, 22.2), 
                                                                       (2.9, 5.0, 9.0, 13.0, 15.0, 17.0, 21.0, 23.0)]]))
    wall_eff_rvalues['ps'] = dict(zip(wall_ext_finish_types[:-1],[dict(zip((11,13,15,19,21),x))
                                                                  for x in [(17.1, 19.1, 21.1, 25.1, 27.1), 
                                                                            (16.4, 18.4, 20.4, 24.4, 26.4), 
                                                                            (16.3, 18.3, 20.3, 24.3, 26.3), 
                                                                            (16.2, 18.2, 20.2, 24.2, 26.2), 
                                                                            (17.0, 19.0, 21.0, 25.0, 27.0)]]))
    wall_eff_rvalues['ov'] = dict(zip(wall_ext_finish_types[:-1],[dict(zip((19,21,27,33,38),x))
                                                                  for x in [(21.0, 23.0, 29.0, 35.0, 40.0), 
                                                                            (20.3, 22.3, 28.3, 34.3, 39.3), 
                                                                            (20.1, 22.1, 28.1, 34.1, 39.1), 
                                                                            (20.1, 22.1, 28.1, 34.1, 39.1), 
                                                                            (20.9, 22.9, 28.9, 34.9, 39.9)]]))
    wall_eff_rvalues['br'] = {'nn': dict(zip((0,5,10),(2.9,7.9,12.8)))}
    wall_eff_rvalues['cb'] = dict(zip(('st','br','nn'),[dict(zip((0,3,6),x)) 
                                                        for x in [(4.1, 5.7, 8.5),
                                                                  (5.6, 7.2, 10),
                                                                  (4, 5.6, 8.3)]]))
    wall_eff_rvalues['sb'] = {'st': {0: 58.8}}

    # build HEScore walls
    for side in sidemap.values():
        heswall = {}
        heswall['side'] = side
        if len(hpxmlwalls[side]) == 1 and hpxmlwalls[side][0]['area'] is None:
            hpxmlwalls[side][0]['area'] = 1.0
        elif len(hpxmlwalls[side]) > 1 and None in [x['area'] for x in hpxmlwalls[side]]:
            raise TranslationError('The %s side of the house has %d walls and they do not all have areas.' % (side,len(hpxmlwalls[side])))
        wall_const_type_areas = dict(zip(wall_const_types,[0] * len(wall_const_types)))
        wall_ext_finish_areas = dict(zip(wall_ext_finish_types, [0] * len(wall_ext_finish_types)))
        wallra = 0
        walltotalarea = 0
        for walld in hpxmlwalls[side]:
            const_type = walld['assembly_code'][2:4]
            ext_finish = walld['assembly_code'][6:8]
            rvalue = int(walld['assembly_code'][4:6])
            eff_rvalue = wall_eff_rvalues[const_type][ext_finish][rvalue]
            wallra += walld['area'] * eff_rvalue
            walltotalarea += walld['area']
            wall_const_type_areas[const_type] += walld['area']
            wall_ext_finish_areas[ext_finish] += walld['area']
        const_type = max(wall_const_type_areas.keys(), key=lambda x: wall_const_type_areas[x])
        ext_finish = max(wall_ext_finish_areas.keys(), key=lambda x: wall_ext_finish_areas[x])
        try:
            roffset = wall_eff_rvalues[const_type][ext_finish][0]
        except KeyError:
            rvalue, eff_rvalue = min(wall_eff_rvalues[const_type][ext_finish].items(),key=lambda x: x[0])
            roffset = eff_rvalue - rvalue
        if const_type == 'ps':
            roffset += 4.16
        comb_rvalue = min(wall_eff_rvalues[const_type][ext_finish].keys(), 
                          key=lambda x: abs(wallra / walltotalarea - roffset - x))
        heswall['wall_assembly_code'] = 'ew%s%02d%s' % (const_type,comb_rvalue,ext_finish)
        bldg_zone['zone_wall'].append(heswall)
    
    # building.zone.zone_wall.zone_window--------------------------------------
    bldg_zone['window_construction_same'] = False
    
    # Assign each window to a side of the house
    hpxmlwindows = dict([(side,[]) for side in sidemap.values()])
    for hpxmlwndw in b.xpath('h:BuildingDetails/h:Enclosure/h:Windows/h:Window',namespaces=ns):

        # Get the area, uvalue, SHGC, or window_code
        windowd = {'area': convert_to_type(float,doxpath(hpxmlwndw,'h:Area/text()'))}
        windowd['uvalue'] = convert_to_type(float,doxpath(hpxmlwndw,'h:UFactor/text()'))
        windowd['shgc'] = convert_to_type(float,doxpath(hpxmlwndw,'h:SHGC/text()'))
        if windowd['uvalue'] is not None and windowd['shgc'] is not None:
            windowd['window_code'] = None
        else:
            windowd['window_code'] = get_window_code(hpxmlwndw)
        
        # Window side
        window_sides = []
        attached_to_wall_id = doxpath(hpxmlwndw,'h:AttachedToWall/@idref')
        if attached_to_wall_id is not None and not bldg_zone['wall_construction_same']:
            # Give preference to the Attached to Wall element to determine the side of the house.
            for side,walls in hpxmlwalls.items():
                for wall in walls:
                    if attached_to_wall_id == walld['id']:
                        window_sides.append(side)
                        break
        else:
            # If there's not Attached to Wall element, figure it out from the Azimuth/Orientation
            try:
                wndw_azimuth = get_nearest_azimuth(doxpath(hpxmlwndw,'h:Azimuth/text()'),doxpath(hpxmlwndw,'h:Orientation/text()'))
                window_sides = [sidemap[wndw_azimuth]]
            except AssertionError:
                # there's no directional information in the window
                raise TranslationError('All windows need to have either an AttachedToWall, Orientation, or Azimuth sub element.')
            else:
                try:
                    window_sides = [sidemap[wndw_azimuth]]
                except KeyError:
                    # the direction of the window is between sides, split area
                    window_sides = [sidemap[unspin_azimuth(wndw_azimuth+x)] for x in (-45,45)]
        
        # Assign properties and areas to the correct side of the house
        for window_side in window_sides:
            windowd['area'] /= float(len(window_sides))
            hpxmlwindows[window_side].append(dict(windowd))
    
    # Determine the predominant window characteristics and create HEScore windows 
    bldg_zone['window_construction_same'] = False
    for side,windows in hpxmlwindows.items():
        
        # Add to the correct wall
        for heswall in bldg_zone['zone_wall']:
            if heswall['side'] == side:
                break
        
        zone_window = {}
        heswall['zone_window'] = zone_window
        
        # If there are no windows on that side of the house
        if len(windows) == 0:
            zone_window['window_area'] = 0
            zone_window['window_code'] = 'scna'
            continue
        
        # Get the list of uvalues and shgcs for the windows on this side of the house.
        uvalues,shgcs,areas = map(list,zip(*[[window[x] for x in ('uvalue','shgc','area')] for window in windows]))
        
        # Make sure every window has an area
        assert None not in areas
        zone_window['window_area'] = sum(areas)

        # Remove windows from the calculation where a uvalue or shgc isn't set.
        idxstoremove = set()
        for i,uvalue in enumerate(uvalues):
            if uvalue is None:
                idxstoremove.add(i)
        for i,shgc in enumerate(shgcs):
            if shgc is None:
                idxstoremove.add(i)
        for i in sorted(idxstoremove,reverse=True):
            uvalues.pop(i)
            shgcs.pop(i)
            areas.pop(i)
        assert len(uvalues) == len(shgcs)
        
        if len(uvalues) > 0:
            # Use an area weighted average of the uvalues, shgcs
            zone_window['window_method'] = 'custom'
            zone_window['window_u_value'] = sum([uvalue * area for (uvalue,area) in zip(uvalues,areas)]) / sum(areas)
            zone_window['window_shgc'] = sum([shgc * area for (shgc,area) in zip(shgcs,areas)]) / sum(areas)
        else:
            # Use a window construction code
            zone_window['window_method'] = 'code'
            # Use the properties of the largest window on the side
            window_code_areas = {}
            for window in windows:
                assert window['window_code'] is not None
                try:
                    window_code_areas[window['window_code']] += window['area']
                except KeyError:
                    window_code_areas[window['window_code']] = window['area']
            zone_window['window_code'] = max(window_code_areas.items(),key=lambda x: x[1])[0]
            
    # systems.heating----------------------------------------------------------
    eff_method_map = {'user': 'efficiency', 'shipment_weighted': 'year'}
    bldg_systems = {}
    bldg['systems'] = bldg_systems
    sys_heating = {}
    bldg_systems['heating'] = sys_heating
        
    # Use the primary heating system specified in the HPXML file if that element exists.
    primaryhtgsys = doxpath(b,'//h:HVACPlant/*[//h:HVACPlant/h:PrimarySystems/h:PrimaryHeatingSystem/@idref=h:SystemIdentifier/@id]')
    
    if primaryhtgsys is None:
        # A primary heating system isn't specified, get the properties of all of them
        htgsystems = []    
        for htgsys in b.xpath('//h:HVACPlant/h:HeatingSystem|//h:HVACPlant/h:HeatPump',namespaces=ns):
            try:
                htgsysd = get_heating_system_type(htgsys)
            except TranslationError:
                continue
            else:
                htgsystems.append(htgsysd)
        capacities = [x['capacity'] for x in htgsystems]
        if None in capacities:
            if len(capacities) == 1:
                htgsystems[0]['capacity'] = 1.0
            else:
                raise TranslationError('If a primary heating system is not defined, each heating system must have a capacity')   
    else:
        htgsystems = [get_heating_system_type(primaryhtgsys)]
    
    htgsys_by_capacity = {}
    htgsys_groupby_keys = ('type','fuel_primary','efficiency_method')
    for htgsysd in htgsystems:
        try:
            combhtgsys = htgsys_by_capacity[tuple([htgsysd[x] for x in htgsys_groupby_keys])]
        except KeyError:
            combhtgsys = {'totalcapacity': 0, 'n': 0, 'sum': 0}
            for key in htgsys_groupby_keys:
                combhtgsys[key] = htgsysd[key]
            htgsys_by_capacity[tuple([htgsysd[x] for x in htgsys_groupby_keys])] = combhtgsys
        
        combhtgsys['totalcapacity'] += htgsysd['capacity']
        combhtgsys['sum'] +=  htgsysd[eff_method_map[combhtgsys['efficiency_method']]] * htgsysd['capacity']
        combhtgsys['n'] += 1
    
    for combhtgsys in htgsys_by_capacity.values():
        if combhtgsys['efficiency_method'] == 'user':
            if combhtgsys['type'] in ('heat_pump','gchp'):
                htg_round_decimal_places = 1
            else:
                htg_round_decimal_places = 2 
            combhtgsys[eff_method_map[combhtgsys['efficiency_method']]] = round(combhtgsys['sum'] / combhtgsys['totalcapacity'], htg_round_decimal_places)
        else:
            assert combhtgsys['efficiency_method'] == 'shipment_weighted'
            combhtgsys[eff_method_map[combhtgsys['efficiency_method']]] = int(round(combhtgsys['sum'] / combhtgsys['totalcapacity']))
        del combhtgsys['sum']
        del combhtgsys['n']

    if len(htgsys_by_capacity) > 0:
        sys_heating.update(max(htgsys_by_capacity.values(),key=lambda x: x['totalcapacity']))
        del sys_heating['totalcapacity']
    else:
        sys_heating = {'type': 'none'}
        
    # systems.cooling ---------------------------------------------------------
    sys_cooling = {}
    bldg_systems['cooling'] = sys_cooling
    
    primaryclgsys = doxpath(b,'//h:HVACPlant/*[//h:HVACPlant/h:PrimarySystems/h:PrimaryCoolingSystem/@idref=h:SystemIdentifier/@id]')
    
    if primaryclgsys is None:
        # A primary cooling system isn't specified, get the properties of all of them.
        clgsystems = []
        for clgsys in b.xpath('//h:HVACPlant/h:CoolingSystem|//h:HVACPlant/h:HeatPump',namespaces=ns):
            try:
                clgsysd = get_cooling_system_type(clgsys)
            except TranslationError:
                continue
            else:
                clgsystems.append(clgsysd)
        capacities = [x['capacity'] for x in clgsystems]
        if None in capacities:
            if len(capacities) == 1:
                clgsystems[0]['capacity'] = 1.0
            else:
                raise TranslationError('If a primary cooling system is not defined, each cooling system must have a capacity')
    else:
        clgsystems = [get_cooling_system_type(primaryclgsys)]
     
    clgsys_by_capacity = {}
    clgsys_groupby_keys = ('type','efficiency_method')
    for clgsysd in clgsystems:
        try:
            combclgsys = clgsys_by_capacity[tuple([clgsysd[x] for x in clgsys_groupby_keys])]
        except KeyError:
            combclgsys = {'totalcapacity': 0, 'n': 0, 'sum': 0}
            for key in clgsys_groupby_keys:
                combclgsys[key] = clgsysd[key]
            clgsys_by_capacity[tuple([clgsysd[x] for x in clgsys_groupby_keys])] = combclgsys
        
        combclgsys['totalcapacity'] += clgsysd['capacity']
        combclgsys['sum'] += clgsysd[eff_method_map[combclgsys['efficiency_method']]] * clgsysd['capacity']
        combclgsys['n'] += 1
    
    for combclgsys in clgsys_by_capacity.values():
        if combclgsys['efficiency_method'] == 'user':
            combclgsys[eff_method_map[combclgsys['efficiency_method']]] = round(combclgsys['sum'] / combclgsys['totalcapacity'],1)
        else:
            assert combclgsys['efficiency_method'] == 'shipment_weighted'
            combclgsys[eff_method_map[combclgsys['efficiency_method']]] = int(round(combclgsys['sum'] / combclgsys['totalcapacity']))
        del combclgsys['sum']
        del combclgsys['n']
    
    if len(clgsys_by_capacity) > 0:
        sys_cooling.update(max(clgsys_by_capacity.values(),key=lambda x: x['totalcapacity']))
        del sys_cooling['totalcapacity']
    else:
        sys_cooling = {'type': 'none'}
        
    # systems.hvac_distribution -----------------------------------------------
    bldg_systems['hvac_distribution'] = []
    duct_location_map = {'conditioned space': 'cond_space', 
                         'unconditioned space': None, 
                         'unconditioned basement': 'uncond_basement', 
                         'unvented crawlspace': 'unvented_crawl', 
                         'vented crawlspace': 'vented_crawl', 
                         'crawlspace': None, 
                         'unconditioned attic': 'uncond_attic', 
                         'interstitial space': None, 
                         'garage': None, 
                         'outside': None}
    airdistributionxpath = '//h:HVACDistribution/h:DistributionSystemType/h:AirDistribution'
    allhave_cfaserved = True
    allmissing_cfaserved = True
    airdistsystems_ductfracs = []
    hescore_ductloc_has_ins = {}
    airdistsys_issealed = []
    for airdistsys in b.xpath(airdistributionxpath,namespaces=ns):
        airdistsys_ductfracs = {}
        airdistsys_issealed.append(airdistsys.xpath('h:DuctLeakageMeasurement[not(h:DuctType) or h:DuctType="supply"]/h:LeakinessObservedVisualInspection="connections sealed w mastic"',namespaces=ns))
        for duct in airdistsys.xpath('h:Ducts[not(h:DuctType) or h:DuctType="supply"]',namespaces=ns):
            frac_duct_area = float(doxpath(duct,'h:FractionDuctArea/text()'))
            hpxml_duct_location = doxpath(duct,'h:DuctLocation/text()')
            hescore_duct_location = duct_location_map[hpxml_duct_location]
            if hescore_duct_location is None:
                raise TranslationError('No comparable duct location in HEScore: %s' % hpxml_duct_location)
            try:
                airdistsys_ductfracs[hescore_duct_location] += frac_duct_area
            except KeyError:
                airdistsys_ductfracs[hescore_duct_location] = frac_duct_area
            duct_has_ins = duct.xpath('h:DuctInsulationRValue > 0 or h:DuctInsulationThickness > 0',namespaces=ns)
            try:
                hescore_ductloc_has_ins[hescore_duct_location] = hescore_ductloc_has_ins[hescore_duct_location] or duct_has_ins
            except KeyError:
                hescore_ductloc_has_ins[hescore_duct_location] = duct_has_ins
        assert abs(1 - sum(airdistsys_ductfracs.values())) < 0.001
        cfaserved = doxpath(airdistsys.getparent().getparent(),'h:ConditionedFloorAreaServed/text()')
        if cfaserved is not None:
            cfaserved = float(cfaserved)
            airdistsys_ductfracs = dict([(key,value * cfaserved) for key,value in airdistsys_ductfracs.items()])
            allmissing_cfaserved = False
        else:
            allhave_cfaserved = False
        airdistsystems_ductfracs.append(airdistsys_ductfracs)
    allsame_cfaserved = allhave_cfaserved or allmissing_cfaserved
        
    # Combine all
    ductfracs = {}
    issealedfracs = {}
    if (len(airdistsystems_ductfracs) > 1 and allsame_cfaserved) or len(airdistsystems_ductfracs) == 1:
        for airdistsys_ductfracs,issealed in zip(airdistsystems_ductfracs,airdistsys_issealed):
            for key,value in airdistsys_ductfracs.items():
                try:
                    ductfracs[key] += value
                except KeyError:
                    ductfracs[key] = value
                try:
                    issealedfracs[key] += value * float(issealed)
                except KeyError:
                    issealedfracs[key] = value * float(issealed)
                    
    else:
        raise TranslationError('All HVACDistribution elements need to have or NOT have the ConditionFloorAreaServed subelement.')  
    
    # Make sure there are only three locations and normalize to percentages
    top3locations = sorted(ductfracs.keys(), key=lambda x: ductfracs[x], reverse=True)[0:3]
    for location in ductfracs.keys():
        if location not in top3locations:
            del ductfracs[location]
            del hescore_ductloc_has_ins[location]
            del issealedfracs[location]
    issealedfracs = dict([(key,bool(round(x / ductfracs[key]))) for key,x in issealedfracs.items()])
    normalization_denominator = sum(ductfracs.values())
    ductfracs = dict([(key,int(round(x / normalization_denominator * 100))) for key,x in ductfracs.items()])
    # Sometimes with the rounding it adds up to a number slightly off of 100, adjust the largest fraction to make it add up to 100
    ductfracs[top3locations[0]] += 100 - sum(ductfracs.values())
    
    for i,location in enumerate(top3locations,1):
        hvacd = {}
        hvacd['name'] = 'duct%d' % i
        hvacd['location'] = location
        hvacd['fraction'] = ductfracs[location]
        hvacd['insulated'] = hescore_ductloc_has_ins[location]
        hvacd['sealed'] = issealedfracs[location]
        bldg_systems['hvac_distribution'].append(hvacd)
    
    # systems.domestic_hot_water ----------------------------------------------
    sys_dhw = {}
    bldg_systems['domestic_hot_water'] = sys_dhw
    
    water_heating_systems = doxpath(b,'//h:WaterHeatingSystem')
    if isinstance(water_heating_systems,list):
        dhwfracs = map(lambda x: None if x is None else float(x), 
                       [doxpath(water_heating_system,'h:FractionDHWLoadServed/text()') for water_heating_system in water_heating_systems])
        if None in dhwfracs:
            primarydhw = water_heating_systems[0]
        else:
            primarydhw = max(zip(water_heating_systems,dhwfracs),key=lambda x: x[1])[0]
    elif water_heating_systems is None:
        raise TranslationError('No water heating systems found.')
    else:
        primarydhw = water_heating_systems
    water_heater_type = doxpath(primarydhw,'h:WaterHeaterType/text()')
    if water_heater_type in ('storage water heater','instantaneous water heater'):
        sys_dhw['category'] = 'unit'
        sys_dhw['type'] = 'storage'
    elif water_heater_type == 'space-heating boiler with storage tank':
        sys_dhw['category'] = 'combined'
        sys_dhw['type'] = 'indirect'
    elif water_heater_type == 'space-heating boiler with tankless coil':
        sys_dhw['category'] = 'combined'
        sys_dhw['type'] = 'tankless_coil'
    elif water_heater_type == 'heat pump water heater':
        sys_dhw['category'] = 'unit'
        sys_dhw['type'] = 'heat_pump'
        sys_dhw['fuel_primary'] = 'electric'
    else:
        raise TranslationError('HEScore cannot model the water heater type: %s' % water_heater_type)
    
    sys_dhw['fuel_primary'] = fuel_type_mapping[doxpath(primarydhw,'h:FuelType/text()')]
    
    if not sys_dhw['category'] == 'combined':
        energyfactor = doxpath(primarydhw,'h:EnergyFactor/text()')
        if energyfactor is not None:
            sys_dhw['efficiency_method'] = 'user'
            sys_dhw['energy_factor'] = round(float(energyfactor),2)
        else:
            dhwyear = int(doxpath(primarydhw,'(h:YearInstalled|h:ModelYear)[1]/text()'))
            if dhwyear < 1972:
                dhwyear = 1972
            sys_dhw['efficiency_method'] = 'shipment_weighted'
            sys_dhw['year'] = dhwyear
            
    return hescore_inputs
    

def main():
    parser = argparse.ArgumentParser(description='Convert HPXML v1.1.1 files to HEScore inputs')
    parser.add_argument('hpxml_input',help='Filename or directory name of hpxml file(s)')
    parser.add_argument('-o','--output', type=argparse.FileType('w'), default=sys.stdout,
                        help='Filename of output file in json format. If not provided, will go to stdout.')
    parser.add_argument('--outdir',help='output directory if inputs are a directory')
    parser.add_argument('--bldgid',help='HPXML building id to score if there are more than one <Building/> elements. Default: first one.')
    parser.add_argument('--nrelassumptions',action='store_true',help='Use the NREL assumptions to guess at data elements that are missing.')
    
    args = parser.parse_args()
    
    if os.path.isdir(args.hpxml_input):
        assert os.path.isdir(args.outdir)
        # Directory of hpxml files
        for filename in os.listdir(args.hpxml_input):
            basename, ext = os.path.splitext(filename)
            if not ext == '.xml':
                continue
            logging.debug('Translating %s',filename)
            try:
                with open(os.path.join(os.path.abspath(args.outdir), basename + '.json'),'w') as f:
                    hpxml_to_hescore_json(os.path.join(os.path.abspath(args.hpxml_input),filename),
                                            f,
                                            nrel_assumptions=args.nrelassumptions)
            except:
                tb = traceback.format_exc()
                tblist = tb.splitlines()
                for tb in tblist:
                    logging.error(tb)
            
    else:
        # One hpxml file
        assert os.path.isfile(args.hpxml_input)
        hpxml_to_hescore_json(os.path.abspath(args.hpxml_input),args.output,nrel_assumptions=args.nrelassumptions)

if __name__ == '__main__':
    main()