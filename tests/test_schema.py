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
        errors.append(error.message)
    return errors


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
        js_schema = jsonschema.Draft7Validator(schema)
        js = get_example_json(hpxml_filebase)
        errors = get_error_messages(js, js_schema)
        assert len(errors) == 0


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_building_about(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1_about = copy.deepcopy(js['building']['about'])
    del js1['building']['about']
    js1['building']['about'] = []
    js1['building']['about'].append(js1_about)
    js1['building']['about'].append(js1_about)
    errors = get_error_messages(js1, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        assert any(error.startswith("[{'assessment_date': '2014-12-02', 'shape': 'town_house'") and
                   error.endswith("is not of type 'object'") for error in errors)
    elif hpxml_filebase == 'house1':
        assert any(error.startswith("[{'assessment_date': '2014-10-23', 'shape': 'rectangle'") and
                   error.endswith("is not of type 'object'") for error in errors)

    js2 = copy.deepcopy(js)
    # dependent building.about properties
    if hpxml_filebase == 'townhouse_walls':
        del js2['building']['about']['envelope_leakage']
        errors = get_error_messages(js2, js_schema)
        assert "'envelope_leakage' is a required property" in errors
        assert "'air_sealing_present' is a required property" not in errors
        js2['building']['about']['blower_door_test'] = False
        errors = get_error_messages(js2, js_schema)
        assert "'air_sealing_present' is a required property" in errors
    elif hpxml_filebase == 'house1':
        del js2['building']['about']['air_sealing_present']
        errors = get_error_messages(js2, js_schema)
        assert "'envelope_leakage' is a required property" not in errors
        assert "'air_sealing_present' is a required property" in errors
    # required building.about properties
    del js2['building']['about']['assessment_date']
    del js2['building']['about']['shape']
    del js2['building']['about']['year_built']
    del js2['building']['about']['number_bedrooms']
    del js2['building']['about']['num_floor_above_grade']
    del js2['building']['about']['floor_to_ceiling_height']
    del js2['building']['about']['conditioned_floor_area']
    del js2['building']['about']['orientation']
    del js2['building']['about']['blower_door_test']
    errors = get_error_messages(js2, js_schema)
    assert "'assessment_date' is a required property" in errors
    assert "'shape' is a required property" in errors
    assert "'year_built' is a required property" in errors
    assert "'number_bedrooms' is a required property" in errors
    assert "'num_floor_above_grade' is a required property" in errors
    assert "'floor_to_ceiling_height' is a required property" in errors
    assert "'conditioned_floor_area' is a required property" in errors
    assert "'orientation' is a required property" in errors
    assert "'blower_door_test' is a required property" in errors
    if hpxml_filebase == 'townhouse_walls':
        del js2['building']['about']['town_house_walls']
        errors = get_error_messages(js2, js_schema)
        assert "'town_house_walls' is a required property" in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_building_zone(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)
    zone = copy.deepcopy(js['building']['zone'])
    del js['building']['zone']
    js['building']['zone'] = []
    js['building']['zone'].append(zone)
    js['building']['zone'].append(zone)
    errors = get_error_messages(js, js_schema)
    if hpxml_filebase == 'townhouse_walls':
        assert any(error.startswith("[{'zone_roof': [{'roof_name': 'roof1', 'roof_area': 1200.0") and
                   error.endswith("is not of type 'object'") for error in errors)
    elif hpxml_filebase == 'house1':
        assert any(error.startswith("[{'zone_roof': [{'roof_name': 'roof1', 'roof_area': 810") and
                   error.endswith("is not of type 'object'") for error in errors)


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_roof(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)
    # dependent building.zone.zone_roof properties
    del js['building']['zone']['zone_roof'][0]['roof_assembly_code']
    del js['building']['zone']['zone_roof'][0]['roof_color']
    del js['building']['zone']['zone_roof'][0]['roof_type']
    del js['building']['zone']['zone_roof'][0]['ceiling_assembly_code']
    errors = get_error_messages(js, js_schema)
    assert "'roof_assembly_code' is a required property" in errors
    assert "'roof_color' is a required property" in errors
    assert "'roof_type' is a required property" in errors
    assert "'ceiling_assembly_code' is a required property" not in errors
    assert "'roof_absorptance' is a required property" not in errors


def test_invalid_skylight():
    hpxml_filebase = 'townhouse_walls'
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)
    # dependent building.zone.zone_skylight properties
    js['building']['zone']['zone_roof'][0]['zone_skylight']['skylight_method'] = 'custom'
    errors = get_error_messages(js, js_schema)
    assert "'skylight_u_value' is a required property" in errors
    assert "'skylight_shgc' is a required property" in errors
    del js['building']['zone']['zone_roof'][0]['zone_skylight']['skylight_method']
    del js['building']['zone']['zone_roof'][0]['zone_skylight']['skylight_code']
    errors = get_error_messages(js, js_schema)
    assert "'skylight_method' is a required property" in errors
    assert "'skylight_code' is a required property" not in errors
    assert "'skylight_u_value' is a required property" not in errors
    assert "'skylight_shgc' is a required property" not in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_floor(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)
    # dependent building.zone.zone_roof properties
    del js['building']['zone']['zone_floor'][0]['foundation_type']
    del js['building']['zone']['zone_floor'][0]['foundation_insulation_level']
    errors = get_error_messages(js, js_schema)
    assert "'foundation_type' is a required property" in errors
    assert "'foundation_insulation_level' is a required property" in errors
    del js['building']['zone']['zone_floor'][0]['floor_area']
    del js['building']['zone']['zone_floor'][0]['floor_assembly_code']
    errors = get_error_messages(js, js_schema)
    assert "'floor_area' is a required property" in errors
    assert "'foundation_type' is a required property" not in errors
    assert "'foundation_insulation_level' is a required property" not in errors
    assert "'floor_assembly_code' is a required property" not in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_wall_window_construction_same(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)
    # required building.zone properties
    del js['building']['zone']['wall_construction_same']
    del js['building']['zone']['window_construction_same']
    errors = get_error_messages(js, js_schema)
    assert "'wall_construction_same' is a required property" in errors
    assert "'window_construction_same' is a required property" in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_wall(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)
    # required building.zone.zone_wall properties
    del js['building']['zone']['zone_wall'][0]['side']
    errors = get_error_messages(js, js_schema)
    assert "'side' is a required property" in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_heating(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['building']['systems']['hvac'][0]['hvac_name']
    errors = get_error_messages(js1, js_schema)
    assert "'hvac_name' is a required property" in errors

    js2 = copy.deepcopy(js)
    js2['building']['systems']['hvac'][0]['heating']['type'] = 'none'
    del js2['building']['systems']['hvac'][0]['heating']['fuel_primary']
    del js2['building']['systems']['hvac'][0]['heating']['efficiency_method']
    errors = get_error_messages(js2, js_schema)
    assert len(errors) == 0
    del js2['building']['systems']['hvac'][0]['heating']['type']
    errors = get_error_messages(js2, js_schema)
    assert "'type' is a required property" in errors

    js3 = copy.deepcopy(js)
    del js3['building']['systems']['hvac'][0]['heating']['efficiency']
    errors = get_error_messages(js3, js_schema)
    assert "'efficiency' is a required property" in errors
    js3['building']['systems']['hvac'][0]['heating']['efficiency_method'] = 'shipment_weighted'
    errors = get_error_messages(js3, js_schema)
    assert "'year' is a required property" in errors
    js3['building']['systems']['hvac'][0]['heating']['fuel_primary'] = 'electric'
    errors = get_error_messages(js3, js_schema)
    assert len(errors) == 0


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_cooling(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['building']['systems']['hvac'][0]['hvac_name']
    errors = get_error_messages(js1, js_schema)
    assert "'hvac_name' is a required property" in errors

    js2 = copy.deepcopy(js)
    js2['building']['systems']['hvac'][0]['cooling']['type'] = 'none'
    del js2['building']['systems']['hvac'][0]['cooling']['efficiency_method']
    errors = get_error_messages(js2, js_schema)
    assert len(errors) == 0
    del js2['building']['systems']['hvac'][0]['cooling']['type']
    errors = get_error_messages(js2, js_schema)
    assert "'type' is a required property" in errors

    js3 = copy.deepcopy(js)
    del js3['building']['systems']['hvac'][0]['cooling']['efficiency']
    errors = get_error_messages(js3, js_schema)
    assert "'efficiency' is a required property" in errors
    js3['building']['systems']['hvac'][0]['cooling']['efficiency_method'] = 'shipment_weighted'
    errors = get_error_messages(js3, js_schema)
    assert "'year' is a required property" in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_hvac_distribution(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1['building']['systems']['hvac'][0]['heating']['type'] = 'wall_furnace'
    js1['building']['systems']['hvac'][0]['cooling']['type'] = 'packaged_dx'
    del js1['building']['systems']['hvac'][0]['hvac_distribution'][0]['location']
    del js1['building']['systems']['hvac'][0]['hvac_distribution'][0]['insulated']
    del js1['building']['systems']['hvac'][0]['hvac_distribution'][0]['sealed']
    errors = get_error_messages(js1, js_schema)
    assert len(errors) == 0

    js2 = copy.deepcopy(js)
    del js2['building']['systems']['hvac'][0]['hvac_distribution'][0]['name']
    del js2['building']['systems']['hvac'][0]['hvac_distribution'][0]['location']
    del js2['building']['systems']['hvac'][0]['hvac_distribution'][0]['insulated']
    del js2['building']['systems']['hvac'][0]['hvac_distribution'][0]['sealed']
    errors = get_error_messages(js2, js_schema)
    assert "'name' is a required property" in errors
    assert "'location' is a required property" in errors
    assert "'insulated' is a required property" in errors
    assert "'sealed' is a required property" in errors
    del js2['building']['systems']['hvac'][0]['hvac_distribution'][0]['fraction']
    errors = get_error_messages(js2, js_schema)
    assert "'fraction' is a required property" in errors
    assert "'location' is a required property" not in errors
    assert "'insulated' is a required property" not in errors
    assert "'sealed' is a required property" not in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_domestic_hot_water(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)
    js['building']['systems']['domestic_hot_water']['type'] = 'combined'
    errors = get_error_messages(js, js_schema)
    assert "'fuel_primary' is a required property" not in errors
    assert "'efficiency_method' is a required property" not in errors
    assert "'energy_factor' is a required property" not in errors
    del js['building']['systems']['domestic_hot_water']['category']
    del js['building']['systems']['domestic_hot_water']['type']
    del js['building']['systems']['domestic_hot_water']['fuel_primary']
    del js['building']['systems']['domestic_hot_water']['efficiency_method']
    errors = get_error_messages(js, js_schema)
    assert "'category' is a required property" in errors
    assert "'type' is a required property" in errors
    assert "'fuel_primary' is a required property" in errors
    assert "'efficiency_method' is a required property" in errors
    if hpxml_filebase == 'townhouse_walls':
        del js['building']['systems']['domestic_hot_water']['year']
        errors = get_error_messages(js, js_schema)
        assert "'year' is a required property" in errors
    elif hpxml_filebase == 'house1':
        del js['building']['systems']['domestic_hot_water']['energy_factor']
        errors = get_error_messages(js, js_schema)
        assert "'energy_factor' is a required property" in errors


@pytest.mark.parametrize('hpxml_filebase', hescore_examples)
def test_invalid_solar_electric(hpxml_filebase):
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)
    js['building']['systems'] = {'generation': {'solar_electric': {'capacity_known': False}}}
    errors = get_error_messages(js, js_schema)
    assert "'num_panels' is a required property" in errors
    assert "'year' is a required property" in errors
    assert "'array_azimuth' is a required property" in errors
    js['building']['systems']['generation']['solar_electric']['capacity_known'] = True
    errors = get_error_messages(js, js_schema)
    assert "'system_capacity' is a required property" in errors
    assert "'year' is a required property" in errors
    assert "'array_azimuth' is a required property" in errors
    # js['building']['systems']['generation']['solar_electric'] = {'year': 2021}
    js['building']['systems']['generation']['solar_electric']['year'] = 2021
    del js['building']['systems']['generation']['solar_electric']['capacity_known']
    errors = get_error_messages(js, js_schema)
    assert "'capacity_known' is a required property" in errors
    assert "'array_azimuth' is a required property" in errors
    assert "'num_panels' is a required property" not in errors
    assert "'system_capacity' is a required property" not in errors
