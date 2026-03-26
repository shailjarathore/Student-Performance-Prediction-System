class Config:
    #Security
    SECRET_KEY = "nexus-project"
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:@localhost/student_performance_db"
    )

    # Disable event tracking
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MODEL_PATH = "ml/model.pkl"
