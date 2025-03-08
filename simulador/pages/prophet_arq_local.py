import streamlit as st
import pandas as pd
import os
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go
from datetime import date

# Pasta onde os arquivos de cotações estão armazenados
PASTA_COTACOES = "cotacoes"

# Listar os arquivos disponíveis na pasta de cotações
def listar_tickers_disponiveis():
    arquivos = [f for f in os.listdir(PASTA_COTACOES) if f.endswith(".csv")]
    tickers = [arquivo.replace(".csv", "") for arquivo in arquivos]
    return tickers

import pandas as pd
import yfinance as yf

import pandas as pd
import os

def carregar_dados(ticker, dt_inicial, dt_final):
    caminho_arquivo = os.path.join("cotacoes", f"{ticker}.csv")

    # Verificar se o arquivo existe
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo {caminho_arquivo} não encontrado.")

    # Carregar os dados do arquivo CSV
    df = pd.read_csv(caminho_arquivo, parse_dates=["Date"], index_col="Date")

    # Garantir que as colunas essenciais estão presentes
    colunas_esperadas = {"Close"}
    if not colunas_esperadas.issubset(df.columns):
        raise ValueError(f"O arquivo {caminho_arquivo} não contém as colunas necessárias: {colunas_esperadas}")

    # Filtrar pelo intervalo de datas
    df = df.loc[(df.index >= pd.to_datetime(dt_inicial)) & (df.index <= pd.to_datetime(dt_final))]

    return df



# Realizar previsão com Prophet
def prever_dados(df, periodo):
    df = df[["Close"]].copy()
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "ds", "Close": "y"}, inplace=True)

    modelo = Prophet()
    modelo.fit(df)

    datas_futuras = modelo.make_future_dataframe(periods=int(periodo) * 30)
    previsoes = modelo.predict(datas_futuras)
    return modelo, previsoes

# Interface do Streamlit
st.markdown("""
# Análise Preditiva
### Prevendo o valor de ações na Bolsa de Valores
""")

with st.sidebar:
    st.header("Menu")
    tickers_disponiveis = listar_tickers_disponiveis()
    ticker = st.selectbox("Selecione a ação:", tickers_disponiveis)
    dt_inicial = st.date_input("Data Inicial", value=date(2020, 1, 1))
    dt_final = st.date_input("Data Final")
    meses = st.number_input("Meses de Previsão", 1, 24, value=6)

# Converter dt_inicial e dt_final para string antes de passar para a função
dados = carregar_dados(ticker, str(dt_inicial), str(dt_final))


if dados is not None and not dados.empty:
    st.header(f"Dados da Ação - {ticker}")
    st.dataframe(dados)

    st.subheader("Variação no Período")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dados.index, y=dados["Close"], name="Close"))
    st.plotly_chart(fig)

    st.header(f"Previsão para os próximos {meses} meses")
    modelo, previsoes = prever_dados(dados, meses)
    fig = plot_plotly(modelo, previsoes, xlabel="Período", ylabel="Valor")
    st.plotly_chart(fig)

    # Formatando e exibindo previsões
    previsoes["ds"] = previsoes["ds"].dt.date
    previsoes = previsoes.sort_values(by="ds", ascending=False)
    st.dataframe(previsoes, width=800, height=400)
else:
    st.warning("Nenhum dado encontrado no período selecionado!")
