import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime

TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "TCS.NS", "INFY.NS"]

def fetch_and_store():
    all_data = []

    for ticker in TICKERS:
        print(f"Fetching {ticker}...")
        stock = yf.Ticker(ticker)

        df = stock.history(period="1y")
        df["Ticker"] = ticker

        info = stock.info
        df["Sector"] = info.get("sector", "Unknown")
        df["MarketCap"] = info.get("marketCap", 0)

        all_data.append(df)

    # Combine all tickers
    combined = pd.concat(all_data)
    combined = combined.reset_index()

    # FIX: Safely convert Date no matter what format it arrives in
    combined["Date"] = pd.to_datetime(combined["Date"], utc=True).dt.strftime("%Y-%m-%d")

    combined.rename(columns={
        "Date": "date", "Open": "open", "High": "high",
        "Low": "low", "Close": "close", "Volume": "volume"
    }, inplace=True)

    # Keep only needed columns
    combined = combined[["date", "Ticker", "open", "high", "low",
                          "close", "volume", "Sector", "MarketCap"]]

    # Calculate indicators
    combined = combined.sort_values(["Ticker", "date"]).reset_index(drop=True)

    combined["daily_return"] = (
        combined.groupby("Ticker")["close"].pct_change() * 100
    )
    combined["ma_20"] = (
        combined.groupby("Ticker")["close"]
        .transform(lambda x: x.rolling(20).mean())
    )
    combined["ma_50"] = (
        combined.groupby("Ticker")["close"]
        .transform(lambda x: x.rolling(50).mean())
    )
    combined["volatility_30d"] = (
        combined.groupby("Ticker")["daily_return"]
        .transform(lambda x: x.rolling(30).std())
    )
    combined["daily_range"] = combined["high"] - combined["low"]

    # Round all float columns to 4 decimal places
    float_cols = ["open", "high", "low", "close", "daily_return",
                  "ma_20", "ma_50", "volatility_30d", "daily_range"]
    combined[float_cols] = combined[float_cols].round(4)

    # Save to SQLite
    conn = sqlite3.connect("stocks.db")
    combined.to_sql("stock_data", conn, if_exists="replace", index=False)
    conn.close()

    # Save to CSV for Power BI
    combined.to_csv("stocks_data.csv", index=False)

    print(f"\nDone! Saved {len(combined)} rows at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tickers: {list(combined['Ticker'].unique())}")
    print(f"Date range: {combined['date'].min()} to {combined['date'].max()}")
    print(combined[["date", "Ticker", "close", "ma_20", "daily_return"]].tail(6))

fetch_and_store()