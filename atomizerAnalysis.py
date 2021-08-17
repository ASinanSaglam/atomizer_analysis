from sqlite3.dbapi2 import Error, OperationalError
import bionetgen, os, time, math, sys, requests, re, contextlib, io
from numpy.core.numeric import False_
import sqlite3 as sl
import urllib.request
import pandas as pd
import subprocess as sb
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
from difflib import SequenceMatcher
from bs4 import BeautifulSoup as BS
from bionetgen.atomizer.atomizeTool import AtomizeTool


class AtomizerDatabase:
    def __init__(self, dbase_path="atomizer.db"):
        self.dbase_path = dbase_path
        self.dbase_con = sl.connect(self.dbase_path)
        self.last_call = time.time()
        self.current_max_models = 1017
        self.TRANSLATION_SUCCESS = 1
        self.TRANSLATION_FAIL = -1
        self.TRANSLATION_UNATTEMPTED = 0
        self.TRANSLATION_MAJOR_ERROR = 2
        self.RESULT_FAIL_BNGL = -2
        self.RESULT_FAIL_STANDARD = -1
        self.RESULT_FAIL_VALIDATION = -3
        self.RESULT_SUCC_BNGL = 2
        self.RESULT_SUCC_STANDARD = 1
        self.RESULT_SUCC_VALIDATION = 3
        self.RESULT_UNATTEMPTED = 0
        # need to correctly initialize tables
        self.add_translation_table()
        self.add_model_table()
        self.add_results_table()

    def get_path(self, test_no):
        query = "SELECT PATH FROM MODELS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        paths = q.fetchall()
        if len(paths) > 0:
             if paths[0][0] is not None:
                path = bytes.fromhex(paths[0][0]).decode("utf-8")
                return path
        else:
            return None

    def set_path(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE MODELS SET PATH = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False
    
    def divine_path(self, test_no):
        # we will try to find a path for a SBML model
        suggested_path = os.path.join("curated","bmd{:010d}.xml".format(test_no))
        suggested_path = os.path.abspath(suggested_path)
        if os.path.isfile(suggested_path):
            # we got a model
            self.set_path(test_no, suggested_path)
            return suggested_path
        else:
            return None

    def get_sbml(self, test_no):
        query = "SELECT SBML FROM MODELS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        sbmls = q.fetchall()
        if len(sbmls) > 0:
            # gotta decode the hex
            if sbmls[0][0] is not None:
                sbml = bytes.fromhex(sbmls[0][0]).decode("utf-8")
                return sbml
        return None

    def set_sbml(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE MODELS SET SBML = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_bngl(self, test_no, type="FLAT"):
        # type options "FLAT", "ATOM"
        if type == "FLAT":
            return self.get_bngl_flat(test_no)
        elif type == "ATOM":
            return self.get_bngl_atom(test_no)
        else:
            print(f"bngl type {type} not recognized, options are 'FLAT' and 'ATOM'")
            return None

    def set_bngl(self, test_no, value, type="FLAT"):
        if type == "FLAT":
            return self.set_bngl_flat(test_no, value)
        elif type == "ATOM":
            return self.set_bngl_atom(test_no, value)
        else:
            print(f"bngl type {type} not recognized, options are 'FLAT' and 'ATOM'")
            return None

    def get_bngl_flat(self, test_no):
        query = "SELECT BNGL_FLAT FROM MODELS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        bngls = q.fetchall()
        if len(bngls) > 0:
            if bngls[0][0] is not None:
                bngl = bytes.fromhex(bngls[0][0]).decode("utf-8")
                return bngl
        return None

    def set_bngl_flat(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE MODELS SET BNGL_FLAT = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_bngl_atom(self, test_no):
        query = "SELECT BNGL_ATOM FROM MODELS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        bngls = q.fetchall()
        if len(bngls) > 0:
            if bngls[0][0] is not None:
                bngl = bytes.fromhex(bngls[0][0]).decode("utf-8")
                return bngl
        return None

    def set_bngl_atom(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE MODELS SET BNGL_ATOM = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_atomized_bngxml(self, test_no):
        query = "SELECT ATOM_BNGXML FROM MODELS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        xmls = q.fetchall()
        if len(xmls) > 0:
            if xmls[0][0] is not None:
                return bytes.fromhex(xmls[0][0]).decode("utf-8")
        return None

    def set_atomized_bngxml(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE MODELS SET ATOM_BNGXML = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_flat_bngxml(self, test_no):
        query = "SELECT FLAT_BNGXML FROM MODELS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        xmls = q.fetchall()
        if len(xmls) > 0:
            if xmls[0][0] is not None:
                return bytes.fromhex(xmls[0][0]).decode("utf-8")
        return None

    def set_flat_bngxml(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE MODELS SET FLAT_BNGXML = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def download_model(self, model_no, file_path=None, overwrite=False):
        # don't overwhelm the servers by making sure
        # we wait at least 10 seconds
        since_last = time.time() - self.last_call
        if not (since_last > 15):
            wait_for = math.ceil(15 - since_last)
            print(f"waiting {wait_for}s to make sure we are not flooding the server")
            time.sleep(wait_for)
        # if a file path is not given, get a default
        if file_path is None:
            if not os.path.isdir("curated"):
                os.mkdir("curated")
            file_path = os.path.join("curated", f"bmd{model_no:010}.xml")
        # first we need to pull the actual website to get file download link
        url = f"https://www.ebi.ac.uk/biomodels/BIOMD{model_no:010}"
        headers = headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        }
        html = requests.get(url, headers=headers).text
        to_find = (
            f"(/biomodels/model/download/BIOMD{model_no:010})(.+)(filename=)(.+)(.xml)"
        )
        links = re.findall(to_find, html)
        try:
            dl_link = "".join(links[0])
        except IndexError as e:
            print(f"Model ID {model_no} doesn't have a download link")
            print(e)
            return False, None
        dl_link = "https://www.ebi.ac.uk" + dl_link
        print(f"found download link: {dl_link})")
        # try downloading
        try:
            print("fetching file")
            with urllib.request.urlopen(dl_link) as f:
                html = f.read().decode("utf-8")
            self.last_call = time.time()
            print("got an XML file")
        except Exception as e:
            self.last_call = time.time()
            print(e)
            return False, None
        # write to a file
        if os.path.isfile(file_path):
            if overwrite:
                with open(file_path, "w") as f:
                    f.write(html)
            else:
                False, file_path
        else:
            with open(file_path, "w") as f:
                f.write(html)
        # return status and path
        return True, file_path

    def check_model(self, model_no, TABLE="MODELS"):
        q = self.dbase_con.execute(f"SELECT * FROM {TABLE} WHERE id={model_no}")
        r = q.fetchall()
        if len(r) == 0:
            return False
        else:
            return True

    def insert_model(self, model_no, TABLE="MODELS"):
        i_str = f"INSERT INTO {TABLE} (ID) VALUES ({model_no})"
        try:
            self.dbase_con.execute(i_str)
            self.dbase_con.commit()
            return True
        except Exception as e:
            print("failed to insert")
            print(e)
            return False

    def add_translation_table(self):
        try:
            self.dbase_con.execute(
                """
                CREATE TABLE TRANSLATION (
                    ID INT PRIMARY KEY NOT NULL,
                    ATOM_STATUS INT,
                    FLAT_STATUS INT,
                    ATOM_LOG TEXT,
                    FLAT_LOG TEXT,
                    ATOM_NOTES TEXT,
                    FLAT_NOTES TEXT,
                    STRUCT_RAT REAL
                );
            """
            )
            self.dbase_con.commit()
            return True
        except:
            return False

    def get_trans_atom_log(self, test_no):
        query = "SELECT ATOM_LOG FROM TRANSLATION WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        logs = q.fetchall()
        if len(logs) > 0:
            if logs[0][0] is not None:
                return bytes.fromhex(logs[0][0]).decode("utf-8")
        return None

    def set_trans_atom_log(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE TRANSLATION SET ATOM_LOG = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_trans_flat_log(self, test_no):
        query = "SELECT FLAT_LOG FROM TRANSLATION WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        logs = q.fetchall()
        if len(logs) > 0:
            if logs[0][0] is not None:
                return bytes.fromhex(logs[0][0]).decode("utf-8")
        return None

    def set_trans_flat_log(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE TRANSLATION SET FLAT_LOG = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_trans_struct_rat(self, test_no):
        query = "SELECT STRUCT_RAT FROM TRANSLATION WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        srs = q.fetchall()
        if len(srs) > 0:
            if srs[0][0] is not None:
                # return bytes.fromhex(srs[0][0]).decode("utf-8")
                return srs[0][0]
        return None

    def set_trans_struct_rat(self, test_no, value):
        query = "UPDATE TRANSLATION SET STRUCT_RAT = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_trans_atom_notes(self, test_no):
        query = "SELECT ATOM_NOTES FROM TRANSLATION WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        notes = q.fetchall()
        if len(notes) > 0:
            if notes[0][0] is not None:
                return bytes.fromhex(notes[0][0]).decode("utf-8")
        return None

    def set_trans_atom_note(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE TRANSLATION SET ATOM_NOTES = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_trans_flat_notes(self, test_no):
        query = "SELECT FLAT_NOTES FROM TRANSLATION WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        notes = q.fetchall()
        if len(notes) > 0:
            if notes[0][0] is not None:
                return bytes.fromhex(notes[0][0]).decode("utf-8")
        return None

    def set_trans_flat_note(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE TRANSLATION SET FLAT_NOTES = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_trans_atom_status(self, test_no):
        query = "SELECT ATOM_STATUS FROM TRANSLATION WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        srs = q.fetchall()
        if len(srs) > 0:
            if srs[0][0] == self.TRANSLATION_SUCCESS:
                return "Success"
            elif srs[0][0] == self.TRANSLATION_FAIL:
                return "Fail"
            elif srs[0][0] == self.TRANSLATION_UNATTEMPTED:
                return "Unattempted"
            elif srs[0][0] == self.TRANSLATION_MAJOR_ERROR:
                return "Error"
            else:
                return srs[0][0]
        else:
            return None

    def set_trans_atom_status(self, test_no, value):
        query = "UPDATE TRANSLATION SET ATOM_STATUS = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_trans_flat_status(self, test_no):
        query = "SELECT FLAT_STATUS FROM TRANSLATION WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        srs = q.fetchall()
        if len(srs) > 0:
            if srs[0][0] == self.TRANSLATION_SUCCESS:
                return "Success"
            elif srs[0][0] == self.TRANSLATION_FAIL:
                return "Fail"
            elif srs[0][0] == self.TRANSLATION_UNATTEMPTED:
                return "Unattempted"
            elif srs[0][0] == self.TRANSLATION_MAJOR_ERROR:
                return "Error"
            else:
                return srs[0][0]
        else:
            return None

    def set_trans_flat_status(self, test_no, value):
        query = "UPDATE TRANSLATION SET FLAT_STATUS = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def add_results_table(self):
        try:
            self.dbase_con.execute(
                """
                CREATE TABLE RESULTS (
                    ID INT PRIMARY KEY NOT NULL,
                    T_END INT NOT NULL,
                    N_STEPS INT NOT NULL,
                    ATOM_VAL_RATIO REAL,
                    FLAT_VAL_RATIO REAL,
                    COPASI_LOG TEXT,
                    BNG_ATOM_LOG TEXT,
                    BNG_FLAT_LOG TEXT,
                    VALIDATING_SERIES TEXT,
                    FAILING_SERIES TEXT,
                    CUR_KEYS TEXT,
                    ATOM_STATUS INT,
                    FLAT_STATUS INT
                );
            """
            )
            self.dbase_con.commit()
            return True
        except:
            return False

    def get_result_tend(self, test_no):
        query = "SELECT T_END FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        r = q.fetchall()
        if len(r) > 0:
            return r[0][0]
        else:
            return None

    def set_result_tend(self, test_no, value):
        query = "UPDATE RESULTS SET T_END = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_nsteps(self, test_no):
        query = "SELECT N_STEPS FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        r = q.fetchall()
        if len(r) > 0:
            return r[0][0]
        else:
            return None

    def set_result_nsteps(self, test_no, value):
        query = "UPDATE RESULTS SET N_STEPS = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_curkeys(self, test_no):
        query = "SELECT CUR_KEYS FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        r = q.fetchall()
        if len(r) > 0:
            return r[0][0]
        else:
            return None

    def set_result_curkeys(self, test_no, value):
        query = "UPDATE RESULTS SET CUR_KEYS = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_atomized_valratio(self, test_no):
        query = "SELECT ATOM_VAL_RATIO FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        r = q.fetchall()
        if len(r) > 0:
            return r[0][0]
        else:
            return None

    def set_result_atomized_valratio(self, test_no, value):
        query = "UPDATE RESULTS SET ATOM_VAL_RATIO = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_flat_valratio(self, test_no):
        query = "SELECT FLAT_VAL_RATIO FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        r = q.fetchall()
        if len(r) > 0:
            return r[0][0]
        else:
            return None

    def set_result_flat_valratio(self, test_no, value):
        query = "UPDATE RESULTS SET FLAT_VAL_RATIO = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False
    
    def get_result_atom_status(self, test_no):
        query = "SELECT ATOM_STATUS FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        r = q.fetchall()
        if len(r) > 0:
            return r[0][0]
        else:
            return None

    def set_result_atom_status(self, test_no, value):
        query = "UPDATE RESULTS SET ATOM_STATUS = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False
        
    def get_result_flat_status(self, test_no):
        query = "SELECT FLAT_STATUS FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        r = q.fetchall()
        if len(r) > 0:
            return r[0][0]
        else:
            return None

    def set_result_flat_status(self, test_no, value):
        query = "UPDATE RESULTS SET FLAT_STATUS = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def set_result_validating_series(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE RESULTS SET VALIDATING_SERIES = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_validating_series(self, test_no):
        query = "SELECT VALIDATING_SERIES FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        srs = q.fetchall()
        if len(srs) > 0:
            if srs[0][0] is not None:
                return bytes.fromhex(srs[0][0]).decode("utf-8")
        return None
    
    def set_result_failing_series(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE RESULTS SET FAILING_SERIES = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_failing_series(self, test_no):
        query = "SELECT FAILING_SERIES FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        srs = q.fetchall()
        if len(srs) > 0:
            if srs[0][0] is not None:
                return bytes.fromhex(srs[0][0]).decode("utf-8")
        return None

    def set_result_copasi_log(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE RESULTS SET COPASI_LOG = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_copasi_log(self, test_no):
        query = "SELECT COPASI_LOG FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        srs = q.fetchall()
        if len(srs) > 0:
            if srs[0][0] is not None:
                return bytes.fromhex(srs[0][0]).decode("utf-8")
        return None
    
    def set_result_bng_atom_log(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE RESULTS SET BNG_ATOM_LOG = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_bng_atom_log(self, test_no):
        query = "SELECT BNG_ATOM_LOG FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        srs = q.fetchall()
        if len(srs) > 0:
            if srs[0][0] is not None:
                return bytes.fromhex(srs[0][0]).decode("utf-8")
        return None

    def set_result_bng_flat_log(self, test_no, value):
        value = value.encode("utf-8").hex()
        query = "UPDATE RESULTS SET BNG_FLAT_LOG = ? WHERE id=?"
        try:
            q = self.dbase_con.execute(query, (value, test_no))
            self.dbase_con.commit()  # is this necessary?
            return True
        except Exception as e:
            print(e)
            return False

    def get_result_bng_flat_log(self, test_no):
        query = "SELECT BNG_FLAT_LOG FROM RESULTS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        srs = q.fetchall()
        if len(srs) > 0:
            if srs[0][0] is not None:
                return bytes.fromhex(srs[0][0]).decode("utf-8")
        return None

    def print_atomized_translation_status(self, detailed=False):
        succ = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE ATOM_STATUS = ?",
            (self.TRANSLATION_SUCCESS,),
        )
        succ = succ.fetchall()
        fail = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE ATOM_STATUS = ?", (self.TRANSLATION_FAIL,)
        )
        fail = fail.fetchall()
        unatmpt = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE ATOM_STATUS = ?",
            (self.TRANSLATION_UNATTEMPTED,),
        )
        unatmpt = unatmpt.fetchall()
        error = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE ATOM_STATUS = ?",
            (self.TRANSLATION_MAJOR_ERROR,),
        )
        error = error.fetchall()
        print(
            f"{len(succ)} models were successful, {len(fail)} models failed, {len(error)} models have major errors and {len(unatmpt)} models remain unattempted"
        )
        if detailed:
            print(f"Successful models: {[i[0] for i in succ]}")
            print(f"Failed models: {[i[0] for i in fail]}")
            print(f"Major error models: {[i[0] for i in error]}")
            print(f"Unattempted models: {[i[0] for i in unatmpt]}")

    def print_flat_translation_status(self, detailed=False):
        succ = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE FLAT_STATUS = ?",
            (self.TRANSLATION_SUCCESS,),
        )
        succ = succ.fetchall()
        fail = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE FLAT_STATUS = ?", (self.TRANSLATION_FAIL,)
        )
        fail = fail.fetchall()
        unatmpt = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE FLAT_STATUS = ?",
            (self.TRANSLATION_UNATTEMPTED,),
        )
        unatmpt = unatmpt.fetchall()
        error = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE FLAT_STATUS = ?",
            (self.TRANSLATION_MAJOR_ERROR,),
        )
        error = error.fetchall()
        print(
            f"{len(succ)} models were successful, {len(fail)} models failed, {len(error)} models have major errors and {len(unatmpt)} models remain unattempted"
        )
        if detailed:
            print(f"Successful models: {[i[0] for i in succ]}")
            print(f"Failed models: {[i[0] for i in fail]}")
            print(f"Major error models: {[i[0] for i in error]}")
            print(f"Unattempted models: {[i[0] for i in unatmpt]}")

    def print_translation_status(self, detailed=False):
        print("## Atomized tranlation results: ")
        self.print_atomized_translation_status(detailed=detailed)
        print("## Flat tranlation results: ")
        self.print_flat_translation_status(detailed=detailed)

    def print_results_summary(self, detailed=False):
        self.print_results_summary_atom(detailed=detailed)
        self.print_results_summary_flat(detailed=detailed)

    def print_results_summary_atom(self, detailed=False):
        print("## Summary of atomized results:")
        # successful ones
        succ_std = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_STATUS = ?",
            (self.RESULT_SUCC_STANDARD,),
        )
        succ_std = succ_std.fetchall()
        succ_bng = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_STATUS = ?",
            (self.RESULT_SUCC_BNGL,),
        )
        succ_bng = succ_bng.fetchall()
        succ_val = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_STATUS = ?",
            (self.RESULT_SUCC_VALIDATION,),
        )
        succ_val = succ_val.fetchall()
        # failed ones
        fail_std = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_STATUS = ?",
            (self.RESULT_FAIL_STANDARD,),
        )
        fail_std = fail_std.fetchall()
        fail_bng = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_STATUS = ?",
            (self.RESULT_FAIL_BNGL,),
        )
        fail_bng = fail_bng.fetchall()
        fail_val = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_STATUS = ?",
            (self.RESULT_FAIL_VALIDATION,),
        )
        fail_val = fail_val.fetchall()
        unatmpt = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_STATUS = ?",
            (self.RESULT_UNATTEMPTED,),
        )
        unatmpt = unatmpt.fetchall()
        # now we get validation stuff
        full_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_VAL_RATIO = ?",
            (1.0,),
        )
        full_valid = full_valid.fetchall()
        high_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_VAL_RATIO > ?",
            (0.7,),
        )
        high_valid = high_valid.fetchall()
        med_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_VAL_RATIO > ?",
            (0.5,),
        )
        med_valid = med_valid.fetchall()
        low_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_VAL_RATIO <= ?",
            (0.5,),
        )
        low_valid = low_valid.fetchall()
        in_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE ATOM_VAL_RATIO = ?",
            (0.0,),
        )
        in_valid = in_valid.fetchall()

        print("## Atomized validation status")
        print(f"Successful standard data acquisition: {len(succ_std)}")
        print(f"Successful bng data acquisition: {len(succ_bng)}")
        print(f"Successful validation calculation: {len(succ_val)}")
        print(f"Failed standard data acquisition: {len(fail_std)}")
        print(f"Failed bng data acquisition: {len(fail_bng)}")
        print(f"Failed validation calculation: {len(fail_val)}")
        print(f"Unattempted: {len(unatmpt)}")
        print("## Atomized validation values report")
        print(f"Fully validating (=1.0): {len(full_valid)}")
        print(f"High VR (>0.7): {len(high_valid)}")
        print(f"Med VR (>0.5): {len(med_valid)}")
        print(f"Low VR (<=0.5 & !=0.0): {len(low_valid)-len(in_valid)}")
        print(f"Invalid VR (=0.0): {len(in_valid)}")
        print("## Structured molecule ratio")
        succ_trans = self.dbase_con.execute(
            "SELECT ID FROM TRANSLATION WHERE ATOM_STATUS = ?",
            (self.TRANSLATION_SUCCESS,),
        )
        succ_trans = succ_trans.fetchall()
        all_struct_rat = np.array([self.get_trans_struct_rat(i[0]) for i in succ_trans])
        # import IPython;IPython.embed()
        print(f"Total average: {np.average(all_struct_rat)}")
        print(f"High VR average: {np.average([self.get_trans_struct_rat(i[0]) for i in high_valid])}")
        print(f"Med VR average: {np.average([self.get_trans_struct_rat(i[0]) for i in med_valid])}")
        print(f"Low VR average: {np.average([self.get_trans_struct_rat(i[0]) for i in low_valid])}")
        print(f"Invalid average: {np.average([self.get_trans_struct_rat(i[0]) for i in in_valid])}")
        print(f"Full SR count: {sum(all_struct_rat==1.0)}")
        print(f"High SR (>0.7) count: {sum(all_struct_rat>0.7)}")
        print(f"Med SR (>0.5) count: {sum(all_struct_rat>0.5)}")
        print(f"Low SR (<=0.5 & != 0) count: {sum(all_struct_rat<=0.5)-sum(all_struct_rat==0.0)}")
        print(f"Zero SR (=0.0) count: {sum(all_struct_rat==0.0)}")


        if detailed:
            print(f"Successful standard data acquisition: {[i[0] for i in succ_std]}")
            print(f"Successful bng data acquisition: {[i[0] for i in succ_bng]}")
            print(f"Successful validation calculation: {[i[0] for i in succ_val]}")
            print(f"Failed standard data acquisition: {[i[0] for i in fail_std]}")
            print(f"Failed bng data acquisition: {[i[0] for i in fail_bng]}")
            print(f"Failed validation calculation: {[i[0] for i in fail_val]}")
            print(f"Unattempted: {[i[0] for i in unatmpt]}")

    def print_results_summary_flat(self, detailed=False):
        print("## Summary of flat results:")
        # successful ones
        succ_std = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_STATUS = ?",
            (self.RESULT_SUCC_STANDARD,),
        )
        succ_std = succ_std.fetchall()
        succ_bng = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_STATUS = ?",
            (self.RESULT_SUCC_BNGL,),
        )
        succ_bng = succ_bng.fetchall()
        succ_val = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_STATUS = ?",
            (self.RESULT_SUCC_VALIDATION,),
        )
        succ_val = succ_val.fetchall()
        # failed ones
        fail_std = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_STATUS = ?",
            (self.RESULT_FAIL_STANDARD,),
        )
        fail_std = fail_std.fetchall()
        fail_bng = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_STATUS = ?",
            (self.RESULT_FAIL_BNGL,),
        )
        fail_bng = fail_bng.fetchall()
        fail_val = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_STATUS = ?",
            (self.RESULT_FAIL_VALIDATION,),
        )
        fail_val = fail_val.fetchall()
        unatmpt = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_STATUS = ?",
            (self.RESULT_UNATTEMPTED,),
        )
        unatmpt = unatmpt.fetchall()
        # now we get validation stuff
        full_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_VAL_RATIO = ?",
            (1.0,),
        )
        full_valid = full_valid.fetchall()
        high_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_VAL_RATIO > ?",
            (0.7,),
        )
        high_valid = high_valid.fetchall()
        med_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_VAL_RATIO > ?",
            (0.5,),
        )
        med_valid = med_valid.fetchall()
        low_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_VAL_RATIO <= ?",
            (0.5,),
        )
        low_valid = low_valid.fetchall()
        in_valid = self.dbase_con.execute(
            "SELECT ID FROM RESULTS WHERE FLAT_VAL_RATIO = ?",
            (0.0,),
        )
        in_valid = in_valid.fetchall()
        
        print("## Flat validation status")
        print(f"Successful standard data acquisition: {len(succ_std)}")
        print(f"Successful bng data acquisition: {len(succ_bng)}")
        print(f"Successful validation calculation: {len(succ_val)}")
        print(f"Failed standard data acquisition: {len(fail_std)}")
        print(f"Failed bng data acquisition: {len(fail_bng)}")
        print(f"Failed validation calculation: {len(fail_val)}")
        print(f"Unattempted: {len(unatmpt)}")
        print("## Flat validation values report")
        print(f"Fully validating (=1.0): {len(full_valid)}")
        print(f"High VR (>0.7): {len(high_valid)}")
        print(f"Med VR (>0.5): {len(med_valid)}")
        print(f"Low VR (<=0.5): {len(low_valid)}")
        print(f"Invalid VR (=0.0): {len(in_valid)}")
        
        if detailed:
            print(f"Successful standard data acquisition: {[i[0] for i in succ_std]}")
            print(f"Successful bng data acquisition: {[i[0] for i in succ_bng]}")
            print(f"Successful validation calculation: {[i[0] for i in succ_val]}")
            print(f"Failed standard data acquisition: {[i[0] for i in fail_std]}")
            print(f"Failed bng data acquisition: {[i[0] for i in fail_bng]}")
            print(f"Failed validation calculation: {[i[0] for i in fail_val]}")
            print(f"Unattempted: {[i[0] for i in unatmpt]}")

    def get_sim_param(self, test_no):
        t_end = self.get_result_tend(test_no)
        n_steps = self.get_result_nsteps(test_no)
        if t_end is None:
            self.dbase_con.execute("INSERT INTO RESULTS (ID,T_END,N_STEPS) VALUES (?,1000,100)", (test_no,))
            self.dbase_con.commit()
            t_end = self.get_result_tend(test_no)
            n_steps = self.get_result_nsteps(test_no)
        return t_end, n_steps

    def add_model_table(self):
        try:
            self.dbase_con.execute(
                """
                CREATE TABLE MODELS (
                    ID INT PRIMARY KEY NOT NULL,
                    TSTAMP INT,
                    PATH TEXT,
                    SBML TEXT,
                    NAME TEXT,
                    BNGL_FLAT TEXT,
                    BNGL_ATOM TEXT,
                    FLAT_BNGXML TEXT,
                    ATOM_BNGXML TEXT
                );
            """
            )
        except OperationalError as oe:
            print("Model table already exits")
            print(oe)

    def get_models(self):
        # get list of models already in database
        existing_models = self.dbase_con.execute("SELECT ID FROM MODELS")
        existing_models = existing_models.fetchall()
        existing_models = [i[0] for i in existing_models]
        # this needs to download each model, save it
        # in a field in a table
        worked_on = []
        for model_id in range(1, self.current_max_models + 1):
            print(f"Working on model ID: {model_id}")
            # if model_id not in database
            if model_id in existing_models:
                continue
            # now we download
            print("downloading model")
            r, p = self.download_model(model_id)
            if (not r) and (p is None):
                print(f"download for model {model_id} failed!")
                continue
            print("download complete")
            # if download is successful OR we aleady had the file
            if r or (not r and p is not None):
                print("adding to database")
                # add to database
                with open(p, "r") as f:
                    sbml_text = f.read()
                i_str = "INSERT INTO MODELS "
                i_str += "(ID, TSTAMP, PATH, SBML) "
                i_str += f"VALUES ({model_id}, {math.ceil(time.time())}, '{p}', '{sbml_text.encode('utf-8').hex()}');"
                self.dbase_con.execute(i_str)
                print("database addition complete")
            self.dbase_con.commit()
            worked_on.append(model_id)
        print("Finished working on these", worked_on)


class AtomizerAnalyzer:
    def __init__(self, database, copasi_path=None):
        self.database = database
        self.copasi_path = copasi_path
        self.set_stdIO_context()
        self.base_dir = os.path.abspath(os.getcwd())

    def set_stdIO_context(self):
        self.sde = io.StringIO()
        self.sdo = io.StringIO()
        self.sdo_context = contextlib.redirect_stdout(self.sdo)
        self.sde_context = contextlib.redirect_stderr(self.sde)

    def reset_stdIO(self):
        self.sde.truncate(0)
        self.sde.seek(0)
        self.sde.truncate(0)
        self.sdo.seek(0)

    def translate(self, test_no, bid=False, atomize=True, overwrite=False):
        # check to see if we got a translation first
        if not overwrite:
            if atomize:
                translation = self.database.get_bngl_atom(test_no)
                if translation is not None:
                    print(f"found atomized translation of model {test_no}")
                    return translation
            else:
                translation = self.database.get_bngl_flat(test_no)
                if translation is not None:
                    print(f"found flat translation of model {test_no}")
                    return translation
        if not os.path.isdir("atomized_bngxml"):
            os.mkdir("atomized_bngxml")
        if not os.path.isdir("flat_bngxml"):
            os.mkdir("flat_bngxml")
        if atomize:
            if not os.path.isdir("atomized"):
                os.mkdir("atomized")
            outfold = "atomized"
            ext = "atomized"
        else:
            if not os.path.isdir("flat"):
                os.mkdir("flat")
            outfold = "flat"
            ext = "flat"
        # getting our information from the database
        # TODO: at some point make it so that atomizer can just
        # take in some string instead of a file
        infile = self.database.get_path(test_no)
        if infile is None:
            # we don't have a path to a model, let's see if we can divine one
            infile = self.database.divine_path(test_no)
            # import IPython;IPython.embed()
            if infile is None:
                # we can't divine a path
                print(f"We can't divine a path for model {test_no}")
                e = RuntimeError(f"We can't divine a path for model {test_no}")
                if atomize:
                    self.database.set_trans_atom_note(test_no, str(e))
                    self.database.set_trans_atom_status(
                        test_no, self.database.TRANSLATION_FAIL
                    )
                else:
                    self.database.set_trans_flat_note(test_no, str(e))
                    self.database.set_trans_flat_status(
                        test_no, self.database.TRANSLATION_FAIL
                    )
                return None
        filename = f"bmd{test_no:010}_{ext}.bngl"
        outfile = os.path.join(outfold, filename)
        opt = {
            "input": infile,
            "output": outfile,
            "atomize": atomize,
            "molecule_id": bid,
            "pathwaycommons": True
        }
        a = AtomizeTool(options_dict=opt)
        try:
            with self.sde_context:
                with self.sdo_context:
                    rarray = a.run()
            try:
                struct_rat = float(self.sdo.getvalue().split(":")[-1].strip())
            except ValueError as e:
                struct_rat = 0.0

            stderr = self.sde.getvalue()
            print(f"our sdterr was: {stderr[:100]}")
            self.reset_stdIO()
            # now we can update the database too
            if atomize:
                self.database.set_trans_struct_rat(test_no, struct_rat)
                self.database.set_trans_atom_log(test_no, stderr)
                self.database.set_bngl_atom(test_no, rarray.finalString)
                self.database.set_trans_atom_status(
                    test_no, self.database.TRANSLATION_SUCCESS
                )
                # TODO: doesn't corectly move the file
                bngxml = filename.replace(".bngl", ".xml")
                if os.path.isfile(bngxml):
                    with open(bngxml, "r") as f:
                        self.database.set_atomized_bngxml(test_no, f.read())
                    os.rename(bngxml, os.path.join("atomized_bngxml", bngxml))
            else:
                self.database.set_bngl_flat(test_no, rarray.finalString)
                self.database.set_trans_flat_log(test_no, stderr)
                self.database.set_trans_flat_status(
                    test_no, self.database.TRANSLATION_SUCCESS
                )
                # TODO: doesn't corectly move the file
                bngxml = filename.replace(".bngl", ".xml")
                if os.path.isfile(bngxml):
                    with open(bngxml, "r") as f:
                        self.database.set_flat_bngxml(test_no, f.read())
                    os.rename(bngxml, os.path.join("flat_bngxml", bngxml))
            return rarray.finalString
        except Exception as e:
            if atomize:
                self.database.set_trans_atom_note(test_no, str(e))
                self.database.set_trans_atom_status(
                    test_no, self.database.TRANSLATION_FAIL
                )
            else:
                self.database.set_trans_flat_note(test_no, str(e))
                self.database.set_trans_flat_status(
                    test_no, self.database.TRANSLATION_FAIL
                )
            return None
    
    def run_and_load_test_standard(self, test_no, sim="copasi", overwrite=False):
        # sim options: copasi or librr
        if sim.lower() == "copasi":
            return self.run_copasi_and_load(test_no, overwrite=overwrite)
        elif sim.lower() == "librr":
            return self.run_librr_and_load(test_no)
        else:
            raise NotImplementedError

    def copasi_load(self, fname):
        print("loading copasi results")
        with open(fname, "r") as f:
            # Get column names from first line of file
            line = f.readline()
            names = list(map(lambda x: x.replace("]","").strip(), line.split("[")))
            unique_names = []
            names_to_return = []
            ctr = 0
            for name in names:
                if not name in unique_names:
                    unique_names.append(name)
                    names_to_return.append(name)
                else:
                    unique_names.append("TRASH_DUMP_THIS_{}".format(ctr))
                    ctr+=1
            dtypes = list(zip(unique_names, ['f8' for i in unique_names]))
            result = pd.read_table(f,sep='\s+',header=None,names=list(unique_names))
        result = result[result.columns.drop(list(result.filter(regex="TRASH")))]
        print("returning copasi results")
        return result, names_to_return

    def run_copasi_and_load(self, test_no, overwrite=False):
        if self.copasi_path is None:
            print("Copasi path is not set!")
            return None, None
        # we presumably have copasi, get sim params and sbml path
        t_end, n_steps = self.database.get_sim_param(test_no)
        path = os.path.abspath(self.database.get_path(test_no))
        print("Running copasi on {}".format(path))
        # First we need to get the cps file, go into copasi folder
        os.chdir(self.base_dir)
        if not os.path.isdir("copasi"):
            os.mkdir("copasi")
        os.chdir("copasi")
        cps_file = "{:05d}.cps".format(test_no)
        if (not os.path.isfile("{:05d}_tc.dat".format(test_no))) or overwrite:
            cmds = [self.copasi_path,
                    "-i", path,
                    "-s", cps_file]
            ret = sb.run(cmds, capture_output=True)
            if ret.returncode != 0:
                log_str = f"STDO: {ret.stdout} -- STDE: {ret.stderr}"
                self.database.set_result_copasi_log(test_no, log_str)
                return None, None
            # Now we need to load it in and edit timeCourse
            # task to enable it and change the output file
            # Note: can't use XML parsing to output but we
            # can for parsing some information we need,
            # the output is wrong if written by XML parsers

            # We need to extract some information first
            # let's use an XML parser to get the info
            print("copasi worked, let's start analyzing the cps")
            # We need these
            compartment_name_map = {}
            compartment_map = {}
            metabolites = []
            model_name = None
            t = ET.parse(cps_file)
            r = t.getroot()
            for i in r.iter():
                key = i.get("key")
                if key is not None:
                    if "Metabolite" in key:
                        metabolites.append(i.get("name"))
                        compartment_map[i.get("name")] = i.get("compartment")
                    if "Model" in key and "ModelValue" not in key and model_name is None:
                        model_name = i.get("name")
                        model_name = model_name.replace(",","\,")
                    if "Compartment" in key:
                        # For some dumbass reson we need the key to map to
                        # metabolites refer to the key but then report
                        # asks for name
                        compartment_name_map[i.get('key')] = i.get("name")
            # Some text we'll need for this
            # report line to associate time course with a report
            report_association_line = '<Report reference="Report_100" target="{:05d}_tc.dat" append="0" confirmOverwrite="1"/>\n'.format(test_no)
            # lines to generate the actual key
            report_lines = '<Report key="Report_100" name="tc" taskType="timeCourse" separator="&#x09;" precision="6">\n'
            report_lines += '<Table printTitle="1">\n'
            report_lines += '<Object cn="CN=Root,Model={},Reference=Time"/>\n'.format(model_name)

            for metabolite in metabolites:
                report_lines += '<Object cn="CN=Root,Model={},Vector=Compartments[{}],Vector=Metabolites[{}],Reference=Concentration"/>\n'.format(model_name, compartment_name_map[compartment_map[metabolite]], metabolite)
            report_lines += '</Table>\n'
            report_lines += '</Report>\n'

            print("opening file")
            # Now we have the info and know what we need to add
            # we can write the file by hand
            with open("{:05d}.cps".format(test_no),"r") as f:
                lines = f.readlines()
            updated_lines = []
            print("looping over lines to adjust manually")
            step_size = float(t_end)/(n_steps)
            for iline, line in enumerate(lines):
                # timeCourse only appears in one line, so we can do this
                if "timeCourse" in line:
                    line = line.replace('scheduled="false"','scheduled="true"')
                    updated_lines.append(line)
                    updated_lines.append(report_association_line)
                    continue
                # Same for list of reports
                elif "<ListOfReports>" in line:
                    # print("list of reports")
                    updated_lines.append(line)
                    updated_lines.append(report_lines)
                    # print(updated_lines[-10:])
                    continue
                elif "StepNumber" in line:
                    line = line.replace('value="100"','value="{}"'.format(n_steps))
                    updated_lines.append(line)
                    continue
                elif "StepSize" in line:
                    line = line.replace('value="0.01"','value="{}"'.format(step_size))
                    updated_lines.append(line)
                    continue
                updated_lines.append(line)
                # we also need to define the output file
            # Now write back
            with open(cps_file,"w") as f:
                f.writelines(updated_lines)
            # Now that we have the cps file correct, we run it
            print("Running Copasi")
            cmds = [self.copasi_path, cps_file]
            ret = sb.run(cmds, capture_output=True)
            # save copasi log here
            o = ret.stdout.decode("utf-8")
            e = ret.stderr.decode("utf-8")
            log_str = f"STDO: {o} -- STDE: {e}"
            self.database.set_result_copasi_log(test_no, log_str)
            # done saving copasi log
            if ret.returncode != 0:
                return None,None
        # And this gives us the result from copasi
        # let's load and return
        result, names = self.copasi_load("{:05d}_tc.dat".format(test_no))
        try:
            result = result.set_index("time")
        except:
            pass
        try:
            result = result.set_index("Time")
        except:
            pass
        os.chdir(self.base_dir)
        return result, names

    def run_librr_and_load(self, test_no):
        try:
            import roadrunner as rr
        except ImportError as e:
            print("libroadrunner is not installed run `pip install libroadrunner`")
            print(e)
            return None
        sbml = self.database.get_sbml(test_no)
        t_end, n_steps = self.database.get_sim_param(test_no)
        # Note, can get the model directly from BioModels if we want
        sim = rr.RoadRunner(sbml)
        result = sim.simulate(0, t_end, n_steps)
        names = result.colnames
        lpd = pd.DataFrame(result)
        try:
            lpd = lpd.set_index("time")
        except:
            pass
        try:
            lpd = lpd.set_index("Time")
        except:
            pass
        return lpd, list(lpd.columns)
    
    def run_and_load_bngl_res(self, test_no, atomize=True):
        print(f"## Running bngl, atomization status: {atomize}")
        if atomize:
            bng_path = os.path.abspath(f"atomized/bmd{test_no:010}_atomized.bngl")
        else:
            bng_path = os.path.abspath(f"flat/bmd{test_no:010}_flat.bngl")
        t_end, n_steps = self.database.get_sim_param(test_no)
        with open(bng_path, "r") as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.find("end model") >= 0:
                break
        sim_str = '\nsimulate({'
        sim_str += f'method=>"ode",t_end=>{t_end},n_steps=>{n_steps},print_functions=>1,atol=>1e-12,rtol=>1e-6'
        sim_str += '})'
        new_lines.append(sim_str)
        with open(bng_path, "w") as f:
            f.writelines(new_lines)
        ## 
        r = bionetgen.run(bng_path, timeout=120)
        log_str = f"STDO: {r.output.stdout} -- STDE: {r.output.stderr}"
        if atomize:
            self.database.set_result_bng_atom_log(test_no, log_str)
        else:
            self.database.set_result_bng_flat_log(test_no, log_str)
        ## 
        rpd = pd.DataFrame(r[0])
        try:
            rpd = rpd.set_index("time")
        except:
            pass
        try:
            rpd = rpd.set_index("Time")
        except:
            pass
        return rpd,list(rpd.columns)

    def get_curation_keys(self, test_no):
        # We also want to get relevant keys using modeller
        # defined species. Include this in results for plotting
        # UNCOMMENT FOR CURATION KEYS
        try:
            URL = "https://www.ebi.ac.uk/biomodels/BIOMD{:010d}#Components".format(test_no)
            # without these headers we get HTMLError 415, unsupported media type
            headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
            # Get the website
            r = requests.get(URL, headers=headers)
            # Load it into beautiful soup (HTML parser) so we can pull images out
            parsed = BS(r.content, 'lxml')
        except:
            pass
        # Now find curation section_ends = self.t_endsn
        cur_keys = None
        # UNCOMMENT FOR CURATION KEYS
        try:
            if(parsed):
                rtable = None
                tables = parsed.findAll(lambda tag: tag.name=='table')
                for table in tables:
                    ths = table.findAll(lambda tag: tag.name=="th")
                    for th in ths:
                        if th.contents[0].strip() == "Species":
                            rtable = table
                    if rtable:
                        break
                if rtable:
                    rows = rtable.findAll("span",{"class":"legend-green"})
                    cur_keys = [row.contents[0] for row in rows]
        except:
            pass
        return cur_keys

    def get_ratio(self, s1, s2):
        return SequenceMatcher(None, s1, s2).ratio()

    def get_keys(self, std_names, bng_names, cur_keys=None):
        # TODO: Use cur_keys if given, I'm just going to skip it
        # for now at least because I know it doesn't work well
        skeys_used = []
        bkeys_used = []
        skeys = std_names
        bkeys = bng_names
        slen = len(skeys)
        blen = len(bkeys)
        # to determine this properly we need to
        # check the similarty for every key to
        # every other key
        ratio_matrix = np.zeros((slen,blen))
        for i in range(slen):
            for j in range(blen):
                bkey_transform = bkeys[j].replace("__","")
                ratio_matrix[i][j] = self.get_ratio(skeys[i],bkey_transform)
        # we need the max in a column to also be the max in a row
        # we pull each one that's like that and leave the rest?
        # we will also ignore matches that are < 0.5
        ratio_matrix[ratio_matrix<0.5] = 0.0
        key_pairs = []
        for i in range(slen):
            stob = ratio_matrix[i,:].max()
            bkey_ind = np.where(ratio_matrix[i,:] == stob)[0][0]
            btos = ratio_matrix[:,bkey_ind].max()
            if stob == btos and stob != 0:
                skey_ind = np.where(ratio_matrix[:,bkey_ind] == btos)[0][0]
                skey = skeys[skey_ind]
                bkey = bkeys[bkey_ind]
                if skey not in skeys_used:
                    if bkey not in bkeys_used:
                        key_pairs.append((skey,bkey))
                        skeys_used.append(skey)
                        bkeys_used.append(bkey)
        return key_pairs

    def calc_rmsd(self, arr1, arr2):
        return np.sqrt( ( (arr2-arr1)**2).mean() )

    def calculate_validation(self, test_no, standard_tpl, bngl_tpl, use_cur_keys=False, plot=True, atomize=True):
        std_dat, std_names = standard_tpl
        bng_dat, bng_names = bngl_tpl
        # try to get the species from website (optional)
        if use_cur_keys:
            cur_keys = self.get_curation_keys(test_no)
        else:
            cur_keys = None
        # get key pairs we will be using
        key_pairs = self.get_keys(std_names, bng_names, cur_keys)
        keys_used = []
        validates = []
        fails = []
        rmsds = {}
        for key_pair in key_pairs:
            skey, bkey = key_pair
            # Get guaranteed single dataset for sample
            if len(std_dat[skey].values.shape) > 1:
                if std_dat[skey].values.shape[1] > 1:
                    print("we have one too many datasets for the same key")
                    sdata = std_dat[skey].iloc[:,0]
                else:
                    sdata = std_dat[skey].values
            else:
                sdata = std_dat[skey].values
            # And for BNGL result
            if len(bng_dat[bkey].values.shape) > 1:
                if bng_dat[bkey].values.shape[1] > 1:
                    print("we have one too many datasets for the same key")
                    bdata = bng_dat[bkey].iloc[:,0]
                else:
                    bdata = bng_dat[bkey].values
            else:
                bdata = bng_dat[bkey].values
            if len(sdata) == 0:
                continue
            if len(bdata) == 0:
                continue
            print("we used BNG key {} and SBML key {}".format(bkey, skey))
            # we can finally actually calculate RMSD
            validation_per = 0
            # Calculate RMSD
            rmsds[bkey] = self.calc_rmsd(sdata, bdata)
            norm_tolerance = 1e-1
            if abs(sdata.max()) != 0:
                norm_tolerance = norm_tolerance * sdata.max()
            if rmsds[bkey] < (norm_tolerance) or rmsds[bkey] < 1e-10:
                validates.append(bkey)
                validation_per += 1
            else:
                fails.append(bkey)
                print("{} won't validate".format(skey))
            keys_used.append((skey,bkey))
        total = float(len(validates) + len(fails))
        if total > 0:
            validation_per = len(validates)/total
        else:
            validation_per = None
        print("Keys used: {}".format(keys_used))
        validating_str = ", ".join(validates)
        failing_str = ", ".join(fails)
        print(f"Validating series: {validating_str}")
        print(f"Failing series: {failing_str}")
        # TODO: we need a flat and atomized versions of these
        self.database.set_result_validating_series(test_no, validating_str)
        self.database.set_result_failing_series(test_no, failing_str)
        print("val per {}".format(validation_per))
        self.plot_results(test_no, std_dat, bng_dat, keys=keys_used, rmsds=rmsds, atomize=atomize)
        return validation_per

    def plot_results(self, test_no, sdat, bdat, keys=None, rmsds=None, legend=True, save_fig=True, xlim=None, ylim=None, atomize=True):
        # plot both
        sd, bd, keys = sdat, bdat, keys
        fig, ax = plt.subplots(1,2)
        fig.tight_layout()

        for ik, ks in enumerate(keys):
            skey, bkey = ks
            if rmsds is not None:
                label = "{0:.10}: {1:.3E}".format(bkey,rmsds[bkey])
            else:
                label = f"{bkey}"
            ax[0].plot(sd.index, sd[skey], label=label)
            ax[1].plot(bd.index, bd[bkey], label=label)
        if legend:
            plt.legend(frameon=False)
        if xlim is not None:
            ax[0].set_xlim(xlim)
            ax[1].set_xlim(xlim)
        if ylim is not None:
            ax[0].set_ylim(ylim)
            ax[1].set_ylim(ylim)
        if save_fig:            
            if atomize:
                if not os.path.isdir("plots_atom"):
                    os.mkdir("plots_atom")
                plt.savefig(os.path.join("plots_atom", "{:05d}_results.png".format(test_no)), dpi=300)
            else:
                if not os.path.isdir("plots_flat"):
                    os.mkdir("plots_flat")
                plt.savefig(os.path.join("plots_flat", "{:05d}_results.png".format(test_no)), dpi=300)
            plt.close()


if __name__ == "__main__":
    # Initialize database, connect if exists
    a = AtomizerDatabase()

    # Create tables
    # TODO: Need to create tables if need be

    # Get models, if we don't have them
    # a.get_models() # only run when you don't have models setup already, takes a while

    # Initialize analyzer tool
    aa = AtomizerAnalyzer(a, copasi_path="/home/monoid/apps/copasi/4.27/bin/CopasiSE")
    # models_to_check = [
    #     394,398,396,223,262,399,250,452,453,251,
    #     263,264,594,595,562,826,427,827,477,656,
    #     648,653,655,654,652
    # ]
    # for i in sorted(models_to_check):
    #     print(f"\n\n### PRINTING INFORMATION ON MODEL {i:05} ###\n")
    #     # print(f"## TRANSLATION LOG ##\n")
    #     # print(aa.database.get_trans_atom_log(i))
    #     # print("\n\n")
    #     # print(f"## COPASI LOG ##\n")
    #     # print(aa.database.get_result_copasi_log(i))
    #     # print("\n\n")
    #     # print(f"## BNGL LOG ##\n")
    #     # print(aa.database.get_result_bng_log(i))
    #     # print("\n\n")
    #     print(f"## VALIDATION ##\n")
    #     print("# Validating series: ", aa.database.get_result_validating_series(i))
    #     print("# Failing series: ", aa.database.get_result_failing_series(i))
    #     print(f"# Validation ratio: {aa.database.get_result_atomized_valratio(i)}")
    # sys.exit()
    import IPython;IPython.embed();sys.exit()
    
    # ATOMIZED TRANSLATION
    # these are atomized translation problems
    known_translation_issues = [599, # key error "C4Beii"
        480, # key error "TotalDC"
        749, # key error "0"
        607,610,983, # Index error, 'list index out of range'
        649,694,992,993, # TypeError('expected str, bytes or os.PathLike object, not NoneType')
        766,789, # re.error('missing ), unterminated subpattern at position 6')
        833 # Expected W:(-ABC...), found '_'  (at char 30), (line:1, col:31)
    ]
    too_long = [470,471,472,473,474,496,497,503,506,574,863] # too long? re-run later
    too_much_memory = [542,554,703]
    doesnt_translate = [70,183,247,255,426]
    too_much = too_long + too_much_memory + doesnt_translate

    # FLAT TRANSLATION
    # if we have problems in flat translations add here
    # fails: 480, 607, 610, 649, 691, 694, 766, 789, 811,
    # 983, 992, 993
    # import IPython;IPython.embed();sys.exit()
    # MAIN TRANSLATION LOOP
    atomize = True
    overwrite = True
    for i in range(1,aa.database.current_max_models+1):
        if not aa.database.check_model(i):
            aa.database.insert_model(i)
        # if i > 1:
        #     break
        # if i <= 473:
        #     continue
        # if i != 48:
        #     continue
        # ensure we have the model
        if not (aa.database.check_model(i, TABLE="TRANSLATION")):
            print(f"model {i} not found in translation table, adding model")
            try:
                aa.database.insert_model(i, TABLE="TRANSLATION")
                print(f"model {i} added to translation table")
            except Exception as e:
                print(e)
                if atomize:
                    aa.database.set_trans_atom_status(i, aa.database.TRANSLATION_MAJOR_ERROR)
                else:
                    aa.database.set_trans_flat_status(i, aa.database.TRANSLATION_MAJOR_ERROR)
                continue
        else:
            print(f"model {i} found in translation table")
        print(f"Working on translating model: {i}")

        if i in too_much:
            if atomize:
                aa.database.set_trans_atom_status(i, aa.database.TRANSLATION_MAJOR_ERROR)
            else:
                aa.database.set_trans_flat_status(i, aa.database.TRANSLATION_MAJOR_ERROR)
            continue
        # select the type of translation here
        translation = aa.translate(i, overwrite=overwrite, atomize=atomize)
        if translation is None:
            print(f"We failed translating model: {i}")
        # sys.exit()
        # import IPython;IPython.embed();sys.exit()

    # MAIN VALIDATION LOOP
    # atomize = False
    # overwrite = False
    # first get successfully translated models
    succ = aa.database.dbase_con.execute(
        "SELECT ID FROM TRANSLATION WHERE ATOM_STATUS = ?",
        (aa.database.TRANSLATION_SUCCESS,),
    )
    succ = succ.fetchall()
    succ = sorted([i[0] for i in succ])
    for i in succ:
        # if i > 1:
        #     break
        # if i not in [15, 541, 826, 827]:
            # continue
        print(f"Working on validating model: {i}")
        standard = None
        bngl_res = None
        ## RUNNING COPASI
        try:
            standard = aa.run_and_load_test_standard(i, sim="copasi", overwrite=overwrite)
            os.chdir(aa.base_dir)
            if atomize:
                aa.database.set_result_atom_status(i,aa.database.RESULT_SUCC_STANDARD)
            else:
                aa.database.set_result_flat_status(i,aa.database.RESULT_SUCC_STANDARD)
        except Exception as e:
            print(f"Failed running/loading standard for model {i}")
            print(e)
            if atomize:
                aa.database.set_result_atom_status(i,aa.database.RESULT_FAIL_STANDARD)
            else:
                aa.database.set_result_flat_status(i,aa.database.RESULT_FAIL_STANDARD)
            continue
        
        ## RUNNING BIONETGEN
        try:
            bngl_res = aa.run_and_load_bngl_res(i, atomize=atomize)
            os.chdir(aa.base_dir)
            if atomize:
                aa.database.set_result_atom_status(i,aa.database.RESULT_SUCC_BNGL)
            else:
                aa.database.set_result_flat_status(i,aa.database.RESULT_SUCC_BNGL)
        except Exception as e:
            if atomize:
                aa.database.set_result_atom_status(i,aa.database.RESULT_FAIL_BNGL)
            else:
                aa.database.set_result_flat_status(i,aa.database.RESULT_FAIL_BNGL)
            print(f"Failed running/loading bngl result for model {i}")
            print(e)
            continue
        ## CALCULATING VALIDATION AND PLOTTING
        try:
            val_rat = aa.calculate_validation(i, standard, bngl_res, plot=True, atomize=atomize)
            os.chdir(aa.base_dir)
            if atomize:
                aa.database.set_result_atomized_valratio(i, val_rat)
                aa.database.set_result_atom_status(i,aa.database.RESULT_SUCC_VALIDATION)
            else:
                aa.database.set_result_flat_valratio(i, val_rat)
                aa.database.set_result_flat_status(i,aa.database.RESULT_SUCC_VALIDATION)
        except Exception as e:
            if atomize:
                aa.database.set_result_atom_status(i,aa.database.RESULT_FAIL_VALIDATION)
            else:
                aa.database.set_result_flat_status(i,aa.database.RESULT_FAIL_VALIDATION)
            print(f"Failed running/loading bngl result for model {i}")
            print(e)

    # bng_fail_list = aa.database.dbase_con.execute("SELECT ID FROM RESULTS WHERE ATOM_STATUS = ?", (aa.database.RESULT_FAIL_BNGL,)).fetchall()
    # bng_fail_list = [i[0] for i in bng_fail_list]
    # cvode_errs = []
    # for i in bng_fail_list:
        # s = aa.database.get_result_bng_log(i)
        # if s is not None:
            # if s.find("CVODE") >= 0:
                # cvode_errs.append(i)
    # 
    # import IPython;IPython.embed();sys.exit()
     
    # # testing setup
    # atomize = True
    # bid = False
    # i = 6
    # # config
    # infile = aa.database.get_path(i)
    # outfile = "test.bngl"
    # opt = {
    #   "input": infile,
    #   "output": outfile,
    #   "atomize": atomize,
    #   "molecule_id": bid,
    # }
    # # manually translate
    # a = AtomizeTool(options_dict=opt)
    # translation = a.run()
    # # run validation
    # standard = aa.run_and_load_test_standard(i, sim="copasi", overwrite=False)
    # bngl_res = aa.run_and_load_bngl_res(i, atomize=atomize)
    # val_rat = aa.calculate_validation(i, standard, bngl_res, plot=True, atomize=atomize)