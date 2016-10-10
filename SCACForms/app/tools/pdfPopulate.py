import os
import subprocess
from fdfgen import forge_fdf
import pypyodbc
import fnmatch
import shutil

dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
os.chdir(dir)
form_pdf = r"fixture_form.pdf"
#clean output folder
if os.path.exists(os.path.join(dir, 'output')):
    shutil.rmtree(os.path.join(dir, 'output'))

os.mkdir(os.path.join(dir, 'output'))

acc_db = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                      "SCAC_SYSTEM_PLAN_INVENTORY_QUESTIONAIRE.accdb")
cxn = pypyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + acc_db)
crsr = cxn.cursor()


def build_fields():
    kwargs = dict()
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

    for i in range(20 - 86):
        target_fields.append("Check Box{}".format(i))

    for i in range(2, 13):
        target_fields.append("RUNWAY END_{}".format(i))

    for i in range(90, 99):
        target_fields.append("Check Box{}".format(i))

    for i in range(106, 111):
        target_fields.append("Check Box{}".format(i))

    print(target_fields)

    missing_fields = [x for x in target_fields if x not in total_name_list]
    if not missing_fields:
        return target_fields
    else:
        return "target fields were created that don't exist in the form :: {}".format(missing_fields)


def get_airports(cursor):
    airports = []
    cursor.execute("select DISTINCT FAAID, Name from PublicUseSCairportsMinus5J5")
    rows = cursor.fetchall()
    if rows:
        for x in rows:
            if x not in airports:
                airports.append(tuple(x))

    return airports


class Form:
    """represents a complete form entry"""
    def __init__(self, faaid, name, cursor):
        self.runways = {}
        cursor.execute("select FAAID, RunwayID from Approaches WHERE FAAID='{}'".format(faaid))
        rows = cursor.fetchall()
        if rows:
            for x in rows:
                self.runways[x[1]] = {}
        self.FAAID = faaid
        self.Name = name
        self.cursor = cursor
        self.fields = []
        pass

    def question1(self):
        self.fields.append(("Airport Name", self.Name))
        self.cursor.execute("select ContactPhoneNo, Email from tblFacilities WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        contact = {
            'name': [],
            'phone': [],
            'email': []
        }
        if rows:
            for x in rows:
                if x[0]:
                    contact['name'].append(x[0].split("-")[0].strip())
                    contact['phone'].append("-".join(x[0].split("-")[1:]).strip())
                if x[1]:
                    contact['email'].append(x[1].strip())

        self.fields.append(("Contact Name", " ".join(contact['name'])))
        self.fields.append(("Phone", " ".join(contact['phone'])))
        self.fields.append(("Email", " ".join(contact['email'])))

    def question5(self):
        self.cursor.execute("select FuelType1, FuelType2, FuelType3 from tblAirportSC WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        _jetA = False
        _100LL = False
        OTHER = False
        if rows:
            for types in rows:
                for x in types:
                    if x is not None:
                        if fnmatch.fnmatchcase(x, '100*'):
                            _100LL = True
                        elif fnmatch.fnmatchcase(x, 'A*'):
                            _jetA = True
                        elif len(x):
                            OTHER = True
        if _jetA:
            self.fields.append(('Check Box4', 'Yes'))
        else:
            self.fields.append(('Check Box5', 'Yes'))

        if _100LL:
            self.fields.append(('Check Box6', 'Yes'))
        else:
            self.fields.append(('Check Box7', 'Yes'))

        if OTHER:
            self.fields.append(('Check Box8', 'Yes'))
        else:
            self.fields.append(('Check Box9', 'Yes'))

    def question8(self):
        self.cursor.execute("select RunwayID, Length, Width, GWDW  from tblRunwaySC WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        if rows:
            for row in rows:
                if row[0] not in ['H1', 'H2']:
                    runway = self.runways[row[0]]
                    runway['length'] = row[1]
                    runway['width'] = row[2]
                    runway['max_weight'] = row[3]

        prim_length = 0
        for key in self.runways:
            rnwy = self.runways[key]
            length = int(rnwy['length'])
            if length > prim_length:
                prim_length = length

        primary_count = 0
        for key in self.runways:
            rnwy = self.runways[key]
            if int(rnwy['length']) == prim_length:
                rnwy['primary'] = True
                primary_count += 1
            else:
                rnwy['primary'] = False

        if primary_count > 1:
            print("Multiple runways with the same length, unable to determine the primary :: {}".format(self.FAAID))

        for key in self.runways:
            rnwy = self.runways[key]
            if rnwy['primary']:
                self.fields.append(('1', key))
                self.fields.append(('2', rnwy['length']))
                self.fields.append(('3', rnwy['width']))
                self.fields.append(('4', rnwy['max_weight']))
            else:
                self.fields.append(('1_2', key))
                self.fields.append(('2_2', rnwy['length']))
                self.fields.append(('3_2', rnwy['width']))
                self.fields.append(('4_2', rnwy['max_weight']))

        pass

    def question9(self):
        self.cursor.execute("select RunwayID, REApproachLights from tblRunwaySC WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()

        def lighting_tally(variable):
            reils = 0
            papi_vgsi = 0
            als_odals = 0
            if fnmatch.fnmatchcase(variable, "*REILS*"):
                reils += 1
            elif fnmatch.fnmatchcase(variable, "PAPI") or fnmatch.fnmatchcase(variable, 'VGSI'):
                papi_vgsi += 1
            elif fnmatch.fnmatchcase(variable, "ASL*") or fnmatch.fnmatchcase(variable, "ODALS"):
                als_odals += 1
            return {
                'reils': reils,
                'papi_vgsi': papi_vgsi,
                'als_odals': als_odals
            }

        if rows:
            for row in rows:
                if row[0] in self.runways:
                    if row[1]:
                        self.runways[row[0]]['approach_lighting'] = row[1].upper()
                    else:
                        self.runways[row[0]]['approach_lighting'] = "UNK"
                else:
                    print("runway ID from question 9 was not included in the class initialization :: {}".format(row[0]))
                    if row[0] not in ['H1', 'H2']:
                        raise Exception("runway ID from question 9 was not included in the class initialization :: {}"
                                        .format(row[0]))

            # process each runway end
            i = 21
            t = 1
            for rnwy in iter(self.runways):
                if t == 1:
                    self.fields.append(("RUNWAY END", rnwy))
                if t > 1:
                    self.fields.append(("RUNWAY END_{}".format(t), rnwy))

                lighting = self.runways[rnwy]['approach_lighting']
                results = lighting_tally(lighting)

                if results['reils']:
                    self.fields.append(("Check Box{}".format(i), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 1), "Yes"))
                if results['papi_vgsi']:
                    self.fields.append(("Check Box{}".format(i + 8), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 9), "Yes"))
                if results['als_odals']:
                    self.fields.append(("Check Box{}".format(i + 16), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 17), "Yes"))
                i += 2
                t += 1

        pass

    def process(self):
        self.question1()
        self.question5()
        self.question8()
        self.question9()

        fdf = forge_fdf("", self.fields, [], [], [])
        fdf_file = open("data.fdf", "wb")
        fdf_file.write(fdf)
        fdf_file.close()

        kwargs = dict()
        kwargs['cwd'] = dir
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        kwargs['universal_newlines'] = True
        proc = subprocess.Popen(r"pdftk fixture_form.pdf fill_form data.fdf output output\{}.pdf".format(self.FAAID), **kwargs)
        stdout, stderr = proc.communicate()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        return

if os.path.exists(form_pdf):
    print("located the pdf form")
else:
    raise Exception("form_pdf has not been found")

if os.path.exists(acc_db):
    print("located the access database")
else:
    raise Exception("access database has not been found")


if __name__ == "__main__":
    # target_fields = build_fields()
    airports = get_airports(cursor=crsr)
    for x in airports:
        FAAID = x[0]
        Name = "".join(x[1:])
        frm = Form(FAAID, Name, cursor=crsr)
        frm.process()


