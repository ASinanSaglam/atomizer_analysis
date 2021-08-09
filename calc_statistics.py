import h5py, IPython
import numpy as np
import matplotlib.pyplot as plt

def calc_rmsd(d1, d2):
    assert len(d1) == len(d2), "data have different size"
    assert len(d1) > 0, "data1 doesn't have anything"
    assert len(d2) > 0, "data2 doesn't have anything"
    return np.sqrt(sum((d1-d2)**2)/(float(len(d1))*np.sqrt(d1.dot(d1))))
    # return np.sqrt(sum((d1-d2)**2)/(float(len(d1))))

res = h5py.File("results.h5", "r")

val_rat = []
for bnum in res:
    bgrp = res[bnum]
    try:
        sdat = bgrp["sbml_data"]
    except:
        print("no SBML data in {}".format(bnum))
        continue
    try:
        bdat = bgrp["bngl_data"]
    except:
        print("no BNGL data in {}".format(bnum))
        continue
    # Now we have bdat/sdat 
    # let's get rmsds
    rmsds = {}
    tctr = 0.0
    cctr = 0.0
    for iit, it in enumerate(sdat.dtype.fields.items()):
        name = it[0]
        rmsds[name] = calc_rmsd(sdat[name], bdat[name])
        tctr+=1
        if rmsds[name] < 0.1:
            cctr += 1
    val_rat.append(cctr/tctr)
    print("Model {}, species validation ratio: {}".format(bnum, (cctr/tctr)))

# let's plot validation
val_rat = np.array(val_rat, dtype=np.float)

import seaborn as sns
sns.set_style("white")
_, axs = plt.subplots(1, 1, sharex=True, figsize=(10, 8))
plt.clf()
sns.set_palette("BuGn_d")

sns.distplot(val_rat, bins=10, rug=False, kde=False, hist_kws=dict(alpha=1))
plt.xlabel("species validation ratio", fontsize=18)
plt.ylabel("Number of models", fontsize=18)
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.tight_layout()

plt.savefig("validation_ratio.png")
plt.savefig("validation_ratio.pdf")
