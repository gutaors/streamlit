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

        # ─────────────────────────────────────────────────────────────────────
        # TABELA CONSOLIDADA DE RECOMENDAÇÕES
        # ─────────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("## 📊 Tabela Consolidada de Recomendações")
        st.caption(
            "Recomendações calculadas com base nos dados históricos disponíveis até a data de corte selecionada. "
            "Prophet e Precificação (Graham) são calculados apenas para o ticker selecionado acima."
        )

        import numpy as np

        # ── helpers ──────────────────────────────────────────────────────────
        def _cell(label: str) -> str:
            """Retorna HTML de célula colorida por recomendação."""
            if label == "COMPRA":
                return "<td style='color:#22c55e;font-weight:700;text-align:center'>🟢 COMPRA</td>"
            elif label == "VENDA":
                return "<td style='color:#ef4444;font-weight:700;text-align:center'>🔴 VENDA</td>"
            elif label == "NEUTRO":
                return "<td style='color:#f59e0b;font-weight:700;text-align:center'>🟡 NEUTRO</td>"
            else:
                return "<td style='color:#6b7280;text-align:center'>—</td>"

        def _rec_indicadores(df_ticker: pd.DataFrame) -> str:
            """Recomendação: MM200 + RSI + MACD."""
            if len(df_ticker) < 2:
                return "—"
            try:
                df_ticker = df_ticker.copy()
                df_ticker['_mm200'] = df_ticker['Close'].rolling(200).mean()
                delta = df_ticker['Close'].diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                df_ticker['_rsi'] = 100 - (100 / (1 + rs))
                ema12 = df_ticker['Close'].ewm(span=12, adjust=False).mean()
                ema26 = df_ticker['Close'].ewm(span=26, adjust=False).mean()
                df_ticker['_macd'] = ema12 - ema26
                df_ticker['_signal'] = df_ticker['_macd'].ewm(span=9, adjust=False).mean()
                df_ticker.dropna(subset=['_mm200', '_rsi', '_macd', '_signal'], inplace=True)
                if df_ticker.empty:
                    return "—"
                c = df_ticker.iloc[-1]
                if c['_rsi'] > 50 and c['_macd'] > c['_signal'] and c['Close'] > c['_mm200']:
                    return "COMPRA"
                elif c['_rsi'] < 50 and c['_macd'] < c['_signal'] and c['Close'] < c['_mm200']:
                    return "VENDA"
                else:
                    return "NEUTRO"
            except Exception:
                return "—"

        def _rec_sma_cross(df_ticker: pd.DataFrame) -> str:
            """Recomendação: SMA50 × SMA200 (Golden/Death Cross)."""
            if len(df_ticker) < 200:
                return "—"
            try:
                sma50  = df_ticker['Close'].rolling(50).mean().iloc[-1]
                sma200 = df_ticker['Close'].rolling(200).mean().iloc[-1]
                if np.isnan(sma50) or np.isnan(sma200):
                    return "—"
                return "COMPRA" if sma50 > sma200 else "VENDA"
            except Exception:
                return "—"

        def _rec_prophet(df_ticker: pd.DataFrame, meses: int = 6) -> str:
            """Recomendação via Prophet (lento — só para o ticker selecionado)."""
            try:
                from prophet import Prophet
                df_p = df_ticker[['Close']].copy()
                df_p.reset_index(inplace=True)
                df_p.rename(columns={'Date': 'ds', 'Close': 'y'}, inplace=True)
                df_p['ds'] = pd.to_datetime(df_p['ds'])
                modelo = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
                modelo.fit(df_p)
                futuro = modelo.make_future_dataframe(periods=meses * 30)
                prev = modelo.predict(futuro)
                yhat_final = prev.iloc[-1]['yhat']
                ultimo_real = float(df_ticker['Close'].iloc[-1])
                return "COMPRA" if yhat_final > ultimo_real else "VENDA"
            except Exception:
                return "—"

        def _rec_graham(ticker_str: str) -> str:
            """Recomendação via Fórmula de Graham usando yfinance."""
            try:
                import yfinance as yf
                t = yf.Ticker(ticker_str)
                info = t.info
                lpa = info.get('trailingEps', None)
                vpa = info.get('bookValue', None)
                preco = info.get('currentPrice', info.get('previousClose', None))
                if lpa and vpa and preco and lpa > 0 and vpa > 0:
                    preco_justo = np.sqrt(22.5 * lpa * vpa)
                    return "COMPRA" if preco_justo > preco else "VENDA"
                return "—"
            except Exception:
                return "—"

        # ── Calcular recomendações para todos os tickers ──────────────────────
        with st.spinner("Calculando recomendações para todos os ativos..."):
            # Prophet e Graham só para o ticker selecionado
            prophet_rec_sel  = None
            graham_rec_sel   = None

            linhas_tabela = []
            for tk in arquivos_csv:
                caminho_tk = os.path.join(pasta_cotacoes, tk + '.csv')
                try:
                    df_tk = pd.read_csv(caminho_tk)
                    if 'Date' in df_tk.columns:
                        df_tk['Date'] = pd.to_datetime(df_tk['Date'], errors='coerce')
                        df_tk.dropna(subset=['Date'], inplace=True)
                        df_tk.set_index('Date', inplace=True)
                        df_tk.sort_index(inplace=True)
                    df_tk['Close'] = pd.to_numeric(df_tk.get('Close', pd.Series(dtype=float)), errors='coerce')
                    df_tk.dropna(subset=['Close'], inplace=True)
                    df_tk = df_tk[df_tk.index <= pd.to_datetime(cut_date)]

                    rec_ind  = _rec_indicadores(df_tk)
                    rec_sma  = _rec_sma_cross(df_tk)

                    if tk == ticker_simbolo:
                        with st.spinner(f"Calculando Prophet para {tk}..."):
                            prophet_rec_sel = _rec_prophet(df_tk)
                        with st.spinner(f"Buscando dados Graham para {tk}..."):
                            graham_rec_sel = _rec_graham(tk)
                        rec_prophet = prophet_rec_sel
                        rec_graham  = graham_rec_sel
                    else:
                        rec_prophet = "N/D"
                        rec_graham  = "N/D"

                    linhas_tabela.append({
                        'ticker':      tk,
                        'indicadores': rec_ind,
                        'sma_cross':   rec_sma,
                        'prophet':     rec_prophet,
                        'graham':      rec_graham,
                    })
                except Exception:
                    linhas_tabela.append({
                        'ticker':      tk,
                        'indicadores': '—',
                        'sma_cross':   '—',
                        'prophet':     'N/D',
                        'graham':      'N/D',
                    })

        # ── Renderizar a tabela HTML ──────────────────────────────────────────
        st.markdown("""
        <style>
        .rec-table { width:100%; border-collapse:collapse; font-family:'Segoe UI',sans-serif; }
        .rec-table thead th {
            background:#1e293b; color:#94a3b8;
            font-size:0.75rem; font-weight:700;
            text-transform:uppercase; letter-spacing:0.06em;
            padding:10px 14px; border-bottom:1px solid #334155;
            text-align:center;
        }
        .rec-table thead th:first-child { text-align:left; }
        .rec-table tbody tr { border-bottom:1px solid #1e293b; transition:background 0.15s; }
        .rec-table tbody tr:hover { background:rgba(255,255,255,0.03); }
        .rec-table tbody td { padding:9px 14px; font-size:0.88rem; color:#e2e8f0; }
        .rec-table .pct-alta  { color:#22c55e; font-weight:700; text-align:center; }
        .rec-table .pct-venda { color:#ef4444; font-weight:700; text-align:center; }
        .rec-table .pct-neutro{ color:#f59e0b; font-weight:700; text-align:center; }
        .rec-table .ticker-col{ color:#93c5fd; font-weight:700; }
        .row-alta  { background:rgba(34,197,94,0.06)  !important; }
        .row-venda { background:rgba(239,68,68,0.06)  !important; }
        </style>
        """, unsafe_allow_html=True)

        cabecalho = """
        <table class="rec-table">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Indicadores<br><small>MM200 · RSI · MACD</small></th>
              <th>Médias Móveis<br><small>SMA50 × SMA200</small></th>
              <th>Prophet<br><small>Previsão futura</small></th>
              <th>Precificação<br><small>Graham</small></th>
              <th>% Compra</th>
            </tr>
          </thead>
          <tbody>
        """

        corpo = ""
        for r in linhas_tabela:
            # Contar recomendações (apenas as que têm valor definido: COMPRA ou VENDA)
            todas = [r['indicadores'], r['sma_cross'], r['prophet'], r['graham']]
            validas = [v for v in todas if v in ('COMPRA', 'VENDA', 'NEUTRO')]
            n_compra = sum(1 for v in validas if v == 'COMPRA')
            pct = (n_compra / len(validas) * 100) if validas else 0.0

            if pct >= 75:
                row_cls = "row-alta"
                pct_cls = "pct-alta"
                pct_icon = "🟢"
            elif pct <= 25:
                row_cls = "row-venda"
                pct_cls = "pct-venda"
                pct_icon = "🔴"
            else:
                row_cls = ""
                pct_cls = "pct-neutro"
                pct_icon = "🟡"

            tk_nome = r['ticker'].replace('.SA', '')
            sel_mark = " ★" if r['ticker'] == ticker_simbolo else ""

            corpo += f"""
            <tr class="{row_cls}">
              <td class="ticker-col">{tk_nome}{sel_mark}</td>
              {_cell(r['indicadores'])}
              {_cell(r['sma_cross'])}
              {_cell(r['prophet'])}
              {_cell(r['graham'])}
              <td class="{pct_cls}">{pct_icon} {pct:.0f}%</td>
            </tr>
            """

        rodape = "</tbody></table>"
        st.markdown(cabecalho + corpo + rodape, unsafe_allow_html=True)

        st.caption(
            "★ = ticker selecionado no filtro | "
            "N/D = modelo não executado para este ticker | "
            "— = dados insuficientes para calcular"
        )
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
