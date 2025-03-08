import streamlit as st
import os
import yfinance as yf
import pandas as pd
from datetime import datetime

st.title("Coleta Preço de Ativo")
st.header("Informações a respeito de fechamento e volume de algumas ações")

# Obtém a lista de arquivos CSV da pasta cotacoes
pasta_cotacoes = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cotacoes')
arquivos_csv = [f.replace('.csv', '') for f in os.listdir(pasta_cotacoes) if f.endswith('.csv')]
arquivos_csv.sort()  # Ordena a lista alfabeticamente

opcoes = st.selectbox(
    'Escolha o Ativo',
    arquivos_csv
)

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
