import os
import subprocess
from fdfgen import forge_fdf

dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
os.chdir(dir)
form_pdf = r"fixture_form.pdf"
if os.path.exists(form_pdf):
    print("located the pdf form")
else:
    raise Exception("form_pdf has not been found")
kwargs = {}
kwargs['cwd'] = dir
kwargs['stdout'] = subprocess.PIPE
kwargs['stderr'] = subprocess.PIPE
kwargs['universal_newlines'] = True

proc = subprocess.Popen('pdftk fixture_form.pdf dump_data_fields', **kwargs)
(out, err) = proc.communicate()
if err:
    print(err)
    raise Exception(err)
if out:
    print(out)

grps = out.split(r'---')[1:]
grps = [x.strip() for x in grps]
new_list = []
for g in grps:
    print(g)
    fields = g.split('\n')
    fields = [x.strip() for x in fields]
    new_obj = dict()
    for f in fields:
        if len(f):
            object = f.split(r": ")
            key = object[0]
            value = object[1]
            new_obj[key] = value
    new_list.append(new_obj)

total_name_list = [x['FieldName'] for x in new_list]
print(new_list)

target_fields = [
    "Airport Name",
    "Contact Name",
    "Title",
    "Phone",
    "Email",
    "undefined",
    "RUNWAY END",
    "lighting_13",
    "Other",
    "Other_2"
]

for i in range(2008, 2016):
    target_fields.append("{}BASED AIRCRAFT".format(i))
for i in range(2, 73):
    target_fields.append("undefined_{}".format(i))
for i in range(4, 16):
    target_fields.append("Check Box{}".format(i))
for i in range(1, 5):
    target_fields.append(str(i))
    target_fields.append("{}_2".format(i))
    target_fields.append("{}_3".format(i))
    target_fields.append("{}_4".format(i))
    target_fields.append("{}_5".format(i))
    target_fields.append("{}_6".format(i))

for i in range(5, 9):
    target_fields.append(str(i))
    target_fields.append("{}_2".format(i))
    target_fields.append("{}_3".format(i))
    target_fields.append("{}_4".format(i))

for i in range(20-86):
    target_fields.append("Check Box{}".format(i))

for i in range(2, 13):
    target_fields.append("RUNWAY END_{}".format(i))

for i in range(90, 99):
    target_fields.append("Check Box{}".format(i))

for i in range(106, 111):
    target_fields.append("Check Box{}".format(i))

print(target_fields)

missing_fields = [x for x in target_fields if x not in total_name_list]

if not len(missing_fields):
    pass
    # fdf = forge_fdf("", fields, [], [], [])
    # fdf_file = open("data.fdf", "wb")
    # fdf_file.write(fdf)
    # fdf_file.close()
