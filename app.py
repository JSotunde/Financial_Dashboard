from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'
class Stock(db.Model):
    ticker = db.Column(db.String(10), primary_key=True)
    last_updated = db.Column(db.DateTime, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    market_cap = db.Column(db.Float, nullable=False)
    pe_ratio = db.Column(db.Float, nullable=False)
    revenue = db.Column(db.Float, nullable=False)
    revenue_growth = db.Column(db.Float, nullable=False)
    profit_margins = db.Column(db.Float, nullable=False)
    free_cashflow = db.Column(db.Float, nullable=False)
    debt = db.Column(db.Float, nullable=False)
    analyst_recommendation = db.Column(db.String(50), nullable=False)
    price_target = db.Column(db.Float, nullable=False)




## we need to add dynamic app routes for each ticker
#