from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint

from extensions import db

POST_BODY_LIMIT = 500


watchlist = db.Table(
    'watchlist',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('stock_ticker', db.String(10), db.ForeignKey('stock.ticker'), primary_key=True),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    discussion_posts = db.relationship('DiscussionPost', back_populates='author', lazy=True, cascade="all, delete-orphan")
    watchlist = db.relationship('Stock', secondary=watchlist, back_populates='watched_by', lazy=True)


class Stock(db.Model):
    ticker = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    change_percent = db.Column(db.Float, nullable=True)
    market_cap = db.Column(db.Float, nullable=False)
    pe_ratio = db.Column(db.Float, nullable=False)
    revenue = db.Column(db.Float, nullable=False)
    revenue_growth = db.Column(db.Float, nullable=False)
    profit_margins = db.Column(db.Float, nullable=False)
    free_cashflow = db.Column(db.Float, nullable=False)
    debt = db.Column(db.Float, nullable=False)
    analyst_recommendation = db.Column(db.String(50), nullable=False)
    price_target = db.Column(db.Float, nullable=False)
    discussion_posts = db.relationship('DiscussionPost', back_populates='stock', lazy=True, cascade="all, delete-orphan")
    watched_by = db.relationship('User', secondary=watchlist, back_populates='watchlist', lazy=True)


class DiscussionPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_ticker = db.Column(db.String(10), db.ForeignKey('stock.ticker'), nullable=False)
    body = db.Column(db.String(POST_BODY_LIMIT), nullable=False)
    stance = db.Column(db.String(10), nullable=False, default='neutral')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    author = db.relationship('User', back_populates='discussion_posts')
    stock = db.relationship('Stock', back_populates='discussion_posts')
    __table_args__ = (CheckConstraint("stance IN ('bullish', 'neutral', 'bearish')"),)
