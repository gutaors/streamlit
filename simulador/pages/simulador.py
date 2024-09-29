# FALTA FAZER
# qual ação minha que está dando mais lucro hoje
# qual ação minha que está dando mais preju hoje
# o valor que paguei foi x
# o valor máximo foi x em data tal
# mes com maior volume negociado, volume e média diária
# o mês com melhor mediana foi tal, mediana tal
# o mês com pior mediana foi tal, mediana tal
# se vale mostrar valor do minério
# se petrobras mostrar valor do petroleo
# média móvel com setinha para 1 mes
# média móvel com setinha para 3 meses


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
# df_tickers = pd.read_csv("dados/tickers.csv", sep=";")
# tickers = df_tickers["ticker"].tolist()

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
st.title("Análise de ações")

with st.expander("Simulador"):
    st.title("Simulador")

    def pegar_dados_acoes(arquivo):
        # path = "\\wsl.localhost\Ubuntu\home\gutao\dev\streamlit_docker\acoes\acoes.csv"
        path = "dados/" + arquivo
        return pd.read_csv(path, delimiter=";")

    df = pegar_dados_acoes("acoes.csv")
    df_minhas_acoes = pegar_dados_acoes("tickers.csv")

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
    data_compra_sim = st.sidebar.date_input("Data de Compra (Simulação)")

    data_venda_sim = st.sidebar.date_input("Data de Venda (Simulação)")

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
    valor_sim = st.sidebar.number_input("Valor:", value=1000.00, step=0.01)
    # =================================================================================================

    @st.cache_data
    def pegar_valores_online(sigla_acao):
        df = yf.download(sigla_acao, DATA_INICIO, DATA_FIM)
        df.reset_index(inplace=True)
        return df

    df_valores = pegar_valores_online(acao_escolhida)
    #############
    st.subheader("Simulação - " + nome_acao_escolhida)
    st.write(
        "**Data da compra:**",
        data_compra_sim.strftime("%d/%m/%Y"),
        "  **Data da venda:**",
        data_venda_sim.strftime("%d/%m/%Y"),
    )
    st.write("**Valor:** ", f"R$ {valor_sim:.2f}")

    # Simular a compra
    # Filtrar o DataFrame com base na data de compra
    filtro_data = df_valores["Date"] == pd.to_datetime(data_compra_sim)
    dados_compra = df_valores[filtro_data]
    # caso data de compra não tenha dados retrocede um dia até ter
    while dados_compra.empty:
        data_compra_sim = data_compra_sim - timedelta(days=1)
        filtro_data = df_valores["Date"] == pd.to_datetime(data_compra_sim)
        dados_compra = df_valores[filtro_data]
    # Obter o valor do Adj Close na data de compra
    if not dados_compra.empty:
        close_compra = dados_compra.iloc[0]["Adj Close"]
        # Calcular quantos papéis foram comprados com o valor disponível
        quantidade_comprada = valor_sim / close_compra
        st.write(
            f"Quantidade de papéis comprados com {valor_sim:.2f}: {quantidade_comprada:.2f}"
        )
    else:
        st.write(
            f"**Não há dados para a data de compra especificada:** {data_compra_sim.strftime('%d/%m/%Y')}"
        )

    #############+=============================================================================================
    # Simular a Venda
    # Filtrar o DataFrame com base na data de venda
    filtro_data = df_valores["Date"] == pd.to_datetime(data_venda_sim)
    dados_venda = df_valores[filtro_data]
    # caso data de compra não tenha dados retrocede um dia até ter
    while dados_venda.empty:
        data_venda_sim = data_venda_sim - timedelta(days=1)
        filtro_data = df_valores["Date"] == pd.to_datetime(data_venda_sim)
        dados_venda = df_valores[filtro_data]

    # Obter o valor do Adj Close na data de venda
    if not dados_venda.empty:
        close_venda = dados_venda.iloc[0]["Adj Close"]
        # Calcular quantos papéis foram comprados com o valor disponível
        ###print(close_compra)
        # quantidade_comprada = valor_sim / close_compra
        valor_vendido = quantidade_comprada * close_venda
        st.write(f"Lucro/Prejuízo: {valor_vendido-valor_sim:.2f}")
        st.write(f"Preço ação na data da compra {close_compra:.2f}")
        st.write(f"Preço ação na data da venda {close_venda:.2f}")
        ############## FORMATADO
        # Formate a data de compra
        data_compra_formatada = data_compra_sim.strftime("%d/%m/%Y")
        data_venda_formatada = data_venda_sim.strftime("%d/%m/%Y")
        # Formate o valor_sim como moeda
        valor_formatado = f"R$ {valor_vendido-valor_sim:.2f}"  # Exemplo formatado em reais brasileiros

        # Defina a cor do botão com base no valor
        if valor_vendido - valor_sim >= 0:
            cor_botao = "background-color: green; color: white"
        else:
            cor_botao = "background-color: red; color: white"

        # Exiba os valores dentro de botões coloridos
        st.markdown(
            "<div style='display: flex; justify-content: space-between;'>"
            f"<div style='{cor_botao}; padding: 10px; border-radius: 5px;'>Data da Compra: {data_compra_formatada}</div>"
            f"<div style='{cor_botao}; padding: 10px; border-radius: 5px;'>Data da Venda: {data_venda_formatada}</div>"
            f"<div style='{cor_botao}; padding: 10px; border-radius: 5px;'>Lucro/Prejuízo: {valor_vendido-valor_sim:.2f}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        ############## FORMATADO
    else:
        f"**Não há dados para a data de venda especificada:** {data_venda_sim.strftime('%d/%m/%Y')}"

    st.write(df_valores.tail(3))

    # ================================================================================================================================================

    # Filtra as linhas correspondentes às datas de compra e venda
    row_compra = df_valores[df_valores["Date"].dt.date == data_compra_sim]
    row_venda = df_valores[df_valores["Date"].dt.date == data_venda_sim]

    ##############
    st.subheader("Tabela de valores - " + nome_acao_escolhida)
    st.write(df_valores.tail(10))
    st.write(df_valores.tail(10))

    # Criar gráfico de médias móveis

    # Calcular médias móveis de 15 e 50 períodos
    df_valores["MA15"] = df_valores["Close"].rolling(window=15).mean()
    df_valores["MA50"] = df_valores["Close"].rolling(window=50).mean()

    # Criar coluna para identificar cruzamentos
    df_valores["Cruzamento"] = df_valores["MA15"] - df_valores["MA50"]

    # Plotar gráfico com preços, médias móveis e setas para cruzamentos
    st.subheader("Gráfico de Médias Móveis com Cruzamentos")
    fig_ma_cruzamentos = go.Figure()

    fig_ma_cruzamentos.add_trace(
        go.Scatter(
            x=df_valores["Date"],
            y=df_valores["Close"],
            name="Preço de Fechamento",
            line_color="blue",
        )
    )
    fig_ma_cruzamentos.add_trace(
        go.Scatter(
            x=df_valores["Date"],
            y=df_valores["MA15"],
            name="Média Móvel de 15 períodos",
            line_color="orange",
        )
    )
    fig_ma_cruzamentos.add_trace(
        go.Scatter(
            x=df_valores["Date"],
            y=df_valores["MA50"],
            name="Média Móvel de 50 períodos",
            line_color="green",
        )
    )

    # Adicionar setas para cruzamentos
    for index, row in df_valores.iterrows():
        if (
            index > 0
            and df_valores.at[index, "Cruzamento"]
            * df_valores.at[index - 1, "Cruzamento"]
            < 0
        ):
            arrow_color = "green" if df_valores.at[index, "Cruzamento"] > 0 else "red"
            fig_ma_cruzamentos.add_annotation(
                x=row["Date"],
                y=row["Close"],
                ax=row["Date"],
                ay=row["Close"],
                showarrow=True,
                arrowhead=1,
                arrowsize=2,
                arrowwidth=2,
                arrowcolor=arrow_color,
            )

    fig_ma_cruzamentos.update_layout(
        title="Gráfico de Preços e Médias Móveis com Cruzamentos"
    )
    st.plotly_chart(fig_ma_cruzamentos)

    # Criar gráfico de preços

    st.subheader("Gráfico de preços:")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_valores["Date"],
            y=df_valores["Close"],
            name="Preco Fechamento",
            line_color="yellow",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_valores["Date"],
            y=df_valores["Open"],
            name="Preco Abertura",
            line_color="blue",
        )
    )
    st.plotly_chart(fig)

    # previsao

    df_treino = df_valores[["Date", "Close"]]

    # renomear colunas
    df_treino = df_treino.rename(columns={"Date": "ds", "Close": "y"})

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
    mask = (df_valores["Date"] >= data_inicio) & (df_valores["Date"] <= data_fim)
    df_valores_filtrado = df_valores.loc[mask]

    # Agrupa por mês/ano e calcula a média de 'Adj Close'
    df_valores_filtrado["YearMonth"] = df_valores_filtrado["Date"].dt.to_period("M")
    media_por_mes = df_valores_filtrado.groupby("YearMonth")["Adj Close"].mean()

    # Seleciona os três meses com maiores médias
    tres_meses_mais_altos = media_por_mes.nlargest(3)

    st.subheader("Três meses com maiores médias de Adj Close:")
    st.subheader("no último ano")

    for year_month, media in tres_meses_mais_altos.items():
        st.write(f"Mês/Ano: {year_month}, Média: {media:.2f}")

    # Seleciona os três meses com menores médias
    tres_meses_menos_altos = media_por_mes.nsmallest(3)

    st.subheader("Três meses com menores médias de Adj Close:")
    st.subheader("no último ano")
    for year_month, media in tres_meses_menos_altos.items():
        st.write(f"Mês/Ano: {year_month}, Média: {media:.2f}")


with st.expander("Painel Resumido"):
    st.title("Painel Resumido")
    # Pega a ação selecionada e mostra o maior valor nos últimos cinco anos
    # ticker_selecionado = df_acao.iloc[0]["sigla_acao"]
    # ticker_selecionado = ticker_selecionado + ".SA"
    # st.write(df.head(10))
    # st.write(df_minhas_acoes.head(10))
    # st.write(df_valores.head(10))
    # st.write(df_valores_filtrado.head(10))

    # ENCONTRAR DATA EXATA DE CINCO ANOS ATRÁS

    # Subtraia cinco anos
    data_cinco_anos_atras = pd.to_datetime(data_atual) - timedelta(days=5 * 365)
    # Métricas entre data_atual e data_cinco_anos_atras
    data_cinco_anos_atras = pd.to_datetime(data_cinco_anos_atras)
    data_atual = pd.to_datetime(data_atual)

    # Filtrar as linhas no período desejado
    df_periodo = df_valores.loc[
        (df_valores["Date"] >= data_cinco_anos_atras)
        & (df_valores["Date"] <= data_atual)
    ]

    # Calcular as métricas
    valor_maximo = df_periodo["Close"].max()
    valor_minimo = df_periodo["Close"].min()
    valor_medio = df_periodo["Close"].mean()
    variancia = df_periodo["Close"].var()
    valor_inicio_periodo = df_periodo["Close"].iloc[0]
    valor_final_periodo = df_periodo["Close"].iloc[-1]
    date_inicio_periodo = df_periodo["Date"].iloc[0]
    date_final_periodo = df_periodo["Date"].iloc[-1]

    # Exibir os resultados

    st.write(
        f"Valor <span style='color:red; font-weight:bold;'>Máximo</span> de Close no Período: <span style='font-weight:bold;'>R$ {valor_maximo:.2f}</span>",
        unsafe_allow_html=True,
    )
    st.write(
        f"Valor <span style='color:red; font-weight:bold;'>Mínimo</span> de Close no Período: <span style='font-weight:bold;'>R$ {valor_minimo:.2f}</span>",
        unsafe_allow_html=True,
    )
    st.write(
        f"Valor <span style='color:red; font-weight:bold;'>Médio</span> de Close no Período: <span style='font-weight:bold;'>R$ {valor_medio:.2f}</span>",
        unsafe_allow_html=True,
    )
    st.write(
        f"<span style='color:red; font-weight:bold;'>Variância</span> do Valor Close no Período: <span style='font-weight:bold;'>R$ {variancia:.2f}</span>",
        unsafe_allow_html=True,
    )
    st.write(
        f"Valor de <span style='color:red; font-weight:bold;'>cinco anos</span> atrás: <span style='font-weight:bold;'>R$ {valor_inicio_periodo:.2f}</span>",
        unsafe_allow_html=True,
    )
    st.write(
        f"Valor <span style='color:red; font-weight:bold;'>atual</span>: <span style='font-weight:bold;'>R$ {valor_final_periodo:.2f}</span>",
        unsafe_allow_html=True,
    )
    st.write(
        "Data de  <span style='color:red; font-weight:bold;'>cinco anos</span> atrás:<span style='font-weight:bold;'>",
        date_inicio_periodo.strftime("%d/%m/%Y"),
        "</span>",
        unsafe_allow_html=True,
    )
    st.write(
        f"Data  <span style='color:red; font-weight:bold;'>atual</span>:<span style='font-weight:bold;'>",
        date_final_periodo.strftime("%d/%m/%Y"),
        "</span>",
        unsafe_allow_html=True,
    )

    # Box com valor que está mais próximo do atual, médio, máx ou mínimo
    # Calcula a diferença entre o valor_final_periodo e cada um dos outros valores
    dif_minimo = abs(valor_final_periodo - valor_minimo)
    dif_maximo = abs(valor_final_periodo - valor_maximo)
    dif_medio = abs(valor_final_periodo - valor_medio)

    # Encontra o valor mais próximo
    valor_mais_proximo = min(
        valor_minimo,
        valor_maximo,
        valor_medio,
        key=lambda x: abs(x - valor_final_periodo),
    )

    # Define o nome da variável mais próxima
    if valor_mais_proximo == valor_minimo:
        nome_var_proxima = "Valor Mínimo"
    elif valor_mais_proximo == valor_maximo:
        nome_var_proxima = "Valor Máximo"
    else:
        nome_var_proxima = "Valor Médio"

    # Cria um box com fundo laranja e texto em negrito
    st.markdown(
        f"""
        <div style="background-color: orange; padding: 10px">
            <p style="font-weight: bold; color: black">
                Valor Atual está mais próximo de {nome_var_proxima}:
            </p>
            <p style="font-size: 18px; color: black">
                Valor Atual: R$ {valor_final_periodo:.2f}<br>
                {nome_var_proxima}: R$ {valor_mais_proximo:.2f}
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Plotar gráfico com preços, médias móveis e setas para cruzamentos
    st.subheader("Gráfico de Médias Móveis com Cruzamentos")
    fig_ma_cruzamentos = go.Figure()

    fig_ma_cruzamentos.add_trace(
        go.Scatter(
            x=df_valores["Date"],
            y=df_valores["Close"],
            name="Preço de Fechamento",
            line_color="blue",
        )
    )
    fig_ma_cruzamentos.add_trace(
        go.Scatter(
            x=df_valores["Date"],
            y=df_valores["MA15"],
            name="Média Móvel de 15 períodos",
            line_color="orange",
        )
    )
    fig_ma_cruzamentos.add_trace(
        go.Scatter(
            x=df_valores["Date"],
            y=df_valores["MA50"],
            name="Média Móvel de 50 períodos",
            line_color="green",
        )
    )

    # Adicionar setas para cruzamentos
    for index, row in df_valores.iterrows():
        if (
            index > 0
            and df_valores.at[index, "Cruzamento"]
            * df_valores.at[index - 1, "Cruzamento"]
            < 0
        ):
            arrow_color = "green" if df_valores.at[index, "Cruzamento"] > 0 else "red"
            fig_ma_cruzamentos.add_annotation(
                x=row["Date"],
                y=row["Close"],
                ax=row["Date"],
                ay=row["Close"],
                showarrow=True,
                arrowhead=1,
                arrowsize=2,
                arrowwidth=2,
                arrowcolor=arrow_color,
            )

    fig_ma_cruzamentos.update_layout(
        title="Gráfico de Preços e Médias Móveis com Cruzamentos"
    )
    st.plotly_chart(fig_ma_cruzamentos)


with st.expander("Minhas Ações"):

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
