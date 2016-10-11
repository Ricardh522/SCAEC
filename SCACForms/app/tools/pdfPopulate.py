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
                      "SCAC_SYSTEM_PLAN_INVENTORY_QUESTIONAIRE_version2.accdb")
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
        self.cursor.execute("select KeyContact, AirportManager, Sal, FirstName, LastName, Title, Phone, Email from tblDirectory WHERE Faaid='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        contact = {
            "type": "",
            'name': "",
            'title': "",
            'phone': "",
            'email': ""
        }

        if rows:
            for row in rows:
                KeyContact, AirportManager, Sal, FirstName, LastName, Title, Phone, Email = row
                fields = [KeyContact, AirportManager, Sal, FirstName, LastName, Title, Phone, Email]

                if row[1]:
                    if contact['type'] != 'manager':
                        contact['name'] = "{} {} {}".format(Sal, FirstName, LastName)
                        contact['title'] = Title
                        contact['phone'] = Phone
                        contact['email'] = Email
                        contact['type'] = 'manager'

                elif row[0]:
                    if contact['type'] != 'manager':
                        contact['name'] = "{} {} {}".format(Sal, FirstName, LastName)
                        contact['title'] = Title
                        contact['phone'] = Phone
                        contact['email'] = Email
                        contact['type'] = 'contact'

        self.fields.append(("Contact Name", contact['name']))
        self.fields.append(("Title", contact['title']))
        self.fields.append(("Phone", contact['phone']))
        self.fields.append(("Email", contact['email']))

    def question2(self):
        self.cursor.execute("select Total, InfoDate from BasedAircraftByYear WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        based = dict()
        if len(rows):
            for row in rows:
                total = int(row[0])
                year = row[1].split("/")[-1]
                based[year] = total
        for year in based:
            self.fields.append(("{}BASED AIRCRAFT".format(year), based[year]))

    def question3(self):
        self.cursor.execute("select AirCarrier, AirTaxi, LocalOps, ItinOps, MilitaryOps, Total, OpYear from OperationsByYear WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        ops = dict()
        if len(rows):
            for row in rows:
                air_carrier, air_taxi, local_ops, itin_ops, military_ops, total_ops, year = row
                fields = [air_carrier, air_taxi, local_ops, itin_ops, military_ops, total_ops, year]
                new_fields = list()
                for x in fields[:-1]:
                    if x is None:
                        new_fields.append(0)
                    else:
                        new_fields.append("{:,}".format(int(x)))
                new_fields.append(int(year))
                ops[new_fields[6]] = {
                    "air_carrier": new_fields[0],
                    "air_taxi": new_fields[1],
                    "local_ops": new_fields[2],
                    "itin_ops": new_fields[3],
                    "military_ops": new_fields[4],
                    "total_ops": new_fields[5]
                }
        keys = list(ops.keys())
        keys.sort()
        for year in keys:
            obj = ops[year]
            if year == 2008:
                start = 1
                self.fields.append(("undefined", obj["air_carrier"]))
            else:
                dif = year - 2008
                start = dif + 1
                self.fields.append(("undefined_{}".format(start), obj["air_carrier"]))

            self.fields.append(("undefined_{}".format(start + 9), obj["air_taxi"]))
            self.fields.append(("undefined_{}".format(start + 18), obj["military_ops"]))
            self.fields.append(("undefined_{}".format(start + 27), obj["itin_ops"]))
            self.fields.append(("undefined_{}".format(start + 36), obj["local_ops"]))
            self.fields.append(("undefined_{}".format(start + 45), obj["total_ops"]))

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
        self.cursor.execute("select RunwayID, BaseEndID, REID, BeREIL, BeSlopeIndicators, BeApproachLights,"
                            "REREIL, RESlopeIndicators, REApproachLights from tblRunwaySC WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        if rows:
            filtered_rows = []
            for x in rows:
                if x[0] not in ['H1', 'H2', 'H']:
                    filtered_rows.append(x)

            if len(filtered_rows) > 2:
                rem_rows = []
                # get the two longest runways
                runways = list(self.runways.keys())
                lengths = []
                for run in runways:
                    lengths.append(self.runways[run]['length'])
                lengths.sort(reverse=True)
                lengths = lengths[:2]

                for run in runways:
                    if self.runways[run]['length'] not in lengths:
                        for filt in filtered_rows:
                            if filt[0] == run:
                                rem_rows.append(filt)
                print("These runways for airport '{}' will not fit on the questionnaire :: {}".format(self.FAAID, rem_rows))
                filtered_rows = [x for x in filtered_rows if x not in rem_rows]

            for row in filtered_rows:
                RunwayID, BaseEndID, REID, BeREIL, BeSlopeIndicators, BeApproachLights,\
                REREIL, RESlopeIndicators, REApproachLights = row

                runway_id = row[0]
                if runway_id in self.runways:
                    self.runways[runway_id]["Base"] = {
                        'name': BaseEndID,
                        'REIL': False,
                        'PAPI': False,
                        'ALS': False
                    }

                    self.runways[runway_id]["RE"] = {
                        'name': REID,
                        'REIL': False,
                        'PAPI': False,
                        'ALS': False
                    }

                    base_obj = self.runways[runway_id]["Base"]

                    if BeREIL is not None and BeREIL not in ["", "No", "NO", "N"]:
                        base_obj['REIL'] = True
                    if BeSlopeIndicators is not None and BeSlopeIndicators not in ["", "No", "NO", "N"]:
                        base_obj['PAPI'] = True
                    if BeApproachLights is not None and BeApproachLights not in ["", "No", "NO", "N"]:
                        base_obj['ALS'] = True

                    re_obj = self.runways[runway_id]["RE"]
                    if REREIL is not None and REREIL not in ["", "No", "NO", "N"]:
                        re_obj['REIL'] = True
                    if RESlopeIndicators is not None and RESlopeIndicators not in ["", "No", "NO", "N"]:
                        re_obj['PAPI'] = True
                    if REApproachLights is not None and REApproachLights not in ["", "No", "NO", "N"]:
                        re_obj['ALS'] = True


                else:
                    print("runway ID from question 9 was not included in the class initialization :: {}".format(row[0]))
                    if row[0] not in ['H1', 'H2']:
                        raise Exception("runway ID from question 9 was not included in the class initialization :: {} :: FAAID-{}"
                                        .format(row[0], self.FAAID))

            # process each runway end
            t = 1
            i = 21
            for rnwy in filtered_rows:
                runway_id = rnwy[0]
                base_obj = self.runways[runway_id]["Base"]
                if t == 1:
                    self.fields.append(("RUNWAY END", base_obj['name']))
                if t > 1:
                    self.fields.append(("RUNWAY END_{}".format(t), base_obj['name']))

                if base_obj['REIL']:
                    self.fields.append(("Check Box{}".format(i), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i+1), "Yes"))
                if base_obj['PAPI']:
                    self.fields.append(("Check Box{}".format(i + 8), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 9), "Yes"))
                if base_obj['ALS']:
                    self.fields.append(("Check Box{}".format(i + 16), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 17), "Yes"))

                t += 1
                i += 2

                re_obj = self.runways[runway_id]["RE"]
                self.fields.append(("RUNWAY END_{}".format(t), re_obj['name']))

                if re_obj['REIL']:
                    self.fields.append(("Check Box{}".format(i), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 1), "Yes"))
                if re_obj['PAPI']:
                    self.fields.append(("Check Box{}".format(i + 8), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 9), "Yes"))
                if re_obj['ALS']:
                    self.fields.append(("Check Box{}".format(i + 16), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 17), "Yes"))
                t += 1
                i += 2

        pass

    def question10(self):
        self.cursor.execute("select RWY_BE, ILS_BE, RNAV_BE, LPV_BE, VISUAL_BE,"
                            "OTHER_BE, RWY_RE, ILS_RE, RNAV_RE, LPV_RE, VISUAL_RE,"
                            "OTHER_RE from ApproachLighting WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        if rows:
            t = 5
            i = 45
            for row in rows:
                RWY_BE, ILS_BE, RNAV_BE, LPV_BE, VISUAL_BE,\
                OTHER_BE, RWY_RE, ILS_RE, RNAV_RE, LPV_RE, VISUAL_RE,\
                OTHER_RE = row

                self.fields.append(("RUNWAY END_{}".format(t), int(RWY_BE)))
                t += 1

                if ILS_BE == "Y":
                    self.fields.append(("Check Box{}".format(i), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i+1), "Yes"))
                if RNAV_BE == "Y":
                    self.fields.append(("Check Box{}".format(i+8), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i+9), "Yes"))
                if LPV_BE == "Y":
                    self.fields.append(("Check Box{}".format(i+16), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i+17), "Yes"))
                if VISUAL_BE == "Y":
                    self.fields.append(("Check Box{}".format(i+24), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i+25), "Yes"))
                if OTHER_BE == "Y":
                    self.fields.append(("Check Box{}".format(i+32), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i+33), "Yes"))

                i += 2

                self.fields.append(("RUNWAY END_{}".format(t), int(RWY_RE)))
                t += 1

                if ILS_RE == "Y":
                    self.fields.append(("Check Box{}".format(i), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 1), "Yes"))
                if RNAV_RE == "Y":
                    self.fields.append(("Check Box{}".format(i + 8), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 9), "Yes"))
                if LPV_RE == "Y":
                    self.fields.append(("Check Box{}".format(i + 16), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 17), "Yes"))
                if VISUAL_RE == "Y":
                    self.fields.append(("Check Box{}".format(i + 24), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 25), "Yes"))
                if OTHER_RE == "Y":
                    self.fields.append(("Check Box{}".format(i + 32), "Yes"))
                else:
                    self.fields.append(("Check Box{}".format(i + 33), "Yes"))

                i += 2

    def question11(self):
        self.cursor.execute("select RWY_BE, BE_CLOSE_IN, RWY_RE, RE_CLOSE_IN  from RunwayObstructions_CloseIn WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        obstructions = dict()

        if rows:
            for row in rows:
                RWY_BE, BE_CLOSE_IN, RWY_RE, RE_CLOSE_IN = row
                RWY_BE = RWY_BE.zfill(2)
                RWY_RE = RWY_RE.zfill(2)

                obstructions["{}/{}".format(RWY_BE, RWY_RE)] = {
                        RWY_BE: dict(),
                        RWY_RE: dict()
                }
                main_obj = obstructions["{}/{}".format(RWY_BE, RWY_RE)]
                be_end = main_obj[RWY_BE]
                if BE_CLOSE_IN == "Y":
                    be_end['CloseIn'] = "Yes"
                else:
                    be_end['CloseIn'] = "No"

                re_end = main_obj[RWY_RE]
                if RE_CLOSE_IN == "Y":
                    re_end['CloseIn'] = "Yes"
                else:
                    re_end['CloseIn'] = "No"

            self.cursor.execute("select BaseEndID, REID, BEThreshLength, BeCODescript, BeCOMarked, BECOHeight, BECODistance, BECOOffset,"
                                "BECOClearance, REThreshLength, RECODescript, RECOMarked, RECOHeight, RECODistance,"
                                "RECOOffset, RECOClearance from tblRunwaySC where FAAID='{}'".format(self.FAAID))
            rows = self.cursor.fetchall()
            if rows:
                for row in rows:
                    BaseEndID, REID, BEThreshLength, BeCODescript, BeCOMarked, BECOHeight, BECODistance, BECOOffset,\
                    BECOClearance, REThreshLength, RECODescript, RECOMarked, RECOHeight, RECODistance,\
                    RECOOffset, RECOClearance = row

                    if BaseEndID not in ['H1', 'H2', 'H'] and REID not in ['H1', 'H2', 'H']:

                        runway = "{}/{}".format(BaseEndID, REID)
                        if runway in obstructions:
                            main_obj = obstructions[runway]
                            be_obj = main_obj[BaseEndID]
                            be_obj['BEThreshLength'] = BEThreshLength
                            be_obj['BeCODescript'] = BeCODescript
                            be_obj['BeCOMarked'] = BeCOMarked
                            be_obj['BECOHeight'] = BECOHeight
                            be_obj['BECODistance'] = BECODistance
                            be_obj['BECOOffset'] = BECOOffset
                            be_obj['BECOClearance'] = BECOClearance

                            re_obj = main_obj[REID]
                            re_obj['REThreshLength'] = REThreshLength
                            re_obj['RECODescript'] = RECODescript
                            re_obj['RECOMarked'] = RECOMarked
                            re_obj['RECOHeight'] = RECOHeight
                            re_obj['RECODistance'] = RECODistance
                            re_obj['RECOOffset'] = RECOOffset
                            re_obj['RECOClearance'] = RECOClearance
                        else:
                            print("runway {} not found in the obstructions object {}".format(runway, obstructions))
            t = 9
            i = 103
            for x in list(obstructions.keys()):
                be_id = x.split("/")[0]
                re_id = x.split("/")[-1]

                be_atts = obstructions[x][be_id]
                re_atts = obstructions[x][re_id]

                self.fields.append(("RUNWAY END_{}".format(t), be_id))
                t += 1
                self.fields.append(("RUNWAY END_{}".format(t), re_id))
                t += 1

                self.fields.append(("{}".format(i), be_atts['BEThreshLength']))
                self.fields.append(("{}".format(i+4), be_atts['BeCODescript']))
                self.fields.append(("{}".format(i+8), be_atts['BeCOMarked']))
                self.fields.append(("{}".format(i+12), be_atts['BECOHeight']))
                self.fields.append(("{}".format(i+16), be_atts['BECODistance']))
                self.fields.append(("{}".format(i+20), be_atts['BECOOffset']))
                self.fields.append(("{}".format(i+24), be_atts['BECOClearance']))
                self.fields.append(("{}".format(i + 28), be_atts['CloseIn']))
                i += 1

                self.fields.append(("{}".format(i), re_atts['REThreshLength']))
                self.fields.append(("{}".format(i + 4), re_atts['RECODescript']))
                self.fields.append(("{}".format(i + 8), re_atts['RECOMarked']))
                self.fields.append(("{}".format(i + 12), re_atts['RECOHeight']))
                self.fields.append(("{}".format(i + 16), re_atts['RECODistance']))
                self.fields.append(("{}".format(i + 20), re_atts['RECOOffset']))
                self.fields.append(("{}".format(i + 24), re_atts['RECOClearance']))
                self.fields.append(("{}".format(i + 28), re_atts['CloseIn']))
                i += 1

    def question12(self):
        self.cursor.execute("select TAXIWAY_SYSTEM  from TaxiwaySystem WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        if rows:
            target_fields = {
                "full_parallel": "Check Box86",
                "partial_parallel": "Check Box87",
                "turn_around_both": "Check Box88",
                "turn_around_one": "Check Box89_0",
                "no_supporting": "Check Box89_1"
            }
            for row in rows:
                if 'NO SUPPORTING' in row[0].upper():
                    self.fields.append((target_fields['no_supporting'], "Yes"))
                elif 'ONE TURN' in row[0].upper():
                    self.fields.append((target_fields['turn_around_one'], "Yes"))
                elif 'FULL PARALLEL' in row[0].upper():
                    self.fields.append((target_fields['full_parallel'], "Yes"))
                elif 'BOTH TURN' in row[0].upper():
                    self.fields.append((target_fields['turn_around_both'], "Yes"))
                elif 'PARTIAL PARALLEL' in row[0].upper():
                    self.fields.append((target_fields['partial_parallel'], "Yes"))

    def question16(self):
        self.cursor.execute("select StaType from tblASOS_AWOS WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        weather_types = {
            "AWOS": False,
            "ASOS": False,
            "Super Unicom": False,
            "Weather Observer": False
        }
        if rows:
            for row in rows:
                if row[0] is not None:
                    if 'AWOS' in row[0].upper():
                        weather_types["AWOS"] = True
                    elif 'ASOS' in row[0].upper():
                        weather_types["ASOS"] = True

        for k, v in iter(weather_types.items()):
            if v:
                if k == "AWOS":
                    self.fields.append(("Check Box94", "Yes"))
                elif k == "ASOS":
                    self.fields.append(("Check Box95", "Yes"))

    def question18(self):
        self.cursor.execute("select Thangars, THangarsSqFt, ThangarsRate, CorporateHangars, CorporateHangarsSqFt, CorporateHangarsRate,"\
                            "BoxHangars, BoxHangarsSqFt, BoxHangarsRate, HangarPorts, HangarPortsSqFt, HangarPortsRate,"\
                            "UnknownHangars, UnknownHangarsSqFt, UnknownHangarsRate, TieDowns, TieDownsRate from tblFacilities WHERE FAAID='{}'".format(self.FAAID))
        rows = self.cursor.fetchall()
        hangars = dict()
        if len(rows):
            for row in rows:
                THangars, THangarsSqFt, ThangarsRate, CorporateHangars, CorprateHangarsSqFt, CorporateHangarsRate,\
                BoxHangars, BoxHangarsSqFt, BoxHangarsRate, HangerPorts, HangarPortsSqFt, HangarPortsRate,\
                UnknownHangars, UnknownHangarsSqFt, UnknownHangarsRate, TieDowns, TieDownsRate = row

                fields = [THangars, THangarsSqFt, ThangarsRate, CorporateHangars, CorprateHangarsSqFt, CorporateHangarsRate,
                BoxHangars, BoxHangarsSqFt, BoxHangarsRate, HangerPorts, HangarPortsSqFt, HangarPortsRate,
                UnknownHangars, UnknownHangarsSqFt, UnknownHangarsRate]

                target_fields = ["undefined_{}".format(i) for i in range(55, 70)]

                fields.extend([TieDowns, TieDownsRate])
                target_fields.extend(["undefined_70", "undefined_72"])

                mixed = zip(target_fields, fields)
                for combo in mixed:
                    self.fields.append(combo)

    def process(self):
        self.question1()
        self.question2()
        self.question3()
        self.question5()
        self.question8()
        self.question9()
        self.question10()
        self.question11()
        self.question12()
        self.question16()
        self.question18()

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


