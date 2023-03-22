import pathlib
from hescorehpxml import HPXMLtoHEScoreTranslator


def main():
    exampledir = pathlib.Path(__file__).resolve().parent.parent / 'examples'
    for filename in exampledir.glob('*.json'):
        print(filename)
        tr = HPXMLtoHEScoreTranslator(str(filename.with_suffix('.xml')))
        with open(filename, 'w') as f:
            tr.hpxml_to_hescore_json(f)


if __name__ == '__main__':
    main()
