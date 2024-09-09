import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from io import StringIO

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

# Convert the input data to a DataFrame
data = StringIO(input_data)
df_shares = pd.read_csv(data, sep='\t', names=['Date', 'SharesOutstanding'])
df_shares['Date'] = pd.to_datetime(df_shares['Date'])
df_shares['SharesOutstanding'] = df_shares['SharesOutstanding'] * 1_000_000  # Convert to actual number of shares

# Step 2: Interpolate shares outstanding for daily data
df_shares.set_index('Date', inplace=True)
df_shares_daily = df_shares.resample('D').interpolate(method='linear')

# Step 3: Fetch stock prices using yfinance
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT)", 'AAPL')
start_date = df_shares_daily.index.min()
end_date = df_shares_daily.index.max()

if st.button('Fetch Data and Plot'):
    stock_data = yf.download(ticker, start=start_date, end=end_date)

    if 'Adj Close' in stock_data.columns:
        stock_data['Price'] = stock_data['Adj Close']
    else:
        stock_data['Price'] = stock_data['Close']

    # Step 4: Merge stock prices with shares outstanding
    stock_data.index = pd.to_datetime(stock_data.index)
    df_merged = pd.merge(stock_data[['Price']], df_shares_daily, left_index=True, right_index=True, how='inner')

    # Step 5: Calculate market capitalization
    df_merged['MarketCap'] = df_merged['Price'] * df_merged['SharesOutstanding']

    # Step 6: Plot the data using Plotly
    fig = px.line(df_merged, x=df_merged.index, y='MarketCap', title=f'Market Capitalization of {ticker}')
    st.plotly_chart(fig)
