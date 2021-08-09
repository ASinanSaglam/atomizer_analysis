import h5py, IPython, pickle, glob, sys, os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

with open("meta_data_backup.pickle", "rb") as f:
    meta = pickle.load(f)

adb = pd.read_hdf("bngl_xml_filesDB.h5", 'atomization')
adb_ind = adb.index.tolist()
for filep in adb.index:
    num = filep.replace("bngl_xml_files/","").replace(".xml","")
    try:
        num = int(num)
    except:
        continue
    if num in meta:
        curr_ind = adb_ind.index(filep)
        meta[num]['yield'] = adb['yild'][curr_ind]
        meta[num]['score'] = adb['score'][curr_ind]
        meta[num]['length'] = adb['length'][curr_ind]
        meta[num]['weight'] = adb['weight'][curr_ind]
        meta[num]['syndel'] = adb['syndel'][curr_ind]
        meta[num]['numspecies'] = adb['numspecies'][curr_ind]
flist = glob.glob("0*.log")
for fpath in flist:
    bname = os.path.basename(fpath)
    bionum = int(bname.replace(".log", ""))
    if not (bionum in meta.keys()):
        continue
    with open(fpath) as f:
        log_list = f.readlines()
    meta[bionum]["ERROR"]  = False 
    meta[bionum]["SYMERR"] = False 
    meta[bionum]["WARN"]   = False 
    meta[bionum]["STOI"]   = False
    meta[bionum]["EPS"]    = False
    for logline in log_list:
        splt = logline.split(":")
        if splt[0] == "ERROR":
            meta[bionum]["ERROR"] = True
            if splt[1] == "SYMP002" or splt[1] == "SYMP001":
                meta[bionum]["SYMERR"] = True
            if splt[1] == "Simulation":
                meta[bionum]["STOI"] = True
        if splt[0] == "WARNING":
            meta[bionum]["WARN"] = True
            if splt[1] == "RATE001":
                meta[bionum]["EPS"] = True

with open("meta_data_updated.pickle", "wb") as f:
    pickle.dump(meta,f)
