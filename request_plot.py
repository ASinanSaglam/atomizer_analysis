import matplotlib.pyplot as plt 
# import seaborn as sns

# sns.set_style("white")
_, axs = plt.subplots(1, 1, sharex=True, figsize=(10, 8))
# sns.set_palette("BuGn_d")
dat = [609,188,62,50] 
# bins = [0,1,5,10,100000]
# sns.distplot(data, kde=False, rug=False, bins=bins, hist_kws=dict(alpha=1))
plt.bar([0,1,2,3], dat, tick_label=["0", "1-5", "6-10", ">10"], color=["darkgreen","green","limegreen","lightgreen"], edgecolor="k")
# "ax = plt.gca()\n",
# "ax.spines['right'].set_visible(False)\n",
# "ax.spines['top'].set_visible(False)\n",
plt.xlabel("Requests for user input", fontsize=18)
plt.ylabel("Number of models", fontsize=18)
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.tight_layout()

plt.savefig("user_reqs.png")

# "for tick in ax.xaxis.get_major_ticks():\n",
# "    tick.label.set_fontsize(6) \n",
# "for tick in ax.yaxis.get_major_ticks():\n",
# "    tick.label.set_fontsize(6) \n",
# "plt.subplots_adjust(top=1.0, right=1.0)\n",
# "_ = plt.xlabel(\"Requests for user input \\n ({} models)\".format(sum(hist)), fontsize=6, fontweight='bold')\n",
# "_ = plt.ylabel(\"Number of Models\", fontsize=6, fontweight='bold')\n",
# "# plt.hist(ureq_l, bins=[0,1,5,10,100])\n",
# "acc = np.array(list(itt.accumulate(hist, func=lambda x,y: x+y)))\n",
# "per_acc = acc/float(sum(hist))\n",
# "print(acc, per_acc, 1-per_acc)\n",
# "plt.savefig(\"curated_user_inp_req.pdf\")"
# 
