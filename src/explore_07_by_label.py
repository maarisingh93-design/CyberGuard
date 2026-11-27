import pandas as pd

df = pd.read_parquet("data/processed/cyberguard_clean.parquet")

features = ["Flow Duration", "Total Fwd Packets", "Flow Packets/s"]
table = df.groupby("Label")[features].median()
table["Duration (sec)"] = table["Flow Duration"] / 1_000_000

pd.set_option("display.float_format", "{:,.2f}".format)
print(table)