
# %matplotlib notebook
import os, re, sys, urllib, requests, base64, IPython, io, pickle, glob
import itertools as itt
import numpy as np
import subprocess as sb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import roadrunner
from bs4 import BeautifulSoup as BS
from IPython.display import Image, display
from matplotlib import rcParams
import analyzerTools as AT

def run_test(analyzer, test_no, t_end=1000, atomize=False):
    if(analyzer.run_single_test(test_no, t_end=100, atomize=atomize)):
        print("run successful {}".format(test_no))
        analyzer.plot_results(test_no, legend=True, save_fig=True)
#     if(analyzer.run_old_test(test_no, t_end=100, atomize=atomize)):
#         print("run successful {}".format(test_no))
#         analyzer.plot_old_results(test_no, legend=False, save_fig=True)
    else:
        print("run failed {}".format(test_no))
        
def update_results(results, fname="analyzer.pkl"):
    if os.path.isfile(fname):
        with open(fname, "rb") as f:
            old_results = pickle.load(f)
        for key in results.keys():
            old_results[key] = results[key]
        with open(fname, "wb") as f:
            pickle.dump(old_results, f)
    else:
        with open(fname, "wb") as f:
            pickle.dump(results, f)
    print("updated results")
    return True

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

# test_no = 3cleanup 1.0s symbolically, should fix some errors, less bug prone for future
# imgdats = ba.load_test_data(test_no)207
# print(len(imgdats))
# Image(imgdats[0])
# 
# if(ba.run_single_test(test_no, t_end=100)):
#     ba.plot_results(test_no,legend=False)print(r)

# Let's re-run everything
# tests = list(range(419,730))
tests = list(range(1,915))
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

too_long = set([64,574,426,70,217,247,503,469,471,473,506,451,595,  # WAAAY TOO LONG - debug
                332,334, # ATOMIZER BREAKS THESE
                217,247,293,426,469 # too long when atomized 
               ])

################# NEW CHECKS ##############
# A complete new set of checks to see the latest state of the tool as we are 
# writing the manuscript.
new_checks = set([64,217, # too long
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
# run tests
for test_no in tests:
    #if test_no in all_issues:
    #    continue
    if test_no in w_event or test_no in new_checks or test_no in run_fails:
        continue
    if (os.path.isfile("../curated/BIOMD{0:010d}.xml".format(test_no))):
        run_test(ba, test_no, t_end=100, atomize=False)
        # update_results(ba.all_results)
    else: 
        print("number {} doesn't exist".format(test_no))
