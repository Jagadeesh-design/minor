import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="Stock Dashboard", layout="wide")


st.markdown("""
**Tips:**
- Use the date inputs in the sidebar to adjust the time period.
- Select multiple metrics in the dropdown to compare different indicators.
- Use the range slider below the chart to zoom in/out.
- Toggle technical indicators in the sidebar for technical analysis.
""")
st.markdown("---")
# Title of dashboard
st.title("📈 Interactive Stock Market Dashboard")

# Sidebar controls
st.sidebar.title("⚙️ Controls")
raw_ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL)", "AAPL")
ticker = raw_ticker.strip().split()[0]  # Take first ticker if multiple are entered
start_date = st.sidebar.date_input("Start Date", datetime(2020, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.today())

# Add technical indicators
st.sidebar.subheader("Technical Indicators")
show_sma = st.sidebar.checkbox("Simple Moving Average (50 days)")
show_ema = st.sidebar.checkbox("Exponential Moving Average (20 days)")
show_rsi = st.sidebar.checkbox("Relative Strength Index (RSI)")

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data(ticker, start, end):
    """Fetch stock data from Yahoo Finance"""
    try:
        data = yf.download(ticker, start=start, end=end)
        if not data.empty:
            # Calculate technical indicators
            if show_sma:
                data['SMA_50'] = data['Close'].rolling(window=50).mean()
            if show_ema:
                data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
            if show_rsi:
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
            return data
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Load data
df = load_data(ticker, start_date, end_date)

# Flatten multi-index if present
df.columns = df.columns.get_level_values(0)

# Main display area
if not df.empty:
    # Display metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("First Date", df.index.min().strftime('%Y-%m-%d'))
    with col2:
        st.metric("Last Date", df.index.max().strftime('%Y-%m-%d'))
    with col3:
        latest_close = float(df['Close'].iloc[-1])
        previous_close = float(df['Close'].iloc[-2]) if len(df) > 1 else latest_close
        
        # Fix: Ensure previous_close is a scalar value
        if previous_close != 0:
            change = ((latest_close - previous_close) / previous_close) * 100
        else:
            change = 0.0
            
        st.metric("Latest Close Price", f"${latest_close:.2f}", f"{change:.2f}%")

    # Interactive price chart
    st.subheader(f"{ticker} Stock Analysis")
    
    # Select features to plot
    available_features = [col for col in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'SMA_50', 'EMA_20', 'RSI'] if col in df.columns]
    
    selected_features = st.multiselect(
        "Select metrics to visualize:",
        options=available_features,
        default=['Close'] if 'Close' in available_features else []
    )

    # Create interactive Plotly chart
    if selected_features:
        fig = px.line(df, x=df.index, y=selected_features, 
                      title=f"{ticker} Stock Price History",
                      labels={'value': 'Price (USD)', 'variable': 'Metric'},
                      template='plotly_dark')
        
        # Add range slider
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

    # Display raw data
    if st.checkbox("Show Raw Data"):
        st.subheader("Raw Data")
        st.dataframe(df.sort_index(ascending=False).style.format({
            'Open': '{:.2f}',
            'High': '{:.2f}',
            'Low': '{:.2f}',
            'Close': '{:.2f}',
            'Adj Close': '{:.2f}',
            'Volume': '{:,}'
        }))

    # Additional metrics
    st.subheader("Key Statistics")
    cols = st.columns(4)
    with cols[0]:
        st.metric("52 Week High", f"${float(df['High'].max()):.2f}")
    with cols[1]:
        st.metric("52 Week Low", f"${float(df['Low'].min()):.2f}")
    with cols[2]:
        st.metric("Average Volume", f"{float(df['Volume'].mean()):,.0f}")
    with cols[3]:
        st.metric("Current Volume", f"{float(df['Volume'].iloc[-1]):,.0f}")

else:
    st.warning("Please enter a valid stock ticker and date range")



