import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns

with open("only_rats.txt", "r") as f:
    rats = f.readlines()

r = [float(i.split(":")[1].strip()) for i in rats]
r = np.array(r)

print(r.mean())
print(len(r[r>0])/len(r))
print(r[r>0].mean())

sns.set_style("white")
_, axs = plt.subplots(1, 1, sharex=True, figsize=(10, 8))
plt.clf()
sns.set_palette("BuGn_d")
sns.distplot(r, bins=10, rug=False, kde=False, hist_kws=dict(alpha=1))
plt.xlabel("Structured species ratio", fontsize=18)
plt.ylabel("Number of models", fontsize=18)
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.tight_layout()
plt.savefig("struc_spec.png")
