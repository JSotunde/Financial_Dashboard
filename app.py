import os
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db, login_manager
from auth import auth_bp
from models import User, Stock, DiscussionPost, WatchlistItem, POST_BODY_LIMIT
from stock_service import (
    get_or_refresh_global_news,
    get_or_refresh_historical_data,
    get_or_refresh_news,
    get_or_refresh_stock,
)
from financial_data import get_stock_data, get_news, get_global_news
def abbreviate_number(num):
    if not num:
        return "-"
    if num >= 1_000_000_000_000:
        return f"{num / 1_000_000_000_000:.2f}T"
    elif num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    return f"{num:,}"
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager.init_app(app)
login_manager.login_view = 'auth.login'
db.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')


@app.template_filter('money')
def money_filter(value):
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


@app.template_filter('num')
def num_filter(value):
    if value is None:
        return "N/A"
    return f"{value:,.2f}"


@app.template_filter('pct')
def pct_filter(value):
    if value is None:
        return "N/A"
    return f"{value:,.2f}%"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    for item in current_user.watchlist_items:
        item.stock = get_or_refresh_stock(item.stock)
    stocks = [item.stock for item in current_user.watchlist_items]
    global_news = get_or_refresh_global_news()
   
    return render_template('dashboard.html', stocks=stocks, global_news=global_news)

@app.route('/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    ticker = request.form.get('ticker', '').upper().strip()
    if not ticker:
        return {"error": "Ticker parameter is required"}, 400

    stock = db.session.get(Stock, ticker)
    
    if not stock:
        try:
            stock_data = get_stock_data(ticker)
        except Exception as e:
            print(f"Error occurred while fetching stock data for ticker '{ticker}': {str(e)}")
            flash(f"Error occurred while fetching stock data for ticker '{ticker}': {str(e)}", "error")
            return redirect(url_for('dashboard'))
        if not stock_data:
            flash(f"Stock data for ticker '{ticker}' not found! Try a different ticker.", "error")
            return redirect(url_for('dashboard'))
        print(stock_data)
        stock = Stock(
            ticker=ticker,
            name=stock_data['name'],
            last_updated=datetime.now(timezone.utc),
            current_price=stock_data.get('currentPrice'),
            change_percent=stock_data.get('changePercent'),
            market_cap=stock_data.get('marketCap'),
            pe_ratio=stock_data.get('trailingPE'),
            revenue=stock_data.get('totalRevenue'),
            revenue_growth=stock_data.get('revenueGrowth'),
            profit_margins=stock_data.get('profitMargins'),
            free_cashflow=stock_data.get('freeCashflow'),
            debt=stock_data.get('totalDebt'),
            analyst_recommendation=stock_data.get('recommendationKey'),
            price_target=stock_data.get('targetMeanPrice'),
        )
        db.session.add(stock)
        db.session.commit()
    stock = get_or_refresh_stock(stock)
    already_watched = WatchlistItem.query.filter_by(
        user_id=current_user.id, stock_ticker=stock.ticker
    ).first()
    if not already_watched:
        db.session.add(WatchlistItem(user_id=current_user.id, stock_ticker=stock.ticker))
        db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/watchlist/remove/<ticker>', methods=['POST'])
@login_required
def remove_from_watchlist(ticker):
    item = WatchlistItem.query.filter_by(
        user_id=current_user.id, stock_ticker=ticker.upper()
    ).first()
    if not item:
        return {"error": "Stock not found in watchlist"}, 404

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.post("/stock/<ticker>/discussion")
@login_required
def create_post(ticker):
    stock = db.session.get(Stock, ticker.upper())

    if stock is None:
        return {"error": "Stock not found"}, 404

    data = request.form

    body = data.get("body", "").strip()
    stance = data.get("stance", "neutral")

    if not body:
        flash("Post body cannot be empty", "error")
        return redirect(url_for("stock_details", ticker=stock.ticker))

    if len(body) > POST_BODY_LIMIT:
        message = f"Post body cannot exceed {POST_BODY_LIMIT} characters"
        flash(message, "error")
        return redirect(url_for("stock_details", ticker=stock.ticker))

    if stance not in ("bullish", "neutral", "bearish"):
        flash("Invalid stance", "error")
        return redirect(url_for("stock_details", ticker=stock.ticker))

    post = DiscussionPost(
        author=current_user,
        stock=stock,
        body=body,
        stance=stance,
    )

    db.session.add(post)
    db.session.commit()

    return redirect(url_for("stock_details", ticker=stock.ticker))

@app.get("/stock/<ticker>")
def stock_details(ticker):
    stock = db.session.get(Stock, ticker.upper())

    if stock is None:
        return {"error": "Stock not found"}, 404

    try:
        stock = get_or_refresh_stock(stock)
        historical_prices = get_or_refresh_historical_data(stock)
        news_articles = get_or_refresh_news(stock)
    except Exception as e:
        return {"error": "Unable to retrieve stock data: " + str(e)}, 503

    posts = db.session.scalars(
        db.select(DiscussionPost)
        .where(DiscussionPost.stock_ticker == stock.ticker)
        .order_by(DiscussionPost.created_at.desc())
    ).all()
    stock_news = get_or_refresh_news(stock)

    return render_template(
        "stock.html",
        stock=stock,
        historical_prices=historical_prices,
        news_articles=news_articles,
        posts=posts,
        stock_news=stock_news,
        post_body_limit=POST_BODY_LIMIT,
    )


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
