from flask import Flask, render_template, request, redirect, url_for
import pickle
import numpy as np
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# load model
model = pickle.load(open("model.pkl", "rb"))

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mysql@121",
    database="student_performance_system"
)
cursor = db.cursor()

# home route
@app.route("/")
def home():
    return render_template("index.html")

# predict page
@app.route("/predict-page")
def predict_page():
    return render_template("predict.html")

# prediction logic
@app.route("/predict", methods=["POST"])
def predict():
    try:
        name = request.form.get("name")
        attendance = float(request.form.get("attendance"))
        marks = float(request.form.get("marks"))
        assignment = float(request.form.get("assignment"))
        study_hours = float(request.form.get("study_hours"))

        features = np.array([[attendance, marks, assignment, study_hours]])
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0][1] * 100

        if probability >= 75:
            risk = "Low Risk"
            suggestion = "Keep up the great work!"
        elif probability >= 50:
            risk = "Medium Risk"
            suggestion = "Focus more on weak subjects and practice daily."
        else:
            risk = "High Risk"
            suggestion = "Immediate improvement needed. Increase study hours and attendance."

        return render_template(
            "result.html",
            name=name,
            risk=risk,
            probability=round(probability, 2),
            suggestion=suggestion
        )

    except Exception as e:
        return f"Error occurred: {str(e)}"