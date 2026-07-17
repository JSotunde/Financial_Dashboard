from flask_login import UserMixin
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
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
