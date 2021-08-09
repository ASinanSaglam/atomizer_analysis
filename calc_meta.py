import h5py, IPython, pickle, sys
import numpy as np
import matplotlib.pyplot as plt
import sys

# with open("meta_data_updated.pickle", "rb") as f:
with open(sys.argv[1], "rb") as f:
    meta = pickle.load(f)

too_long = list(filter(lambda x: meta[x]["avoid"] if "avoid" in meta[x].keys() else False, meta))
exists = list(filter(lambda x: meta[x]["file"] if "file" in meta[x].keys() else False, meta))
copasi_runs = list(filter(lambda x: meta[x]["copasi_run"] if "copasi_run" in meta[x].keys() else False, exists))
translates = list(filter(lambda x: meta[x]["translate"] if "translate" in meta[x].keys() else False, copasi_runs))
runnable = list(filter(lambda x: meta[x]["runnable"] if "runnable" in meta[x].keys() else False, translates))
not_run = list(filter(lambda x: not meta[x]["runnable"] if "runnable" in meta[x].keys() else False, translates))
success = list(filter(lambda x: meta[x]["success"] if "success" in meta[x].keys() else False, runnable))
# Calc lengths
exists_l = len(exists)
too_lo_l = len(too_long)
exists_l += too_lo_l
copasi_l = len(copasi_runs)
transl_l = len(translates)
runnab_l = len(runnable)
succes_l = len(success)
supported = exists_l - too_lo_l 
print(" ## WITHOUT ERROR FILTRATION ## ")
print("total number of models {}".format(exists_l))
print("copasi runs {} avoid {}".format(copasi_l, too_lo_l))
print("supported {}".format(supported))
print("translates {}, {:.3f}%, fails {}".format(transl_l,100*(transl_l/float(supported)),supported-transl_l))
print("runnable {}, {:.3f}%, fails {}".format(runnab_l, 100*(runnab_l/float(transl_l)),transl_l-runnab_l))
print("success {}, {:.3f}%, fails {}".format(succes_l, 100*(succes_l/float(runnab_l)),runnab_l-succes_l))
print("not runnable: {}".format(not_run))

exact = 0
high_vr = 0
low_vr = []
for succ_id in [i for i in success if i not in too_long]:
    vr = meta[succ_id]['valid_rat']
    if vr is not None:
        if float(vr) == 1.0:
            exact += 1
        else:
            low_vr.append(succ_id)
        if float(vr) > 0.7:
            high_vr += 1
exact_perc = 100*(exact/runnab_l)
high_perc = 100*(high_vr/runnab_l)
print("exact count: {} ({:.1f}%), high vr count: {} ({:.1f}%)".format(exact,exact_perc, high_vr, high_perc))
print("low vr models: {}".format(low_vr))

# import sys;sys.exit()
# 
# # ERROR FILTERING 
# with open(sys.argv[1], "rb") as f:
#     meta = pickle.load(f)
# too_long = list(filter(lambda x: meta[x]["avoid"] if "avoid" in meta[x].keys() else False, meta))
# exists = list(filter(lambda x: meta[x]["file"] if "file" in meta[x].keys() else False, meta))
# error = list(filter(lambda x: meta[x]["ERROR"] if "ERROR" in meta[x].keys() else False, exists))
# exists = list(filter(lambda x: not meta[x]["ERROR"] if "ERROR" in meta[x].keys() else True, exists))
# copasi_runs = list(filter(lambda x: meta[x]["copasi_run"] if "copasi_run" in meta[x].keys() else False, exists))
# translates = list(filter(lambda x: meta[x]["translate"] if "translate" in meta[x].keys() else False, copasi_runs))
# runnable = list(filter(lambda x: meta[x]["runnable"] if "runnable" in meta[x].keys() else False, translates))
# success = list(filter(lambda x: meta[x]["success"] if "success" in meta[x].keys() else False, runnable))
# # Calc lengths
# exists_l = len(exists)
# too_lo_l = len(too_long)
# exists_l += too_lo_l
# copasi_l = len(copasi_runs)
# transl_l = len(translates)
# runnab_l = len(runnable)
# succes_l = len(success)
# error_l  = len(error)
# supported = exists_l - too_lo_l 
# print(" ## WITH ERROR FILTRATION ## ")
# print("total number of models {}".format(exists_l))
# print("total number of models with error {}".format(error_l))
# print("copasi runs {} avoid {}".format(copasi_l, too_lo_l))
# print("supported {}".format(supported))
# print("translates {}, {:.3f}%, fails {}".format(transl_l,100*(transl_l/float(supported)),supported-transl_l))
# print("runnable {}, {:.3f}%, fails {}".format(runnab_l, 100*(runnab_l/float(transl_l)),transl_l-runnab_l))
# print("success {}, {:.3f}%, fails {}".format(succes_l, 100*(succes_l/float(runnab_l)),runnab_l-succes_l))
# 
# exact = 0
# high_vr = 0
# low_vr = []
# for succ_id in [i for i in success if i not in too_long]:
#     vr = meta[succ_id]['valid_rat']
#     if vr is not None:
#         if float(vr) == 1.0:
#             exact += 1
#         if float(vr) > 0.7:
#             high_vr += 1
#         else:
#             low_vr.append(succ_id)
# exact_perc = 100*(exact/runnab_l)
# high_perc = 100*(high_vr/runnab_l)
# print("exact count: {} ({:.1f}%), high vr count: {} ({:.1f}%)".format(exact,exact_perc, high_vr, high_perc))
# print("low vr models: {}".format(low_vr))
# # Plot these
# # res = [exists_l,transl_l,runnab_l]
# # plt.bar([0,1,2], res, 
# #         tick_label=["All models", "Translatable", "Runnable"],
# #         color=["r","b","darkgreen"], edgecolor="k")
# # plt.ylim(0,1000)
# # _ = plt.xlabel("Types of models")
# # _ = plt.ylabel("Number of models")
# # plt.savefig("no_filters.png")
# # plt.close()
# 
# # print("too long {}, total {}".format(too_lo_l, too_lo_l+exists_l))
# # IPython.embed()
# # 'success': True},
# # 'file': True,
# # 'copasi_run': True,
# # 'translate': True,
# # 'runnable': True,
# # 'curation_keys': True,
# # 'success': True}}
# with open("meta_data_updated.pickle", "rb") as f:
#     meta = pickle.load(f)
# 
# too_long = list(filter(lambda x: meta[x]["avoid"] if "avoid" in meta[x].keys() else False, meta))
# exists = list(filter(lambda x: meta[x]["file"] if "file" in meta[x].keys() else False, meta))
# error = list(filter(lambda x: meta[x]["ERROR"] if "ERROR" in meta[x].keys() else False, exists))
# exists = list(filter(lambda x: not meta[x]["ERROR"] if "ERROR" in meta[x].keys() else False, exists))
# copasi_runs = list(filter(lambda x: meta[x]["copasi_run"] if "copasi_run" in meta[x].keys() else False, exists))
# translates = list(filter(lambda x: meta[x]["translate"] if "translate" in meta[x].keys() else False, copasi_runs))
# runnable = list(filter(lambda x: meta[x]["runnable"] if "runnable" in meta[x].keys() else False, translates))
# success = list(filter(lambda x: meta[x]["success"] if "success" in meta[x].keys() else False, runnable))
# # Calc lengths
# error_l  = len(error)
# exists_l = len(exists)
# too_lo_l = len(too_long)
# exists_l += too_lo_l
# copasi_l = len(copasi_runs)
# transl_l = len(translates)
# runnab_l = len(runnable)
# succes_l = len(success)
# print()
# print(" ## POST ERROR FILTRATION ## ")
# print("total number of models without error {}".format(exists_l))
# print("total number of models with error {}".format(error_l))
# print("copasi runs {} too long {}".format(copasi_l, too_lo_l))
# print("translates {}, {:.3f}%, fails {}".format(transl_l,100*(transl_l/float(exists_l)),copasi_l-transl_l))
# print("runnable {}, {:.3f}%, fails {}".format(runnab_l, 100*(runnab_l/float(transl_l)),transl_l-runnab_l))
# print("success {}, {:.3f}%, fails {}".format(succes_l, 100*(succes_l/float(exists_l)),exists_l-succes_l))
# 
# # Plot these
# res = [exists_l,transl_l,runnab_l]
# plt.bar([0,1,2], res, 
#         tick_label=["All models", "Translatable", "Runnable"],
#         color=["salmon","skyblue","lightgreen"], edgecolor="k")
# plt.ylim(0,1000)
# _ = plt.xlabel("Types of models")
# _ = plt.ylabel("Number of models")
# # plt.savefig("err_filters.png")
# plt.savefig("both_err_filters.png")
# plt.savefig("both_err_filters.pdf")
# plt.close()
# 
# ###### "Acceptable" list of problems ######
# # Running level:
# cvode = set([9,56,107,122,123,153,158,186,187,192,
#              195,250,269,292,328,336,438,579,597,
#              598,606,617,620,621,628,635,636,678,
#              699,723,760,763,764,822,824,826,849]) # CVODE
# 
# time = set([51,55,162,180,179,208,215,238,268,302,312,
#             412,445,465,466,538,558,568,579,603,604,605,
#             674,691,722]) # Uses time
# 
# not_impl = set([24,25,34,154,155,196,466,568,841, # delay, not implemented
#                 201,562,592,593,696,775, # NaN, not implemented
#                 858,859, # xor, not implemented
#                 245,353,383,384,385,387,463, # non-integer stoichiometry
#                 342,429,457,547,570,627,637,638, # compartment used as parameter
#                 63,245,248,305,556,575,578,542, # rule named used as parameter
#                ]) 
# 
# run_level = set([643,644,645, # Complex "i" is used in function/parameter
#                  426, # breaks notebook?
#                  483,484,486,487, # no reactions fired by BNG
#                  531,532,555,561,563,673,860,864, # no reactions
#                  599,749, # Key error?
#                  607,610, # index error, split incorrectly by =
#                  183, # Doesn't validate, runs
#                  279, # Function ordering
#                  731,840,876, # expecting operator argument?
#                  766, # missing paran )?
#                  802,815, # function name matches paramname
#                  256, # log function somewhere?
#                  856, # molecule missing?
#                  695,814, # bad translation for parameter
#                  833]) # found _ ?
# 
# params_err = set([401,402,403, # if func messes with func ordering?
#                   396,398,499,507,522,577,
#                   705,730,837, # ref not def variable
#                   246, # Missing parameter, due to atomization?
#                   748,880,
#                   601,706,81,125,281,327,437,613
#                   ]) #  undef variable e
# 
# other_errs = set([215,538, # time in parameters
#                   616,783,784,785,825,848,890,893,907, # observable in func
#                   559]) # Copasi .cps file is borked?
# 
# # errors = piece.union(cvode).union(time).union(not_impl).union(run_level).union(params_err).union(other_errs)
# errors = not_impl
# # IPython.embed()
# 
# 
# too_long = list(filter(lambda x: meta[x]["avoid"] if "avoid" in meta[x].keys() else False, meta))
# exists = list(filter(lambda x: meta[x]["file"] if "file" in meta[x].keys() else False, meta))
# exists = list(filter(lambda x: not (x in errors), exists))
# copasi_runs = list(filter(lambda x: meta[x]["copasi_run"] if "copasi_run" in meta[x].keys() else False, exists))
# translates = list(filter(lambda x: meta[x]["translate"] if "translate" in meta[x].keys() else False, copasi_runs))
# runnable = list(filter(lambda x: meta[x]["runnable"] if "runnable" in meta[x].keys() else False, translates))
# runfails = list(filter(lambda x: not meta[x]["runnable"] if "runnable" in meta[x].keys() else False, translates))
# success = list(filter(lambda x: meta[x]["success"] if "success" in meta[x].keys() else False, runnable))
# # Calc lengths
# error_l  = len(errors)
# exists_l = len(exists)
# too_lo_l = len(too_long)
# exists_l += too_lo_l
# copasi_l = len(copasi_runs)
# transl_l = len(translates)
# runnab_l = len(runnable)
# succes_l = len(success)
# print()
# print(" ## POST MANUAL ERROR FILTRATION ## ")
# print("total number of models without error {}".format(exists_l))
# print("total number of models with error {}".format(error_l))
# print("copasi runs {} too long {}".format(copasi_l, too_lo_l))
# print("translates {}, {:.3f}%, fails {}".format(transl_l,100*(transl_l/float(exists_l)),copasi_l-transl_l))
# print("runnable {}, {:.3f}%, fails {}".format(runnab_l, 100*(runnab_l/float(transl_l)),transl_l-runnab_l))
# print("run fails: {}".format(runfails))
# print("success {}, {:.3f}%, fails {}".format(succes_l, 100*(succes_l/float(exists_l)),exists_l-succes_l))
# 
# # Plot these
# res = [exists_l,transl_l,runnab_l,400]
# plt.bar([0,1,2,3], res, 
#         tick_label=["All models", "Translatable", "Runnable", "Valid"],
#         color=["r","b","c","g"], edgecolor="k")
# plt.ylim(0,1000)
# _ = plt.xlabel("Types of models")
# _ = plt.ylabel("Number of models")
# plt.savefig("man_err_filters.png")
# plt.close()

valid_rats = []
yield_vals = []
score_vals = []
bnums = [] 
for num in sorted(meta.keys()):
    try:
        valid_rat = meta[num]['valid_rat']
        yield_val = meta[num]['yield']
        score_val = meta[num]['score']
    except:
        continue
    if (valid_rat is None):
        continue
    if (yield_val is None):
        continue
    if (score_val is None):
        continue
    bnums.append(num)
    valid_rats.append(valid_rat)
    yield_vals.append(yield_val)
    score_vals.append(score_val)

bnums = np.array(bnums)
varr = np.array(valid_rats)
yarr = np.array(yield_vals)
sarr = np.array(score_vals)

import IPython;IPython.embed()
sys.exit()

import seaborn as sns
from scipy import stats

def plot2d(x,y, outname="plot2d.png", plotType=sns.kdeplot, xlim=(0,1), ylim=(0,1), xname="x", yname="y"):
    plt.clf()
    _,_ = plt.subplots(1,1,sharex=True, figsize=(8,6))
    g = sns.JointGrid(x,y,xlim=xlim, ylim=ylim)
    g.plot_marginals(sns.distplot, color="g",bins=None)
    g.plot_joint(plotType, cmap="Greens", shade=True, n_levels=20)
    g.set_axis_labels(xname, yname)
    g.annotate(stats.pearsonr)
    plt.savefig(outname)


plot2d(varr, yarr, xname="valid", yname="yield", outname="valid_yield.png")
plot2d(varr, sarr, xname="valid", yname="score", outname="valid_score.png")

# hist2dvy, vb, yb = np.histogram2d(varr,yarr)
# vdigi = np.digitize(varr, vb)
# ydigi = np.digitize(yarr, vb)
both_high = np.logical_and(varr>0.9, yarr>0.9)
high_yield_models = bnums[both_high]
print("high yield models: {}".format(high_yield_models))
both_high = np.logical_and(varr>0.9, sarr>0.9)
high_score_models = bnums[both_high]
print("high score models: {}".format(high_score_models))
hym_set = set(high_yield_models)
hcm_set = set(high_score_models)
overlapping = hym_set.intersection(hcm_set)
print("ovarlapping ones, {} models: {}".format(len(overlapping), sorted(overlapping)))
only_high_yield = hym_set.difference(hcm_set)
print("only high yield ones: {}".format(sorted(only_high_yield)))
only_high_score = hcm_set.difference(hym_set)
print("only high score ones: {}".format(sorted(only_high_score)))

low_yield = np.logical_and(varr>0.9, yarr<=0.2)
low_yield_models = bnums[low_yield]
print("low yield models: {}".format(low_yield_models))
low_score = np.logical_and(varr>0.9, sarr<=0.2)
low_score_models = bnums[low_score]
print("low score models: {}".format(low_score_models))
lym_set = set(low_yield_models)
lcm_set = set(low_score_models)
overlapping = lym_set.intersection(lcm_set)
print("ovarlapping ones, {} models: {}".format(len(overlapping), sorted(overlapping)))
only_low_yield = lym_set.difference(lcm_set)
print("only low yield ones: {}".format(sorted(only_low_yield)))
only_low_score = lcm_set.difference(lym_set)
print("only low score ones: {}".format(sorted(only_low_score)))

hylc = hym_set.intersection(lcm_set)
print("high yield, low score ones, {} models: {}".format(len(hylc),sorted(hylc)))
lyhc = lym_set.intersection(hcm_set)
print("low yield, high score ones, {} models: {}".format(len(lyhc),sorted(lyhc)))
########################################################
event = set([1,7,56,77,81,87,88,95,96,97,101,104,109,            # models with events
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

## high 
print("### from here on it's low validation score models ###")
low_high = np.logical_and(varr<0.5, yarr>0.9)
high_yield_models = sorted(set(bnums[low_high]).difference(event))
print("high yield models: {}".format(high_yield_models))
low_high = np.logical_and(varr<0.5, sarr>0.9)
high_score_models = sorted(set(bnums[low_high]).difference(event))
print("high score models: {}".format(high_score_models))
hym_set = set(high_yield_models).difference(event)
hcm_set = set(high_score_models).difference(event)
overlapping = hym_set.intersection(hcm_set)
print("ovarlapping ones, {} models: {}".format(len(overlapping), sorted(overlapping)))
only_high_yield = hym_set.difference(hcm_set)
print("only high yield ones: {}".format(sorted(only_high_yield)))
only_high_score = hcm_set.difference(hym_set)
print("only high score ones: {}".format(sorted(only_high_score)))

## low
low_yield = np.logical_and(varr<0.5, yarr<=0.2)
low_yield_models = sorted(set(bnums[low_yield]).difference(event))
print("low yield models: {}".format(low_yield_models))
low_score = np.logical_and(varr<0.5, sarr<=0.2)
low_score_models = sorted(set(bnums[low_score]).difference(event))
print("low score models: {}".format(low_score_models))
lym_set = set(low_yield_models).difference(event)
lcm_set = set(low_score_models).difference(event)
overlapping = lym_set.intersection(lcm_set)
print("ovarlapping ones, {} models: {}".format(len(overlapping), sorted(overlapping)))
only_low_yield = lym_set.difference(lcm_set)
print("only low yield ones: {}".format(sorted(only_low_yield)))
only_low_score = lcm_set.difference(lym_set)
print("only low score ones: {}".format(sorted(only_low_score)))

hylc = hym_set.intersection(lcm_set)
print("high yield, low score ones, {} models: {}".format(len(hylc),sorted(hylc)))
lyhc = lym_set.intersection(hcm_set)
print("low yield, high score ones, {} models: {}".format(len(lyhc),sorted(lyhc)))

## mid valid models
print("### from here on it's mid validation score models ###")
low_high = np.logical_and(np.logical_and(varr>0.5, varr<1.0), yarr>0.9)
high_yield_models = sorted(set(bnums[low_high]).difference(event))
print("high yield models: {}".format(high_yield_models))
low_high = np.logical_and(np.logical_and(varr>0.5, varr<1.0), sarr>0.9)
high_score_models = sorted(set(bnums[low_high]).difference(event))
print("high score models: {}".format(high_score_models))
hym_set = set(high_yield_models).difference(event)
hcm_set = set(high_score_models).difference(event)
overlapping = hym_set.intersection(hcm_set)
print("ovarlapping ones, {} models: {}".format(len(overlapping), sorted(overlapping)))
only_high_yield = hym_set.difference(hcm_set)
print("only high yield ones: {}".format(sorted(only_high_yield)))
only_high_score = hcm_set.difference(hym_set)
print("only high score ones: {}".format(sorted(only_high_score)))

## low
low_yield = np.logical_and(np.logical_and(varr>0.5, varr<1.0), yarr<=0.2)
low_yield_models = sorted(set(bnums[low_yield]).difference(event))
print("low yield models: {}".format(low_yield_models))
low_score = np.logical_and(np.logical_and(varr>0.5, varr<1.0), sarr<=0.2)
low_score_models = sorted(set(bnums[low_score]).difference(event))
print("low score models: {}".format(low_score_models))
lym_set = set(low_yield_models).difference(event)
lcm_set = set(low_score_models).difference(event)
overlapping = lym_set.intersection(lcm_set)
print("ovarlapping ones, {} models: {}".format(len(overlapping), sorted(overlapping)))
only_low_yield = lym_set.difference(lcm_set)
print("only low yield ones: {}".format(sorted(only_low_yield)))
only_low_score = lcm_set.difference(lym_set)
print("only low score ones: {}".format(sorted(only_low_score)))

hylc = hym_set.intersection(lcm_set)
print("high yield, low score ones, {} models: {}".format(len(hylc),sorted(hylc)))
lyhc = lym_set.intersection(hcm_set)
print("low yield, high score ones, {} models: {}".format(len(lyhc),sorted(lyhc)))

