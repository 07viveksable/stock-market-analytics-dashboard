import pandas as pd
import sqlite3

# Simulate: "I bought these stocks 6 months ago"
portfolio = {
    "AAPL":   {"shares": 10, "buy_price": 165.0},
    "MSFT":   {"shares": 5,  "buy_price": 380.0},
    "GOOGL":  {"shares": 8,  "buy_price": 140.0},
    "TSLA":   {"shares": 15, "buy_price": 200.0},
    "TCS.NS": {"shares": 20, "buy_price": 3500.0},
    "INFY.NS":{"shares": 30, "buy_price": 1500.0},
}

conn = sqlite3.connect("stocks.db")
df = pd.read_sql("SELECT * FROM stock_data", conn)
conn.close()

# Get latest close price for each ticker
latest = df.sort_values("date").groupby("Ticker")["close"].last().reset_index()
latest.columns = ["Ticker", "current_price"]

rows = []
for ticker, details in portfolio.items():
    current = latest[latest["Ticker"]==ticker]["current_price"].values
    if len(current) == 0:
        continue
    cur_price = current[0]
    invested = details["shares"] * details["buy_price"]
    value_now = details["shares"] * cur_price
    pnl = value_now - invested
    pnl_pct = (pnl / invested) * 100
    rows.append({
        "Ticker": ticker,
        "Shares": details["shares"],
        "Buy Price": details["buy_price"],
        "Current Price": round(cur_price, 2),
        "Invested": round(invested, 2),
        "Current Value": round(value_now, 2),
        "P&L": round(pnl, 2),
        "P&L %": round(pnl_pct, 2),
    })

portfolio_df = pd.DataFrame(rows)
print(portfolio_df)

# Save for Power BI
portfolio_df.to_csv("portfolio.csv", index=False)
