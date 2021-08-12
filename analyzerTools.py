# %matplotlib notebook
import os, re, sys, urllib, requests, base64, IPython, io
import numpy as np
import subprocess as sb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import roadrunner
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from bs4 import BeautifulSoup as BS
from IPython.display import Image, display
from matplotlib import rcParams

def read_gdat(file):
    f = open(file)
    # Get column names from first line of file
    line = f.readline()
    names = re.split('\s+',(re.sub('#','',line)).strip())
    gdat = pd.read_table(f,sep='\s+',header=None,names=names)
    # Set the time as index
    gdat = gdat.set_index("time")
    f.close
    return(gdat)

def calc_rmsd(sample, bngl):
    return np.sqrt( ((bngl-sample)**2).mean())
    
class AtomizerAnalyzer:
    def __init__(self, bng_path, sbml_translator_path, config_path, tests_path, 
                 translator_import=None, copasi_path=None):
        '''
        For now we'll assume that we can work in the folder we are in. So do a os.chdir into the 
        working folder first before calling the AtomizerAnalyzer
        '''
        self.translator = sbml_translator_path
        self.imported = False
        if not translator_import is None:
            sys.path.append(translator_import)
            try: 
                import libsbml2bngl as ls2b
                self.ls2b = ls2b
                self.imported = True
                print("Imported libsbml2bngl")
            except:
                print("Issues importing libsbml2bngl library")
        self.bng2 = bng_path
        self.config = config_path
        if not os.path.isdir("config"):
            try:
                os.symlink(config_path, "config")
            except FileExistsError:
                pass
        if tests_path[-1] != os.sep:
            tests_path += os.sep
        self.tests_path = tests_path
        # A way to collect all results
        self.all_results = {}
        self.copasi_path = copasi_path
    
    def setup_import_config(self, test_no, bid=False, atomize=True):
        options = {}
        options['inputFile'] = self.test_sbml_path(test_no)
        conv, useID, naming = self.ls2b.selectReactionDefinitions(options['inputFile'])
        options['outputFile'] = "{:05d}.bngl".format(test_no)
        options['conventionFile'] = conv
        options['userStructure'] = None
        options['namingConventions'] = naming
        options['useId'] = bid 
        options['annotation'] = False
        if atomize:
            options['atomize'] = True
        else:
            options['atomize'] = False
        options['pathwaycommons'] = None
        options['bionetgenAnalysis'] = self.bng2
        options['isomorphismCheck'] = False
        options['ignore'] = False
        options['noConversion'] = True
        return options
    
    def read_gdat(self, file):
        """Read tabular data from BNG gdat or cdat or similar file. Data needs to be 
           whitespace delimited and first line of file contains whitespace delimited
           column names.
        Args:
            file: Text file containing the data.
        Raises:
        Returns:
            gdat: DataFrame containing the data from the file with column names matching 
            the columns of the input file.
        """
        f =open(file)
        # Get column names from first line of file
        line = f.readline()
        names = re.split('\s+',(re.sub('#','',line)).strip())
        gdat = pd.read_table(f,sep='\s+',header=None,names=names)
        # Set the time as index
        gdat = gdat.set_index("time")
        f.close
        return(gdat)
    
    def test_sbml_path(self, test_no):
        return self.tests_path + "{:05d}/{:05d}-sbml-l2v4.xml".format(test_no, test_no)
    
    def test_data_path(self, test_no):
        return self.tests_path + "{:05d}/{:05d}-results.csv".format(test_no, test_no)
    
    def check_and_confirm_config(self):
        if not os.path.isdir("config"):
            os.symlink(self.config, "config")
    
    def translate(self, test_no, bid=False, atomize=True):
        if self.imported:
            # run using imported library
            # return true if suc, false otherwise
            print("Using imported SBML translator")
            options = self.setup_import_config(test_no, bid=bid, atomize=atomize)
            try:
                returnArray = self.ls2b.analyzeFile(options['inputFile'], options['conventionFile'], 
                                           options['useId'], options['namingConventions'],
                                           options['outputFile'], 
                                           speciesEquivalence=options['userStructure'],
                                           atomize=options['atomize'], 
                                           bioGrid=False, pathwaycommons=options['pathwaycommons'],
                                           ignore=options['ignore'], noConversion = options['noConversion'])
                if returnArray:
                    self.ls2b.postAnalyzeFile(options['outputFile'], self.bng2, returnArray.database)
                self.translate_result = returnArray
                return True
            except:
                print("Translation failed using imported translator, moving on")
                return False
        else:
            print("Running sbmlTranslator.py using subprocess")
            cmds = ["python", self.translator, "-i", self.test_sbml_path(test_no), "-o", "{:05d}.bngl".format(test_no)]
            if atomize:
                cmds.append("-a")
            if bid:
                cmds.append("-id")
            ret = sb.run(cmds)
            if ret.returncode != 0:
                return False
            return True
        
    def run_translation(self, test_no, bid=False, atomize=True):
        # run the sbmlTranslator.py on the xml file to get it atomized
        # at the moment I'm running with -a = atomize, -t = keep translation notes
        # and -nc = no unit conversion. I'm not entirely sure if that's the 
        # correct way to run it
        # TODO: Check the exact arguments we want for the translator
        # TODO: We can just import the transltor here and run the translation that way
        # in fact, we might be able to gain a lot more insight that way. Move on to importing
        # the translator
        self.check_and_confirm_config()
        os.system("rm {:05d}.*".format(test_no))
        if not self.translate(test_no, bid=bid, atomize=atomize):
            print("there was an issue with translation in test {:05d}".format(test_no))
            return False
        return True
    
    def load_test_data(self, test_no):
        '''
        This loads in the CSV that is in the test suite to compare our atomzied
        models with
        '''
        # load in the sample data provided in the test suite for comparison
        sample_data = pd.read_csv(self.test_data_path(test_no))
        self.sample_data = sample_data.set_index("time")
        # this is required to figure out the simulation length/steps
        self.n_steps = len(sample_data.index) - 1
        self.t_end = self.sample_data.index[self.n_steps]
        print("running until {} in {} steps".format(self.t_end, self.n_steps))
        return self.t_end, self.n_steps
    
    def run_and_load_simulation(self, test_no):
        '''
        Convenience function to run the BNG2.pl on our atomized model and return
        the loaded in gdat file
        '''
        # run our atomized model
        ret = sb.run([self.bng2, "{:05d}.bngl".format(test_no)])
        if ret.returncode != 0:
            print("there was an issue with simulation in test {:05d}".format(test_no))
            return False
        # Load gdat
        self.bngl_data = self.read_gdat("{:05d}.gdat".format(test_no))
        return True
    
    def run_single_test(self, test_no, bid=False, atomize=True):
        '''
        Convenience function to run a single test
        '''
        print("Running test {:05d}".format(test_no))
        # Run translation
        # TODO: Check if translation is succesful and stop if not
        if not self.run_translation(test_no, bid=bid, atomize=atomize):
            return False
        # Check the time points we need
        t_end, n_steps = self.load_test_data(test_no)
        # Add simulate command 
        with open("{:05d}.bngl".format(test_no),'a') as f:
            f.write("\n")
            f.write("generate_network({overwrite=>1})")
            f.write("\n")
            f.write('simulate({method=>"ode",t_end=>%f,n_steps=>%i})'%(t_end,n_steps))
        # Now simulate the thing
        if not self.run_and_load_simulation(test_no):
            return False
        #if test_no not in self.all_results.keys():
        self.all_results[test_no] = (self.sample_data,self.bngl_data)
        return True
    
    def plot_results(self, test_no, save_fig=False):

        # Now do some comparison
        try:
            for ind in self.sample_data.keys():
                plt.plot(self.sample_data.index, self.sample_data[ind], 
                         label="sbml {}".format(ind))
                # TODO: We need something better to identify the correct key for BNGL results
                bngl_key = [key for key in self.bngl_data.keys() if ind in key]
                if len(bngl_key) > 0:
                    bngl_key = bngl_key[0]
                else:
                    print("Can't find key {} in bngl data structure".format(ind))
                    continue
                plt.plot(self.bngl_data.index, self.bngl_data[bngl_key], label="bngl {}".format(bngl_key))
            plt.legend()
            if save_fig:
                plt.savefig("{:05d}-bngl_results.png".format(test_no), dpi=600)
                plt.close()
        except IndexError:
                print("Some error happened in ploting of {:05d}, moving on".format(test_no))

# for biomodel testing
class BiomodelAnalyzer(AtomizerAnalyzer):    
    def __init__(self,  bng_path, sbml_translator_path, 
                 config_path, tests_path, translator_import=None, copasi_path=None):
        super().__init__(bng_path, sbml_translator_path, 
                         config_path, tests_path, translator_import=translator_import, copasi_path=copasi_path)
        self.t_ends = {}
    
    def test_sbml_path(self, test_no):
        return self.tests_path + "BIOMD{:010d}.xml".format(test_no)
    
    def test_data_path(self, test_no):
        return None
    
    def run_test_data(self, test_no, t_end=1000, n_steps=200):
        if self.copasi_path is None:
            path = self.test_sbml_path(test_no)
            # Note, can get the model directly from BioModels if we want
            self.runner = roadrunner.RoadRunner(path)
            result = self.runner.simulate(0, t_end, n_steps)
            names = self.sample_data.colnames
        else:
            path = self.test_sbml_path(test_no)
            print("Running copasi on {}".format(path))
            # First we need to get the cps file
            cmds = [self.copasi_path, 
                    "-i", self.test_sbml_path(test_no), 
                    "-s", "{:05d}.cps".format(test_no)]
            ret = sb.run(cmds)
            assert ret.returncode == 0, "Copasi failed"
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
            t = ET.parse("{:05d}.cps".format(test_no))
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
            with open("{:05d}.cps".format(test_no),"w") as f:
                f.writelines(updated_lines)
            # Now that we have the cps file correct, we run it
            print("Running Copasi")
            cmds = [self.copasi_path, "{:05d}.cps".format(test_no)]
            ret = sb.run(cmds)
            # assert ret.returncode == 0, "Copasi failed"
            # And this gives us the result from copasi
            # let's load and return
            result, names = self.copasi_load("{:05d}_tc.dat".format(test_no))
        return result, names

    def copasi_load(self, fname):
        print("loading copasi results")
        with open(fname, "r") as f:
            # Get column names from first line of file
            #print("getting names")
            line =f.readline()
            #names = list(map(lambda x: x.replace("[","").replace("]",""), re.split('\s+',line.strip())))
            names = list(map(lambda x: x.replace("]","").strip(), line.split("[")))
            unique_names = []
            names_to_return = []
            ctr = 0 
            for name in names:
                if not name in unique_names:
                    unique_names.append(name)
                    names_to_return.append(name)
                else:
                    # unique_names.append(name+"_{}".format(ctr))
                    unique_names.append("TRASH_DUMP_THIS_{}".format(ctr))
                    ctr+=1
            # list(map(lambda x: x.replace("[","").replace("]",""), re.split('\s+',line.strip())))
            dtypes = list(zip(unique_names, ['f8' for i in unique_names]))
            # result = np.loadtxt(f) # , dtype=dtypes)
            # result = np.rec.array(result, dtype=dtypes)
            # print("loading table")
            result = pd.read_table(f,sep='\s+',header=None,names=list(unique_names))
        result = result[result.columns.drop(list(result.filter(regex="TRASH")))]
        print("returning copasi results")
        return result, names_to_return
        #return result, names
    
    def get_ratio(self, s1, s2):
        return SequenceMatcher(None, s1, s2).ratio()

    def run_single_test(self, test_no, t_end=1000, n_steps=200, bid=False, tolerance=1e-1, atol="1E-10", rtol="1E-10", atomize=True, meta=None, manual_bngl=None):
        '''
        Convenience function to run a single test
        '''
        print("Running test {:05d}".format(test_no))
        # First let's get the RR results
        try:
            self.sample_data, names = self.run_test_data(test_no, t_end=t_end, n_steps=n_steps)
        except:
            if meta:
                meta[test_no]["copasi_run"] = False
            return False
        if meta:
            meta[test_no]["copasi_run"] = True
        self.sample_data = pd.DataFrame(self.sample_data, columns=names)
        # If we have "time" as a dataset, use it as an index
        print("Got test results")
        try:
            self.sample_data = self.sample_data.set_index("time")
        except:
            pass
        try:
            self.sample_data = self.sample_data.set_index("Time")
        except:
            pass
        # Run translation
        # TODO: Check if translation is succesful and stop if not
        if manual_bngl is None:
            if not self.run_translation(test_no, bid=bid, atomize=atomize):
                if meta:
                    meta[test_no]["translate"] = False
                return False
            else:
                if meta:
                    meta[test_no]["translate"] = True
            # Add simulate command 
            with open("{:05d}.bngl".format(test_no),'a') as f:
                f.write("\n")
                f.write("generate_network({overwrite=>1})")
                f.write("\n") 
                opts = 'method=>"ode",print_functions=>1,t_end=>%f,n_steps=>%i'%(t_end,n_steps)# -1)
                if atol:
                    opts += ",atol=>%s"%(atol)
                if rtol:
                    opts += ",rtol=>%s"%(rtol)
                f.write('simulate({%s})'%(opts))
        # Now simulate the thing
        if not self.run_and_load_simulation(test_no):
            if meta:
                meta[test_no]["runnable"] = False
            return False
        else:
            if meta:
                meta[test_no]["runnable"] = True 
        #if test_no not in self.all_results.keys():

        # We also want to get relevant keys using modeller 
        # defined species. Include this in results for plotting
        # UNCOMMENT FOR CURATION KEYS
        # try:
        #     URL = "https://www.ebi.ac.uk/biomodels/BIOMD{:010d}#Components".format(test_no)
        #     # without these headers we get HTMLError 415, unsupported media type
        #     headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
        #     # Get the website
        #     r = requests.get(URL, headers=headers)
        #     # Load it into beautiful soup (HTML parser) so we can pull images out
        #     parsed = BS(r.content, 'lxml')
        # except:
        #     pass
        # # Now find curation sectiot_ends = self.t_endsn
        # cur_keys = None
        # # UNCOMMENT FOR CURATION KEYS
        # try:
        #     if(parsed):
        #         if meta:
        #             meta[test_no]["curation_keys"] = True 
        #         rtable = None
        #         tables = parsed.findAll(lambda tag: tag.name=='table')
        #         for table in tables:
        #             ths = table.findAll(lambda tag: tag.name=="th")
        #             for th in ths:
        #                 if th.contents[0].strip() == "Species":
        #                     rtable = table
        #             if rtable:
        #                 break
        #         if rtable:
        #             rows = rtable.findAll("span",{"class":"legend-green"})
        #             cur_keys = [row.contents[0] for row in rows]
        #     else:
        #         if meta:
        #             meta[test_no]["curation_keys"] = False
        #     # We want to only match the cur_keys and discard the 
        #     # rest for validation purposes 
        #     print("curation keys: {}".format(cur_keys))
        # except:
        #     cur_keys = list(self.sample_data.keys())
        rmsd = {}
        validation_per = 0

        skeys_used = []
        bkeys_used = []
        skeys = list(self.sample_data.keys())
        bkeys = list(self.bngl_data.keys())
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

        keys_used = []
        for key_pair in key_pairs:
            skey, bkey = key_pair
            # Get guaranteed single dataset for sample
            if len(self.sample_data[skey].values.shape) > 1:
                if self.sample_data[skey].values.shape[1] > 1:
                    print("we have one too many datasets for the same key")
                    sdata = self.sample_data[skey].iloc[:,0]
                else:
                    sdata = self.sample_data[skey].values
            else:
                sdata = self.sample_data[skey].values
            # And for BNGL result
            if len(self.bngl_data[bkey].values.shape) > 1:
                if self.bngl_data[bkey].values.shape[1] > 1:
                    print("we have one too many datasets for the same key")
                    bdata = self.bngl_data[bkey].iloc[:,0]
                else:
                    bdata = self.bngl_data[bkey].values
            else:
                bdata = self.bngl_data[bkey].values
            if len(sdata) == 0:
                continue
            if len(bdata) == 0:
                continue
            print("we used BNG key {} and SBML key {}".format(bkey, skey))
            # Calculate RMSD
            rmsd[bkey] = calc_rmsd(sdata, bdata)

            norm_tolerance = 1e-1
            if abs(sdata.max()) != 0:
                norm_tolerance = norm_tolerance * sdata.max()
            # norm_tolerance = max(sdata) * tolerance
            if rmsd[bkey] < (norm_tolerance) or rmsd[bkey] < 1e-10:
                validation_per += 1
            else:
                print("{} won't validate".format(skey))
            skeys_used.append(skey)
            bkeys_used.append(bkey)
            keys_used.append((skey,bkey))

        # if cur_keys:
        #     validation_div = len(cur_keys)
        #     # get subset from interwebs
        #     # by the end we need an RMSD value and if it validates
        #     # or not
        #     keys_used = []
        #     bkeys_used = []
        #     skeys_used = []
        #     # import ipdb;ipdb.set_trace()
        #     for ck in cur_keys:
        #         # Sometimes there are more curation keys 
        #         # than datasets in Copasi results
        #         if len(self.sample_data.keys()) == len(skeys_used):
        #             break
        #         # Get keys
        #         ck_sk_ratios = sorted(list(map(lambda y: (y, self.get_ratio(ck, y)), [i for i in self.sample_data.keys() if i not in skeys_used])), key=lambda z: z[1])
        #         skey = ck_sk_ratios[-1][0]
        #         # now we need to determine if we should rely on CK to determine
        #         # the bkey to select
        #         ck_bk_ratios = sorted(list(map(lambda y: (y, self.get_ratio(ck, y)), [i for i in self.bngl_data.keys() if i not in bkeys_used])), key=lambda z: z[1])
        #         sk_bk_ratios = sorted(list(map(lambda y: (y, self.get_ratio(skey, y)), [i for i in self.bngl_data.keys() if i not in bkeys_used])), key=lambda z: z[1])
        #         # decide on the key to use
        #         # TODO: We might also need to check what happens when
        #         # we remove the last value after an "_" because that's
        #         # frequently the compartment which can lead to mismatches
        #         if ck_bk_ratios[-1][1] > sk_bk_ratios[-1][1]:
        #             bkey = ck_bk_ratios[-1][0]
        #         else:
        #             bkey = sk_bk_ratios[-1][0]
        #         # Get guaranteed single dataset for sample
        #         if len(self.sample_data[skey].values.shape) > 1:
        #             if self.sample_data[skey].values.shape[1] > 1:
        #                 print("we have one too many datasets for the same key")
        #                 sdata = self.sample_data[skey].iloc[:,0]
        #             else:
        #                 sdata = self.sample_data[skey].values
        #         else:
        #             sdata = self.sample_data[skey].values
        #         # And for BNGL result
        #         if len(self.bngl_data[bkey].values.shape) > 1:
        #             if self.bngl_data[bkey].values.shape[1] > 1:
        #                 print("we have one too many datasets for the same key")
        #                 bdata = self.bngl_data[bkey].iloc[:,0]
        #             else:
        #                 bdata = self.bngl_data[bkey].values
        #         else:
        #             bdata = self.bngl_data[bkey].values
        #         if len(sdata) == 0:
        #             continue
        #         if len(bdata) == 0:
        #             continue
        #         print("for key {} we used BNG key {} and SBML key {}".format(ck, bkey, skey))
        #         # Calculate RMSD
        #         # Let's get normalization factors
        #         # sdata_norm = sdata[int(sdata.shape[0]/2):]
        #         # sdata_norm = sdata.max()
        #         # # bdata_norm = bdata[int(bdata.shape[0]/2):]
        #         # bdata_norm = bdata.max()
        #         # sdat_rmsd = sdata/sdata_norm if sdata_norm != 0 else sdata
        #         # bdat_rmsd = bdata/bdata_norm if bdata_norm != 0 else bdata
        #         rmsd[ck] = calc_rmsd(sdata, bdata)

        #         norm_tolerance = 1e-1
        #         if abs(sdata.max()) != 0:
        #             norm_tolerance = norm_tolerance * sdata.max()
        #         # IPython.embed()
        #         # norm_tolerance = max(sdata) * tolerance
        #         if rmsd[ck] < (norm_tolerance) or rmsd[ck] < 1e-10:
        #             validation_per += 1
        #         else:
        #             print("{} won't match".format(skey))
        #         skeys_used.append(skey)
        #         bkeys_used.append(bkey)
        #         keys_used.append((skey,bkey,ck))
        # else:
        #     # do the normal spiel
        #     skeys = set(self.sample_data.keys())
        #     bkeys = set(self.bngl_data.keys())
        #     bkey_map = {}
        #     for bkey in bkeys:
        #         bkey_splt = bkey.split("_")
        #         if len(bkey_splt) > 1:
        #             nkey = "".join(bkey_splt[:-1])
        #         else:
        #             nkey = bkey
        #         bkey_map[nkey] = bkey

        #     keys_used = []
        #     validation_div = len(skeys)
        #     for skey in skeys:
        #         ratios = sorted(list(map(lambda y: (y, self.get_ratio(skey, y)), bkey_map.keys())), key=lambda z: z[1])
        #         key_to_use = bkey_map[ratios[-1][0]]
        #         print("matched keys are sbml: {} and bngl: {}".format(skey, key_to_use))
        #         keys_used.append((skey, key_to_use))
        #         # Get guaranteed single dataset
        #         if len(self.sample_data[skey].values.shape) > 1:
        #             if self.sample_data[skey].values.shape[1] > 1:
        #                 print("we have one too many datasets for the same key")
        #                 sdata = self.sample_data[skey].iloc[:,0]
        #             else:
        #                 sdata = self.sample_data[skey].values
        #         else:
        #             sdata = self.sample_data[skey].values
        #         if len(self.bngl_data[key_to_use].values.shape) > 1:
        #             if self.bngl_data[key_to_use].values.shape[1] > 1:
        #                 print("we have one too many datasets for the same key")
        #                 bdata = self.bngl_data[key_to_use].iloc[:,0]
        #             else:
        #                 bdata = self.bngl_data[key_to_use].values
        #         else:
        #             bdata = self.bngl_data[key_to_use].values

        #         # Let's get normalization factors
        #         # sdata_norm = sdata[int(sdata.shape[0]/2):]
        #         # sdata_norm = sdata.max()
        #         # # bdata_norm = bdata[int(bdata.shape[0]/2):]
        #         # bdata_norm = bdata.max()
        #         # sdat_rmsd = sdata/sdata_norm if sdata_norm != 0 else sdata
        #         # bdat_rmsd = bdata/bdata_norm if bdata_norm != 0 else bdata
        #         # 
        #         rmsd[skey] = calc_rmsd(sdata, bdata)

        #         norm_tolerance = 1e-1
        #         if abs(sdata.max()) != 0:
        #             norm_tolerance = norm_tolerance * sdata.max()

        #         if rmsd[skey] < (norm_tolerance) or rmsd[skey] < 1e-10:
        #             validation_per +=1
        #         else:
        #             print("{} won't match".format(skey))
        validation_div = len(keys_used)
        if validation_div > 0:
            validation_per = validation_per/float(validation_div)
        else:
            validation_per = None
        print("Keys used: {}".format(keys_used))
        print("val per {}".format(validation_per))
        self.all_results[test_no] = (self.sample_data, self.bngl_data, rmsd, validation_per, keys_used)
        return True
    
    def run_old_test(self, test_no, t_end=1000, n_steps=200, bid=False, tolerance=1e-1, atol="1E-8", rtol="1E-8", atomize=True):
        '''
        Convenience function to run a single test
        '''
        print("Running test {:05d}".format(test_no))
        # First let's get the RR results
        try:
            self.sample_data, names = self.run_test_data(test_no, t_end=t_end, n_steps=n_steps)
        except:
            return False
        self.sample_data = pd.DataFrame(self.sample_data, columns=names)
        # If we have "time" as a dataset, use it as an index
        print("Got test results")
        try:
            self.sample_data = self.sample_data.set_index("time")
        except:
            pass
        try:
            self.sample_data = self.sample_data.set_index("Time")
        except:
            pass
        # Run translation
        # TODO: Check if translation is succesful and stop if not
        if not self.run_translation(test_no, bid=bid, atomize=atomize):
            return False
        # Add simulate command 
        with open("{:05d}.bngl".format(test_no),'a') as f:
            f.write("\n")
            f.write("generate_network({overwrite=>1})")
            f.write("\n") 
            opts = 'method=>"ode",t_end=>%f,n_steps=>%i'%(t_end,n_steps)# -1)
            if atol:
                opts += ",atol=>%s"%(atol)
            if rtol:
                opts += ",rtol=>%s"%(rtol)
            f.write('simulate({%s})'%(opts))
        # Now simulate the thing
        if not self.run_and_load_simulation(test_no):
            return False
        # Now also run the old stuff
        old_translation = "/home/monoid/Dropbox/atomizer-models/curated/rawTranslation/output{}.bngl".format(test_no)
        with open(old_translation,'a') as f:
            f.write("\n")
            f.write("generate_network({overwrite=>1})")
            f.write("\n") 
            opts = 'method=>"ode",t_end=>%f,n_steps=>%i'%(t_end,n_steps)# -1)
            f.write('simulate({%s})'%(opts))

        ret = sb.run([self.bng2, old_translation])
        if ret.returncode != 0:
            print("there was an issue with simulation in test {:05d}".format(test_no))
            return False
        # Load gdat
        self.old_data = self.read_gdat("output{}.gdat".format(test_no))
        self.all_results[test_no] = (self.sample_data,self.bngl_data,self.old_data)
        return True

    def plot_results(self, test_no, legend=True, save_fig=False, xlim=None, ylim=None):
        # Now do some comparison
        if not self.all_results[test_no][0] is None:
            # plot both
            sd, bd, _, _, keys = self.all_results[test_no]
            fig, ax = plt.subplots(1,2)
            fig.tight_layout()

            for ik, ks in enumerate(keys):
                skey, bkey = ks
                label = "{0:.10}: {1:.3E}".format(bkey,self.all_results[test_no][2][bkey])
                # if len(ks) == 2:
                #     skey, bkey = ks
                #     ck = None
                # else:
                #     skey, bkey, ck = ks
                # try: 
                #     if ck:
                #         label = "{0:.10}: {1:.3E}".format(bkey,self.all_results[test_no][2][ck])
                #     else:
                #         label = "{0:.10}: {1:.3E}".format(bkey,self.all_results[test_no][2][skey])
                # except KeyError:
                #     label = "ind"
                ax[0].plot(sd.index, sd[skey], label=label)
                ax[1].plot(bd.index, bd[bkey], label=label)
            #for ind in sd.keys():
            #    ax[0].plot(sd.index, sd[ind], label=label)
            if legend:
                plt.legend(frameon=False)
            if xlim is not None:
                ax[0].set_xlim(xlim)
                ax[1].set_xlim(xlim)
            if ylim is not None:
                ax[0].set_ylim(ylim)
                ax[1].set_ylim(ylim)
            #for ind in bd.keys():
            #    #ax[1].plot(bd.index, bd[ind], label="bngl {}".format(ind))
            #    ax[1].plot(bd.index, bd[ind])
        else:
            for ind in self.bngl_data.keys():
                plt.plot(self.bngl_data.index, self.bngl_data[ind], label="bngl {}".format(ind))
        if legend:
            plt.legend(frameon=False)
        if xlim is not None:
            plt.xlim(xlim[0], xlim[1])
        if ylim is not None:
            plt.ylim(ylim[0], ylim[1])
        if save_fig:
            plt.savefig("{:05d}-bngl_results.png".format(test_no), dpi=300)
            plt.close()

    def plot_old_results(self, test_no, legend=True, save_fig=False, xlim=None, ylim=None):
        # Now do some comparison
        if not self.all_results[test_no][0] is None:
            # plot both
            sd, bd, od = self.all_results[test_no]
            fig, ax = plt.subplots(1,3)
            fig.tight_layout()
            for ind in sd.keys():
                label = "ind"
                ax[0].plot(sd.index, sd[ind], label=label)
            if legend:
                plt.legend(frameon=False)
            if xlim is not None:
                ax[0].set_xlim(xlim)
                ax[1].set_xlim(xlim)
                ax[2].set_xlim(xlim)
            if ylim is not None:
                ax[0].set_ylim(ylim)
                ax[1].set_ylim(ylim)
                ax[2].set_ylim(ylim)
            for ind in bd.keys():
                #ax[1].plot(bd.index, bd[ind], label="bngl {}".format(ind))
                ax[1].plot(bd.index, bd[ind])
            for ind in od.keys():
                ax[2].plot(od.index, od[ind])
        else:
            for ind in self.bngl_data.keys():
                plt.plot(self.bngl_data.index, self.bngl_data[ind], label="bngl {}".format(ind))
        if legend:
            plt.legend(frameon=False)
        if xlim is not None:
            plt.xlim(xlim[0], xlim[1])
        if ylim is not None:
            plt.ylim(ylim[0], ylim[1])
        if save_fig:
            plt.savefig("{:05d}-old_results.png".format(test_no), dpi=300)
            plt.close()
            
    def load_test_data(self, test_no):
        '''
        This tries to get the images from BioModel website
        '''
        t_ends = self.t_ends
        # Get the URL
        URL = "https://www.ebi.ac.uk/biomodels/BIOMD{:010d}".format(test_no)
        # without these headers we get HTMLError 415, unsupported media type
        headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
        # Get the website
        r = requests.get(URL, headers=headers)
        # Load it into beautiful soup (HTML parser) so we can pull images out
        parsed = BS(r.content, 'lxml')
        # Now find curation sectiot_ends = self.t_endsn
        if(parsed):
            cur  = parsed.find(id="Curation")
            try:
                imgs = cur.find_all("img")
            except AttributeError:
                return None
            self.imgdats = []
            for img in imgs:
                src = img.get("src")
                img_dat = src.split(",")[1]
                imgdata = base64.b64decode(img_dat)
                self.imgdats.append(imgdata)
            return self.imgdats
        else:
            return None

