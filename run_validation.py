# %matplotlib notebook
import os, re, sys, urllib, requests, base64, IPython, io, pickle, glob
sys.path.append("/home/monoid/Development/fresh_atomizer_checks/atomizer/SBMLparser/test/manual")
import itertools as itt
import numpy as np
import subprocess as sb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import roadrunner, h5py
from bs4 import BeautifulSoup as BS
from IPython.display import Image, display
from matplotlib import rcParams
import analyzerTools as AT

def run_test(analyzer, test_no, t_end=1000, atomize=False, db=None, meta=None):
    
    if(analyzer.run_single_test(test_no, t_end=100, atomize=atomize,meta=meta)):
        if meta:
            meta[test_no]["success"] = True
        print("run successful {}".format(test_no))
        #if db is not None:
        #    # Save results into a DataFrame
        #    res = analyzer.all_results[test_no]
        #    sbml, bngl, rmsd, valid_per, keys = res[0],res[1],res[2],res[3],res[4]            
        #    for key in keys:
        #        # couldn't get the curation keys
        #        if len(key) == 2:
        #            skey, bkey = key
        #        # got curation keys
        #        elif len(key) == 3:
        #            skey, bkey, ckey = key
        #        else:
        #            print("couldn't find keys")
        #        IPython.embed()
        #        sys.exit()
        #        # setting up the database
        #        db.at["{:010d}".format(test_no), "{}_sbml".format(skey)] = res[0][skey]
        #        db.at["{:010d}".format(test_no), "{}_bngl".format(bkey)] = res[1][bkey]
        # analyzer.plot_results(test_no, legend=True, save_fig=True)
#     if(analyzer.run_old_test(test_no, t_end=100, atomize=atomize)):
#         print("run successful {}".format(test_no))
#         analyzer.plot_old_results(test_no, legend=False, save_fig=True)
    else:
        if meta:
            meta[test_no]["success"] = False
        print("run failed {}".format(test_no))

def uniquefy_names(keys):
    unique_keys = []
    if len(keys[0]) == 3:
        bkeys_d = {}
        skeys_d = {}
        ckeys_d = {}
        for key in keys:
            bkey, skey, ckey = key
            if bkey in bkeys_d.keys():
                bkey_new = bkey + "_{}".format(bkeys_d[bkey])
                bkeys_d[bkey] += 1
                bkey = bkey_new
            else:
                bkeys_d[bkey] = 1
            if skey in skeys_d.keys():
                skey_new = skey + "_{}".format(skeys_d[skey])
                skeys_d[skey] += 1
                skey = skey_new
            else:
                skeys_d[skey] = 1
            if ckey in ckeys_d.keys():
                ckey_new = ckey + "_{}".format(ckeys_d[ckey])
                ckeys_d[ckey] += 1
                ckey = ckey_new
            else:
                ckeys_d[ckey] = 1
            unique_keys.append( (bkey,skey,ckey) )
    else:
        bkeys_d = {}
        skeys_d = {}
        for key in keys:
            bkey, skey = key
            if bkey in bkeys_d.keys():
                bkey_new = bkey + "_{}".format(bkeys_d[bkey])
                bkeys_d[bkey] += 1
                bkey = bkey_new
            else:
                bkeys_d[bkey] = 1
            if skey in skeys_d.keys():
                skey_new = skey + "_{}".format(skeys_d[skey])
                skeys_d[skey] += 1
                skey = skey_new
            else:
                skeys_d[skey] = 1
            unique_keys.append( (bkey,skey) )
    return unique_keys

def update_results(results, h5file):
    for key in results:
        if "{:010d}".format(key) in h5file:
            continue
        # create a model group
        res_grp = h5file.create_group("{:010d}".format(key))
        # pull dataframes
        sres, bres, _, _, keys_used = results[key]
        # names
        if len(keys_used) == 0:
            continue
        if len(keys_used[0]) == 2:
            names_to_use = [keys_used[i][1] for i in range(len(keys_used))]
            skeyd = dict([(keys_used[i][1],keys_used[i][0]) for i in range(len(keys_used))])
            bkeyd = dict([(keys_used[i][1],keys_used[i][1]) for i in range(len(keys_used))])
            skn = list(map(lambda x: skeyd[x], names_to_use))
            bkn = list(map(lambda x: bkeyd[x], names_to_use))
        else:
            names_to_use = [keys_used[i][2] for i in range(len(keys_used))]
            skeyd = dict([(keys_used[i][2],keys_used[i][0]) for i in range(len(keys_used))])
            bkeyd = dict([(keys_used[i][2],keys_used[i][1]) for i in range(len(keys_used))])
            skn = list(map(lambda x: skeyd[x], names_to_use))
            bkn = list(map(lambda x: bkeyd[x], names_to_use))
        # make structured arrays
        sdtype = np.dtype({"names":names_to_use,
                  "formats": ["<f8" for i in range(len(names_to_use))]})
        bdtype = np.dtype({"names":names_to_use,
                  "formats": ["<f8" for i in range(len(names_to_use))]})
        # if len(names_to_use) != sres[skn].shape[1]:
        #     # we have multiple datasets per name, drop one
        #     for iname,name in enumerate(names_to_use):
        #         if len(sres[name].shape) > 1:
        #             # 
        stupl = list(map(tuple, sres[skn].values))
        btupl = list(map(tuple, bres[bkn].values))
        sarr = np.array(stupl, dtype=sdtype)
        barr = np.array(btupl, dtype=bdtype)
        # add the data in, if it exists
        if sarr.shape[0] != 0:
            sg = res_grp.create_dataset("sbml_data", data=sarr)
        if barr.shape[0] != 0:
            bg = res_grp.create_dataset("bngl_data", data=barr)
    print("updated results")
    return True

def save_meta(meta, fname="meta_data.pickle"):
    if os.path.isfile(fname):
        with open(fname, "rb") as f:
            m = pickle.load(f)
        for key in meta:
            m[key] = meta[key]
        with open(fname, "wb") as f:
            pickle.dump(m, f)
    else: 
        with open(fname, "wb") as f:
            pickle.dump(meta, f)
# All the paths we need
# The BNG2.pl file for bionetgen runs
bng_path = "/home/monoid/apps/BioNetGen-2.5.0/BNG2.pl"
# This is the python file that can be called from the command line
sbml_translator_path = "/home/monoid/Development/fresh_atomizer_checks/atomizer/SBMLparser/sbmlTranslator.py"
# if you give this the ATOMIZER ANALYZER 5000 will import atomizer and run internally 
# translator_package_path = "/home/monoid/Development/fresh_atomizer_checks/atomizer/SBMLparser"
translator_package_path = None
# This is neccesary for atomizer, has default naming conventions and a lot more 
# this path will be sym linked to everywhere you want to run translator under
config_path = "/home/monoid/Development/fresh_atomizer_checks/atomizer/SBMLparser/config"
# the path to the folder that contains 5 zero padded folders for each test
tests_path = "/home/monoid/Development/fresh_atomizer_checks/atomizer/SBMLparser/test/curated"
# Now we also add COPASI PATH!!_!_
copasi_path = "/home/monoid/apps/copasi/4.27/bin/CopasiSE"
# change directory to where we want to run the tests
os.chdir("/home/monoid/Development/fresh_atomizer_checks/atomizer/SBMLparser/test/analyzerTools")
# The analyzer setup
ba = AT.BiomodelAnalyzer(bng_path, sbml_translator_path, config_path, tests_path, 
                     translator_import=translator_package_path, copasi_path=copasi_path)

# Let's re-run everything
tests = list(range(908,915))
known_issues = set([24,25,34,154,155,196,201,589,613,668,669,696,468, # Not implemented
                    643,644,645, # Complex "i" is used in function/parameter
                    63,245,248,305,556,575,578,542, # rule named used as parameter
                    342,429,457,547,570,627,637,638, # compartment used as parameter
                    527,562,592,593,596,723,250, # Actually broken, even in Copasi
                    304,324,330,331,341,343,345,349,367,371,374,377,381,533,548,
                    549,551,618,642,670,671,680,682,684,118,252,673,531,532,555,
                    561, # no reactions
                    306,307,308,309,310,311,388,390,391,393,409,
                    428,505,512,528,557,566,567,719,641,71,90,173,
                    253, # assignment rules used in reactions
                    610, # function defs for v16/v17   
                    558,568,674,722,412,445,302,208,268,51,55,162,180,179,579,
                    691,465,466,238,312,538,603,604,605,215, # Uses time
                    635,636, # Uses not only time but also encoded strings for parameters
                    119, # single reaction, not really suitable for translation
                    47,483,484,486,487, # initial states should result in no reactions, 
                    164,165,167,326,375,400,554,577,664,672,693,698,
                    234,237,286,450, # Uses piecewise definitions               
                    396,398,507,522,705,
                    499,474, # SBML modeller is careless and uses species that should be params
                    607, # Function not defined properly/links to another function
                    319,206,39,145,353,385,392,463,608,470,472, # non-integer stoichiometry
                    161,182,239, # true multi-compartment model
                    271 # multi-compartment and the modeller has issues
                   ])

# Need to figure out, mostly CVODE
list_of_fails = set([246,336,378,383,384,387,438,9,107,123,183,192,269,
                     279,292,328,617,678,606, # new ones                  
                     616, # Legitimate bug, if species name is very simple AND rate constant 
                     # only depenent on the species concentration AND we end up generating 
                     # an observable with the same name as species name, then BNGL thinkg 
                     # we are giving obs name as the rate constant, leading to a bug
                     255, # Circular dependency in funcs?
                     401,402,403, # if func messes with func ordering
                     559, # can't load copasi result
                     64, # Due to website addition? also in too long set
                     232, # BNG takes too long?
                     172,176,177 # doesn't end up translating, takes a long time?
                    ])

#too_long = set([64,574,426,70,217,247,503,469,471,473,506,451,595,  # WAAAY TOO LONG - debug
#                332,334, # ATOMIZER BREAKS THESE
#                217,247,293,426,469 # too long when atomized 
#               ])

too_long = set([64 ,172,176,177,212,217,235,247,293,385,
                426,451,457,463,469,470,471,472,473,474,
                496,497,503,505,506,574,595,835, 
                863, # transl too long
                232,608, # BNG takes too long
                63,70, # long but completes?
                269 # due to long CVODE error
               ])

################# NEW CHECKS ##############
# A complete new set of checks to see the latest state of the tool as we are 
# writing the manuscript.
new_checks = set([64,217,235,496, # too long
                  497,498, # skey ratio index out of range?
                  63, # fairly long but does complete
                  119,465,468, # no data?
                  247,269,469,470,471,472,473,474,
                  503,505,506,595,606,608,835,863 # long, didn't check if completes
                 ])
################# RUN FAILS ###############
run_fails  = set([9,24,25,34,51,55,107,
                  123,154,155,162,164,165,167,172,176,177,179,180,183,192,
                  201,208,215,232,234,237,238,245,246,248,250,255,268,279,286,292,
                  302,305,312,326,328,332,334,336,353,375,383,384,385,387,396,398,
                  400,401,402,403,412,426,429,438,445,450,451,457,463,466,483,484,
                  486,487,499,507,522,527,531,532,538,542,547,554,555,556,558,559,
                  561,562,574,575,577,578,579,589,592,593,599,600,602,607,610,617,
                  627,635,636,637,638,643,644,645,664,668,669,672,673,674,675,678,
                  687,688,692,693,696,698,705,722,723,730,731,748,749,757,759,760,
                  763,764,766,775,801,802,808,815,824,826,833,837,840,841,849,851,
                  858,859,876,879,880 # run_failed
                 ])
################# EVENTS #################
w_event = set([1,7,56,77,81,87,88,95,96,97,101,104,109,            # models with events
              111,117,120,121,122,124,125,126,127,128,129,130,131, # models with events
              132,133,134,135,136,137,139,140,141,142,144,148,149, # models with events
              152,153,158,186,187,188,189,193,194,195,196,227,235, # models with events
              241,244,256,265,281,285,287,297,301,316,317,318,327, # models with events
              337,338,339,340,342,344,404,408,422,436,437,439,479, # models with events
              480,488,493,494,496,497,534,535,536,537,540,541,563, # models with events
              570,571,597,598,601,612,613,620,621,628,632,634,650, # models with events
              659,681,695,699,702,706,711,718,727,734,735,736,786, # models with events
              789,791,794,806,814,816,817,818,820,822,825,829,834, # models with events
              856,860,862,864,901])                                # models with events
################# END CHECKS ##############
all_issues = known_issues.union(w_event)
all_issues = all_issues.union(list_of_fails)

# Load in database
# dbname = "validation.h5"
# if os.path.isfile(dbname):
#     db = pd.read_hdf(dbname,key="validation")
# else:
#     db = pd.DataFrame()

# run tests
# try:
if os.path.isfile("results.h5"):
    os.remove("results.h5")
    # results_file = h5py.File("results.h5","a")
    results_file = h5py.File("results.h5","w")
else:
    results_file = h5py.File("results.h5","w")

meta_data = {}

for test_no in tests:
    #if test_no in all_issues:
    #    continue
    # if test_no in w_event or test_no in new_checks or test_no in run_fails:
    # if test_no in new_checks or test_no in run_fails:
    #     continue
    if test_no in too_long:
        meta_data[test_no] = {"too_long":True}
        continue
    if (os.path.isfile("/home/monoid/Development/fresh_atomizer_checks/atomizer/SBMLparser/test/curated/BIOMD{0:010d}.xml".format(test_no))):
        #run_test(ba, test_no, t_end=100, atomize=False, db=db)
        meta_data[test_no] = {"file":True, "too_long":False}
        run_test(ba, test_no, t_end=100, atomize=True, meta=meta_data)
        update_results(ba.all_results,results_file)
    else: 
        meta_data[test_no] = {"file":False}
        print("number {} doesn't exist".format(test_no))
    save_meta(meta_data)
#     with open("validation.pickle", 'wb') as f:
#         pickle.dump(ba.all_results, f)
#except:
#    with open("validation.pickle", 'wb') as f:
#        pickle.dump(ba.all_results, f)
#    db.to_hdf(dbname,"validation")
