import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_parquet("data/processed/cyberguard_clean.parquet")

# Chart 1: flows per label (log scale)
counts = df["Label"].value_counts().sort_values()

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(counts.index, counts.values, color="steelblue")
ax.set_xscale("log")
ax.set_xlabel("Number of flows (log scale)")
ax.set_title("CICIDS2017: flows per label")
plt.tight_layout()
plt.savefig("reports/01_label_counts.png", dpi=150)
plt.close()

# Chart 2: normal vs attack (median of selected features)
features = ["Flow Duration", "Total Fwd Packets", "Flow Packets/s", "SYN Flag Count"]
medians = df.groupby("is_attack")[features].median()
print(medians)

fig, axes = plt.subplots(1, 4, figsize=(14, 4))
for ax, feat in zip(axes, features):
    ax.bar(["Normal", "Attack"], medians[feat], color=["steelblue", "indianred"])
    ax.set_title(feat)
plt.tight_layout()
plt.savefig("reports/02_normal_vs_attack.png", dpi=150)
plt.close()

print("Charts saved in reports/")