from google import genai
from google.genai import types
import os

def gemini_eval(stock):
    if not stock:
        return "No stock data available for evaluation."
    prompt = f"""
    You are a financial analyst. Based on the following stock data, provide a BRIEF (3 mini paragraph) evaluation of the stock's performance and potential investment value. Provide a summary of the stock's strengths and weaknesses,
    and a recommendation on whether to buy, hold, or sell the stock. If hold, please recommend when to sell. Use the following data:
    Name {stock.name}
    Current Price: {stock.current_price}
    Market Cap: {stock.market_cap}
    P/E Ratio: {stock.pe_ratio}
    Total Revenue: {stock.revenue}
    Revenue Growth: {stock.revenue_growth}
    Profit Margins: {stock.profit_margins}
    Free Cash Flow: {stock.free_cashflow}
    Total Debt: {stock.debt}
    Analyst Recommendation: {stock.analyst_recommendation}
    Target Mean Price: {stock.price_target}
    """
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        interaction = client.interactions.create(
            model="gemini-3.1-flash-lite",
            input=prompt,
        )
        return interaction.output_text
        
    except Exception as e:
        gemini_output = f"Error during evaluation: {str(e)}"
        return gemini_output