import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

POST_BODY_LIMIT = 500  # characters


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(255))

    discussion_posts: Mapped[list["DiscussionPost"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Stock(db.Model):
    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_price: Mapped[float] = mapped_column(Float)
    market_cap: Mapped[float] = mapped_column(Float)

    pe_ratio: Mapped[float | None] = mapped_column(Float)
    revenue: Mapped[float | None] = mapped_column(Float)
    revenue_growth: Mapped[float | None] = mapped_column(Float)
    profit_margins: Mapped[float | None] = mapped_column(Float)
    free_cashflow: Mapped[float | None] = mapped_column(Float)
    debt: Mapped[float | None] = mapped_column(Float)
    analyst_recommendation: Mapped[str | None] = mapped_column(String(50))
    price_target: Mapped[float | None] = mapped_column(Float)

    discussion_posts: Mapped[list["DiscussionPost"]] = relationship(
        back_populates="stock"
    )


class DiscussionPost(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    ticker: Mapped[str] = mapped_column(String(10), ForeignKey("stock.ticker"))
    body: Mapped[str] = mapped_column(String(POST_BODY_LIMIT))
    stance: Mapped[str] = mapped_column(String(7), default="neutral")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    author: Mapped["User"] = relationship(back_populates="discussion_posts")
    stock: Mapped["Stock"] = relationship(back_populates="discussion_posts")

    __table_args__ = (CheckConstraint("stance IN ('bullish', 'neutral', 'bearish')"),)


@app.post("/users")  # placeholder feel free to add more complex authentication
def create_user():
    data = request.get_json()

    if not data:
        return {"error": "JSON body required"}, 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return {"error": "username, email, and password are required"}, 400

    existing_user = db.session.scalar(
        db.select(User).where((User.username == username) | (User.email == email))
    )

    if existing_user:
        return {"error": "Username or email already exists"}, 409

    user = User(
        username=username,
        email=email,
        password="",
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }, 201


@app.post("/stock/<ticker>/discussion")
def create_post(ticker):
    stock = db.session.get(Stock, ticker.upper())

    if stock is None:
        return {"error": "Stock not found"}, 404

    data = request.get_json()

    if not data:
        return {"error": "JSON body required"}, 400

    user_id = data.get("user_id")
    body = data.get("body", "").strip()
    stance = data.get("stance", "neutral")

    user = db.session.get(User, user_id)

    if user is None:
        return {"error": "User not found"}, 404

    if not body:
        return {"error": "Post body cannot be empty"}, 400

    if len(body) > POST_BODY_LIMIT:
        return {"error": f"Post body cannot exceed {POST_BODY_LIMIT} characters"}, 400

    if stance not in ("bullish", "neutral", "bearish"):
        return {"error": "Invalid stance"}, 400

    post = DiscussionPost(
        author=user,
        stock=stock,
        body=body,
        stance=stance,
    )

    db.session.add(post)
    db.session.commit()

    return {
        "id": post.id,
        "ticker": post.ticker,
        "body": post.body,
        "stance": post.stance,
        "author": post.author.username,
        "created_at": post.created_at.isoformat(),
    }, 201


@app.get("/stock/<ticker>/discussion")
def get_posts(ticker):
    stock = db.session.get(Stock, ticker.upper())

    if stock is None:
        return {"error": "Stock not found"}, 404

    posts = db.session.scalars(
        db.select(DiscussionPost)
        .where(DiscussionPost.ticker == stock.ticker)
        .order_by(DiscussionPost.created_at.desc())
    ).all()

    return [
        {
            "id": post.id,
            "body": post.body,
            "stance": post.stance,
            "author": post.author.username,
            "created_at": post.created_at.isoformat(),
        }
        for post in posts
    ]


with app.app_context():
    db.create_all()

    aapl_stock = db.session.get(Stock, "AAPL")

    if not aapl_stock:
        aapl_stock = Stock(
            ticker="AAPL",
            last_updated=datetime.now(timezone.utc),
            current_price=333.26,
            market_cap=4_894_000_000_000,
        )

        db.session.add(aapl_stock)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
