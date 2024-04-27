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

import streamlit as st
from streamlit_option_menu import option_menu
import yfinance as yf
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objs as go
import os

# importei depois
from datetime import datetime, timedelta
import pandas_datareader.data as web
import matplotlib.pyplot as plt

# from fbprophet import Prophet
# from fbprophet.plot import plot_plotly, plot_components_plotly
from plotly import graph_objs as go

# codigo para processar
df_tickers = pd.read_csv("tickers.csv", sep=";")
tickers = df_tickers["ticker"].tolist()

# Crie uma lista vazia para armazenar os DataFrames de cotações
df_list = []


# Criando a sidebar
# st.sidebar.markdown("[Clique aqui para abrir o Simulador](./simulador.py)")


st.sidebar.header("Escolha a ação")

n_dias = st.slider("Quantidade de dias de previsão", 30, 365)

# Criando a sidebar DATAS
st.sidebar.header("Filtros")


# codigo do dashboard
DATA_INICIO = "2015-01-05"
DATA_FIM = date.today().strftime("%Y-%m-%d")
st.title("Minhas ações")


def pegar_dados_acoes():
    # path = "\\wsl.localhost\Ubuntu\home\gutao\dev\streamlit_docker\acoes\acoes.csv"
    path = "./acoes.csv"
    return pd.read_csv(path, delimiter=";")


def pegar_minhas_acoes():
    # path = "\\wsl.localhost\Ubuntu\home\gutao\dev\streamlit_docker\acoes\acoes.csv"
    path = "./tickers.csv"
    return pd.read_csv(path, delimiter=";")


df = pegar_dados_acoes()
df_minhas_acoes = pegar_minhas_acoes()

acao = df["snome"]
nome_acao_escolhida = st.sidebar.selectbox("Escolha uma ação:", acao)

df_acao = df[df["snome"] == nome_acao_escolhida]
acao_escolhida = df_acao.iloc[0]["sigla_acao"]
acao_escolhida = acao_escolhida + ".SA"

ticker_selecionado = df_acao.iloc[0]["sigla_acao"] + ".SA"
acao_registro = df_minhas_acoes[df_minhas_acoes["ticker"] == ticker_selecionado]

# Verificar se há dados no DataFrame acao_registro
# if not acao_registro.empty:
#    data_registro = acao_registro.iloc[0]["data"]
#    data_compra_sim = data_registro
#    # Atualizar o valor do campo data_compra_sim na sidebar
#    st.sidebar.date_input(
#        "Data de Compra (Simulação)", value=pd.to_datetime(data_compra_sim)
#    )
# else:
# data_compra_sim = st.sidebar.date_input("Data de Compra (Simulação)")

# data_venda_sim = st.sidebar.date_input("Data de Venda (Simulação)")

# =================================================================================================
# Verificar se há dados no DataFrame acao_registro
# if not acao_registro.empty:
#    valor_registro = acao_registro.iloc[0]["investi"]
#    valor_registro = valor_registro.replace(",", ".")
#    valor_registro = float(valor_registro)

#    qtde_sim = acao_registro.iloc[0]["quantidade"]
#    qtde_sim = float(qtde_sim)
#    # Atualizar o valor do campo data_compra_sim na sidebar
#    valor_sim = st.sidebar.number_input("Valor:", value=valor_registro, step=0.01)
# else:
# valor_sim = st.sidebar.number_input("Valor:", value=1000.00, step=0.01)
# =================================================================================================


#############

# Simular a compra
# Filtrar o DataFrame com base na data de compra
#############+=============================================================================================
# Simular a Venda
# Filtrar o DataFrame com base na data de venda
# caso data de compra não tenha dados retrocede um dia até ter
# Obter o valor do Adj Close na data de venda

# ================================================================================================================================================

# Filtra as linhas correspondentes às datas de compra e venda

# Adicionar setas para cruzamentos

# modelo = Prophet()
# modelo.fit(df_treino)

# futuro = modelo.make_future_dataframe(periods=n_dias, freq='B')
# previsao = modelo.predict(futuro)

# st.subheader('Previsão')
# st.write(previsao[['ds', 'yhat','yhat_lower','yhat_upper' ]].tail(n_dias))

# grafico
# grafico1 = plot_plotly(modelo, previsao)
# st.plotly_chart(grafico1)

# grafico2
# grafico2 = plot_components_plotly(modelo, previsao)
# st.plotly_chart(grafico2)

# df_minhas_acoes["ticker"] = df_minhas_acoes["ticker"].str.replace(".SA", "")
# df_minhas_acoes["ticker"] = [
#    ticker[:-3] if ticker.endswith(".sa") else ticker
#    for ticker in df_minhas_acoes["ticker"]
# ]

ticker_selecionado = df_acao.iloc[0]["sigla_acao"]
if ticker_selecionado in df_minhas_acoes["ticker"].values:
    valor_pago = df_minhas_acoes[df_minhas_acoes["ticker"] == ticker_selecionado][
        "paguei"
    ].values[0]
    valor_maximo = df_valores["Close"].max()
    diferenca_valor_maximo = valor_maximo - float(valor_pago.replace(",", "."))
    valor_pago = float(valor_pago.replace(",", "."))
    st.subheader("Análise da Ação: " + nome_acao_escolhida)
    st.write("Ticker selecionado: " + ticker_selecionado)
    st.write("Valor Pago: R$ {:.2f}".format(valor_pago))
    st.write("Valor Máximo: R$ {:.2f}".format(valor_maximo))
    st.write(
        "Diferença entre Valor Máximo e Valor Pago: R$ {:.2f}".format(
            diferenca_valor_maximo
        )
    )

st.subheader("Valores em df_acao['sigla_acao']")
st.write(df_acao["sigla_acao"])

st.subheader("Valores em df_minhas_acoes['ticker']")
st.write(df_minhas_acoes["ticker"])

# Filtra os dados entre as datas da coluna 'data' em df_minhas_acoes e a data atual

data_inicio = datetime.now() - timedelta(
    days=30 * 12
)  # Subtrai 12 meses (aproximadamente 30 dias por mês)

data_atual = datetime.today().strftime("%Y%m%d")
data_fim = data_atual

# Agrupa por mês/ano e calcula a média de 'Adj Close'
# df_valores_filtrado["YearMonth"] = df_valores_filtrado["Date"].dt.to_period("M")
# media_por_mes = df_valores_filtrado.groupby("YearMonth")["Adj Close"].mean()

# Seleciona os três meses com maiores médias
# tres_meses_mais_altos = media_por_mes.nlargest(3)

st.subheader("Três meses com maiores médias de Adj Close:")
st.subheader("no último ano")

# for year_month, media in tres_meses_mais_altos.items():
#    st.write(f"Mês/Ano: {year_month}, Média: {media:.2f}")

# Seleciona os três meses com menores médias
# tres_meses_menos_altos = media_por_mes.nsmallest(3)

st.subheader("Três meses com menores médias de Adj Close:")
st.subheader("no último ano")
# for year_month, media in tres_meses_menos_altos.items():
#    st.write(f"Mês/Ano: {year_month}, Média: {media:.2f}")


st.header("Minhas Ações")

st.title("Minhas Ações")

# Seção de verificação de ação nos dois dataframes
st.subheader("Verificação de Ação")
ticker_selecionado = df_acao.iloc[0]["sigla_acao"]
ticker_selecionado = ticker_selecionado + ".SA"

if ticker_selecionado in df_minhas_acoes["ticker"].values:
    st.write("A ação selecionada está presente nos seus ativos.")
    # Filtra o registro da ação selecionada
    acao_registro = df_minhas_acoes[df_minhas_acoes["ticker"] == ticker_selecionado]

    # Exibe o registro da ação
    st.write("Registro da Ação:")
    st.write(acao_registro)

    # Obtém a data de hoje
    data_atual = datetime.today()

    # Obtém a quantidade do registro da ação selecionada
    quantidade = acao_registro["quantidade"].values[0]

    # Filtra os dados entre as datas da coluna 'data' em df_minhas_acoes e a data atual
    # data_inicio = min(df_minhas_acoes["data"])
    # Supondo que a coluna "data" seja uma string representando datas
    df_minhas_acoes["data"] = pd.to_datetime(df_minhas_acoes["data"])
    # Agora você pode encontrar a data mínima corretamente
    data_inicio = min(df_minhas_acoes["data"])

    data_fim = data_atual
    mask = (df_valores["Date"] >= data_inicio) & (df_valores["Date"] <= data_fim)
    df_valores_filtrado = df_valores.loc[mask]

    # Agrupa por mês/ano e calcula a média de 'Adj Close'
    df_valores_filtrado["YearMonth"] = df_valores_filtrado["Date"].dt.to_period("M")
    media_por_mes = df_valores_filtrado.groupby("YearMonth")["Adj Close"].mean()

    # Seleciona os três meses com maiores médias
    tres_meses_mais_altos = media_por_mes.nlargest(3)

    st.subheader("Três meses com maiores médias de Adj Close:")
    st.subheader("desde quando comprei")

    for year_month, media in tres_meses_mais_altos.items():
        st.write(
            # f"Mês/Ano: {year_month}, Média: {media:.2f}, Delta: {(media-valor_pago)*quantidade:.2f}"
        )

    # Seleciona os três meses com menores médias
    tres_meses_menos_altos = media_por_mes.nsmallest(3)

    st.subheader("Três meses com menores médias de Adj Close:")
    st.subheader("desde quando comprei")
    for year_month, media in tres_meses_menos_altos.items():
        st.write(
            # f"Mês/Ano: {year_month}, Média: {media:.2f}, Delta: {(media-valor_pago)*quantidade:.2f}"
        )

else:
    st.write(
        f"A ação selecionada {ticker_selecionado}, não está presente nos seus ativos {df_minhas_acoes['ticker'].values}."
    )
