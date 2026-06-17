import streamlit as st
import pandas as pd
import yfinance as yf

def get_b3_tickers():
    # List of some common B3 tickers
    tickers = [
        'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
        'B3SA3.SA', 'BBAS3.SA', 'WEGE3.SA', 'RENT3.SA', 'SUZB3.SA'
    ]
    return sorted(tickers)

# Create the selectbox
selected_ticker = st.selectbox(
    'Select a B3 Stock',
    options=get_b3_tickers(),
    help='Choose a stock from B3 (Brazilian Stock Exchange)'
)

# Display the selected ticker
if selected_ticker:
    st.write(f'You selected: {selected_ticker}')