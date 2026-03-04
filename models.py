from extensions import db
from datetime import datetime

class Student(db.Model):
    __tablename__ = "students"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(30),  nullable=False, unique=True)
    department  = db.Column(db.String(80),  nullable=False)
    year        = db.Column(db.String(20),  nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    predictions = db.relationship(
        "Prediction", backref="student",
        lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id":          self.id,
            "name":        self.name,
            "roll_number": self.roll_number,
            "department":  self.department,
            "year":        self.year,
            "created_at":  self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<Student {self.roll_number} - {self.name}>"


#predictions
class Prediction(db.Model):
    __tablename__ = "predictions"

    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id       = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    # Input feature
    attendance       = db.Column(db.Float, nullable=False)   # 0-100 %
    study_hours      = db.Column(db.Float, nullable=False)   # hrs/week
    internal_marks   = db.Column(db.Float, nullable=False)   # out of 50
    assignment_score = db.Column(db.Float, nullable=False)   # 0-100 %
    midterm_score    = db.Column(db.Float, nullable=False)   # 0-100 %
    extracurricular  = db.Column(db.Float, nullable=False)   # 0-10 index

    # ML model output
    composite_score  = db.Column(db.Float,     nullable=False)  # 0-100
    risk_level       = db.Column(db.String(20), nullable=False)  # High/Medium/Low
    predicted_grade  = db.Column(db.String(5),  nullable=False)  # A/B/C/D
    risk_score       = db.Column(db.Float,      nullable=False)  # 0-100
    percentile       = db.Column(db.Integer,    nullable=False)  # estimated rank

    predicted_at     = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":               self.id,
            "student_id":       self.student_id,
            "student_name":     self.student.name        if self.student else None,
            "roll_number":      self.student.roll_number if self.student else None,
            "department":       self.student.department  if self.student else None,
            "year":             self.student.year        if self.student else None,
            "attendance":       self.attendance,
            "study_hours":      self.study_hours,
            "internal_marks":   self.internal_marks,
            "assignment_score": self.assignment_score,
            "midterm_score":    self.midterm_score,
            "extracurricular":  self.extracurricular,
            "composite_score":  self.composite_score,
            "risk_level":       self.risk_level,
            "predicted_grade":  self.predicted_grade,
            "risk_score":       self.risk_score,
            "percentile":       self.percentile,
            "predicted_at":     self.predicted_at.isoformat()
        }

    def __repr__(self):
        return f"<Prediction id={self.id} level={self.risk_level}>"
