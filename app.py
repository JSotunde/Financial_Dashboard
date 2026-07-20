import os
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required

from extensions import db, login_manager
from auth import auth_bp
from models import User, Stock, DiscussionPost, POST_BODY_LIMIT

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
    return render_template('dashboard.html', stocks = current_user.watchlist)

@app.route('/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    ticker = request.form.get('ticker', '').upper().strip()
    if not ticker:
        return {"error": "Ticker parameter is required"}, 400

    stock = db.session.get(Stock, ticker)
    if not stock:
        get_stock_data = __import__('financial_data').get_stock_data
        stock_data = get_stock_data(ticker)
        if not stock_data:
            flash(f"Stock data for ticker '{ticker}' not found! Try a different ticker.", "error")
            return redirect(url_for('dashboard'))
        print(stock_data)
        stock = Stock(
            ticker=ticker,
            name=stock_data['name'],
            last_updated=datetime.now(timezone.utc),
            current_price=stock_data['currentPrice'],
            change_percent=stock_data['changePercent'],
            market_cap=stock_data['marketCap'],
            pe_ratio=stock_data['trailingPE'],
            revenue=stock_data['totalRevenue'],
            revenue_growth=stock_data['revenueGrowth'],
            profit_margins=stock_data['profitMargins'],
            free_cashflow=stock_data['freeCashflow'],
            debt=stock_data['totalDebt'],
            analyst_recommendation=stock_data['recommendationKey'],
            price_target=stock_data['targetMeanPrice'],
        )
        db.session.add(stock)
        db.session.commit()

    current_user.watchlist.append(stock)
    db.session.commit()
    return redirect(url_for('dashboard'))
    

@app.route('/watchlist/remove/<ticker>', methods=['POST'])
@login_required
def remove_from_watchlist(ticker):
    stock = db.session.get(Stock, ticker.upper())
    if not stock:
        return {"error": "Stock not found"}, 404

    current_user.watchlist.remove(stock)
    db.session.commit()

    return redirect(url_for('dashboard'))

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


if __name__ == '__main__':
    app.run(debug=True)
