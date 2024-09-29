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
# aplicar_formatacao(df_analises, colunas_para_formatar, formatar_valor)

# Lista de colunas que você deseja formatar
colunas_para_formatar = [
    "Dt_Maior_MM_15",
    "Dt_Menor_MM_15",
    "Dt_Maior_Val_Periodo",
    "Dt_Menor_Val_Periodo",
]

# aplicar_formatacao(df_analises, colunas_para_formatar, formatar_data)
df_cotacoes
# for ticker in tickers:
#    df_tickers.loc[df_tickers["Ticker"] == ticker]


# Função para encontrar o valor máximo da coluna 'Adj Close' e a data correspondente para cada ticker
def encontrar_valor_maximo_com_data(df):
    max_values = df.groupby("Ticker").apply(lambda x: x.loc[x["Adj Close"].idxmax()])
    return max_values[["Adj Close", "Date"]]


# Títulos e subtítulos para a aplicação
st.title('Valores Máximos da Coluna "Adj Close" por Ticker')
st.subheader(
    'Valores máximos da coluna "Adj Close" e suas datas correspondentes para cada ticker no DataFrame:'
)

# Chamando a função para encontrar os valores máximos e as datas correspondentes
valores_maximos_com_data = encontrar_valor_maximo_com_data(df_cotacoes)

# Exibindo os valores máximos e as datas correspondentes
st.write(valores_maximos_com_data)
df_maximos = pd.DataFrame(valores_maximos_com_data)


# Função para encontrar o valor mínimo da coluna 'Adj Close' e a data correspondente para cada ticker
def encontrar_valor_minimo_com_data(df):
    min_values = df.groupby("Ticker").apply(lambda x: x.loc[x["Adj Close"].idxmin()])
    return min_values[["Adj Close", "Date"]]


# Títulos e subtítulos para a aplicação
st.title('Valores Minimos da Coluna "Adj Close" por Ticker')
st.subheader(
    'Valores minimos da coluna "Adj Close" e suas datas correspondentes para cada ticker no DataFrame:'
)

# Chamando a função para encontrar os valores máximos e as datas correspondentes
valores_minimos_com_data = encontrar_valor_minimo_com_data(df_cotacoes)

# Exibindo os valores máximos e as datas correspondentes
st.write(valores_minimos_com_data)
df_minimos = pd.DataFrame(valores_minimos_com_data)


# Calculando a média móvel de 20 dias (MM15) para cada ticker
df_cotacoes["MM15"] = df_cotacoes.groupby("Ticker")["Adj Close"].transform(
    lambda x: x.rolling(window=20).mean()
)


# Função para encontrar o valor máximo da MM15 e a data correspondente para cada ticker
#def encontrar_MM15_maximo_com_data(df):
   # max_values = df.groupby("Ticker").apply(lambda x: x.loc[x["MM15"].dropna().idxmax()] if x["MM15"].dropna().any() #else None)
def encontrar_MM15_maximo_com_data(df):
    print("DataFrame original:\n", df)
    max_values = df.groupby("Ticker").apply(lambda x: x.loc[x["MM15"].dropna().idxmax()] if x["MM15"].dropna().any() else None)
    print("Máximos encontrados:\n", max_values)
    return max_values



    #max_values = df.groupby("Ticker").apply(lambda x: x.loc[x["MM15"].idxmax()])
    return max_values[["MM15", "Date"]]


# Chamando a função para encontrar os valores máximos da MM15 e as datas correspondentes
MM15_maximos_com_data = encontrar_MM15_maximo_com_data(df_cotacoes)

# Criando um novo DataFrame com os valores máximos da MM15 e as datas correspondentes
df_MM15_maximos = pd.DataFrame(MM15_maximos_com_data)

# Títulos e subtítulos para a aplicação
st.title("Valores Máximos da Média Móvel de 20 dias (MM15) por Ticker")
st.subheader(
    "Valores máximos da MM15 e suas datas correspondentes para cada ticker no DataFrame:"
)

# Exibindo os valores máximos da MM15 e as datas correspondentes
st.write(df_MM15_maximos)


# Função para encontrar o valor minimo da MM15 e a data correspondente para cada ticker
def encontrar_MM15_minimo_com_data(df):
    print("DataFrame original:\n", df)
    min_values = df.groupby("Ticker").apply(lambda x: x.loc[x["MM15"].dropna().idxmin()] if not x["MM15"].dropna().empty else pd.Series())
    print("Mínimos encontrados:\n", min_values)
    return min_values



# Chamando a função para encontrar os valores máximos da MM15 e as datas correspondentes
MM15_minimos_com_data = encontrar_MM15_minimo_com_data(df_cotacoes)

# Criando um novo DataFrame com os valores máximos da MM15 e as datas correspondentes
df_MM15_minimos = pd.DataFrame(MM15_minimos_com_data)

# Títulos e subtítulos para a aplicação
st.title("Valores Minimos da Média Móvel de 20 dias (MM15) por Ticker")
st.subheader(
    "Valores minimos da MM15 e suas datas correspondentes para cada ticker no DataFrame:"
)

# Exibindo os valores máximos da MM15 e as datas correspondentes
st.write(df_MM15_minimos)


##JUNTANDO TUDO

# Juntando os DataFrames usando a coluna 'Ticker' como chave de junção
df_analises = pd.merge(
    df_tickers, df_maximos, left_index=True, right_index=True, how="inner"
)

# Títulos e subtítulos para a aplicação
st.title("Junção de DataFrames")
# st.subheader("DataFrame resultante da junção de df_tickers e df_maximos:")

# Exibindo o DataFrame resultante
st.write(df_analises)
