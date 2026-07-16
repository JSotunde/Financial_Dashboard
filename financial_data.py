import requests
import os
params = {
    "fields": "currentPrice,marketCap,trailingPE,totalRevenue,revenueGrowth,profitMargins,freeCashflow,totalDebt,recommendationKey,targetMeanPrice"
}
headers = {
    "x-api-key": os.getenv('SUGRA_API')
}

def get_stock_data(ticker):
    url = f"https://sugra.ai/api/v2/quotes/{ticker}"
    response = requests.get(url, headers=headers, params=params)
    return response.json()["data"]
def get_news(ticker):
    news_url = f"https://sugra.ai/api/v2/quotes/{ticker}/news"
    news_response = requests.get(news_url, headers=headers)
    return news_response.json()["data"]
