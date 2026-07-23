import hashlib
from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint

from extensions import db

POST_BODY_LIMIT = 500

ANIMAL_NAMES = [
    "Panda", "Otter", "Falcon", "Koala", "Lynx", "Heron", "Badger", "Ibex",
    "Raven", "Marlin", "Gecko", "Puffin", "Wombat", "Mongoose", "Bison",
    "Tapir", "Ocelot", "Narwhal", "Meerkat", "Kestrel", "Caracal", "Serval",
    "Toucan", "Peccary", "Antelope", "Cormorant", "Dingo", "Jackal",
    "Pangolin", "Quokka",
]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    has_seen_welcome = db.Column(db.Boolean, nullable=False, default=False)
    discussion_posts = db.relationship('DiscussionPost', back_populates='author', lazy=True, cascade="all, delete-orphan")
    watchlist_items = db.relationship('WatchlistItem', back_populates='user', lazy=True, cascade="all, delete-orphan")

    @property
    def anonymous_name(self):
        digest = hashlib.md5(str(self.id).encode()).hexdigest()
        index = int(digest, 16) % len(ANIMAL_NAMES)
        return f"Anonymous {ANIMAL_NAMES[index]}"


class Stock(db.Model):
    ticker = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_updated = db.Column(db.DateTime)
    news_last_updated = db.Column(db.DateTime)
    ai_summary = db.Column(db.Text)
    ai_summary_updated = db.Column(db.DateTime)
    current_price = db.Column(db.Float)
    change_percent = db.Column(db.Float, nullable=True)
    market_cap = db.Column(db.Float)
    pe_ratio = db.Column(db.Float)
    revenue = db.Column(db.Float)
    revenue_growth = db.Column(db.Float)
    profit_margins = db.Column(db.Float)
    free_cashflow = db.Column(db.Float)
    debt = db.Column(db.Float)
    analyst_recommendation = db.Column(db.String(50))
    price_target = db.Column(db.Float)
    discussion_posts = db.relationship('DiscussionPost', back_populates='stock', lazy=True, cascade="all, delete-orphan")
    watchlist_items = db.relationship('WatchlistItem', back_populates='stock', lazy=True, cascade="all, delete-orphan")
    historical_prices = db.relationship('HistoricalPrice', back_populates='stock', lazy=True, cascade="all, delete-orphan")
    news_articles = db.relationship('NewsArticle', back_populates='stock', lazy=True, cascade="all, delete-orphan")


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
        nullable=True
    )

    title = db.Column(db.String(300), nullable=False)
    source = db.Column(db.String(100))
    source_name = db.Column(db.String(100))
    url = db.Column(db.String(500), nullable=False, unique=True)
    published_at = db.Column(db.DateTime)
    fetched_at = db.Column(db.DateTime)

    stock = db.relationship("Stock", back_populates="news_articles")
