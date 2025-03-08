import streamlit as st
import os
import pandas as pd

st.title("Coleta Preço de Ativo")
st.header("Informações a respeito de fechamento e volume de algumas ações")

# Define a pasta onde estão os arquivos CSV
pasta_cotacoes = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cotacoes')
arquivos_csv = [f.replace('.csv', '') for f in os.listdir(pasta_cotacoes) if f.endswith('.csv')]
arquivos_csv.sort()

# Permite a escolha do ativo pelo usuário
ticker_simbolo = st.selectbox('Escolha o Ativo', arquivos_csv)

# Monta o caminho para o arquivo CSV correspondente
caminho_csv = os.path.join(pasta_cotacoes, ticker_simbolo + '.csv')

# Lê o arquivo CSV
tickerDF = pd.read_csv(caminho_csv)

# Se existir a coluna 'Date', converte para datetime e define como índice
if 'Date' in tickerDF.columns:
    tickerDF['Date'] = pd.to_datetime(tickerDF['Date'], errors='coerce')
    tickerDF = tickerDF.dropna(subset=['Date'])  # Remove linhas com datas inválidas
    tickerDF.set_index('Date', inplace=True)
    tickerDF.sort_index(inplace=True)

# Converte a coluna 'Close' para numérico (se existir) e remove valores nulos
if 'Close' in tickerDF.columns:
    tickerDF['Close'] = pd.to_numeric(tickerDF['Close'], errors='coerce')
    dados_close = tickerDF['Close'].dropna()
else:
    dados_close = None

st.write("Visualizando os dados:", tickerDF.head())

# Plota o gráfico de fechamento, se houver dados
if dados_close is not None and not dados_close.empty:
    st.header("Gráfico de Fechamento")
    st.line_chart(dados_close)
else:
    st.write("Coluna 'Close' não encontrada ou sem dados.")

# Gráfico de Volume
if 'Volume' in tickerDF.columns:
    tickerDF['Volume'] = pd.to_numeric(tickerDF['Volume'], errors='coerce')
    dados_volume = tickerDF['Volume'].dropna()
    if not dados_volume.empty:
        st.header("Gráfico de Volume")
        st.line_chart(dados_volume)
    else:
        st.write("Coluna 'Volume' sem dados válidos.")
else:
    st.write("Coluna 'Volume' não encontrada.")

# Gráfico de Dividendos
if 'Dividends' in tickerDF.columns:
    tickerDF['Dividends'] = pd.to_numeric(tickerDF['Dividends'], errors='coerce')
    dados_dividends = tickerDF['Dividends'].dropna()
    if not dados_dividends.empty:
        st.header("Gráfico de Dividendos")
        st.line_chart(dados_dividends)
    else:
        st.write("Coluna 'Dividends' sem dados válidos.")
else:
    st.write("Dados de dividendos não disponíveis.")
