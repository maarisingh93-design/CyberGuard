import pandas as pd
from sklearn.tree import DecisionTreeClassifier

train_df = pd.read_parquet("data/processed/train.parquet")
test_df = pd.read_parquet("data/processed/test.parquet")

drop_cols = ["Label", "is_attack"]
X_train = train_df.drop(columns=drop_cols)
y_train = train_df["is_attack"]
X_test = test_df.drop(columns=drop_cols)

model = DecisionTreeClassifier(max_depth=10, random_state=42)
model.fit(X_train, y_train)

test_df = test_df.copy()
test_df["pred"] = model.predict(X_test)

attacks = test_df[test_df["is_attack"] == 1]
result = attacks.groupby("Label")["pred"].agg(["sum", "count"])
result.columns = ["caught", "total"]
result["missed"] = result["total"] - result["caught"]
result["recall_%"] = (result["caught"] / result["total"] * 100).round(1)

print(result.sort_values("recall_%"))
