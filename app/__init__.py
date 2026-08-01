from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    db.init_app(app)

    from app.auth.routes import auth_bp
    from app.exams.routes import exams_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(exams_bp)

    @app.route('/')
    def home():
        from flask import render_template
        return render_template('home.html')

    return app