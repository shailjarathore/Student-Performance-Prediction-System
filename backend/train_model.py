import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

df = pd.read_csv("dataset/student_data.csv")

le = LabelEncoder()
df["performance"] = le.fit_transform(df["performance"])

X = df.drop("performance", axis=1)
y = df["performance"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

dt_model = DecisionTreeClassifier(random_state=42)
dt_model.fit(X_train, y_train)

rf_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)
rf_model.fit(X_train, y_train)

dt_pred = dt_model.predict(X_test)
rf_pred = rf_model.predict(X_test)

dt_acc = accuracy_score(y_test, dt_pred)
rf_acc = accuracy_score(y_test, rf_pred)

print(f"Decision Tree Accuracy: {dt_acc * 100:.2f}%")
print(f"Random Forest Accuracy: {rf_acc * 100:.2f}%")

print("\nDecision Tree Report:\n")
print(classification_report(y_test, dt_pred))

print("\nRandom Forest Report:\n")
print(classification_report(y_test, rf_pred))

joblib.dump(dt_model, "backend/student_model.pkl")
joblib.dump(le, "backend/label_encoder.pkl")

print("\nModel and encoder saved successfully!")