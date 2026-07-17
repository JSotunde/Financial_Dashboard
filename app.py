from dotenv import load_dotenv
from flask_login import login_required
load_dotenv()
import os
from models import User
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from extensions import db, login_manager
from auth import auth_bp
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
db.init_app(app)
app.register_blueprint(auth_bp, url_prefix='/auth')
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
with app.app_context():
    db.create_all()
@app.route('/')
def index():
    return render_template('index.html')
@login_required
def dashboard():
    return render_template('dashboard.html')
if __name__ == '__main__':
    app.run(debug=True)

##Jacob : im gonna addd logout, and start working on backend (dashboard etc.)