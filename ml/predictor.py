"""
ml/predictor.py - Machine Learning engine
Decision Tree classifier with 6 academic features.
"""
import os, joblib
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

MODEL_FILE = os.path.join(os.path.dirname(__file__), "model.pkl")
LABELS = ["Low", "Medium", "High"]
WEIGHTS = {
    "attendance": 0.20, "study_hours_norm": 0.15,
    "internal_norm": 0.25, "assignment_score": 0.20,
    "midterm_score": 0.15, "extra_norm": 0.05,
}

def _generate_training_data(n=1200):
    np.random.seed(42)
    rows = []
    for _ in range(n):
        tier = np.random.choice([0, 1, 2], p=[0.25, 0.35, 0.40])
        if tier == 2:
            att=np.random.uniform(75,100); study=np.random.uniform(25,60)
            intm=np.random.uniform(35,50); assn=np.random.uniform(70,100)
            mid=np.random.uniform(70,100); extra=np.random.uniform(5,10)
        elif tier == 1:
            att=np.random.uniform(55,85); study=np.random.uniform(10,35)
            intm=np.random.uniform(22,40); assn=np.random.uniform(45,78)
            mid=np.random.uniform(45,75); extra=np.random.uniform(2,7)
        else:
            att=np.random.uniform(20,65); study=np.random.uniform(0,20)
            intm=np.random.uniform(5,28); assn=np.random.uniform(10,55)
            mid=np.random.uniform(10,52); extra=np.random.uniform(0,5)
        rows.append([att, study, intm, assn, mid, extra, tier])
    cols = ["attendance","study_hours","internal_marks",
            "assignment_score","midterm_score","extracurricular","label"]
    return pd.DataFrame(rows, columns=cols)

def _feature_cols():
    return ["attendance","study_hours_norm","internal_norm",
            "assignment_score","midterm_score","extra_norm"]

def train_model():
    print("Training Decision Tree model...")
    df = _generate_training_data(1200)
    df["study_hours_norm"] = (df["study_hours"] / 60) * 100
    df["internal_norm"]    = (df["internal_marks"] / 50) * 100
    df["extra_norm"]       = (df["extracurricular"] / 10) * 100
    X = df[_feature_cols()].values
    y = df["label"].values
    X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", DecisionTreeClassifier(max_depth=8, min_samples_split=10,
                                        min_samples_leaf=5, random_state=42))
    ])
    pipeline.fit(X_train, y_train)
    print(classification_report(y_test, pipeline.predict(X_test), target_names=LABELS))
    joblib.dump(pipeline, MODEL_FILE)
    print(f"Model saved -> {MODEL_FILE}")
    return pipeline

_model = None

def _load_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_FILE) if os.path.exists(MODEL_FILE) else train_model()
    return _model

def predict(attendance, study_hours, internal_marks, assignment_score, midterm_score, extracurricular):
    model = _load_model()
    study_norm  = min((study_hours / 60) * 100, 100)
    int_norm    = min((internal_marks / 50) * 100, 100)
    extra_norm  = min((extracurricular / 10) * 100, 100)
    norm = {"attendance": attendance, "study_hours_norm": study_norm,
            "internal_norm": int_norm, "assignment_score": assignment_score,
            "midterm_score": midterm_score, "extra_norm": extra_norm}
    X = np.array([[norm[f] for f in _feature_cols()]])
    label_idx    = int(model.predict(X)[0])
    probabilities = model.predict_proba(X)[0].tolist()
    risk_level   = LABELS[label_idx]
    composite    = round(sum(norm[k]*v for k,v in WEIGHTS.items()), 2)
    if risk_level == "High":
        grade="A"; risk_score=max(5, round(100-composite,1)); percentile=min(99,85+int((composite-72)/2))
    elif risk_level == "Medium":
        grade="B"; risk_score=round(100-composite,1); percentile=max(30,40+int((composite-48)/1.2))
    else:
        grade="C"; risk_score=max(50,round(100-composite,1)); percentile=max(5,int(composite*0.6))
    return {
        "risk_level": risk_level, "composite_score": composite,
        "predicted_grade": grade, "risk_score": risk_score, "percentile": percentile,
        "probabilities": {"Low": round(probabilities[0]*100,1),
                          "Medium": round(probabilities[1]*100,1),
                          "High": round(probabilities[2]*100,1)},
        "feature_scores": {
            "attendance": round(attendance,1), "study_hours": round(study_norm,1),
            "internal_marks": round(int_norm,1), "assignment_score": round(assignment_score,1),
            "midterm_score": round(midterm_score,1), "extracurricular": round(extra_norm,1),
        }
    }
