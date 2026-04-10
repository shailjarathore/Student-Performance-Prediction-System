import os

class Config:
    SECRET_KEY = "nexus-project"
    SQLALCHEMY_DATABASE_URI = "sqlite:///site.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")