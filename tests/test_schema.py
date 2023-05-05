import os
import jsonschema
import json
import pathlib
import copy
import glob
import pytest

hescore_examples = [
    'townhouse_walls',
    'house1'
]


def get_example_json(filebase):
    rootdir = pathlib.Path(__file__).resolve().parent.parent
    jsonfilepath = str(rootdir / 'examples' / f'{filebase}.json')
    with open(jsonfilepath) as f:
        js = json.load(f)
    return js


def get_json_schema():
    this_path = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(os.path.dirname(this_path), 'hescorehpxml', 'schemas', 'hescore_json.schema.json')
    with open(schema_path, 'r') as js:
        schema = json.loads(js.read())
    return schema


def get_error_messages(jsonfile, jsonschema):
    errors = []
    for error in sorted(jsonschema.iter_errors(jsonfile), key=str):
        try:
            errors.append(error.schema["error_msg"])
        except KeyError:
            errors.append(error.message)
    return errors


def assert_required_error(errors, *required_fields):
    fields = ', '.join(f"'{x}'" for x in required_fields)
    assert any(x.endswith(f"should not be valid under {{'required': [{fields}]}}") for x in errors)


def test_schema_version_validation():
    schema = get_json_schema()
    error = jsonschema.Draft7Validator.check_schema(schema)
    assert error is None


def test_example_files():
    rootdir = pathlib.Path(__file__).resolve().parent.parent
    examplefiles = str(rootdir / 'examples' / '*.json')
    for examplefile in glob.glob(examplefiles):
        hpxml_filebase = os.path.basename(examplefile).split('.')[0]
        schema = get_json_schema()
        js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
        js = get_example_json(hpxml_filebase)
        errors = get_error_messages(js, js_schema)
        assert len(errors) == 0, f"{examplefile} is invalid"


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_building_about(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1_about = copy.deepcopy(js['about'])
    del js1['about']
    js1['about'] = []
    js1['about'].append(js1_about)
    js1['about'].append(js1_about)
    errors = get_error_messages(js1, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        assert any(error.find("single_family_attached") > -1 and
                   error.endswith("is not of type 'object'") for error in errors)
    elif hpxml_filebase == 'house1':
        assert any(error.find("single_family_detached") > -1 and
                   error.endswith("is not of type 'object'") for error in errors)

    js2 = copy.deepcopy(js)
    if hpxml_filebase == 'townhouse_walls':
        del js2['about']['envelope_leakage']
        errors = get_error_messages(js2, js_schema)
        assert "'envelope_leakage' is a required property" in errors
        assert "'air_sealing_present' is a required property" not in errors
        js2['about']['blower_door_test'] = False
        errors = get_error_messages(js2, js_schema)
        assert "'air_sealing_present' is a required property" in errors
    elif hpxml_filebase == 'house1':
        del js2['about']['air_sealing_present']
        errors = get_error_messages(js2, js_schema)
        assert "'envelope_leakage' is a required property" not in errors
        assert "'air_sealing_present' is a required property" in errors
    del js2['about']['assessment_date']
    del js2['about']['dwelling_unit_type']
    del js2['about']['year_built']
    del js2['about']['number_bedrooms']
    del js2['about']['num_floor_above_grade']
    del js2['about']['floor_to_ceiling_height']
    del js2['about']['conditioned_floor_area']
    del js2['about']['orientation']
    del js2['about']['blower_door_test']
    errors = get_error_messages(js2, js_schema)
    assert "'assessment_date' is a required property" in errors
    assert "'dwelling_unit_type' is a required property" in errors
    assert "'year_built' is a required property" in errors
    assert "'number_bedrooms' is a required property" in errors
    assert "'num_floor_above_grade' is a required property" in errors
    assert "'floor_to_ceiling_height' is a required property" in errors
    assert "'conditioned_floor_area' is a required property" in errors
    assert "'orientation' is a required property" in errors
    assert "'blower_door_test' is a required property" in errors

    js3 = copy.deepcopy(js)
    js3['about']['assessment_date'] = '2021'
    errors = get_error_messages(js3, js_schema)
    assert "'2021' is not a 'date'" in errors
    if hpxml_filebase == 'townhouse_walls':
        js3['about']['air_sealing_present'] = True
        errors = get_error_messages(js3, js_schema)
        assert_required_error(errors, 'air_sealing_present')
    elif hpxml_filebase == 'house1':
        js3['about']['envelope_leakage'] = 1204
        errors = get_error_messages(js3, js_schema)
        assert_required_error(errors, 'envelope_leakage')


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_building_zone(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)
    zone = copy.deepcopy(js['zone'])
    del js['zone']
    js['zone'] = []
    js['zone'].append(zone)
    js['zone'].append(zone)
    errors = get_error_messages(js, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        assert any(error.startswith("[{'zone_roof': [{'roof_name': 'roof1', 'roof_assembly_code': 'rfwf00co'") and
                   error.endswith("is not of type 'object'") for error in errors)
    elif hpxml_filebase == 'house1':
        assert any(error.startswith("[{'zone_roof': [{'roof_name': 'roof1', 'roof_assembly_code': 'rfrb00co'") and
                   error.endswith("is not of type 'object'") for error in errors)


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_roof(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['zone']['zone_roof'][0]['roof_assembly_code']
    del js1['zone']['zone_roof'][0]['roof_color']
    del js1['zone']['zone_roof'][0]['ceiling_assembly_code']
    errors = get_error_messages(js1, js_schema)
    assert "'roof_assembly_code' is a required property" in errors
    assert "'roof_color' is a required property" in errors
    assert "'ceiling_assembly_code' is a required property" in errors
    assert "'roof_absorptance' is a required property" not in errors

    js2 = copy.deepcopy(js)
    js2['zone']['zone_roof'][0]['roof_type'] = 'cath_ceiling'
    js2['zone']['zone_roof'][0]['roof_absorptance'] = 0.6
    errors = get_error_messages(js2, js_schema)
    assert_required_error(errors, 'ceiling_area')
    assert_required_error(errors, 'ceiling_assembly_code')
    assert_required_error(errors, 'roof_absorptance')

    js3 = copy.deepcopy(js)
    js3['zone']['zone_roof'][0]['roof_type'] = 'flat_roof'
    errors = get_error_messages(js3, js_schema)
    assert "'roof_area' is a required property" in errors

    js4 = copy.deepcopy(js)
    js4['zone']['zone_roof'][0]['roof_type'] = 'below_other_unit'
    js4['zone']['zone_roof'][0]['roof_area'] = 1000
    del js4['zone']['zone_roof'][0]['ceiling_area']
    errors = get_error_messages(js4, js_schema)
    assert "'ceiling_area' is a required property" in errors
    assert_required_error(errors, 'ceiling_assembly_code')
    assert_required_error(errors, 'roof_area')


def test_manufactured_home_sections():
    hpxml_filebase = 'townhouse_walls'
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1['about']['manufactured_home_sections'] = 'single-wide'
    errors = get_error_messages(js1, js_schema)
    assert_required_error(errors, 'manufactured_home_sections')

    js2 = copy.deepcopy(js)
    js2['about']['dwelling_unit_type'] = 'manufactured_home'
    errors = get_error_messages(js2, js_schema)
    assert "'manufactured_home_sections' is a required property" in errors


def test_invalid_skylight():
    hpxml_filebase = 'townhouse_walls'
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1['zone']['zone_roof'][0]['zone_skylight']['skylight_method'] = 'custom'
    errors = get_error_messages(js1, js_schema)
    assert "'skylight_u_value' is a required property" in errors
    assert "'skylight_shgc' is a required property" in errors
    assert_required_error(errors, 'skylight_code')
    del js1['zone']['zone_roof'][0]['zone_skylight']['skylight_method']
    del js1['zone']['zone_roof'][0]['zone_skylight']['skylight_code']
    errors = get_error_messages(js1, js_schema)
    assert "'skylight_method' is a required property" in errors
    assert "'skylight_code' is a required property" not in errors
    assert "'skylight_u_value' is a required property" not in errors
    assert "'skylight_shgc' is a required property" not in errors

    js2 = copy.deepcopy(js)
    js2['zone']['zone_roof'][0]['zone_skylight']['skylight_area'] = 0
    del js2['zone']['zone_roof'][0]['zone_skylight']['skylight_method']
    errors = get_error_messages(js2, js_schema)
    assert "'skylight_method' is a required property" not in errors

    js3 = copy.deepcopy(js)
    js3['zone']['zone_roof'][0]['zone_skylight']['skylight_u_value'] = 0.5
    errors = get_error_messages(js3, js_schema)
    assert_required_error(errors, 'skylight_u_value')


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_floor(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['zone']['zone_floor'][0]['foundation_type']
    del js1['zone']['zone_floor'][0]['foundation_insulation_level']
    errors = get_error_messages(js1, js_schema)
    assert "'foundation_type' is a required property" in errors
    assert "'foundation_insulation_level' is a required property" in errors
    del js1['zone']['zone_floor'][0]['floor_area']
    del js1['zone']['zone_floor'][0]['floor_assembly_code']
    errors = get_error_messages(js1, js_schema)
    assert "'floor_area' is a required property" in errors
    assert "'foundation_type' is a required property" not in errors
    assert "'foundation_insulation_level' is a required property" not in errors
    assert "'floor_assembly_code' is a required property" not in errors

    js2 = copy.deepcopy(js)
    js2['zone']['zone_floor'][0]['foundation_type'] = 'slab_on_grade'
    errors = get_error_messages(js2, js_schema)
    assert_required_error(errors, 'floor_assembly_code')
    js2['zone']['zone_floor'][0]['foundation_type'] = 'above_other_unit'
    errors = get_error_messages(js2, js_schema)
    assert_required_error(errors, 'floor_assembly_code')


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_wall(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['zone']['zone_wall'][0]['side']
    del js1['zone']['zone_wall'][1]['wall_assembly_code']
    errors = get_error_messages(js1, js_schema)
    assert "'side' is a required property" in errors
    assert "'wall_assembly_code' is a required property" in errors


def test_invalid_wall_adjacent_to():
    hpxml_filebase = 'house9'
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1['zone']['zone_wall'][1]['adjacent_to'] = 'other_unit'
    errors = get_error_messages(js1, js_schema)
    assert "single family detached and manufactured homes only allow adjacent_to \"outside\"" in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_window(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    if hpxml_filebase == 'townhouse_walls':
        del js1['zone']['zone_wall'][0]['zone_window']['window_u_value']
    del js1['zone']['zone_wall'][0]['zone_window']['window_area']
    del js1['zone']['zone_wall'][2]['zone_window']['window_code']
    errors = get_error_messages(js1, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        assert "'window_area' is a required property" in errors
        assert "{'window_area': 3.0, 'window_method': 'code', 'solar_screen': False} is not valid under any of the given schemas" in errors  # noqa
        assert "{'window_method': 'custom', 'window_shgc': 0.75, 'solar_screen': False} is not valid under any of the given schemas" in errors  # noqa
    elif hpxml_filebase == 'house1':
        assert "'window_area' is a required property" in errors
        assert "{'window_area': 135.3333333, 'window_method': 'code', 'solar_screen': False} is not valid under any of the given schemas" in errors  # noqa
    del js1['zone']['zone_wall'][2]['zone_window']['window_method']
    errors = get_error_messages(js1, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        assert "{'window_area': 3.0, 'solar_screen': False} is not valid under any of the given schemas" in errors
    elif hpxml_filebase == 'house1':
        assert "{'window_area': 135.3333333, 'solar_screen': False} is not valid under any of the given schemas" in errors  # noqa
    js1['zone']['zone_wall'][0]['zone_window']['window_shgc'] = 1
    errors = get_error_messages(js1, js_schema)
    assert '1 is greater than or equal to the maximum of 1' in errors

    js2 = copy.deepcopy(js)
    js2['zone']['zone_wall'][0]['zone_window']['window_u_value'] = 0.5
    errors = get_error_messages(js2, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        assert len(errors) == 0
    elif hpxml_filebase == 'house1':
        assert "{'window_area': 108.0, 'window_method': 'code', 'window_code': 'dcaa', 'solar_screen': False, 'window_u_value': 0.5} is not valid under any of the given schemas" in errors # noqa

    js3 = copy.deepcopy(js)
    js3['zone']['zone_wall'][0]['zone_window']['window_code'] = 'dcaa'
    errors = get_error_messages(js3, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        assert "{'window_area': 1.0, 'window_method': 'custom', 'window_u_value': 1.0, 'window_shgc': 0.75, 'solar_screen': False, 'window_code': 'dcaa'} is not valid under any of the given schemas" in errors # noqa
    elif hpxml_filebase == 'house1':
        assert len(errors) == 0


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_heating(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['systems']['hvac'][0]['hvac_name']
    errors = get_error_messages(js1, js_schema)
    assert "'hvac_name' is a required property" in errors

    js2 = copy.deepcopy(js)
    js2['systems']['hvac'][0]['heating']['type'] = 'none'
    del js2['systems']['hvac'][0]['heating']['fuel_primary']
    del js2['systems']['hvac'][0]['heating']['efficiency_method']
    errors = get_error_messages(js2, js_schema)
    assert len(errors) == 0
    del js2['systems']['hvac'][0]['heating']['type']
    errors = get_error_messages(js2, js_schema)
    assert "'type' is a required property" in errors

    js3 = copy.deepcopy(js)
    # natural gas central furnace
    del js3['systems']['hvac'][0]['heating']['efficiency']
    errors = get_error_messages(js3, js_schema)
    assert "'efficiency' is a required property" in errors
    del js3['systems']['hvac'][0]['heating']['efficiency_method']
    errors = get_error_messages(js3, js_schema)
    assert "'efficiency_method' is a required property" in errors
    js3['systems']['hvac'][0]['heating']['efficiency_method'] = 'shipment_weighted'
    errors = get_error_messages(js3, js_schema)
    assert "'year' is a required property" in errors
    js3['systems']['hvac'][0]['heating']['efficiency'] = 0.5
    errors = get_error_messages(js3, js_schema)
    assert "0.5 is less than the minimum of 0.6" in errors
    assert_required_error(errors, 'efficiency')
    del js3['systems']['hvac'][0]['heating']['fuel_primary']
    errors = get_error_messages(js3, js_schema)
    assert "'fuel_primary' is a required property" in errors
    # electric central furnace
    js3['systems']['hvac'][0]['heating']['fuel_primary'] = 'electric'
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0
    # electric wall furnace
    js3['systems']['hvac'][0]['heating']['type'] = 'wall_furnace'
    del js3['systems']['hvac'][0]['heating']['efficiency']
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0
    # electric boiler
    js3['systems']['hvac'][0]['heating']['type'] = 'boiler'
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0
    # heat pump
    js3['systems']['hvac'][0]['heating']['type'] = 'heat_pump'
    js3['systems']['hvac'][0]['heating']['efficiency'] = 1.1
    errors = get_error_messages(js3, js_schema)
    assert "1.1 is less than the minimum of 6" in errors
    # mini-split
    js3['systems']['hvac'][0]['heating']['type'] = 'mini_split'
    js3['systems']['hvac'][0]['heating']['efficiency'] = 20.1
    errors = get_error_messages(js3, js_schema)
    assert "20.1 is greater than the maximum of 20" in errors
    # gchp
    js3['systems']['hvac'][0]['heating']['type'] = 'gchp'
    errors = get_error_messages(js3, js_schema)
    assert "20.1 is greater than the maximum of 5" in errors
    # electric baseboard
    js3['systems']['hvac'][0]['heating']['type'] = 'baseboard'
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0
    # electric wood stove
    js3['systems']['hvac'][0]['heating']['type'] = 'wood_stove'
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0
    # natural gas wood stove
    js3['systems']['hvac'][0]['heating']['fuel_primary'] = 'natural_gas'
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0

    js4 = copy.deepcopy(js)
    del js4['systems']['hvac'][0]['hvac_fraction']
    errors = get_error_messages(js4, js_schema)
    assert "'hvac_fraction' is a required property" in errors

    js5 = copy.deepcopy(js)
    js5['systems']['hvac'][0]['heating']['year'] = 2021
    errors = get_error_messages(js5, js_schema)
    assert_required_error(errors, 'year')


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_cooling(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['systems']['hvac'][0]['hvac_name']
    js1['systems']['hvac'][0]['cooling']['year'] = 2021
    errors = get_error_messages(js1, js_schema)
    assert "'hvac_name' is a required property" in errors
    assert_required_error(errors, 'year')

    js2 = copy.deepcopy(js)
    js2['systems']['hvac'][0]['cooling']['type'] = 'none'
    del js2['systems']['hvac'][0]['cooling']['efficiency_method']
    errors = get_error_messages(js2, js_schema)
    assert len(errors) == 0
    del js2['systems']['hvac'][0]['cooling']['type']
    errors = get_error_messages(js2, js_schema)
    assert "'type' is a required property" in errors

    js3 = copy.deepcopy(js)
    # split dx
    del js3['systems']['hvac'][0]['cooling']['efficiency']
    errors = get_error_messages(js3, js_schema)
    assert "'efficiency' is a required property" in errors
    del js3['systems']['hvac'][0]['cooling']['efficiency_method']
    errors = get_error_messages(js3, js_schema)
    assert "'efficiency_method' is a required property" in errors
    js3['systems']['hvac'][0]['cooling']['efficiency_method'] = 'shipment_weighted'
    errors = get_error_messages(js3, js_schema)
    assert "'year' is a required property" in errors
    js3['systems']['hvac'][0]['cooling']['efficiency'] = 7.9
    errors = get_error_messages(js3, js_schema)
    assert "7.9 is less than the minimum of 8" in errors
    assert_required_error(errors, 'efficiency')
    # heat pump
    js3['systems']['hvac'][0]['cooling']['type'] = 'heat_pump'
    errors = get_error_messages(js3, js_schema)
    assert "7.9 is less than the minimum of 8" in errors
    # packaged dx
    js3['systems']['hvac'][0]['cooling']['type'] = 'packaged_dx'
    js3['systems']['hvac'][0]['cooling']['efficiency'] = 40.1
    errors = get_error_messages(js3, js_schema)
    assert "40.1 is greater than the maximum of 40" in errors
    # mini-split
    js3['systems']['hvac'][0]['cooling']['type'] = 'mini_split'
    errors = get_error_messages(js3, js_schema)
    assert "40.1 is greater than the maximum of 40" in errors
    # gchp
    js3['systems']['hvac'][0]['cooling']['efficiency'] = 40.1
    js3['systems']['hvac'][0]['cooling']['type'] = 'gchp'
    errors = get_error_messages(js3, js_schema)
    assert "40.1 is greater than the maximum of 40" in errors
    # dec
    js3['systems']['hvac'][0]['cooling']['type'] = 'dec'
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_hvac_distribution(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1['systems']['hvac'][0]['heating']['type'] = 'wall_furnace'
    js1['systems']['hvac'][0]['cooling']['type'] = 'packaged_dx'
    del js1['systems']['hvac'][0]['hvac_distribution']['duct'][0]['location']
    del js1['systems']['hvac'][0]['hvac_distribution']['duct'][0]['insulated']
    errors = get_error_messages(js1, js_schema)
    assert_required_error(errors, 'hvac_distribution')

    js2 = copy.deepcopy(js)
    del js2['systems']['hvac'][0]['hvac_distribution']['duct'][0]['name']
    del js2['systems']['hvac'][0]['hvac_distribution']['duct'][0]['location']
    del js2['systems']['hvac'][0]['hvac_distribution']['duct'][0]['insulated']
    errors = get_error_messages(js2, js_schema)
    assert "'name' is a required property" in errors
    assert "'location' is a required property" in errors
    assert "'insulated' is a required property" in errors
    del js2['systems']['hvac'][0]['hvac_distribution']['duct'][0]['fraction']
    errors = get_error_messages(js2, js_schema)
    assert "'fraction' is a required property" in errors
    assert "'location' is a required property" not in errors
    assert "'insulated' is a required property" not in errors

    js3 = copy.deepcopy(js)
    del js3['systems']['hvac'][0]['hvac_distribution']
    errors = get_error_messages(js3, js_schema)
    assert "'hvac_distribution' is a required property" in errors
    js3['systems']['hvac'][0]['hvac_fraction'] = 0
    errors = get_error_messages(js3, js_schema)
    assert "'hvac_distribution' is a required property" in errors
    js3['systems']['hvac'][0]['hvac_fraction'] = 1
    js3['systems']['hvac'][0]['heating']['type'] = 'mini_split'
    js3['systems']['hvac'][0]['heating']['efficiency'] = 6
    js3['systems']['hvac'][0]['cooling']['type'] = 'packaged_dx'
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0

    js4 = copy.deepcopy(js)
    del js4['systems']['hvac'][0]['hvac_distribution']['leakage_method']
    errors = get_error_messages(js4, js_schema)
    assert "'leakage_method' is a required property" in errors
    js4['systems']['hvac'][0]['hvac_distribution']['leakage_method'] = 'quantitative'
    errors = get_error_messages(js4, js_schema)
    assert "'leakage_to_outside' is a required property" in errors
    assert_required_error(errors, 'sealed')

    js5 = copy.deepcopy(js)
    del js5['systems']['hvac'][0]['hvac_distribution']['sealed']
    errors = get_error_messages(js5, js_schema)
    assert "'sealed' is a required property" in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_duct_location(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1['zone']['zone_roof'][0]['roof_type'] = "cath_ceiling"
    js1['systems']['hvac'][0]['hvac_distribution']['duct'][0]['location'] = "uncond_attic"
    errors = get_error_messages(js1, js_schema)
    assert "duct/location[\"uncond_attic\"] is not allowed as there is no attic." in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_domestic_hot_water(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['systems']['domestic_hot_water']['category']
    del js1['systems']['domestic_hot_water']['efficiency_method']
    errors = get_error_messages(js1, js_schema)
    assert "'category' is a required property" in errors
    assert "'efficiency_method' is a required property" not in errors

    js2 = copy.deepcopy(js)
    del js2['systems']['domestic_hot_water']['efficiency_method']
    errors = get_error_messages(js2, js_schema)
    assert "'efficiency_method' is a required property" in errors

    js3 = copy.deepcopy(js)
    del js3['systems']['domestic_hot_water']['type']
    del js3['systems']['domestic_hot_water']['fuel_primary']
    errors = get_error_messages(js3, js_schema)
    assert "'type' is a required property" in errors
    assert "'fuel_primary' is a required property" in errors
    if hpxml_filebase == 'townhouse_walls':
        del js3['systems']['domestic_hot_water']['year']
        errors = get_error_messages(js3, js_schema)
        assert "'year' is a required property" in errors
    elif hpxml_filebase == 'house1':
        del js3['systems']['domestic_hot_water']['energy_factor']
        errors = get_error_messages(js3, js_schema)
        assert "'energy_factor' is a required property" in errors
        js3['systems']['domestic_hot_water']['category'] = 'combined'
        errors = get_error_messages(js3, js_schema)
        assert ("The category element can only be set to \"combined\" if the heating/type is \"boiler\""
                " and the boiler provides the domestic hot water") in errors
        js3['systems']['hvac'][0]['heating']['type'] = 'boiler'
        errors = get_error_messages(js3, js_schema)
        assert ("The category element can only be set to \"combined\" if the heating/type is \"boiler\""
                " and the boiler provides the domestic hot water") not in errors

    js4 = copy.deepcopy(js)
    js4['systems']['domestic_hot_water']['energy_factor'] = 0.44
    errors = get_error_messages(js4, js_schema)
    assert "0.44 is less than the minimum of 0.45" in errors
    js4['systems']['domestic_hot_water']['type'] = 'tankless'
    errors = get_error_messages(js4, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        js4['systems']['domestic_hot_water']['efficiency_method'] = 'user'
        del js4['systems']['domestic_hot_water']['year']
    errors = get_error_messages(js4, js_schema)
    assert "0.44 is less than the minimum of 0.45" in errors
    js4['systems']['domestic_hot_water']['type'] = 'heat_pump'
    js4['systems']['domestic_hot_water']['energy_factor'] = 4.1
    errors = get_error_messages(js4, js_schema)
    assert any(x.startswith("4.1 is greater than the maximum") for x in errors)
    js4['systems']['domestic_hot_water']['type'] = 'indirect'
    errors = get_error_messages(js4, js_schema)
    assert "'combined' was expected" in errors

    js5 = copy.deepcopy(js)
    js5['systems']['domestic_hot_water']['fuel_primary'] = 'natural_gas'
    js5['systems']['domestic_hot_water']['energy_factor'] = 0.96
    errors = get_error_messages(js5, js_schema)
    assert "0.96 is greater than the maximum of 0.95" in errors
    js5['systems']['domestic_hot_water']['type'] = 'tankless'
    js5['systems']['domestic_hot_water']['energy_factor'] = 1.0
    if hpxml_filebase == 'townhouse_walls':
        js5['systems']['domestic_hot_water']['efficiency_method'] = 'user'
        del js5['systems']['domestic_hot_water']['year']
    errors = get_error_messages(js5, js_schema)
    assert "1.0 is greater than the maximum of 0.99" in errors

    js6 = copy.deepcopy(js)
    if hpxml_filebase == 'townhouse_walls':
        js6['systems']['domestic_hot_water']['energy_factor'] = 0.6
        errors = get_error_messages(js6, js_schema)
        assert_required_error(errors, 'energy_factor')
    elif hpxml_filebase == 'house1':
        js6['systems']['domestic_hot_water']['year'] = 2021
        errors = get_error_messages(js6, js_schema)
        assert_required_error(errors, 'year')


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_solar_electric(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1['systems'] = {'generation': {'solar_electric': {'capacity_known': False, 'system_capacity': 50}}}
    errors = get_error_messages(js1, js_schema)
    assert "'num_panels' is a required property" in errors
    assert "'year' is a required property" in errors
    assert "'array_azimuth' is a required property" in errors
    assert "'array_tilt' is a required property" in errors
    assert_required_error(errors, 'system_capacity')

    js2 = copy.deepcopy(js)
    js2['systems'] = {'generation': {'solar_electric': {'capacity_known': True, 'num_panels': 5}}}
    errors = get_error_messages(js2, js_schema)
    assert "'system_capacity' is a required property" in errors
    assert "'year' is a required property" in errors
    assert "'array_azimuth' is a required property" in errors
    assert "'array_tilt' is a required property" in errors
    assert_required_error(errors, 'num_panels')

    js3 = copy.deepcopy(js)
    js3['systems'] = {'generation': {'solar_electric': {'year': 2021}}}
    errors = get_error_messages(js3, js_schema)
    assert "'capacity_known' is a required property" in errors
    assert "'array_azimuth' is a required property" in errors
    assert "'array_tilt' is a required property" in errors
    assert "'num_panels' is a required property" not in errors
    assert "'system_capacity' is a required property" not in errors
