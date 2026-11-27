import glob
import numpy as np
import pandas as pd

files = sorted(glob.glob("data/raw/*.parquet"))
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

print("Shape:", df.shape)
print("Memory (MB):", round(df.memory_usage(deep=True).sum() / 1024**2, 1))
print()

print("Missing values:", df.isna().sum().sum())

numeric = df.select_dtypes(include=[np.number])
print("Infinity values:", np.isinf(numeric).sum().sum())

print("Duplicate rows:", df.duplicated().sum())