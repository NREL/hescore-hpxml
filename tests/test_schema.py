import os
import jsonschema
import json
import pathlib
import copy
import glob


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


def test_invalid_files():
    hpxml_filebase = 'townhouse_walls'
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    js1_about = copy.deepcopy(js['building']['about'])
    del js1['building']['about']
    js1['building']['about'] = []
    js1['building']['about'].append(js1_about)
    js1['building']['about'].append(js1_about)
    js1_zone = copy.deepcopy(js['building']['zone'])
    del js1['building']['zone']
    js1['building']['zone'] = []
    js1['building']['zone'].append(js1_zone)
    js1['building']['zone'].append(js1_zone)
    errors = get_error_messages(js1, js_schema)
    assert any(error.startswith("[{'assessment_date': '2014-12-02', 'shape': 'town_house'") and
               error.endswith("is not of type 'object'") for error in errors)
    assert any(error.startswith("[{'zone_roof': [{'roof_name': 'roof1', 'roof_area': 1200.0") and
               error.endswith("is not of type 'object'") for error in errors)

    js2 = copy.deepcopy(js)
    # dependent building.about properties
    del js2['building']['about']['envelope_leakage']
    errors = get_error_messages(js2, js_schema)
    assert "'envelope_leakage' is a required property" in errors
    assert "'air_sealing_present' is a required property" not in errors
    js2['building']['about']['blower_door_test'] = False
    errors = get_error_messages(js2, js_schema)
    assert "'air_sealing_present' is a required property" in errors
    # required building.about properties
    del js2['building']['about']['town_house_walls']
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
    assert "'town_house_walls' is a required property" in errors
    assert "'assessment_date' is a required property" in errors
    assert "'shape' is a required property" in errors
    assert "'year_built' is a required property" in errors
    assert "'number_bedrooms' is a required property" in errors
    assert "'num_floor_above_grade' is a required property" in errors
    assert "'floor_to_ceiling_height' is a required property" in errors
    assert "'conditioned_floor_area' is a required property" in errors
    assert "'orientation' is a required property" in errors
    assert "'blower_door_test' is a required property" in errors

    js3 = copy.deepcopy(js)
    # required building.zone properties
    del js3['building']['zone']['wall_construction_same']
    del js3['building']['zone']['window_construction_same']
    errors = get_error_messages(js3, js_schema)
    assert "'wall_construction_same' is a required property" in errors
    assert "'window_construction_same' is a required property" in errors

    js4 = copy.deepcopy(js)
    # dependent building.zone.zone_roof properties
    del js4['building']['zone']['zone_roof'][0]['roof_assembly_code']
    del js4['building']['zone']['zone_roof'][0]['roof_color']
    del js4['building']['zone']['zone_roof'][0]['roof_type']
    del js4['building']['zone']['zone_roof'][0]['ceiling_assembly_code']
    errors = get_error_messages(js4, js_schema)
    assert "'roof_assembly_code' is a required property" in errors
    assert "'roof_color' is a required property" in errors
    assert "'roof_type' is a required property" in errors
    assert "'ceiling_assembly_code' is a required property" not in errors
    assert "'roof_absorptance' is a required property" not in errors

    js5 = copy.deepcopy(js)
    # dependent building.zone.zone_skylight properties
    js5['building']['zone']['zone_roof'][0]['zone_skylight']['skylight_method'] = 'custom'
    errors = get_error_messages(js5, js_schema)
    assert "'skylight_u_value' is a required property" in errors
    assert "'skylight_shgc' is a required property" in errors
    del js5['building']['zone']['zone_roof'][0]['zone_skylight']['skylight_method']
    del js5['building']['zone']['zone_roof'][0]['zone_skylight']['skylight_code']
    errors = get_error_messages(js5, js_schema)
    assert "'skylight_method' is a required property" in errors
    assert "'skylight_code' is a required property" not in errors
    assert "'skylight_u_value' is a required property" not in errors
    assert "'skylight_shgc' is a required property" not in errors
