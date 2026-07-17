from datetime import datetime, timedelta, timezone

from extensions import db
from financial_data import get_stock_data

PRICE_CACHE_DURATION = timedelta(hours=1)
HISTORY_CACHE_DURATION = timedelta(hours=24)
NEWS_CACHE_DURATION = timedelta(hours=4)

def get_or_refresh_stock(stock):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if stock.last_updated is not None and stock.last_updated + PRICE_CACHE_DURATION > now:
        return stock

    try:
        data = get_stock_data(stock.ticker)

        stock.current_price = data.get("price")
        stock.market_cap = data.get("marketCap")
        stock.pe_ratio = data.get("peRatio")
        stock.revenue = data.get("revenue")
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