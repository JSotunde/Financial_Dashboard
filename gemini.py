from google import genai
from google.genai import types
import os

def gemini_eval(stock):
    if not stock:
        return "No stock data available for evaluation."
    prompt = f"""
    You are a financial analyst. Based on the following stock data, provide a BRIEF (3 mini paragraph) evaluation of the stock's performance and potential investment value. Provide a summary of the stock's strengths and weaknesses,
    and a recommendation on whether to buy, hold, or sell the stock. However, your audience is new to the stock market, and you are part of an app meant to help new investors understand metrics and make informed decisions. However, do not mention that. State your final recommendation in plain english.
 Use the following data:
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


def gemini_suggestion(stocks):
    if not stocks:
        return "No stocks in your watchlist yet, add some to get a suggestion."

    watchlist_lines = "\n".join(
        f"- {stock.name} ({stock.ticker}): Price {stock.current_price}, P/E {stock.pe_ratio}, "
        f"Market Cap {stock.market_cap}, Analyst Recommendation {stock.analyst_recommendation}, "
        f"Target Price {stock.price_target}"
        for stock in stocks
    )

    prompt = f"""
    You are a financial analyst. A user is looking at their stock watchlist below and wants two NEW stock picks:
    one "safer bet" (a lower-risk, more conservative pick) and one "higher risk" pick (higher risk, higher
    potential reward). Do NOT recommend any stock that is already on the watchlist below - both picks must be
    different stocks the user does not already have. Using up-to-date market information, pick one stock for
    each category. For each pick, give ONLY the stock's name, its ticker, and 1-2 brief sentences on why it fits
    that category. Do not add any other commentary. Format your response exactly like this:

    Safer bet: <Name> (<Ticker>) - <1-2 sentences>
    Higher risk: <Name> (<Ticker>) - <1-2 sentences>

    Watchlist (do not recommend any of these, and do not add any commentary about them, the user is already tracking them):
    {watchlist_lines}
    """
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        interaction = client.interactions.create(
            model="gemini-3.1-flash-lite",
            input=prompt,
        )
        return interaction.output_text

    except Exception as e:
        gemini_output = f"Error during suggestion: {str(e)}"
        return gemini_output