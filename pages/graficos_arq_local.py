import streamlit as st
import os
import pandas as pd
from datetime import date

st.title("Coleta Preço de Ativo")
st.header("Informações a respeito de fechamento, volume, MM200, RSI e MACD")

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

# Se existir a coluna 'Date', converte para datetime, define como índice e ordena
if 'Date' in tickerDF.columns:
    tickerDF['Date'] = pd.to_datetime(tickerDF['Date'], errors='coerce')
    tickerDF = tickerDF.dropna(subset=['Date'])
    tickerDF.set_index('Date', inplace=True)
    tickerDF.sort_index(inplace=True)

# Campo Data de Corte (pré-preenchido com a data atual)
cut_date = st.date_input("Data de Corte", value=date.today())

# Cria um novo dataframe filtrado até a data de corte
df_cut = tickerDF[tickerDF.index <= pd.to_datetime(cut_date)]
st.write("Dados filtrados até a data de corte:", df_cut.head())

# Converte a coluna 'Close' para numérico e remove valores nulos
if 'Close' in df_cut.columns:
    df_cut['Close'] = pd.to_numeric(df_cut['Close'], errors='coerce')
    df_cut = df_cut.dropna(subset=['Close'])
    dados_close = df_cut['Close']
else:
    dados_close = None

if dados_close is not None and not dados_close.empty:
    # Cálculo da Média Móvel de 200 dias (MM200)
    df_cut['MM200'] = df_cut['Close'].rolling(window=200).mean()

    # Cálculo do RSI (período de 14 dias)
    delta = df_cut['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df_cut['RSI'] = 100 - (100 / (1 + rs))

    # Cálculo do MACD e da linha de sinal
    ema12 = df_cut['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df_cut['Close'].ewm(span=26, adjust=False).mean()
    df_cut['MACD'] = ema12 - ema26
    df_cut['Signal'] = df_cut['MACD'].ewm(span=9, adjust=False).mean()

    # Gráfico de Fechamento com MM200
    st.header("Gráfico de Fechamento com MM200")
    chart_data = df_cut[['Close', 'MM200']].dropna()
    st.line_chart(chart_data)

    # Gráficos dos indicadores
    st.header("Gráfico de RSI")
    st.line_chart(df_cut[['RSI']].dropna())

    st.header("Gráfico de MACD")
    st.line_chart(df_cut[['MACD', 'Signal']].dropna())

    # Definindo uma tolerância para considerar que o preço "tocou" a MM200 (1%)
    tol = 0.01

    if len(df_cut) >= 2:
        current = df_cut.iloc[-1]
        previous = df_cut.iloc[-2]

        # Condição para "tocar" a MM200 vindo de cima (alertas 1 e 2)
        tocou_de_cima = previous['Close'] > previous['MM200'] and abs(current['Close'] - current['MM200']) / current['MM200'] < tol

        # Condição para "tocar" a MM200 vindo de baixo (alertas 4 e 5)
        tocou_de_baixo = previous['Close'] < previous['MM200'] and abs(current['Close'] - current['MM200']) / current['MM200'] < tol

        # ALERTA 1: Preço do ativo cai para a MM200
        if tocou_de_cima:
            st.info("Alerta 1: Preço do ativo **caiu para a MM200**.")
            st.markdown("<span style='color: green; font-weight: bold;'>Recomendação: Fique atento a este nível para identificar oportunidades de compra se confirmado pelos indicadores.</span>", unsafe_allow_html=True)

            # ALERTA 2: Suporte forte (RSI e MACD confirmam tendência de alta)
            if current['RSI'] > 50 and current['MACD'] > current['Signal']:
                st.success("Alerta 2: **Suporte forte**: Em tendência de alta (RSI > 50 e MACD acima da linha de sinal), o toque na MM200 pode indicar um bom ponto de compra.")
                st.markdown("<span style='color: green; font-weight: bold;'>Recomendação: Considere aproveitar o suporte para comprar, pois a tendência de alta pode se manter.</span>", unsafe_allow_html=True)

        # ALERTA 3: Rompimento baixista – preço cruza de cima para abaixo da MM200
        if previous['Close'] > previous['MM200'] and current['Close'] < current['MM200']:
            st.error("Alerta 3: **Rompimento baixista**: O preço caiu abaixo da MM200 e pode indicar o início de uma tendência de baixa.")
            st.markdown("<span style='color: red; font-weight: bold;'>Recomendação: Considere reduzir posições ou proteger seus investimentos, pois o rompimento pode indicar uma tendência de baixa.</span>", unsafe_allow_html=True)

        # ALERTA 4: Preço do ativo sobe para a MM200
        if tocou_de_baixo:
            st.info("Alerta 4: Preço do ativo **subiu para a MM200**.")
            st.markdown("<span style='color: red; font-weight: bold;'>Recomendação: Acompanhe de perto, pois a subida pode indicar resistência e uma possível reversão.</span>", unsafe_allow_html=True)

            # ALERTA 5: Resistência forte (RSI e MACD confirmam tendência de baixa)
            if current['RSI'] < 50 and current['MACD'] < current['Signal']:
                st.success("Alerta 5: **Resistência forte**: Em tendência de baixa (RSI < 50 e MACD abaixo da linha de sinal), o toque na MM200 pode indicar forte resistência.")
                st.markdown("<span style='color: red; font-weight: bold;'>Recomendação: Evite compras e considere estratégias de proteção, pois a resistência pode manter a queda dos preços.</span>", unsafe_allow_html=True)

        # ALERTA 6: Rompimento altista – preço cruza de baixo para acima da MM200
        if previous['Close'] < previous['MM200'] and current['Close'] > current['MM200']:
            st.success("Alerta 6: **Rompimento altista**: O preço superou a MM200 e pode indicar o início de uma tendência de alta.")
            st.markdown("<span style='color: green; font-weight: bold;'>Recomendação: Considere uma oportunidade de compra, pois o rompimento altista pode sinalizar o início de uma tendência de alta.</span>", unsafe_allow_html=True)

        # ALERTA 7: Exibição dos valores atuais dos indicadores com explicação e recomendação
        st.markdown("### Alerta 7: Confirmação com Indicadores (RSI e MACD)")
        st.markdown("""
- **RSI (Relative Strength Index):** Indica a força do movimento do preço. Valores acima de 50 sugerem pressão compradora (tendência de alta), enquanto valores abaixo de 50 apontam para pressão vendedora (tendência de baixa).
- **MACD (Moving Average Convergence Divergence):** Mede a relação entre duas médias móveis. Quando o MACD cruza acima da sua linha de sinal, confirma a tendência de alta; o cruzamento para baixo indica tendência de baixa.
""")
        st.markdown("<span style='color: green; font-weight: bold;'>Recomendação: Utilize os indicadores RSI e MACD para confirmar os sinais e ajustar sua estratégia de investimento conforme a situação do mercado.</span>", unsafe_allow_html=True)

        # Exibição dos valores atuais em campos de texto (somente leitura)
        st.text_input("RSI Atual", f"{current['RSI']:.2f}", disabled=True)
        st.text_input("MACD Atual", f"{current['MACD']:.2f}", disabled=True)
        st.text_input("MACD Signal", f"{current['Signal']:.2f}", disabled=True)
        st.text_input("MM200", f"{current['MM200']:.2f}", disabled=True)
        st.text_input("Preço Atual", f"{current['Close']:.2f}", disabled=True)

    # Gráficos de Volume e Dividendos (se disponíveis)
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

    # Resumo Final dos Indicadores e Recomendação Geral
    if len(df_cut) >= 2:
        current = df_cut.iloc[-1]
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

        # Recomendação geral baseada na análise dos indicadores
        if current['RSI'] > 50 and current['MACD'] > current['Signal'] and current['Close'] > current['MM200']:
            rec = "<span style='color: green; font-weight: bold;'>Tendência Altista: Recomenda-se manter ou aumentar posições de compra.</span>"
        elif current['RSI'] < 50 and current['MACD'] < current['Signal'] and current['Close'] < current['MM200']:
            rec = "<span style='color: red; font-weight: bold;'>Tendência Baixista: Recomenda-se cautela, redução de posições ou proteção dos investimentos.</span>"
        else:
            rec = "<span style='color: orange; font-weight: bold;'>Sinal Neutro/Misto: Aguarde confirmações adicionais antes de tomar uma decisão.</span>"

        st.markdown("### Resumo da Recomendação")
        st.markdown(rec, unsafe_allow_html=True)
else:
    st.write("Coluna 'Close' não encontrada ou sem dados.")
