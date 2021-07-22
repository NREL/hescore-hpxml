import os
from hescorehpxml import (
    HPXMLtoHEScoreTranslator,
    main
)

thisdir = os.path.dirname(os.path.abspath(__file__))
xml_path = os.path.join(thisdir, 'xmls')
out_path = os.path.join(thisdir, 'output')
if not os.path.exists(out_path):
    os.makedirs(out_path)
for file in os.listdir(out_path):
    os.remove(os.path.join(out_path, file))

for xml in os.listdir(xml_path):
    if xml.split('.')[-1] != 'xml': continue
    print(f"Running {xml}")
    file_name = xml.split('.')[0]
    command = 'hpxml2hescore ' + os.path.join(xml_path, xml) + ' --resstock ' + '-o ' + os.path.join(out_path, file_name + '.json')
    os.system(command)