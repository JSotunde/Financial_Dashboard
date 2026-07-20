from datetime import datetime, timedelta, timezone

from extensions import db
from financial_data import get_news, get_stock_data
from models import NewsArticle

PRICE_CACHE_DURATION = timedelta(hours=1)
HISTORY_CACHE_DURATION = timedelta(hours=24)
NEWS_CACHE_DURATION = timedelta(hours=4)

def get_or_refresh_stock(stock):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if stock.last_updated is not None and stock.last_updated + PRICE_CACHE_DURATION > now:
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

        stock.last_updated = now

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

def get_or_refresh_historical_data(stock):
    # refresh and save historical prices once Sugra is in place
    return stock.historical_prices
