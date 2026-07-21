from google import genai
from google.genai import types
import os

def gemini_eval(stock_data):
    if not stock_data:
        return "No stock data available for evaluation."
    prompt = f"""
    You are a financial analyst. Based on the following stock data, provide a concise evaluation of the stock's performance and potential investment value. Provide a summary of the stock's strengths and weaknesses,
    and a recommendation on whether to buy, hold, or sell the stock. If hold, please recommend when to sell. Use the following data:
    Current Price: {stock_data['currentPrice']}
    Market Cap: {stock_data['marketCap']}
    P/E Ratio: {stock_data['trailingPE']}
    Total Revenue: {stock_data['totalRevenue']}
    Revenue Growth: {stock_data['revenueGrowth']}
    Profit Margins: {stock_data['profitMargins']}
    Free Cash Flow: {stock_data['freeCashflow']}
    Total Debt: {stock_data['totalDebt']}
    Analyst Recommendation: {stock_data['recommendationKey']}
    Target Mean Price: {stock_data['targetMeanPrice']}
    """
    try:
        client = genai.Client(api_key=os.getenv('GEMINI_API'))
        response = client.models.generate_content(model = 'gemini-3.1-flash-lite',
                                                  contents = prompt)
        gemini_output = response.text()
    except Exception as e:
        gemini_output = f"Error during evaluation: {str(e)}"