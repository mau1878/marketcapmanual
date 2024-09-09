import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from io import StringIO
from datetime import date, timedelta

# Streamlit app
st.title('Market Capitalization Plot Based on Shares Outstanding')

# Step 1: User input for shares outstanding data
st.subheader("Insert Quarterly Shares Outstanding Data (Date, Shares in Millions)")
example_data = """
2024-06-30\t54
2024-03-31\t54
2023-12-31\t55
2023-09-30\t55
2023-06-30\t55
2023-03-31\t55
2022-12-31\t55
2022-09-30\t55
2022-06-30\t55
2022-03-31\t55
2021-12-31\t56
2021-09-30\t57
2021-06-30\t56
2021-03-31\t58
2020-12-31\t58
2020-09-30\t63
2020-06-30\t63
2020-03-31\t56
2019-12-31\t68
2019-09-30\t73
2019-06-30\t73
2019-03-31\t74
2018-12-31\t81
2018-09-30\t80
2018-06-30\t81
2018-03-31\t83
2017-12-31\t79
2017-09-30\t77
2017-06-30\t77
2017-03-31\t77
2016-12-31\t69
2016-09-30\t68
2016-06-30\t68
2016-03-31\t68
2015-12-31\t64
2015-09-30\t63
2015-06-30\t63
2015-03-31\t62
2014-12-31\t59
2014-09-30\t57
2014-06-30\t53
2014-03-31\t53
2013-12-31\t53
2013-09-30\t53
2013-06-30\t53
2013-03-31\t53
2012-12-31\t62
2012-09-30\t53
2012-06-30\t52
2012-03-31\t70
2011-12-31\t53
2011-09-30\t49
2011-06-30\t61
2011-03-31\t74
"""
input_data = st.text_area("Enter the data in the format `YYYY-MM-DD\tShares in Millions`", example_data, height=300)

# Clean and preprocess the data
def clean_data(data_str):
    data_str = data_str.strip()
    data = StringIO(data_str)
    try:
        df = pd.read_csv(data, sep='\t', names=['Date', 'SharesOutstanding'])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True)
        df['SharesOutstanding'] = df['SharesOutstanding'] * 1_000_000  # Convert to actual number of shares
        return df
    except Exception as e:
        st.error(f"Error processing data: {e}")
        return pd.DataFrame()

df_shares = clean_data(input_data)

# Step 2: Interpolate shares outstanding for daily data and fill forward the last available value for future dates
if not df_shares.empty:
    df_shares.set_index('Date', inplace=True)
    df_shares_daily = df_shares.resample('D').interpolate(method='linear')
    df_shares_daily = df_shares_daily.ffill()

    # Step 3: User selects the stock ticker, start, and end dates
    ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT)", 'AAPL')

    min_date = df_shares_daily.index.min().date()
    max_date = max(df_shares_daily.index.max().date(), date.today())

    # Allow user to pick an end date that includes today + 1 day
    today_plus_one = date.today() + timedelta(days=1)

    start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=today_plus_one)
    end_date = st.date_input("End Date", today_plus_one, min_value=min_date, max_value=today_plus_one)

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Step 4: Fetch stock prices using yfinance for the selected date range
    if st.button('Fetch Data and Plot'):
        stock_data = yf.download(ticker, start=start_date, end=end_date)

        if 'Adj Close' in stock_data.columns:
            stock_data['Price'] = stock_data['Adj Close']
        else:
            stock_data['Price'] = stock_data['Close']

        # Step 5: Merge stock prices with shares outstanding
        stock_data.index = pd.to_datetime(stock_data.index)
        df_merged = pd.merge(stock_data[['Price']], df_shares_daily, left_index=True, right_index=True, how='left')
        df_merged['SharesOutstanding'].fillna(method='ffill', inplace=True)

        # Step 6: Calculate market capitalization
        df_merged['MarketCap'] = df_merged['Price'] * df_merged['SharesOutstanding']

        # Step 7: Plot the data using Plotly Graph Objects for dual axes
        fig = go.Figure()

        # Plot Market Capitalization on primary y-axis
        fig.add_trace(go.Scatter(x=df_merged.index, y=df_merged['MarketCap'], name='Market Cap', yaxis='y1', line=dict(color='blue')))

        # Plot Price evolution on secondary y-axis
        fig.add_trace(go.Scatter(x=df_merged.index, y=df_merged['Price'], name='Price', yaxis='y2', line=dict(color='green', dash='dot')))

        # Update layout for dual y-axes and watermark
        fig.update_layout(
            title=f'Market Capitalization and Price Evolution of {ticker}',
            yaxis=dict(
                title='Market Cap',
                titlefont=dict(color='blue'),
                tickfont=dict(color='blue'),
            ),
            yaxis2=dict(
                title='Price',
                titlefont=dict(color='green'),
                tickfont=dict(color='green'),
                overlaying='y',
                side='right'
            ),
            annotations=[
                dict(
                    text="MTaurus - X: MTaurus_ok",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    xanchor="center", yanchor="middle",
                    opacity=0.1,
                    font=dict(size=60, color="lightgrey"),
                    showarrow=False
                )
            ]
        )

        st.plotly_chart(fig)
