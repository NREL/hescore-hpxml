import os

thisdir = os.path.dirname(os.path.abspath(__file__))
xml_path = os.path.join(thisdir, 'xmls')
out_path = os.path.join(thisdir, 'output')
if not os.path.exists(out_path):
    os.makedirs(out_path)
for subdir, dirs, files in os.walk(out_path):
    for file in files:
        os.remove(os.path.join(subdir, file))

for subdir, dirs, files in os.walk(xml_path):
    project_name = subdir.split('\\')[-1]
    sub_out_path = os.path.join(out_path, project_name)
    if 'project' in project_name:
        print('\n', project_name)
    else:
        continue
    if not os.path.exists(sub_out_path):
        os.makedirs(sub_out_path)
    for filename in files:
        if filename.split('.')[-1] != 'xml':
            continue
        filepath = subdir + os.sep + filename
        print(f"    Translating {subdir}\\{filename}")
        file_name = filename.split('.')[0]
        command = 'hpxml2hescore ' + filepath + ' --resstock ' + '-o ' + os.path.join(sub_out_path, file_name + '.json')
        os.system(command)
