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
    errors = get_error_messages(js1, js_schema)
    assert any(error.startswith("[{'assessment_date': '2014-12-02', 'shape': 'town_house'") and
               error.endswith("is not of type 'object'") for error in errors)

    js2 = copy.deepcopy(js)
    js2_zone = copy.deepcopy(js['building']['zone'])
    del js2['building']['zone']
    js2['building']['zone'] = []
    js2['building']['zone'].append(js2_zone)
    js2['building']['zone'].append(js2_zone)
    errors = get_error_messages(js2, js_schema)
    assert any(error.startswith("[{'zone_roof': [{'roof_name': 'roof1', 'roof_area': 1200.0") and
               error.endswith("is not of type 'object'") for error in errors)

    js3 = copy.deepcopy(js)
    del js3['building']['about']['town_house_walls']
    errors = get_error_messages(js3, js_schema)
    assert "'town_house_walls' is a required property" in errors

    js4 = copy.deepcopy(js)
    del js4['building']['about']['assessment_date']
    errors = get_error_messages(js4, js_schema)
    assert "'assessment_date' is a required property" in errors

    js5 = copy.deepcopy(js)
    del js5['building']['about']['shape']
    errors = get_error_messages(js5, js_schema)
    assert "'shape' is a required property" in errors

    js6 = copy.deepcopy(js)
    del js6['building']['about']['shape']
    errors = get_error_messages(js6, js_schema)
    assert "'shape' is a required property" in errors

    # TODO: Add more tests
