import os
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request
from flask_login import login_required

from extensions import db, login_manager
from auth import auth_bp
from models import User, Stock, DiscussionPost, POST_BODY_LIMIT
from stock_service import get_or_refresh_stock

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager.init_app(app)
login_manager.login_view = 'auth.login'
db.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/dashboard')
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
        "ticker": post.stock_ticker,
        "body": post.body,
        "stance": post.stance,
        "author": post.author.email,
        "created_at": post.created_at.isoformat(),
    }, 201

@app.get("/stock/<ticker>")
def stock_details(ticker):
    stock = db.session.get(Stock, ticker.upper())

    if stock is None:
        return {"error": "Stock not found"}, 404

    try:
        stock = get_or_refresh_stock(stock)
    except Exception:
        return {"error": "Unable to retrieve stock data"}, 503

    return {
        "ticker": stock.ticker,
        "last_updated": (
            stock.last_updated.isoformat()
            if stock.last_updated
            else None
        ),
        "current_price": stock.current_price,
        "market_cap": stock.market_cap,
        "pe_ratio": stock.pe_ratio,
        "revenue": stock.revenue,
        "revenue_growth": stock.revenue_growth,
        "profit_margins": stock.profit_margins,
        "free_cashflow": stock.free_cashflow,
        "debt": stock.debt,
        "analyst_recommendation": stock.analyst_recommendation,
        "price_target": stock.price_target,
    }


@app.get("/stock/<ticker>/discussion")
def get_posts(ticker):
    stock = db.session.get(Stock, ticker.upper())

    if stock is None:
        return {"error": "Stock not found"}, 404

    posts = db.session.scalars(
        db.select(DiscussionPost)
        .where(DiscussionPost.stock_ticker == stock.ticker)
        .order_by(DiscussionPost.created_at.desc())
    ).all()

    return [
        {
            "id": post.id,
            "body": post.body,
            "stance": post.stance,
            "author": post.author.email,
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
            pe_ratio=34.5,
            revenue=391_000_000_000,
            revenue_growth=0.08,
            profit_margins=0.26,
            free_cashflow=99_000_000_000,
            debt=110_000_000_000,
            analyst_recommendation="buy",
            price_target=250.0,
        )

        db.session.add(aapl_stock)
        db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
