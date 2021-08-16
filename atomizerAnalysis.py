from sqlite3.dbapi2 import DatabaseError, OperationalError
import bionetgen, os, time, math, sys, requests, re, contextlib, io, importlib
import sqlite3 as sl
import urllib.request
import pandas as pd
import subprocess as sb
import xml.etree.ElementTree as ET
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

    def get_path(self, test_no):
        query = "SELECT PATH FROM MODELS WHERE id=?"
        q = self.dbase_con.execute(query, (test_no,))
        paths = q.fetchall()
        if len(paths) > 0:
            return paths[0][0]
            # return bytes.fromhex(paths[0][0]).decode("utf-8")
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
            return bytes.fromhex(srs[0][0]).decode("utf-8")
        else:
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
                    CUR_KEYS TEXT,
                    ATOM_VAL_RATIO REAL,
                    FLAT_VAL_RATIO REAL
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

    def get_sim_param(self, test_no):
        t_end = self.get_result_tend(test_no)
        n_steps = self.get_result_nsteps(test_no)
        if t_end is None:
            self.dbase_con.execute("INSERT INTO RESULTS (ID,T_END,N_STEPS) VALUES (?,1000,100)", (test_no,))
            self.dbase_con.commit()
            t_end = self.get_result_tend(test_no)
            n_steps = self.get_result_nsteps(test_no)
        return t_end, n_steps

    def get_models(self):
        try:
            self.dbase_con.execute(
                """
                CREATE TABLE MODELS (
                    ID INT PRIMARY KEY NOT NULL,
                    TSTAMP INT NOT NULL,
                    PATH TEXT NOT NULL,
                    SBML TEXT NOT NULL,
                    NAME TEXT,
                    BNGL_FLAT TEXT,
                    BNGL_ATOM TEXT,
                    BNGXML TEXT
                );
            """
            )
        except OperationalError as oe:
            print("Model table already exits")
            print(oe)
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
        # import ipdb;ipdb.set_trace()
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
        filename = f"bmd{test_no:010}_{ext}.bngl"
        outfile = os.path.join(outfold, filename)
        opt = {
            "input": infile,
            "output": outfile,
            "atomize": atomize,
            "molecule_id": bid,
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
            # import IPython;IPython.embed()
            # now we can update the database too
            if atomize:
                self.database.set_trans_struct_rat(test_no, struct_rat)
                self.database.set_trans_atom_log(test_no, stderr)
                self.database.set_bngl_atom(test_no, rarray.finalString)
                self.database.set_trans_atom_status(
                    test_no, self.database.TRANSLATION_SUCCESS
                )
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
        curr_dir = os.getcwd()
        if not os.path.isdir("copasi"):
            os.mkdir("copasi")
        os.chdir("copasi")
        cps_file = "{:05d}.cps".format(test_no)
        if not os.path.isfile(cps_file):
            cmds = [self.copasi_path,
                    "-i", path,
                    "-s", cps_file]
            ret = sb.run(cmds)
            if ret.returncode == 0:
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
            # import IPython;IPython.embed()
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
            ret = sb.run(cmds)
            if ret.returncode == 0:
                return None,None
        # And this gives us the result from copasi
        # let's load and return
        result, names = self.copasi_load("{:05d}_tc.dat".format(test_no))
        os.chdir(curr_dir)
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
        return result, names
    
    def run_and_load_bngl_res(self, test_no, atomize=True):
        if atomize:
            bng_path = os.path.abspath(f"atomized/bmd{test_no:010}_atomized.bngl")
        else:
            bng_path = os.path.abspath(f"flat/bmd{test_no:010}_flat.bngl")
        t_end, n_steps = self.database.get_sim_param(test_no)
        with open(bng_path, "a") as f:
            sim_str = '\nsimulate({'
            sim_str += f'method=>"ode",t_end=>{t_end},n_steps=>{n_steps}'
            sim_str += '})'
            f.write(sim_str)
        r = bionetgen.run(bng_path)
        return r[0],list(r[0].dtype.names)

    def calculate_validation(self, standard_tpl, bngl_tpl):
        return 0.0


if __name__ == "__main__":
    # Initialize database, connect if exists
    a = AtomizerDatabase()

    # Create tables
    # TODO: Need to create tables if need be

    # Get models, if we don't have them
    # a.get_models() # only run when you don't have models setup already, takes a while

    # Initialize analyzer tool
    aa = AtomizerAnalyzer(a, copasi_path="/home/monoid/apps/copasi/4.27/bin/CopasiSE")

    ## ATOMIZED TRANSLATION
    # these are atomized translation problems
    # known_translation_issues = [599, # key error "C4Beii"
    #     480, # key error "TotalDC"
    #     749, # key error "0"
    #     607,610,983, # Index error, 'list index out of range'
    #     649,694,992,993, # TypeError('expected str, bytes or os.PathLike object, not NoneType')
    #     766,789, # re.error('missing ), unterminated subpattern at position 6')
    #     833 # Expected W:(-ABC...), found '_'  (at char 30), (line:1, col:31)
    # ]
    # too_long = [473,474,496,497,503,506,574,863] # too long? re-run later
    # too_much_memory = [542,554,703]
    # doesnt_translate = [70,183,247,255,426]
    # too_much = too_long + too_much_memory + doesnt_translate

    ## FLAT TRANSLATION
    # if we have problems in flat translations add here
    # fails: 480, 607, 610, 649, 691, 694, 766, 789, 811,
    # 983, 992, 993

    # MAIN TRANSLATION LOOP
    atomize = True
    # for i in range(1,aa.database.current_max_models+1):
    #     # if i < 480:
    #     #     continue
    #     # ensure we have the model
    #     if not (aa.database.check_model(i, TABLE="TRANSLATION")):
    #         print(f"model {i} not found in translation table, adding model")
    #         try:
    #             aa.database.insert_model(i, TABLE="TRANSLATION")
    #             print(f"model {i} added to translation table")
    #         except Exception as e:
    #             print(e)
    #             import IPython;IPython.embed()
    #             sys.exit()
    #     else:
    #         print(f"model {i} found in translation table")
    #     print(f"Working on translating model: {i}")

    #     if i in too_much:
    #         if atomize:
    #             aa.database.set_trans_atom_status(i, aa.database.TRANSLATION_MAJOR_ERROR)
    #         else:
    #             aa.database.set_trans_flat_status(i, aa.database.TRANSLATION_MAJOR_ERROR)
    #         continue
    #     # select the type of translation here
    #     translation = aa.translate(i, overwrite=True, atomize=atomize)
    #     # import IPython;IPython.embed()
    #     if translation is None:
    #         print(f"We failed translating model: {i}")
    #         # import IPython;IPython.embed()

    # import IPython;IPython.embed()
    # sys.exit()

    ## MAIN VALIDATION LOOP
    # first get successfully translated models
    succ = aa.database.dbase_con.execute(
        "SELECT ID FROM TRANSLATION WHERE ATOM_STATUS = ?",
        (aa.database.TRANSLATION_SUCCESS,),
    )
    succ = succ.fetchall()
    succ = [i[0] for i in succ]
    for i in succ:
        print(f"Working on validating model: {i}")
        #
        standard = None
        bngl_res = None
        try:
            standard = aa.run_and_load_test_standard(i, sim="copasi", overwrite=False)
            aa.database.set_result_atom_status(i,aa.database.RESULT_SUCC_STANDARD)
            aa.database.set_result_flat_status(i,aa.database.RESULT_SUCC_STANDARD)
        except Exception as e:
            print(f"Failed running/loading standard for model {i}")
            print(e)
            aa.database.set_result_atom_status(i,aa.database.RESULT_FAIL_STANDARD)
            aa.database.set_result_flat_status(i,aa.database.RESULT_FAIL_STANDARD)
            continue

        try:
            bngl_res = aa.run_and_load_bngl_res(i, atomize=atomize)
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

        try:
            val_rat = aa.calculate_validation(standard, bngl_res)
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


#     def get_ratio(self, s1, s2):
#         return SequenceMatcher(None, s1, s2).ratio()

#     def run_single_test(self, test_no, t_end=1000, n_steps=200, bid=False, tolerance=1e-1, atol="1E-10", rtol="1E-10", atomize=True, meta=None, manual_bngl=None):
#         '''
#         Convenience function to run a single test
#         '''
#         print("Running test {:05d}".format(test_no))
#         # First let's get the RR results
#         try:
#             self.sample_data, names = self.run_test_data(test_no, t_end=t_end, n_steps=n_steps)
#         except:
#             if meta:
#                 meta[test_no]["copasi_run"] = False
#             return False
#         if meta:
#             meta[test_no]["copasi_run"] = True
#         self.sample_data = pd.DataFrame(self.sample_data, columns=names)
#         # If we have "time" as a dataset, use it as an index
#         print("Got test results")
#         try:
#             self.sample_data = self.sample_data.set_index("time")
#         except:
#             pass
#         try:
#             self.sample_data = self.sample_data.set_index("Time")
#         except:
#             pass
#         # Run translation
#         # TODO: Check if translation is succesful and stop if not
#         if manual_bngl is None:
#             if not self.run_translation(test_no, bid=bid, atomize=atomize):
#                 if meta:
#                     meta[test_no]["translate"] = False
#                 return False
#             else:
#                 if meta:
#                     meta[test_no]["translate"] = True
#             # Add simulate command
#             with open("{:05d}.bngl".format(test_no),'a') as f:
#                 f.write("\n")
#                 f.write("generate_network({overwrite=>1})")
#                 f.write("\n")
#                 opts = 'method=>"ode",print_functions=>1,t_end=>%f,n_steps=>%i'%(t_end,n_steps)# -1)
#                 if atol:
#                     opts += ",atol=>%s"%(atol)
#                 if rtol:
#                     opts += ",rtol=>%s"%(rtol)
#                 f.write('simulate({%s})'%(opts))
#         # Now simulate the thing
#         if not self.run_and_load_simulation(test_no):
#             if meta:
#                 meta[test_no]["runnable"] = False
#             return False
#         else:
#             if meta:
#                 meta[test_no]["runnable"] = True
#         #if test_no not in self.all_results.keys():

#         # We also want to get relevant keys using modeller
#         # defined species. Include this in results for plotting
#         # UNCOMMENT FOR CURATION KEYS
#         # try:
#         #     URL = "https://www.ebi.ac.uk/biomodels/BIOMD{:010d}#Components".format(test_no)
#         #     # without these headers we get HTMLError 415, unsupported media type
#         #     headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
#         #     # Get the website
#         #     r = requests.get(URL, headers=headers)
#         #     # Load it into beautiful soup (HTML parser) so we can pull images out
#         #     parsed = BS(r.content, 'lxml')
#         # except:
#         #     pass
#         # # Now find curation sectiot_ends = self.t_endsn
#         # cur_keys = None
#         # # UNCOMMENT FOR CURATION KEYS
#         # try:
#         #     if(parsed):
#         #         if meta:
#         #             meta[test_no]["curation_keys"] = True
#         #         rtable = None
#         #         tables = parsed.findAll(lambda tag: tag.name=='table')
#         #         for table in tables:
#         #             ths = table.findAll(lambda tag: tag.name=="th")
#         #             for th in ths:
#         #                 if th.contents[0].strip() == "Species":
#         #                     rtable = table
#         #             if rtable:
#         #                 break
#         #         if rtable:
#         #             rows = rtable.findAll("span",{"class":"legend-green"})
#         #             cur_keys = [row.contents[0] for row in rows]
#         #     else:
#         #         if meta:
#         #             meta[test_no]["curation_keys"] = False
#         #     # We want to only match the cur_keys and discard the
#         #     # rest for validation purposes
#         #     print("curation keys: {}".format(cur_keys))
#         # except:
#         #     cur_keys = list(self.sample_data.keys())
#         rmsd = {}
#         validation_per = 0

#         skeys_used = []
#         bkeys_used = []
#         skeys = list(self.sample_data.keys())
#         bkeys = list(self.bngl_data.keys())
#         slen = len(skeys)
#         blen = len(bkeys)
#         # to determine this properly we need to
#         # check the similarty for every key to
#         # every other key
#         ratio_matrix = np.zeros((slen,blen))
#         for i in range(slen):
#             for j in range(blen):
#                 bkey_transform = bkeys[j].replace("__","")
#                 ratio_matrix[i][j] = self.get_ratio(skeys[i],bkey_transform)

#         # we need the max in a column to also be the max in a row
#         # we pull each one that's like that and leave the rest?
#         # we will also ignore matches that are < 0.5
#         ratio_matrix[ratio_matrix<0.5] = 0.0
#         key_pairs = []
#         for i in range(slen):
#             stob = ratio_matrix[i,:].max()
#             bkey_ind = np.where(ratio_matrix[i,:] == stob)[0][0]
#             btos = ratio_matrix[:,bkey_ind].max()
#             if stob == btos and stob != 0:
#                 skey_ind = np.where(ratio_matrix[:,bkey_ind] == btos)[0][0]
#                 skey = skeys[skey_ind]
#                 bkey = bkeys[bkey_ind]
#                 if skey not in skeys_used:
#                     if bkey not in bkeys_used:
#                         key_pairs.append((skey,bkey))
#                         skeys_used.append(skey)
#                         bkeys_used.append(bkey)

#         keys_used = []
#         for key_pair in key_pairs:
#             skey, bkey = key_pair
#             # Get guaranteed single dataset for sample
#             if len(self.sample_data[skey].values.shape) > 1:
#                 if self.sample_data[skey].values.shape[1] > 1:
#                     print("we have one too many datasets for the same key")
#                     sdata = self.sample_data[skey].iloc[:,0]
#                 else:
#                     sdata = self.sample_data[skey].values
#             else:
#                 sdata = self.sample_data[skey].values
#             # And for BNGL result
#             if len(self.bngl_data[bkey].values.shape) > 1:
#                 if self.bngl_data[bkey].values.shape[1] > 1:
#                     print("we have one too many datasets for the same key")
#                     bdata = self.bngl_data[bkey].iloc[:,0]
#                 else:
#                     bdata = self.bngl_data[bkey].values
#             else:
#                 bdata = self.bngl_data[bkey].values
#             if len(sdata) == 0:
#                 continue
#             if len(bdata) == 0:
#                 continue
#             print("we used BNG key {} and SBML key {}".format(bkey, skey))
#             # Calculate RMSD
#             rmsd[bkey] = calc_rmsd(sdata, bdata)

#             norm_tolerance = 1e-1
#             if abs(sdata.max()) != 0:
#                 norm_tolerance = norm_tolerance * sdata.max()
#             # norm_tolerance = max(sdata) * tolerance
#             if rmsd[bkey] < (norm_tolerance) or rmsd[bkey] < 1e-10:
#                 validation_per += 1
#             else:
#                 print("{} won't validate".format(skey))
#             skeys_used.append(skey)
#             bkeys_used.append(bkey)
#             keys_used.append((skey,bkey))

#         # if cur_keys:
#         #     validation_div = len(cur_keys)
#         #     # get subset from interwebs
#         #     # by the end we need an RMSD value and if it validates
#         #     # or not
#         #     keys_used = []
#         #     bkeys_used = []
#         #     skeys_used = []
#         #     # import ipdb;ipdb.set_trace()
#         #     for ck in cur_keys:
#         #         # Sometimes there are more curation keys
#         #         # than datasets in Copasi results
#         #         if len(self.sample_data.keys()) == len(skeys_used):
#         #             break
#         #         # Get keys
#         #         ck_sk_ratios = sorted(list(map(lambda y: (y, self.get_ratio(ck, y)), [i for i in self.sample_data.keys() if i not in skeys_used])), key=lambda z: z[1])
#         #         skey = ck_sk_ratios[-1][0]
#         #         # now we need to determine if we should rely on CK to determine
#         #         # the bkey to select
#         #         ck_bk_ratios = sorted(list(map(lambda y: (y, self.get_ratio(ck, y)), [i for i in self.bngl_data.keys() if i not in bkeys_used])), key=lambda z: z[1])
#         #         sk_bk_ratios = sorted(list(map(lambda y: (y, self.get_ratio(skey, y)), [i for i in self.bngl_data.keys() if i not in bkeys_used])), key=lambda z: z[1])
#         #         # decide on the key to use
#         #         # TODO: We might also need to check what happens when
#         #         # we remove the last value after an "_" because that's
#         #         # frequently the compartment which can lead to mismatches
#         #         if ck_bk_ratios[-1][1] > sk_bk_ratios[-1][1]:
#         #             bkey = ck_bk_ratios[-1][0]
#         #         else:
#         #             bkey = sk_bk_ratios[-1][0]
#         #         # Get guaranteed single dataset for sample
#         #         if len(self.sample_data[skey].values.shape) > 1:
#         #             if self.sample_data[skey].values.shape[1] > 1:
#         #                 print("we have one too many datasets for the same key")
#         #                 sdata = self.sample_data[skey].iloc[:,0]
#         #             else:
#         #                 sdata = self.sample_data[skey].values
#         #         else:
#         #             sdata = self.sample_data[skey].values
#         #         # And for BNGL result
#         #         if len(self.bngl_data[bkey].values.shape) > 1:
#         #             if self.bngl_data[bkey].values.shape[1] > 1:
#         #                 print("we have one too many datasets for the same key")
#         #                 bdata = self.bngl_data[bkey].iloc[:,0]
#         #             else:
#         #                 bdata = self.bngl_data[bkey].values
#         #         else:
#         #             bdata = self.bngl_data[bkey].values
#         #         if len(sdata) == 0:
#         #             continue
#         #         if len(bdata) == 0:
#         #             continue
#         #         print("for key {} we used BNG key {} and SBML key {}".format(ck, bkey, skey))
#         #         # Calculate RMSD
#         #         # Let's get normalization factors
#         #         # sdata_norm = sdata[int(sdata.shape[0]/2):]
#         #         # sdata_norm = sdata.max()
#         #         # # bdata_norm = bdata[int(bdata.shape[0]/2):]
#         #         # bdata_norm = bdata.max()
#         #         # sdat_rmsd = sdata/sdata_norm if sdata_norm != 0 else sdata
#         #         # bdat_rmsd = bdata/bdata_norm if bdata_norm != 0 else bdata
#         #         rmsd[ck] = calc_rmsd(sdata, bdata)

#         #         norm_tolerance = 1e-1
#         #         if abs(sdata.max()) != 0:
#         #             norm_tolerance = norm_tolerance * sdata.max()
#         #         # IPython.embed()
#         #         # norm_tolerance = max(sdata) * tolerance
#         #         if rmsd[ck] < (norm_tolerance) or rmsd[ck] < 1e-10:
#         #             validation_per += 1
#         #         else:
#         #             print("{} won't match".format(skey))
#         #         skeys_used.append(skey)
#         #         bkeys_used.append(bkey)
#         #         keys_used.append((skey,bkey,ck))
#         # else:
#         #     # do the normal spiel
#         #     skeys = set(self.sample_data.keys())
#         #     bkeys = set(self.bngl_data.keys())
#         #     bkey_map = {}
#         #     for bkey in bkeys:
#         #         bkey_splt = bkey.split("_")
#         #         if len(bkey_splt) > 1:
#         #             nkey = "".join(bkey_splt[:-1])
#         #         else:
#         #             nkey = bkey
#         #         bkey_map[nkey] = bkey

#         #     keys_used = []
#         #     validation_div = len(skeys)
#         #     for skey in skeys:
#         #         ratios = sorted(list(map(lambda y: (y, self.get_ratio(skey, y)), bkey_map.keys())), key=lambda z: z[1])
#         #         key_to_use = bkey_map[ratios[-1][0]]
#         #         print("matched keys are sbml: {} and bngl: {}".format(skey, key_to_use))
#         #         keys_used.append((skey, key_to_use))
#         #         # Get guaranteed single dataset
#         #         if len(self.sample_data[skey].values.shape) > 1:
#         #             if self.sample_data[skey].values.shape[1] > 1:
#         #                 print("we have one too many datasets for the same key")
#         #                 sdata = self.sample_data[skey].iloc[:,0]
#         #             else:
#         #                 sdata = self.sample_data[skey].values
#         #         else:
#         #             sdata = self.sample_data[skey].values
#         #         if len(self.bngl_data[key_to_use].values.shape) > 1:
#         #             if self.bngl_data[key_to_use].values.shape[1] > 1:
#         #                 print("we have one too many datasets for the same key")
#         #                 bdata = self.bngl_data[key_to_use].iloc[:,0]
#         #             else:
#         #                 bdata = self.bngl_data[key_to_use].values
#         #         else:
#         #             bdata = self.bngl_data[key_to_use].values

#         #         # Let's get normalization factors
#         #         # sdata_norm = sdata[int(sdata.shape[0]/2):]
#         #         # sdata_norm = sdata.max()
#         #         # # bdata_norm = bdata[int(bdata.shape[0]/2):]
#         #         # bdata_norm = bdata.max()
#         #         # sdat_rmsd = sdata/sdata_norm if sdata_norm != 0 else sdata
#         #         # bdat_rmsd = bdata/bdata_norm if bdata_norm != 0 else bdata
#         #         #
#         #         rmsd[skey] = calc_rmsd(sdata, bdata)

#         #         norm_tolerance = 1e-1
#         #         if abs(sdata.max()) != 0:
#         #             norm_tolerance = norm_tolerance * sdata.max()

#         #         if rmsd[skey] < (norm_tolerance) or rmsd[skey] < 1e-10:
#         #             validation_per +=1
#         #         else:
#         #             print("{} won't match".format(skey))
#         validation_div = len(keys_used)
#         if validation_div > 0:
#             validation_per = validation_per/float(validation_div)
#         else:
#             validation_per = None
#         print("Keys used: {}".format(keys_used))
#         print("val per {}".format(validation_per))
#         self.all_results[test_no] = (self.sample_data, self.bngl_data, rmsd, validation_per, keys_used)
#         return True

#     def plot_results(self, test_no, legend=True, save_fig=False, xlim=None, ylim=None):
#         # Now do some comparison
#         if not self.all_results[test_no][0] is None:
#             # plot both
#             sd, bd, _, _, keys = self.all_results[test_no]
#             fig, ax = plt.subplots(1,2)
#             fig.tight_layout()

#             for ik, ks in enumerate(keys):
#                 skey, bkey = ks
#                 label = "{0:.10}: {1:.3E}".format(bkey,self.all_results[test_no][2][bkey])
#                 # if len(ks) == 2:
#                 #     skey, bkey = ks
#                 #     ck = None
#                 # else:
#                 #     skey, bkey, ck = ks
#                 # try:
#                 #     if ck:
#                 #         label = "{0:.10}: {1:.3E}".format(bkey,self.all_results[test_no][2][ck])
#                 #     else:
#                 #         label = "{0:.10}: {1:.3E}".format(bkey,self.all_results[test_no][2][skey])
#                 # except KeyError:
#                 #     label = "ind"
#                 ax[0].plot(sd.index, sd[skey], label=label)
#                 ax[1].plot(bd.index, bd[bkey], label=label)
#             #for ind in sd.keys():
#             #    ax[0].plot(sd.index, sd[ind], label=label)
#             if legend:
#                 plt.legend(frameon=False)
#             if xlim is not None:
#                 ax[0].set_xlim(xlim)
#                 ax[1].set_xlim(xlim)
#             if ylim is not None:
#                 ax[0].set_ylim(ylim)
#                 ax[1].set_ylim(ylim)
#             #for ind in bd.keys():
#             #    #ax[1].plot(bd.index, bd[ind], label="bngl {}".format(ind))
#             #    ax[1].plot(bd.index, bd[ind])
#         else:
#             for ind in self.bngl_data.keys():
#                 plt.plot(self.bngl_data.index, self.bngl_data[ind], label="bngl {}".format(ind))
#         if legend:
#             plt.legend(frameon=False)
#         if xlim is not None:
#             plt.xlim(xlim[0], xlim[1])
#         if ylim is not None:
#             plt.ylim(ylim[0], ylim[1])
#         if save_fig:
#             plt.savefig("{:05d}-bngl_results.png".format(test_no), dpi=300)
#             plt.close()