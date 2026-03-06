class Config:
    #Security
    SECRET_KEY = "nexus-project"
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:Mysql%40121@localhost:3306/student_performance_db"
    )

    # Disable event tracking
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MODEL_PATH = "ml/model.pkl"
