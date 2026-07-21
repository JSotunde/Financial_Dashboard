import requests
import os
params = {
    "fields": "currentPrice,marketCap,trailingPE,totalRevenue,revenueGrowth,profitMargins,freeCashflow,totalDebt,recommendationKey,targetMeanPrice"
}
headers = {
    "x-api-key": os.getenv('SUGRA_API')
}
commmon_stock_names = {
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla, Inc.",
    "TSM": "Taiwan Semiconductor Manufacturing Company Limited",
    "META": "Meta Platforms, Inc.",
    "NVDA": "NVIDIA Corporation",
    "SPCX": "Space Exploration Technologies Corp.",
    "NFLX": "Netflix, Inc.",
    "BRK.A": "Berkshire Hathaway Inc.",
    "JPM": "JPMorgan Chase & Co.",
}

def get_stock_data(ticker):
    url = f"https://sugra.ai/api/v2/quotes/{ticker}/info"
    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    if "data" not in json_data or not json_data["data"]:
        return None
    last_price_url = f"https://sugra.ai/api/v2/quotes/{ticker}/historical"
    last_price_response = requests.get(last_price_url, headers=headers)
    last_price_json = last_price_response.json()
    last_price = last_price_json["data"]["data"][-1]["close"]
    change_percent = ((response.json()["data"]["currentPrice"] - last_price) / last_price) * 100
    json_data["data"]["changePercent"] = change_percent
    
    if ticker in commmon_stock_names:
        json_data["data"]["name"] = commmon_stock_names[ticker]
    else:   
        name_url = f'https://sugra.ai/api/v1/fundamentals/{ticker}/profile'
        name_response = requests.get(name_url, headers=headers)
        json_data["data"]["name"] = name_response.json()["data"]["entity_name"]
    return json_data["data"]
def get_news(ticker):
    news_url = f"https://sugra.ai/api/v2/quotes/{ticker}/news"
    news_params = {
        "count": 5,}
    news_response = requests.get(news_url, headers=headers, params=news_params)
    return news_response.json()["data"]
def get_global_news():
    global_news_url = 'https://sugra.ai/api/v1/news/search'
    global_news_params = {
        "q": "stocks",
        "limit": 4,
    }
    global_news_response = requests.get(global_news_url, headers=headers, params=global_news_params)
    return global_news_response.json()["data"]