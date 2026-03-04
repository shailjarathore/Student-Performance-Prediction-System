CREATE DATABASE student_performance_db;
USE student_performance_db;

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    roll_number VARCHAR(30) NOT NULL UNIQUE,
    department VARCHAR(80) NOT NULL,
    year VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance FLOAT NOT NULL,
    study_hours FLOAT NOT NULL,
    internal_marks FLOAT NOT NULL,
    assignment_score FLOAT NOT NULL,
    midterm_score FLOAT NOT NULL,
    extracurricular FLOAT NOT NULL,
    composite_score FLOAT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    predicted_grade VARCHAR(5) NOT NULL,
    risk_score FLOAT NOT NULL,
    percentile INT NOT NULL,
    predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE INDEX idx_risk_level ON predictions (risk_level);
CREATE INDEX idx_student_id ON predictions (student_id);
CREATE INDEX idx_predicted_at ON predictions (predicted_at);