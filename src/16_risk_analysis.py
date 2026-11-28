import joblib
import pandas as pd

pd.set_option("display.width", 200)

test_df = pd.read_parquet("data/processed/test.parquet")
columns = joblib.load("models/feature_columns.joblib")
X_test = test_df[columns]

dt = joblib.load("models/decision_tree.joblib")
rf = joblib.load("models/random_forest.joblib")
iso = joblib.load("models/isolation_forest.joblib")

result = pd.DataFrame(
    {
        "rf_prob": rf.predict_proba(X_test)[:, 1],
        "dt": dt.predict(X_test),
        "iso": (iso.predict(X_test) == -1).astype(int),
        "is_attack": test_df["is_attack"].values,
        "Label": test_df["Label"].values,
    }
)
result["rf"] = (result["rf_prob"] >= 0.5).astype(int)
result["votes"] = result["rf"] + result["dt"] + result["iso"]


def attack_rate(group_by):
    table = result.groupby(group_by)["is_attack"].agg(flows="count", attacks="sum")
    table["attack_%"] = (table["attacks"] / table["flows"] * 100).round(1)
    return table


print("By number of models voting Attack:")
print(attack_rate("votes"))
print()
print("By exact combination (rf, dt, iso):")
print(attack_rate(["rf", "dt", "iso"]))

missed = result[(result["rf"] == 0) & (result["dt"] == 0) & (result["is_attack"] == 1)]
print()
print("Attacks missed by both Random Forest and Decision Tree:", len(missed))
print("Of these, flagged by Isolation Forest:", int(missed["iso"].sum()))
print(missed["Label"].value_counts().head(5))

middle = ((result["rf_prob"] > 0.05) & (result["rf_prob"] < 0.95)).mean() * 100
print()
print("RF probability between 0.05 and 0.95:", round(middle, 1), "%")