import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask_login import login_required
load_dotenv()
import os
from models import User
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()


from extensions import db, login_manager
from auth import auth_bp
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
db.init_app(app)
POST_BODY_LIMIT = 500 
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
if __name__ == '__main__':
    app.run(debug=True)

##Jacob : im gonna addd logout, and start working on backend (dashboard etc.)