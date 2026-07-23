import pandas as pd
import sqlite3

conn = sqlite3.connect("stocks.db")
df = pd.read_sql("SELECT * FROM stock_data", conn)
conn.close()

# Check basic info
print("Shape:", df.shape)           # should be ~1500 rows (6 tickers × 250 trading days)
print("Columns:", df.columns.tolist())
print("Tickers:", df["Ticker"].unique())
print("Date range:", df["date"].min(), "to", df["date"].max())
print(df.head())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Summary stats
print("\nClose price stats:")
print(df.groupby("Ticker")["close"].describe())

df.to_csv("stocks_data.csv", index=False)
print("CSV exported!")
