import glob
import pandas as pd

files = sorted(glob.glob("data/raw/*.parquet"))
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
print("Loaded:", df.shape)

df = df.drop_duplicates().reset_index(drop=True)
print("After removing duplicates:", df.shape)

df["Label"] = df["Label"].str.replace(r"[^\x00-\x7F]", "-", regex=True)

df["is_attack"] = (df["Label"] != "Benign").astype(int)

print()
print(df["Label"].value_counts())
print()
print(df["is_attack"].value_counts())

df.to_parquet("data/processed/cyberguard_clean.parquet", index=False)
print()
print("Saved to data/processed/cyberguard_clean.parquet")