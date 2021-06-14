import os
import jsonschema
import json
import pathlib
import copy


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


def test_invalid_files():
    hpxml_filebase = 'townhouse_walls'
    schema = get_json_schema()
    js_schema = jsonschema.Draft7Validator(schema)
    js = get_example_json(hpxml_filebase)

    js1 = copy.deepcopy(js)
    del js1['building']['about']['town_house_walls']
    errors = get_error_messages(js1, js_schema)
    assert "'town_house_walls' is a required property" in errors

    js2 = copy.deepcopy(js)
    js2_about = copy.deepcopy(js['building']['about'])
    del js2['building']['about']
    js2['building']['about'] = []
    js2['building']['about'].append(js2_about)
    js2['building']['about'].append(js2_about)
    errors = get_error_messages(js2, js_schema)
    assert any(error.startswith("[{'assessment_date': '2014-12-02', 'shape': 'town_house'") and
               error.endswith("is not of type 'object'") for error in errors)

    js3 = copy.deepcopy(js)
    js3_zone = copy.deepcopy(js['building']['zone'])
    del js3['building']['zone']
    js3['building']['zone'] = []
    js3['building']['zone'].append(js3_zone)
    js3['building']['zone'].append(js3_zone)
    errors = get_error_messages(js3, js_schema)
    assert any(error.startswith("[{'zone_roof': [{'roof_name': 'roof1', 'roof_area': 1200.0") and
               error.endswith("is not of type 'object'") for error in errors)

    # TODO: Add more tests