from flask import Blueprint, request, jsonify
from extensions import db
from models import Student, Prediction
from ml.predictor import predict as ml_predict

predict_bp = Blueprint("predict", __name__)

def ok(data, code=200):
    return jsonify({"success": True, "data": data}), code

def err(msg, code=400):
    return jsonify({"success": False, "error": msg}), code

def _validate(val, name, lo, hi):
    if val is None:
        return f"'{name}' is required"
    try:
        val = float(val)
    except (TypeError, ValueError):
        return f"'{name}' must be a number"
    if not (lo <= val <= hi):
        return f"'{name}' must be between {lo} and {hi}"
    return None


@predict_bp.route("/", methods=["POST"])
def run_prediction():
    body = request.get_json()
    if not body:
        return err("JSON body required")

    for f in ("name", "roll_number", "department", "year"):
        if not body.get(f):
            return err(f"'{f}' is required")

    checks = [
        ("attendance",       0, 100),
        ("study_hours",      0,  60),
        ("internal_marks",   0,  50),
        ("assignment_score", 0, 100),
        ("midterm_score",    0, 100),
        ("extracurricular",  0,  10),
    ]
    for name, lo, hi in checks:
        e = _validate(body.get(name), name, lo, hi)
        if e:
            return err(e)

    roll = body["roll_number"].strip().upper()
    student = Student.query.filter_by(roll_number=roll).first()
    if not student:
        student = Student(
            name=body["name"].strip(),
            roll_number=roll,
            department=body["department"].strip(),
            year=body["year"].strip()
        )
        db.session.add(student)
        db.session.flush()

    result = ml_predict(
        attendance=float(body["attendance"]),
        study_hours=float(body["study_hours"]),
        internal_marks=float(body["internal_marks"]),
        assignment_score=float(body["assignment_score"]),
        midterm_score=float(body["midterm_score"]),
        extracurricular=float(body["extracurricular"]),
    )

    prediction = Prediction(
        student_id=student.id,
        attendance=float(body["attendance"]),
        study_hours=float(body["study_hours"]),
        internal_marks=float(body["internal_marks"]),
        assignment_score=float(body["assignment_score"]),
        midterm_score=float(body["midterm_score"]),
        extracurricular=float(body["extracurricular"]),
        composite_score=result["composite_score"],
        risk_level=result["risk_level"],
        predicted_grade=result["predicted_grade"],
        risk_score=result["risk_score"],
        percentile=result["percentile"],
    )
    db.session.add(prediction)
    db.session.commit()

    return ok({
        "prediction_id":   prediction.id,
        "student":         student.to_dict(),
        "result":          result,
        "recommendations": _recommendations(result["risk_level"]),
        "saved_to_db":     True,
    }, 201)


def _recommendations(level):
    if level == "High":
        return [
            {"icon": "star",     "title": "Maintain Momentum",      "detail": "Keep study habits and attendance consistent throughout the semester."},
            {"icon": "book",     "title": "Pursue Advanced Study",   "detail": "Explore research papers, electives, and competitive exams in your domain."},
            {"icon": "users",    "title": "Peer Mentoring",          "detail": "Mentoring at-risk peers reinforces your own learning."},
            {"icon": "trophy",   "title": "Enter Competitions",      "detail": "Hackathons and project expos strengthen your academic profile."},
        ]
    elif level == "Medium":
        return [
            {"icon": "calendar", "title": "Structure Your Schedule", "detail": "Create a daily timetable with dedicated study blocks per subject."},
            {"icon": "check",    "title": "Submit All Assignments",   "detail": "Assignment scores carry 20% weight — consistency moves you up a tier."},
            {"icon": "chat",     "title": "Faculty Office Hours",     "detail": "Visit faculty to clarify doubts proactively before exams."},
            {"icon": "chart",    "title": "Target Internal Marks",    "detail": "A 10-point improvement in internals can change your risk level."},
        ]
    else:
        return [
            {"icon": "alert",    "title": "Immediate Faculty Alert",  "detail": "Notify your academic advisor now. Early action dramatically improves outcomes."},
            {"icon": "clock",    "title": "2 Hours Daily Minimum",    "detail": "Commit to focused daily study. Reduce all distractions."},
            {"icon": "school",   "title": "Remedial Classes",         "detail": "Enroll in remedial sessions offered by your department."},
            {"icon": "heart",    "title": "Student Support Centre",   "detail": "Low performance often has personal causes. Reach out to counselling."},
        ]