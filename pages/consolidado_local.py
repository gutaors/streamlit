import streamlit as st
import os
import pandas as pd
from datetime import date
import datetime as dt

# Configuração única da página (deve ser chamada antes de qualquer outra função Streamlit)
st.set_page_config(page_title="Stock Analysis App", layout="wide")

# Menu de navegação para escolher a funcionalidade
app_mode = st.selectbox("Selecione a aplicação:", ("Indicadores", "Previsão com Prophet", "Previsão com GPT"))

# ======================== Página 1: Indicadores ========================
if app_mode == "Indicadores":
    st.title("Coleta Preço de Ativo")
    st.header("Informações a respeito de fechamento, volume, MM200, RSI e MACD")

    # Define a pasta onde estão os arquivos CSV
    pasta_cotacoes = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cotacoes')
    arquivos_csv = [f.replace('.csv', '') for f in os.listdir(pasta_cotacoes) if f.endswith('.csv')]
    arquivos_csv.sort()

    # Filtros no topo da página usando colunas
    col1, col2 = st.columns(2)
    with col1:
        ticker_simbolo = st.selectbox('Escolha o Ativo', arquivos_csv)
    with col2:
        cut_date = st.date_input("Data de Corte", value=date.today())

    # Monta o caminho para o arquivo CSV correspondente e lê os dados
    caminho_csv = os.path.join(pasta_cotacoes, ticker_simbolo + '.csv')
    tickerDF = pd.read_csv(caminho_csv)

    if 'Date' in tickerDF.columns:
        tickerDF['Date'] = pd.to_datetime(tickerDF['Date'], errors='coerce')
        tickerDF = tickerDF.dropna(subset=['Date'])
        tickerDF.set_index('Date', inplace=True)
        tickerDF.sort_index(inplace=True)

    df_cut = tickerDF[tickerDF.index <= pd.to_datetime(cut_date)]
    st.write("Dados filtrados até a data de corte:", df_cut.head())

    if 'Close' in df_cut.columns:
        df_cut['Close'] = pd.to_numeric(df_cut['Close'], errors='coerce')
        df_cut = df_cut.dropna(subset=['Close'])
        dados_close = df_cut['Close']
    else:
        dados_close = None

    if dados_close is not None and not dados_close.empty:
        # Cálculo dos Indicadores
        df_cut['MM200'] = df_cut['Close'].rolling(window=200).mean()

        delta = df_cut['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df_cut['RSI'] = 100 - (100 / (1 + rs))

        ema12 = df_cut['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df_cut['Close'].ewm(span=26, adjust=False).mean()
        df_cut['MACD'] = ema12 - ema26
        df_cut['Signal'] = df_cut['MACD'].ewm(span=9, adjust=False).mean()

        st.header("Gráficos de Indicadores")
        st.line_chart(df_cut[['Close', 'MM200']].dropna())
        st.line_chart(df_cut[['RSI']].dropna())
        st.line_chart(df_cut[['MACD', 'Signal']].dropna())

        # Alertas e Recomendações
        tol = 0.01
        if len(df_cut) >= 2:
            current = df_cut.iloc[-1]
            previous = df_cut.iloc[-2]

            tocou_de_cima = previous['Close'] > previous['MM200'] and abs(current['Close'] - current['MM200']) / current['MM200'] < tol
            tocou_de_baixo = previous['Close'] < previous['MM200'] and abs(current['Close'] - current['MM200']) / current['MM200'] < tol

            if tocou_de_cima:
                st.info("Alerta 1: Preço do ativo **caiu para a MM200**.")
                st.markdown("<span style='color: green; font-weight: bold;'>Recomendação: Fique atento a este nível para identificar oportunidades de compra se confirmado pelos indicadores.</span>", unsafe_allow_html=True)
                if current['RSI'] > 50 and current['MACD'] > current['Signal']:
                    st.success("Alerta 2: **Suporte forte**: Em tendência de alta, o toque na MM200 pode indicar um bom ponto de compra.")
                    st.markdown("<span style='color: green; font-weight: bold;'>Recomendação: Considere aproveitar o suporte para comprar.</span>", unsafe_allow_html=True)

            if previous['Close'] > previous['MM200'] and current['Close'] < current['MM200']:
                st.error("Alerta 3: **Rompimento baixista**: O preço caiu abaixo da MM200 e pode indicar o início de uma tendência de baixa.")
                st.markdown("<span style='color: red; font-weight: bold;'>Recomendação: Considere reduzir posições ou proteger seus investimentos.</span>", unsafe_allow_html=True)

            if tocou_de_baixo:
                st.info("Alerta 4: Preço do ativo **subiu para a MM200**.")
                st.markdown("<span style='color: red; font-weight: bold;'>Recomendação: Acompanhe de perto, pois a subida pode indicar resistência e uma possível reversão.</span>", unsafe_allow_html=True)
                if current['RSI'] < 50 and current['MACD'] < current['Signal']:
                    st.success("Alerta 5: **Resistência forte**: Em tendência de baixa, o toque na MM200 pode indicar forte resistência.")
                    st.markdown("<span style='color: red; font-weight: bold;'>Recomendação: Evite compras e considere estratégias de proteção.</span>", unsafe_allow_html=True)

            if previous['Close'] < previous['MM200'] and current['Close'] > current['MM200']:
                st.success("Alerta 6: **Rompimento altista**: O preço superou a MM200 e pode indicar o início de uma tendência de alta.")
                st.markdown("<span style='color: green; font-weight: bold;'>Recomendação: Considere uma oportunidade de compra.</span>", unsafe_allow_html=True)

            st.markdown("### Alerta 7: Confirmação com Indicadores (RSI e MACD)")
            st.markdown(
                """- **RSI (Relative Strength Index):** Indica a força do movimento do preço.
- **MACD (Moving Average Convergence Divergence):** Mede a relação entre duas médias móveis."""
            )
            st.markdown("<span style='color: green; font-weight: bold;'>Recomendação: Utilize os indicadores para confirmar os sinais e ajustar sua estratégia de investimento.</span>", unsafe_allow_html=True)

            st.text_input("RSI Atual", f"{current['RSI']:.2f}", disabled=True)
            st.text_input("MACD Atual", f"{current['MACD']:.2f}", disabled=True)
            st.text_input("MACD Signal", f"{current['Signal']:.2f}", disabled=True)
            st.text_input("MM200", f"{current['MM200']:.2f}", disabled=True)
            st.text_input("Preço Atual", f"{current['Close']:.2f}", disabled=True)

        if 'Volume' in df_cut.columns:
            df_cut['Volume'] = pd.to_numeric(df_cut['Volume'], errors='coerce')
            dados_volume = df_cut['Volume'].dropna()
            if not dados_volume.empty:
                st.header("Gráfico de Volume")
                st.line_chart(dados_volume)
            else:
                st.write("Coluna 'Volume' sem dados válidos.")
        else:
            st.write("Coluna 'Volume' não encontrada.")

        if 'Dividends' in df_cut.columns:
            df_cut['Dividends'] = pd.to_numeric(df_cut['Dividends'], errors='coerce')
            dados_dividends = df_cut['Dividends'].dropna()
            if not dados_dividends.empty:
                st.header("Gráfico de Dividendos")
                st.line_chart(dados_dividends)
            else:
                st.write("Coluna 'Dividends' sem dados válidos.")
        else:
            st.write("Dados de dividendos não disponíveis.")

        st.markdown("## Resumo Final dos Indicadores")
        st.write("**Preço Atual:**", f"{current['Close']:.2f}")
        st.write("**Média Móvel 200 (MM200):**", f"{current['MM200']:.2f}")
        st.write("**RSI:**", f"{current['RSI']:.2f}")
        st.write("**MACD:**", f"{current['MACD']:.2f}")
        st.write("**MACD Signal:**", f"{current['Signal']:.2f}")
        if 'Volume' in df_cut.columns:
            current_volume = df_cut['Volume'].dropna().iloc[-1]
            st.write("**Volume:**", f"{current_volume:.2f}")
        if 'Dividends' in df_cut.columns:
            current_dividends = df_cut['Dividends'].dropna().iloc[-1]
            st.write("**Dividendos:**", f"{current_dividends:.2f}")

        if current['RSI'] > 50 and current['MACD'] > current['Signal'] and current['Close'] > current['MM200']:
            rec = "<span style='color: green; font-weight: bold;'>Tendência Altista: Recomenda-se manter ou aumentar posições de compra.</span>"
        elif current['RSI'] < 50 and current['MACD'] < current['Signal'] and current['Close'] < current['MM200']:
            rec = "<span style='color: red; font-weight: bold;'>Tendência Baixista: Recomenda-se cautela ou redução de posições.</span>"
        else:
            rec = "<span style='color: orange; font-weight: bold;'>Sinal Neutro/Misto: Aguarde confirmações adicionais.</span>"

        st.markdown("### Resumo da Recomendação")
        st.markdown(rec, unsafe_allow_html=True)
    else:
        st.write("Coluna 'Close' não encontrada ou sem dados.")

# ======================== Página 2: Previsão com Prophet ========================
elif app_mode == "Previsão com Prophet":
    import os
    from prophet import Prophet
    from prophet.plot import plot_plotly
    from plotly import graph_objs as go

    st.markdown("# Análise Preditiva")
    st.markdown("### Prevendo o valor de ações na Bolsa de Valores")

    # Função para listar tickers disponíveis
    def listar_tickers_disponiveis():
        pasta = "cotacoes"
        arquivos = [f for f in os.listdir(pasta) if f.endswith(".csv")]
        tickers = [arquivo.replace(".csv", "") for arquivo in arquivos]
        return tickers

    # Função para carregar dados
    def carregar_dados(ticker, dt_inicial, dt_final):
        caminho_arquivo = os.path.join("cotacoes", f"{ticker}.csv")
        if not os.path.exists(caminho_arquivo):
            st.error(f"Arquivo {caminho_arquivo} não encontrado.")
            return None
        df = pd.read_csv(caminho_arquivo, parse_dates=["Date"], index_col="Date")
        if "Close" not in df.columns:
            st.error(f"O arquivo {caminho_arquivo} não contém a coluna 'Close'.")
            return None
        df = df.loc[(df.index >= pd.to_datetime(dt_inicial)) & (df.index <= pd.to_datetime(dt_final))]
        return df

    # Função para previsão com Prophet
    def prever_dados(df, periodo):
        df = df[["Close"]].copy()
        df.reset_index(inplace=True)
        df.rename(columns={"Date": "ds", "Close": "y"}, inplace=True)

        modelo = Prophet()
        modelo.fit(df)

        datas_futuras = modelo.make_future_dataframe(periods=int(periodo) * 30)
        previsoes = modelo.predict(datas_futuras)
        return modelo, previsoes

    # Filtros no topo da página
    tickers_disponiveis = listar_tickers_disponiveis()
    ticker = st.selectbox("Selecione a ação:", tickers_disponiveis)
    dt_inicial = st.date_input("Data Inicial", value=date(2020, 1, 1))
    dt_final = st.date_input("Data Final")
    meses = st.number_input("Meses de Previsão", 1, 24, value=6)

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

        previsoes["ds"] = previsoes["ds"].dt.date
        previsoes = previsoes.sort_values(by="ds", ascending=False)
        st.dataframe(previsoes, width=800, height=400)

        ultima_previsao = previsoes.iloc[0]
        valor_previsto = ultima_previsao['yhat']
        valor_inferior = ultima_previsao['yhat_lower']
        valor_superior = ultima_previsao['yhat_upper']
        ultimo_valor_real = dados["Close"].iloc[-1]

        st.markdown("## **Resumo dos Números Gerados pelo Modelo**")
        st.write("**Valor Previsto para o Último Período:**", f"{valor_previsto:.2f}")
        st.write("**Intervalo de Confiança Inferior:**", f"{valor_inferior:.2f}")
        st.write("**Intervalo de Confiança Superior:**", f"{valor_superior:.2f}")
        st.write("**Último Valor Real:**", f"{ultimo_valor_real:.2f}")

        if valor_previsto > ultimo_valor_real:
            rec = "<span style='color: green; font-weight: bold;'>Recomendação: Tendência Altista - Recomenda-se manter ou aumentar posições de compra.</span>"
        else:
            rec = "<span style='color: red; font-weight: bold;'>Recomendação: Tendência Baixista - Recomenda-se cautela ou redução de posições.</span>"

        st.markdown(rec, unsafe_allow_html=True)
    else:
        st.warning("Nenhum dado encontrado no período selecionado!")

# ======================== Página 3: Previsão com GPT ========================
elif app_mode == "Previsão com GPT":
    import torch
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    import matplotlib.pyplot as plt
    import numpy as np
    import re

    st.title("Stock Price Prediction with GPT")
    st.write("Previsão de preços históricos de ações usando GPT-2 e dados de arquivos CSV.")

    cotacoes_dir = "cotacoes"
    tickers = [f.replace('.csv', '') for f in os.listdir(cotacoes_dir) if f.endswith('.csv')]

    if not tickers:
        st.error("Nenhum arquivo CSV encontrado na pasta 'cotacoes'.")
    else:
        ticker = st.selectbox("Selecione o Ticker:", tickers)
        end_date = st.date_input("Data Final:", value=dt.date(2023, 6, 8))
        start_date = end_date - dt.timedelta(days=365)
        st.write(f"Data de início automaticamente definida para: {start_date}")

        if start_date >= end_date:
            st.error("A data de início calculada deve ser anterior à data final.")
        else:
            file_path = os.path.join(cotacoes_dir, f"{ticker}.csv")
            data = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
            data = data[(data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))]

            if data.empty:
                st.error("Nenhum dado encontrado para o intervalo de datas informado.")
            else:
                prices = data["Close"].values.tolist()
                st.write(f"Dados para {ticker}:")
                st.dataframe(data)

                st.write("Carregando modelo GPT-2...")
                tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
                model = GPT2LMHeadModel.from_pretrained("gpt2")

                max_new_tokens = 20
                max_input_length = tokenizer.model_max_length - max_new_tokens

                prompt = "Historical Prices: " + " ".join([str(price) for price in prices]) + "\nPredicted: "
                encoded_prompt = tokenizer.encode(prompt, truncation=True, max_length=max_input_length, return_tensors="pt")

                st.write("Gerando previsões...")
                attention_mask = torch.ones(encoded_prompt.shape, device=encoded_prompt.device)
                generated = model.generate(
                    encoded_prompt,
                    attention_mask=attention_mask,
                    max_new_tokens=max_new_tokens,
                    temperature=0.7,
                    do_sample=True,
                    top_k=50,
                    top_p=0.95,
                    num_return_sequences=1
                )

                generated_tokens = generated[0]
                predicted_tokens = generated_tokens[encoded_prompt.shape[1]:]
                predicted_text = tokenizer.decode(predicted_tokens, skip_special_tokens=True)
                st.write("Texto gerado para previsão:", predicted_text)

                predicted_prices_tokens = predicted_text.split()
                predicted_prices = []
                for token in predicted_prices_tokens:
                    try:
                        token_clean = re.sub(r"[^\d\.]+", "", token)
                        if token_clean:
                            predicted_prices.append(float(token_clean))
                    except ValueError:
                        continue

                if predicted_prices:
                    future_dates = data.index[-1] + pd.to_timedelta(np.arange(1, len(predicted_prices) + 1), 'D')
                else:
                    st.error("Previsões não geradas corretamente para exibir o resumo e a recomendação.")

                plt.figure(figsize=(12, 6))
                plt.plot(data.index, prices, label="Historical Prices")
                if predicted_prices:
                    plt.plot(future_dates, predicted_prices, "g^", label="Predicted Prices")
                plt.xlabel("Data")
                plt.ylabel("Preço")
                plt.title(f"{ticker} - Preços Históricos e Previstos (GPT)")
                plt.legend()
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(plt)

                if predicted_prices:
                    last_predicted_price = predicted_prices[-1]
                    last_historical_price = float(prices[-1])

                    st.markdown("## **Resumo dos Números Gerados pelo Modelo**")
                    st.write("**Último Valor Histórico:**", f"{last_historical_price:.2f}")
                    st.write("**Último Valor Previsto:**", f"{last_predicted_price:.2f}")

                    if last_predicted_price > last_historical_price:
                        rec = "<span style='color: green; font-weight: bold;'>Recomendação: Tendência Altista - Recomenda-se manter ou aumentar posições de compra.</span>"
                    else:
                        rec = "<span style='color: red; font-weight: bold;'>Recomendação: Tendência Baixista - Recomenda-se cautela ou redução de posições.</span>"

                    st.markdown(rec, unsafe_allow_html=True)
                else:
                    st.error("Previsões não geradas corretamente para exibir o resumo e a recomendação.")
