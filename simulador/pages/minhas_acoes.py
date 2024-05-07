# FALTA FAZER

# o valor que paguei foi x
# o valor máximo foi x em data tal
# mes com maior volume negociado, volume e média diária
# o mês com melhor mediana foi tal, mediana tal
# o mês com pior mediana foi tal, mediana tal
# se vale mostrar valor do minério
# se petrobras mostrar valor do petroleo
# média móvel com setinha para 1 mes
# média móvel com setinha para 3 meses


# Tabela com meus tickers
# Quando teve a maior média móvel nos últimos cinco anos
# # Quando teve a menor média móvel nos últimos cinco anos
# qual ação minha que está dando mais lucro hoje
# qual ação minha que está dando mais preju hoje

import yfinance as yf
from datetime import date, datetime, timedelta
import os
import pandas as pd
import plotly.graph_objs as go
import streamlit as st
from streamlit_option_menu import option_menu
import yfinance as yf

# importei depois
import pandas_datareader.data as web
import matplotlib.pyplot as plt

# from fbprophet import Prophet
import os

# Crie uma lista vazia para armazenar os DataFrames de cotações
df_list = []


# Criando a sidebar
# st.sidebar.markdown("[Clique aqui para abrir o Simulador](./simulador.py)")


st.sidebar.header("Escolha a ação")

n_dias = st.slider("Quantidade de dias de previsão", 30, 365)

# Criando a sidebar DATAS
st.sidebar.header("Filtros")


# codigo do dashboard
st.title("Minhas ações")


def pegar_dados_acoes(arquivo, sep):
    # path = "\\wsl.localhost\Ubuntu\home\gutao\dev\streamlit_docker\acoes\acoes.csv"
    path = "dados/" + arquivo
    return pd.read_csv(path, delimiter=sep)


df_tickers = pegar_dados_acoes("tickers.csv", ";")
tickers = df_tickers["ticker"].tolist()


# PEGA DADOS DOS TICKERS A PARTIR DE 2015


# Definindo o período de tempo desejado
start_date = "2015-01-01"
end_date = pd.Timestamp.today().strftime("%Y-%m-%d")

# ESCREVER COTACOES

# Dicionário para armazenar os DataFrames de cotações
quotes = {}

# Pegar csv cotacoes
df_cotacoes = pegar_dados_acoes("cotacoes.csv", ",")

# Se precisar carregar todos os tickers novamente descomentar e executar este código

# Baixar cotações para cada ticker na lista

# for ticker in tickers:
#    data = yf.download(ticker, start=start_date, end=end_date)
#    quotes[ticker] = data

# Concatenar os DataFrames em um DataFrame único
# df_cotacoes = pd.concat(quotes.values(), keys=quotes.keys(), names=['Ticker', 'Date'])

# Resetar o índice
# df_cotacoes.reset_index(inplace=True)

# Salvar em um arquivo CSV
# df_cotacoes.to_csv('dados/cotacoes.csv', index=False)

# Verificar o DataFrame
# print(df_cotacoes.tail())


# Converter a coluna 'Date' para o formato de data
df_cotacoes["Date"] = pd.to_datetime(df_cotacoes["Date"])

datamax = df_cotacoes["Date"].max()
# datamax = datetime.strptime(datamax, "%Y-%m-%d")

ontem = datetime.now() - timedelta(days=1)
encontrou = False

# Verificar se existe cotação para uma data maior do que datamax para os tickers da lista
if datamax.date() < ontem.date():
    for ticker in tickers:
        # Baixar cotações para o ticker
        data = yf.download(
            ticker, start=(datamax + pd.Timedelta(days=1)), end=pd.Timestamp.today()
        )
        # Se houver dados e a data máxima for menor do que a data mais recente dos dados, exibir as cotações
        if not data.empty and data.index.max() > datamax:
            print(f"Existe cotação para o ticker {ticker} após a data máxima:")
            print(data)
            encontrou = True

# Se não encontrou cotações após a data máxima, imprimir mensagem
if not encontrou:
    print(
        "Não foram encontradas cotações após a data máxima para os tickers fornecidos."
    )
    encontrou = False

if encontrou:
    for ticker in tickers:
        data = yf.download(
            ticker, start=datamax, end=datetime.today().strftime("%Y-%m-%d")
        )
        data["Ticker"] = ticker  # Adicionar coluna com o ticker para identificação
        df_cotacoes = pd.concat([df_cotacoes, data], ignore_index=False)
df_tickers

# ANALISES

st.title("Análises das suas ações")

# Convertendo a coluna 'Date' para o tipo datetime
df_cotacoes["Date"] = pd.to_datetime(df_cotacoes["Date"])

# Formatando as datas para exibir apenas a data
df_cotacoes["Date"] = df_cotacoes["Date"].dt.date

# Calculando a média móvel de 15 períodos para cada ticker
df_cotacoes["Media_Movel_15"] = df_cotacoes.groupby("Ticker")["Close"].transform(
    lambda x: x.rolling(window=15).mean()
)

# Encontrando a data e o valor da maior média móvel de 15 períodos
maior_media_movel = df_cotacoes.groupby("Ticker")["Media_Movel_15"].max()
data_maior_media_movel = (
    df_cotacoes.loc[
        df_cotacoes["Media_Movel_15"].isin(maior_media_movel), ["Ticker", "Date"]
    ]
    .groupby("Ticker")
    .first()
)
maior_media_movel_valor = maior_media_movel.rename("Maior_Media_Movel_15")

# Encontrando a data e o valor da menor média móvel de 15 períodos
menor_media_movel = df_cotacoes.groupby("Ticker")["Media_Movel_15"].min()
data_menor_media_movel = (
    df_cotacoes.loc[
        df_cotacoes["Media_Movel_15"].isin(menor_media_movel), ["Ticker", "Date"]
    ]
    .groupby("Ticker")
    .first()
)
menor_media_movel_valor = menor_media_movel.rename("Menor_Media_Movel_15")

# Encontrando o maior e menor valor do período
maior_valor_periodo = df_cotacoes.groupby("Ticker")["Close"].max()
menor_valor_periodo = df_cotacoes.groupby("Ticker")["Close"].min()
data_maior_valor_periodo = (
    df_cotacoes.loc[df_cotacoes["Close"].isin(maior_valor_periodo), ["Ticker", "Date"]]
    .groupby("Ticker")
    .first()
)
data_menor_valor_periodo = (
    df_cotacoes.loc[df_cotacoes["Close"].isin(menor_valor_periodo), ["Ticker", "Date"]]
    .groupby("Ticker")
    .first()
)

# Calculando o lucro/prejuízo
lucro_prejuizo = df_cotacoes.groupby("Ticker").apply(
    lambda x: x["Close"].iloc[-1] - x["Close"].iloc[0]
)

# Criando um DataFrame com os resultados
df_analises = pd.DataFrame(
    {
        "Ticker": df_cotacoes["Ticker"].unique(),
        #   "Quantidade": analises[
        #       "quantidade"
        #   ],  # Adicionando a coluna quantidade do df_minhas_acoes
        "Dt_Maior_MM_15": data_maior_media_movel["Date"].values,
        "Maior_MM_15": maior_media_movel_valor.values,
        "Dt_Menor_MM_15": data_menor_media_movel["Date"].values,
        "Menor_MM_15": menor_media_movel_valor.values,
        "Maior_Val_Periodo": maior_valor_periodo.values,
        "Dt_Maior_Val_Periodo": data_maior_valor_periodo["Date"].values,
        "Menor_Val_Periodo": menor_valor_periodo.values,
        "Dt_Menor_Val_Periodo": data_menor_valor_periodo["Date"].values,
        "Lucro_Prejuizo": lucro_prejuizo.values,
    }
)


# Função para formatar datas
def formatar_data(data):
    return pd.to_datetime(data).strftime("%d/%m/%Y")


# Função para formatar valores
def formatar_valor(valor):
    return "{:,.2f}".format(valor).replace(",", "").replace(".", ",")


def aplicar_formatacao(df, colunas, funcao):
    for coluna in colunas:
        df[coluna] = df[coluna].apply(funcao)


# Lista de colunas que você deseja formatar
colunas_para_formatar = [
    "Maior_MM_15",
    "Menor_MM_15",
    "Maior_Val_Periodo",
    "Menor_Val_Periodo",
    "Lucro_Prejuizo",
]

# Chamada da função para aplicar a formatação
aplicar_formatacao(df_analises, colunas_para_formatar, formatar_valor)

# Lista de colunas que você deseja formatar
colunas_para_formatar = [
    "Dt_Maior_MM_15",
    "Dt_Menor_MM_15",
    "Dt_Maior_Val_Periodo",
    "Dt_Menor_Val_Periodo",
]

aplicar_formatacao(df_analises, colunas_para_formatar, formatar_data)

df_analises
