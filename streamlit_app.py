import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(
    page_title="Stock Analytics Dashboard",
    page_icon="📈",
    layout="wide"
)

# ── Load data from yFinance (works on Streamlit Cloud) ──────
@st.cache_data(ttl=3600)
def load_from_yfinance():
    TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "TCS.NS", "INFY.NS"]
    all_data = []
    for t in TICKERS:
        df = yf.Ticker(t).history(period="1y")
        df["Ticker"] = t
        all_data.append(df)
    combined = pd.concat(all_data).reset_index()

    # Fix date column — remove timezone for clean string
    combined["Date"] = pd.to_datetime(
        combined["Date"], utc=True
    ).dt.strftime("%Y-%m-%d")

    # Rename columns to lowercase to match rest of code
    combined.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume"
    }, inplace=True)

    # Calculate indicators
    combined = combined.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    combined["daily_return"] = (
        combined.groupby("Ticker")["close"].pct_change() * 100
    )
    combined["ma_20"] = combined.groupby("Ticker")["close"].transform(
        lambda x: x.rolling(20).mean()
    )
    combined["ma_50"] = combined.groupby("Ticker")["close"].transform(
        lambda x: x.rolling(50).mean()
    )
    combined["volatility_30d"] = combined.groupby("Ticker")["daily_return"].transform(
        lambda x: x.rolling(30).std()
    )
    combined["daily_range"] = combined["high"] - combined["low"]
    return combined

# ── Load data ────────────────────────────────────────────────
with st.spinner("Loading live stock data... please wait"):
    df = load_from_yfinance()

# ── Sidebar ──────────────────────────────────────────────────
st.sidebar.title("📈 Stock Dashboard")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", [
    "📊 Overview",
    "📉 Technical Analysis",
    "🔍 Comparison",
    "💼 Portfolio P&L"
])
st.sidebar.markdown("---")
st.sidebar.caption("Built by Vivek Sable")
st.sidebar.caption("github.com/07viveksable")

TICKERS = df["Ticker"].unique().tolist()

# ════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ════════════════════════════════════════════════════
if page == "📊 Overview":
    st.title("📊 Stock Market Overview")

    ticker = st.selectbox("Select ticker", TICKERS)
    period = st.slider("Days to show", 30, 365, 180)

    filtered = df[df["Ticker"] == ticker].tail(period).copy()
    latest   = filtered.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price",  f"${latest['close']:.2f}")
    col2.metric("Daily Return",   f"{latest['daily_return']:.2f}%",
                delta=f"{latest['daily_return']:.2f}%")
    col3.metric("MA20",           f"${latest['ma_20']:.2f}")
    col4.metric("30D Volatility", f"{latest['volatility_30d']:.2f}%")

    st.markdown("---")

    fig = px.line(
        filtered, x="Date",
        y=["close", "ma_20", "ma_50"],
        title=f"{ticker} — Price with Moving Averages (1 Year)",
        labels={"value": "Price", "variable": "Indicator"},
        color_discrete_map={
            "close": "#1565C0",
            "ma_20": "#2E7D32",
            "ma_50": "#E65100"
        }
    )
    fig.update_layout(hovermode="x unified", plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(
        filtered.tail(60), x="Date", y="volume",
        title=f"{ticker} — Volume (Last 60 Trading Days)",
        color="volume", color_continuous_scale="Blues"
    )
    fig2.update_layout(plot_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════════════
# PAGE 2 — TECHNICAL ANALYSIS
# ════════════════════════════════════════════════════
elif page == "📉 Technical Analysis":
    st.title("📉 Technical Analysis")

    ticker   = st.selectbox("Select ticker", TICKERS)
    filtered = df[df["Ticker"] == ticker].copy().sort_values("Date")
    latest   = filtered.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    price_vs_ma = ((latest["close"] - latest["ma_20"]) / latest["ma_20"]) * 100
    col1.metric("Price vs MA20",    f"{price_vs_ma:.2f}%",
                delta=f"{price_vs_ma:.2f}%")
    col2.metric("30D Volatility",   f"{latest['volatility_30d']:.2f}%")
    col3.metric("Best Day Return",  f"{filtered['daily_return'].max():.2f}%")
    col4.metric("Worst Day Return", f"{filtered['daily_return'].min():.2f}%")

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        fig = px.scatter(
            filtered, x="daily_return", y="volume",
            title="Daily Return % vs Volume",
            color="daily_return",
            color_continuous_scale="RdYlGn",
            hover_data=["Date"]
        )
        fig.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        fig2 = px.area(
            filtered, x="Date", y="volatility_30d",
            title="30-Day Rolling Volatility",
            color_discrete_sequence=["#E65100"]
        )
        fig2.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Last 30 Trading Days")
    last30 = filtered.tail(30)[["Date","close","daily_return","ma_20"]].copy()
    last30.columns = ["Date", "Close", "Daily Return %", "MA20"]
    last30 = last30.sort_values("Date", ascending=False)

    def color_return(val):
        return f"background-color: {'#c8e6c9' if val > 0 else '#ffcdd2'}"

    styled = last30.style.map(color_return, subset=["Daily Return %"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════
# PAGE 3 — COMPARISON
# ════════════════════════════════════════════════════
elif page == "🔍 Comparison":
    st.title("🔍 All Stocks — Side by Side Comparison")

    summary = df.groupby("Ticker").agg(
        Avg_Return=("daily_return", "mean"),
        Avg_Volatility=("volatility_30d", "mean")
    ).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(summary, x="Ticker", y="Avg_Return",
                     title="Average Daily Return by Stock",
                     color="Avg_Return",
                     color_continuous_scale="RdYlGn")
        fig.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(summary, x="Ticker", y="Avg_Volatility",
                      title="Average 30D Volatility by Stock",
                      color="Avg_Volatility",
                      color_continuous_scale="Reds")
        fig2.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(df, x="Date", y="close", color="Ticker",
                   title="Price Movement — All Stocks (1 Year)")
    fig3.update_layout(hovermode="x unified", plot_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Monthly Return Heatmap")
    df["Month"] = pd.to_datetime(df["Date"]).dt.strftime("%b %Y")
    heatmap_df = df.groupby(["Ticker","Month"])["daily_return"].mean().reset_index()
    heatmap_pivot = heatmap_df.pivot(
        index="Ticker", columns="Month", values="daily_return"
    )
    fig4 = px.imshow(heatmap_pivot,
                     color_continuous_scale="RdYlGn",
                     title="Monthly Avg Return Heatmap",
                     aspect="auto")
    st.plotly_chart(fig4, use_container_width=True)

# ════════════════════════════════════════════════════
# PAGE 4 — PORTFOLIO P&L
# ════════════════════════════════════════════════════
elif page == "💼 Portfolio P&L":
    st.title("💼 Simulated Portfolio P&L Tracker")
    st.caption("Note: Buy prices are simulated for demonstration purposes.")

    portfolio = {
        "AAPL":    {"shares": 10, "buy_price": 165.0},
        "MSFT":    {"shares":  5, "buy_price": 380.0},
        "GOOGL":   {"shares":  8, "buy_price": 140.0},
        "TSLA":    {"shares": 15, "buy_price": 200.0},
        "TCS.NS":  {"shares": 20, "buy_price": 3500.0},
        "INFY.NS": {"shares": 30, "buy_price": 1500.0},
    }

    latest_prices = df.sort_values("Date").groupby("Ticker")["close"].last()

    rows = []
    for t, d in portfolio.items():
        cur       = latest_prices.get(t, d["buy_price"])
        invested  = d["shares"] * d["buy_price"]
        cur_value = d["shares"] * cur
        pnl       = cur_value - invested
        pnl_pct   = (pnl / invested) * 100
        rows.append({
            "Ticker":        t,
            "Shares":        d["shares"],
            "Buy Price":     round(d["buy_price"], 2),
            "Current Price": round(cur, 2),
            "Invested":      round(invested, 2),
            "Current Value": round(cur_value, 2),
            "P&L":           round(pnl, 2),
            "P&L %":         round(pnl_pct, 2)
        })

    port_df        = pd.DataFrame(rows)
    total_invested = port_df["Invested"].sum()
    total_value    = port_df["Current Value"].sum()
    total_pnl      = total_value - total_invested
    total_pnl_pct  = (total_pnl / total_invested) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Invested", f"${total_invested:,.0f}")
    col2.metric("Current Value",  f"${total_value:,.0f}")
    col3.metric("Total P&L",      f"${total_pnl:,.0f}",
                delta=f"${total_pnl:,.0f}")
    col4.metric("P&L %",          f"{total_pnl_pct:.2f}%",
                delta=f"{total_pnl_pct:.2f}%")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(port_df, values="Invested", names="Ticker",
                     title="Portfolio Allocation", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(port_df, x="Ticker", y="P&L %",
                      title="P&L % by Stock",
                      color="P&L %",
                      color_continuous_scale="RdYlGn")
        fig2.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Full Portfolio Breakdown")
    st.dataframe(port_df, use_container_width=True, hide_index=True)
