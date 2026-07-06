import streamlit as st
import os
import pandas as pd
from datetime import date
import datetime as dt

# Configuração única da página (deve ser chamada antes de qualquer outra função Streamlit)
st.set_page_config(page_title="Stock Analysis App", layout="wide")

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

# ══════════════════════════════════════════════════════════════════════════════
# PAINEL DE RECOMENDAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
import numpy as np

def _painel_rec(label: str, valor: str, detalhe: str = "") -> str:
    """Gera um card HTML colorido para o painel."""
    l = label.upper()
    if l == "COMPRAR":
        bg, border, cor, icon = "#052e16", "#16a34a", "#4ade80", "📈"
    elif l == "VENDER":
        bg, border, cor, icon = "#2d0a0a", "#dc2626", "#f87171", "📉"
    elif l == "MANTER":
        bg, border, cor, icon = "#1c1400", "#d97706", "#fbbf24", "⚖️"
    else:
        bg, border, cor, icon = "#1e293b", "#475569", "#94a3b8", "—"
    det = f"<div style='font-size:0.72rem;color:{cor};opacity:0.8;margin-top:4px'>{detalhe}</div>" if detalhe else ""
    return (f"<div style='background:{bg};border:1px solid {border};border-radius:10px;padding:14px 18px;text-align:center;min-width:130px'>" +
            f"<div style='font-size:0.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px'>{valor}</div>" +
            f"<div style='font-size:1.05rem;font-weight:800;color:{cor}'>{icon} {l}</div>" +
            det + "</div>")

def _painel_valor(label: str, valor: str, sub: str = "", destaque: str = "neutro") -> str:
    """Card de valor numérico com cor opcional."""
    if destaque == "positivo":
        cor, bg, border = "#4ade80", "#052e16", "#16a34a"
    elif destaque == "negativo":
        cor, bg, border = "#f87171", "#2d0a0a", "#dc2626"
    else:
        cor, bg, border = "#e2e8f0", "#1e293b", "#334155"
    sub_h = f"<div style='font-size:0.7rem;color:#94a3b8;margin-top:2px'>{sub}</div>" if sub else ""
    return (f"<div style='background:{bg};border:1px solid {border};border-radius:10px;padding:14px 18px;text-align:center;min-width:130px'>" +
            f"<div style='font-size:0.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px'>{label}</div>" +
            f"<div style='font-size:1.15rem;font-weight:800;color:{cor}'>{valor}</div>" +
            sub_h + "</div>")

# ── Calcular todos os indicadores ────────────────────────────────────────────
df_painel = df_cut.copy()
df_painel['Close'] = pd.to_numeric(df_painel['Close'], errors='coerce')
df_painel.dropna(subset=['Close'], inplace=True)

preco_atual = float(df_painel['Close'].iloc[-1]) if not df_painel.empty else None

# --- Rec. MM (RSI + MACD + MM200) ---
rec_mm = "sem dados"
if preco_atual and len(df_painel) >= 200:
    df_painel['_mm200'] = df_painel['Close'].rolling(200).mean()
    _delta = df_painel['Close'].diff()
    _gain = _delta.clip(lower=0).rolling(14).mean()
    _loss = (-_delta.clip(upper=0)).rolling(14).mean()
    _rs = _gain / _loss.replace(0, np.nan)
    df_painel['_rsi'] = 100 - (100 / (1 + _rs))
    _ema12 = df_painel['Close'].ewm(span=12, adjust=False).mean()
    _ema26 = df_painel['Close'].ewm(span=26, adjust=False).mean()
    df_painel['_macd'] = _ema12 - _ema26
    df_painel['_signal'] = df_painel['_macd'].ewm(span=9, adjust=False).mean()
    _c = df_painel.iloc[-1]
    if _c['_rsi'] > 50 and _c['_macd'] > _c['_signal'] and _c['Close'] > _c['_mm200']:
        rec_mm = "COMPRAR"
    elif _c['_rsi'] < 50 and _c['_macd'] < _c['_signal'] and _c['Close'] < _c['_mm200']:
        rec_mm = "VENDER"
    else:
        rec_mm = "MANTER"
    val_mm200 = _c['_mm200']
else:
    val_mm200 = None

# --- Rec. SMA Cross (proxy Torch) ---
rec_torch = "sem dados"
if preco_atual and len(df_painel) >= 200:
    _sma50  = df_painel['Close'].rolling(50).mean().iloc[-1]
    _sma200 = df_painel['Close'].rolling(200).mean().iloc[-1]
    if not (np.isnan(_sma50) or np.isnan(_sma200)):
        rec_torch = "COMPRAR" if _sma50 > _sma200 else "VENDER"

# --- Rec. Prophet ---
rec_prophet = "sem dados"
preco_prophet = None
try:
    from prophet import Prophet as _Prophet
    _df_p = df_painel[['Close']].copy()
    _df_p.reset_index(inplace=True)
    _df_p.rename(columns={'Date': 'ds', 'Close': 'y'}, inplace=True)
    _df_p['ds'] = pd.to_datetime(_df_p['ds'])
    _modelo = _Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    _modelo.fit(_df_p)
    _futuro = _modelo.make_future_dataframe(periods=180)
    _prev = _modelo.predict(_futuro)
    preco_prophet = float(_prev.iloc[-1]['yhat'])
    if preco_atual:
        rec_prophet = "COMPRAR" if preco_prophet > preco_atual else "VENDER"
except Exception:
    rec_prophet = "sem dados"

# --- Graham ---
rec_graham = "sem dados"
preco_graham = None
try:
    import yfinance as _yf
    _t = _yf.Ticker(ticker_simbolo)
    _info = _t.info
    _lpa = _info.get('trailingEps') or 0
    _vpa = _info.get('bookValue') or 0
    _preco_yf = _info.get('currentPrice') or _info.get('previousClose') or 0
    if _lpa > 0 and _vpa > 0:
        preco_graham = float(np.sqrt(22.5 * _lpa * _vpa))
        if preco_atual:
            rec_graham = "COMPRAR" if preco_graham > preco_atual else "VENDER"
except Exception:
    pass

# --- Bazin ---
preco_bazin = None
rec_bazin = "sem dados"
try:
    import yfinance as _yf
    _t2 = _yf.Ticker(ticker_simbolo)
    _divs = _t2.dividends
    if not _divs.empty:
        _div_anual = _divs.resample('YE').sum()
        _div_medio = float(_div_anual.tail(3).mean())
        if _div_medio > 0:
            preco_bazin = _div_medio / 0.06
            if preco_atual:
                rec_bazin = "COMPRAR" if preco_bazin > preco_atual else "VENDER"
except Exception:
    pass

# ── Renderizar painel ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🧭 Painel de Recomendações")

# Linha 1: valores numéricos
cards_valores = ""
if preco_atual:
    cards_valores += _painel_valor("Preço Atual", f"R$ {preco_atual:.2f}", destaque="neutro")
if val_mm200:
    destq = "positivo" if preco_atual and preco_atual > val_mm200 else "negativo"
    cards_valores += _painel_valor("MM 200", f"R$ {val_mm200:.2f}", sub="Média Móvel 200", destaque=destq)
if preco_graham:
    destq_g = "positivo" if preco_atual and preco_graham > preco_atual else "negativo"
    cards_valores += _painel_valor("Preço Justo", f"R$ {preco_graham:.2f}", sub="Graham", destaque=destq_g)
if preco_bazin:
    destq_b = "positivo" if preco_atual and preco_bazin > preco_atual else "negativo"
    cards_valores += _painel_valor("Preço Teto", f"R$ {preco_bazin:.2f}", sub="Bazin (6% DY)", destaque=destq_b)
if preco_prophet:
    destq_p = "positivo" if preco_atual and preco_prophet > preco_atual else "negativo"
    cards_valores += _painel_valor("Prev. Prophet", f"R$ {preco_prophet:.2f}", sub="6 meses", destaque=destq_p)

st.markdown(
    f"<div style='display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px'>{cards_valores}</div>",
    unsafe_allow_html=True,
)

# Linha 2: recomendações
det_prophet = f"Prev: R$ {preco_prophet:.2f}" if preco_prophet else ""
det_graham  = f"Justo: R$ {preco_graham:.2f}" if preco_graham else ""
det_bazin   = f"Teto: R$ {preco_bazin:.2f}" if preco_bazin else ""

cards_recs = (
    _painel_rec("Rec. Prophet", rec_prophet, det_prophet)
    + _painel_rec("Rec. Torch", rec_torch, "SMA50 × SMA200")
    + _painel_rec("Rec. Médias", rec_mm, "MM200 · RSI · MACD")
    + _painel_rec("Graham", rec_graham, det_graham)
    + _painel_rec("Bazin", rec_bazin, det_bazin)
)
st.markdown(
    f"<div style='display:flex;gap:12px;flex-wrap:wrap'>{cards_recs}</div>",
    unsafe_allow_html=True,
)
st.markdown("---")

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
