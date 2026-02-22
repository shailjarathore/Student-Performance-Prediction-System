import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib

df = pd.read_csv("dataset/student_data.csv")

le = LabelEncoder()
df["performance"] = le.fit_transform(df["performance"])

X = df.drop("performance", axis=1)
y = df["performance"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

joblib.dump(model, "backend/student_performance_model.pkl")

print("Model trained and saved successfully!")