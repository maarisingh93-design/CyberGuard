import time
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

train_df = pd.read_parquet("data/processed/train.parquet")
test_df = pd.read_parquet("data/processed/test.parquet")

drop_cols = ["Label", "is_attack"]
benign_train = train_df[train_df["is_attack"] == 0].drop(columns=drop_cols)
X_test = test_df.drop(columns=drop_cols)
y_test = test_df["is_attack"]

print("Training on benign rows only:", benign_train.shape, flush=True)

model = IsolationForest(
    n_estimators=100,
    contamination=0.01,
    n_jobs=-1,
    random_state=42,
)

start = time.time()
model.fit(benign_train)
print("Training time (sec):", round(time.time() - start, 1), flush=True)

y_pred = (model.predict(X_test) == -1).astype(int)

print()
print("Accuracy :", round(accuracy_score(y_test, y_pred), 4))
print("Precision:", round(precision_score(y_test, y_pred), 4))
print("Recall   :", round(recall_score(y_test, y_pred), 4))
print("F1-score :", round(f1_score(y_test, y_pred), 4))
print()
print("Confusion matrix [[TN, FP], [FN, TP]]:")
print(confusion_matrix(y_test, y_pred))

test_df = test_df.copy()
test_df["pred"] = y_pred
attacks = test_df[test_df["is_attack"] == 1]
result = attacks.groupby("Label")["pred"].agg(["sum", "count"])
result.columns = ["caught", "total"]
result["missed"] = result["total"] - result["caught"]
result["recall_%"] = (result["caught"] / result["total"] * 100).round(1)
print()
print(result.sort_values("recall_%"))