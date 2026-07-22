from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from extensions import db
from financial_data import get_global_news, get_news, get_stock_data
from gemini import gemini_eval
from models import NewsArticle, Stock

PRICE_CACHE_DURATION = timedelta(hours=1)
HISTORY_CACHE_DURATION = timedelta(hours=24)
NEWS_CACHE_DURATION = timedelta(hours=8)
AI_SUMMARY_CACHE_DURATION = timedelta(days=1)


def is_market_open(now):
    eastern_now = now.astimezone(ZoneInfo("America/New_York"))

    if eastern_now.weekday() >= 5:
        return False

    if eastern_now.hour < 9 or eastern_now.hour >= 16:
        return False

    if eastern_now.hour == 9 and eastern_now.minute < 30:
        return False

    return True

def get_or_create_stock(ticker):
    ticker = ticker.upper().strip()
    stock = db.session.get(Stock, ticker)
    if stock:
        return stock

    stock_data = get_stock_data(ticker)
    if not stock_data:
        return None

    stock = Stock(
        ticker=ticker,
        name=stock_data['name'],
        last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
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
    return stock

def get_or_refresh_stock(stock):
    now = datetime.now(timezone.utc)
    current_time = now.replace(tzinfo=None)

    if stock.last_updated is not None and stock.last_updated + PRICE_CACHE_DURATION > current_time:
        return stock

    if not is_market_open(now):
        return stock

    try:
        data = get_stock_data(stock.ticker)

        stock.current_price = data.get("currentPrice")
        stock.change_percent = data.get("changePercent")
        stock.market_cap = data.get("marketCap")
        stock.pe_ratio = data.get("trailingPE")
        stock.revenue = data.get("totalRevenue")
        stock.revenue_growth = data.get("revenueGrowth")
        stock.profit_margins = data.get("profitMargins")
        stock.free_cashflow = data.get("freeCashflow")
        stock.debt = data.get("totalDebt")
        stock.analyst_recommendation = data.get("recommendationKey")
        stock.price_target = data.get("targetMeanPrice")

        stock.last_updated = current_time

        db.session.commit()
        return stock

    except Exception:
        db.session.rollback()

        if stock.current_price is not None:
            return stock

        raise

def get_or_refresh_news(stock):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if (
        stock.news_last_updated is not None
        and stock.news_last_updated + NEWS_CACHE_DURATION > now
    ):
        return stock.news_articles

    cached_articles = list(stock.news_articles)

    try:
        news_data = get_news(stock.ticker)
        NewsArticle.query.filter_by(stock_ticker=stock.ticker).delete()
        new_articles = []

        for article_data in news_data:
            url = article_data["link"]
            if NewsArticle.query.filter_by(url=url).first():
                continue

            published_at = article_data.get("pubDate")
            if published_at:
                published_at = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                ).replace(tzinfo=None)

            article = NewsArticle(
                stock_ticker=stock.ticker,
                title=article_data["title"],
                source=article_data.get("source"),
                url=url,
                published_at=published_at,
            )
            db.session.add(article)
            new_articles.append(article)

        stock.news_last_updated = now
        db.session.commit()
        return new_articles

    except Exception:
        db.session.rollback()

        if cached_articles:
            return cached_articles

        raise

def get_or_refresh_global_news():
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    cached_articles = NewsArticle.query.filter_by(stock_ticker=None).all()

    last_fetched = max(
        (article.fetched_at for article in cached_articles if article.fetched_at is not None),
        default=None,
    )
    if last_fetched is not None and last_fetched + NEWS_CACHE_DURATION > now:
        return cached_articles

    try:
        news_data = get_global_news()
        NewsArticle.query.filter_by(stock_ticker=None).delete()
        new_articles = []

        for article_data in news_data["items"]:
            url = article_data["link"]
            if NewsArticle.query.filter_by(url=url).first():
                continue

            published_at = article_data.get("published")
            if published_at:
                published_at = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                ).replace(tzinfo=None)

            article = NewsArticle(
                stock_ticker=None,
                title=article_data["title"],
                source=article_data.get("source"),
                source_name=article_data.get("source_name"),
                url=url,
                published_at=published_at,
                fetched_at=now,
            )
            db.session.add(article)
            new_articles.append(article)

        db.session.commit()
        return new_articles

    except Exception:
        db.session.rollback()

        if cached_articles:
            return cached_articles

        raise

def get_or_refresh_ai_summary(stock):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if (
        stock.ai_summary_updated is not None
        and stock.ai_summary_updated + AI_SUMMARY_CACHE_DURATION > now
    ):
        return stock.ai_summary

    cached_summary = stock.ai_summary

    try:
        stock.ai_summary = gemini_eval(stock)
        stock.ai_summary_updated = now
        db.session.commit()
        return stock.ai_summary

    except Exception:
        db.session.rollback()

        if cached_summary is not None:
            return cached_summary

        raise

def get_or_refresh_historical_data(stock):
    # refresh and save historical prices once Sugra is in place
    return stock.historical_prices
