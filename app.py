from flask import Flask, render_template
from flask_cors import CORS
from config import Config
from extensions import db
from routes.reports import report_bp
from routes.batch  import batch_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.route("/")
    def index():
        return render_template("index.html")

    db.init_app(app)

    from routes.predict import predict_bp
    app.register_blueprint(predict_bp, url_prefix="/api/predict")
    app.register_blueprint(report_bp)
    app.register_blueprint(batch_bp)

    with app.app_context():
        db.create_all()
        print("Database tables created / verified.")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)