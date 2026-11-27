import time
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.tree import DecisionTreeClassifier

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

train_df = pd.read_parquet("data/processed/train.parquet")
test_df = pd.read_parquet("data/processed/test.parquet")

drop_cols = ["Label", "is_attack"]
X_train = train_df.drop(columns=drop_cols)
y_train = train_df["is_attack"]
X_test = test_df.drop(columns=drop_cols)
y_test = test_df["is_attack"]
benign_train = X_train[y_train == 0]

joblib.dump(list(X_train.columns), "models/feature_columns.joblib")

models = {
    "decision_tree": DecisionTreeClassifier(max_depth=20, random_state=42),
    "random_forest": RandomForestClassifier(
        n_estimators=100, max_depth=20, n_jobs=-1, random_state=42
    ),
    "isolation_forest": IsolationForest(
        n_estimators=100, contamination=0.01, n_jobs=-1, random_state=42
    ),
}

rows = []
attack_recall = {}

for name, model in models.items():
    start = time.time()
    if name == "isolation_forest":
        model.fit(benign_train)
        pred = (model.predict(X_test) == -1).astype(int)
    else:
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
    seconds = round(time.time() - start, 1)

    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    rows.append(
        {
            "model": name,
            "accuracy": round(accuracy_score(y_test, pred), 4),
            "precision": round(precision_score(y_test, pred), 4),
            "recall": round(recall_score(y_test, pred), 4),
            "f1": round(f1_score(y_test, pred), 4),
            "FP": fp,
            "FN": fn,
            "train_sec": seconds,
        }
    )

    result = pd.DataFrame({"Label": test_df["Label"].values, "pred": pred})
    result = result[y_test.values == 1]
    attack_recall[name] = result.groupby("Label")["pred"].mean().mul(100).round(1)

    joblib.dump(model, f"models/{name}.joblib", compress=3)
    print(name, "done and saved in", seconds, "sec", flush=True)

print()
print(pd.DataFrame(rows).set_index("model"))
print()
print("Recall % per attack type:")
print(pd.DataFrame(attack_recall).sort_values("random_forest"))