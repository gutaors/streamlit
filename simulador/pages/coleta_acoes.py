# EXEMPLO DO CURSO DA UDEMY
#streamlit run coleta_acoes.py

import streamlit as st
import os
import yfinance as yf
import pandas as pd
from datetime import datetime

st.title("Coleta Preço de Ativo")
st.header("Informações a respeito de fechamento e volume de algumas ações")

# ENBR3.SA
# BBAS3.SA
# BBDC4.SA
# PETR4.SA
# VALE3.SA

opcoes = st.selectbox(
    'Escolha o Ativo',
    ('ENBR3.SA','BBAS3.SA', 'BBDC4.SA', 'PETR4.SA', 'VALE3.SA')
)

#tickersimbolo = "PETR4.SA"
tickersimbolo = opcoes

tickerdata = yf.Ticker(tickersimbolo)


tickerDF = tickerdata.history(period='1d', start = '2009-5-9', end = '2022-5-19')

#Open High Low Close Volume Dividends Stock

st.header ("Gráfico de Fechamento")
st.line_chart (tickerDF.Close)

st.header ("Gráfico de Volume")
st.line_chart (tickerDF.Volume)


st.header ("Gráfico de Dividendos")
st.line_chart (tickerDF.Dividends)
