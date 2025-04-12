import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
import pytz

# Set page configuration
st.set_page_config(page_title="Stock Dashboard", layout="wide")

# Tips
st.markdown("""
**Tips:**
- Use the date inputs in the sidebar to adjust the time period.
- Select multiple metrics in the dropdown to compare different indicators.
- Use the range slider below the chart to zoom in/out.
- Toggle technical indicators in the sidebar for technical analysis.
""")
st.markdown("---")

# Title
st.title("📈 Interactive Stock Market Dashboard")

# Sidebar
st.sidebar.title("⚙️ Controls")
raw_ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL)", "AAPL")
ticker = raw_ticker.strip().split()[0]
start_date = st.sidebar.date_input("Start Date", datetime(2020, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now(pytz.timezone('US/Eastern')).date())

# Indicators
st.sidebar.subheader("Technical Indicators")
show_sma = st.sidebar.checkbox("Simple Moving Average (50 days)")
show_ema = st.sidebar.checkbox("Exponential Moving Average (20 days)")
show_rsi = st.sidebar.checkbox("Relative Strength Index (RSI)")

# Data loader
@st.cache_data(ttl=3600)
def load_data(ticker, start_str, end_str):
    try:
        data = yf.download(ticker, start=start_str, end=end_str)
        return data if not data.empty else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_data(ticker, str(start_date), str(end_date))

# Flatten multi-index
if not df.empty and isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Add indicators
if not df.empty:
    if show_sma:
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
    if show_ema:
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    if show_rsi:
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

    df.dropna(inplace=True)  # drop NaNs from indicators

# Main area
if not df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("First Date", df.index.min().strftime('%Y-%m-%d'))
    with col2:
        st.metric("Last Date", df.index.max().strftime('%Y-%m-%d'))
    with col3:
        latest_close = df['Close'].iloc[-1]
        previous_close = df['Close'].iloc[-2] if len(df) > 1 else latest_close
        change = ((latest_close - previous_close) / previous_close) * 100 if previous_close != 0 else 0.0
        st.metric("Latest Close Price", f"${latest_close:.4f}", f"{change:.2f}%")

    st.subheader(f"{ticker} Stock Analysis")

    # Auto-select default features
    available_features = [col for col in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'SMA_50', 'EMA_20', 'RSI'] if col in df.columns]
    default_features = ['Close']
    if show_sma: default_features.append('SMA_50')
    if show_ema: default_features.append('EMA_20')
    if show_rsi: default_features.append('RSI')

    selected_features = st.multiselect(
        "Select metrics to visualize:",
        options=available_features,
        default=default_features
    )

    if selected_features:
        fig = px.line(df, x=df.index, y=selected_features,
                      title=f"{ticker} Stock Price History",
                      labels={'value': 'Price (USD)', 'variable': 'Metric'},
                      template='plotly_dark')
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one metric to visualize.")

    if st.checkbox("Show Raw Data"):
        st.subheader("Raw Data")
        st.dataframe(df.sort_index(ascending=False).style.format({
            'Open': '{:.4f}',
            'High': '{:.4f}',
            'Low': '{:.4f}',
            'Close': '{:.4f}',
            'Adj Close': '{:.4f}',
            'Volume': '{:,}',
            'SMA_50': '{:.4f}' if 'SMA_50' in df.columns else None,
            'EMA_20': '{:.4f}' if 'EMA_20' in df.columns else None,
            'RSI': '{:.2f}' if 'RSI' in df.columns else None
        }))

    # Statistics
    st.subheader("Key Statistics")
    cols = st.columns(4)
    with cols[0]:
        st.metric("52 Week High", f"${df['High'].max():.4f}")
    with cols[1]:
        st.metric("52 Week Low", f"${df['Low'].min():.4f}")
    with cols[2]:
        st.metric("Average Volume", f"{df['Volume'].mean():,.0f}")
    with cols[3]:
        st.metric("Current Volume", f"{df['Volume'].iloc[-1]:,.0f}")

else:
    st.warning("Please enter a valid stock ticker and date range.")
