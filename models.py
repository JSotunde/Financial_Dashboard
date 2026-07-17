from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint

from extensions import db

POST_BODY_LIMIT = 500


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    discussion_posts = db.relationship('DiscussionPost', back_populates='author', lazy=True, cascade="all, delete-orphan")
    watchlist_items = db.relationship('WatchlistItem', back_populates='user', lazy=True, cascade="all, delete-orphan")


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
    discussion_posts = db.relationship('DiscussionPost', back_populates='stock', lazy=True, cascade="all, delete-orphan")
    watchlist_items = db.relationship('WatchlistItem', back_populates='stock', lazy=True, cascade="all, delete-orphan")
    historical_prices = db.relationship('HistoricalPrice', back_populates='stock', lazy=True, cascade="all, delete-orphan")


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

class WatchlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stock_ticker = db.Column(db.String(10), db.ForeignKey("stock.ticker"), nullable=False)

    user = db.relationship("User", back_populates="watchlist_items")
    stock = db.relationship("Stock", back_populates="watchlist_items")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "stock_ticker",
        ),
    )

class HistoricalPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    stock_ticker = db.Column(db.String(10), db.ForeignKey("stock.ticker"), nullable=False)

    date = db.Column(db.Date, nullable=False)
    close = db.Column(db.Float, nullable=False)

    stock = db.relationship("Stock", back_populates="historical_prices")

    __table_args__ = (
        db.UniqueConstraint(
            "stock_ticker",
            "date",
        ),
    )

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    stock_ticker = db.Column(
        db.String(10),
        db.ForeignKey("stock.ticker"),
        nullable=False
    )

    title = db.Column(db.String(300), nullable=False)
    source = db.Column(db.String(100))
    url = db.Column(db.String(500), nullable=False, unique=True)
    published_at = db.Column(db.DateTime)