import streamlit as st
import pandas as pd
import numpy as np
import os
import random
from datetime import date, timedelta

st.set_page_config(page_title="Testa Datas", layout="wide")

st.title("🔬 Testa Datas")
st.markdown(
    "Sorteia **10 datas** aleatórias desde a data escolhida até hoje, "
    "roda os modelos de previsão para todos os tickers e verifica se houve lucro de ≥ 10%."
)

st.info(
    "⏳ O primeiro carregamento pode levar alguns minutos — Prophet treina um modelo por ticker × data. "
    "Resultados ficam em cache: trocar de data sorteia novas datas e recalcula apenas as combinações novas.",
    icon="ℹ️",
)

# ── Configuração ──────────────────────────────────────────────────────────────
PASTA_COTACOES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cotacoes")
tickers = sorted([f.replace(".csv", "") for f in os.listdir(PASTA_COTACOES) if f.endswith(".csv")])

# ── Filtro de data ─────────────────────────────────────────────────────────────
col_fi, col_sp = st.columns([1, 3])
with col_fi:
    data_inicial = st.date_input(
        "📅 Data Inicial",
        value=date.today() - timedelta(days=365),
        max_value=date.today() - timedelta(days=30),
    )

today = date.today()
delta_days = (today - data_inicial).days

if delta_days < 10:
    st.error("A data inicial deve ser de pelo menos 10 dias atrás.")
    st.stop()

# ── Sortear 10 datas ──────────────────────────────────────────────────────────
# Usar a data inicial como seed para as datas serem reprodutíveis
random.seed(str(data_inicial))
_candidatas = [data_inicial + timedelta(days=i) for i in range(1, delta_days)]
datas_sorteadas = sorted(random.sample(_candidatas, min(10, len(_candidatas))))

st.markdown(f"**Datas sorteadas:** {' · '.join(d.strftime('%d/%m/%Y') for d in datas_sorteadas)}")
st.markdown("---")

# ── Funções de carregamento e cálculo ─────────────────────────────────────────

@st.cache_data(show_spinner=False)
def carregar_ticker(ticker: str) -> pd.DataFrame:
    path = os.path.join(PASTA_COTACOES, ticker + ".csv")
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date"], inplace=True)
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df.dropna(subset=["Close"], inplace=True)
    return df


def rec_series(df_ate: pd.DataFrame) -> str:
    """SMA50 × SMA200 (Golden/Death Cross)."""
    if len(df_ate) < 200:
        return "—"
    sma50  = df_ate["Close"].rolling(50).mean().iloc[-1]
    sma200 = df_ate["Close"].rolling(200).mean().iloc[-1]
    if np.isnan(sma50) or np.isnan(sma200):
        return "—"
    return "COMPRAR" if sma50 > sma200 else "VENDER"


def rec_torch(df_ate: pd.DataFrame) -> str:
    """MM200 + RSI + MACD (indicadores técnicos)."""
    if len(df_ate) < 200:
        return "—"
    try:
        df = df_ate.copy()
        df["mm200"] = df["Close"].rolling(200).mean()
        _d = df["Close"].diff()
        _g = _d.clip(lower=0).rolling(14).mean()
        _l = (-_d.clip(upper=0)).rolling(14).mean()
        _rs = _g / _l.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + _rs))
        e12 = df["Close"].ewm(span=12, adjust=False).mean()
        e26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["macd"]   = e12 - e26
        df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df.dropna(subset=["mm200", "rsi", "macd", "signal"], inplace=True)
        if df.empty:
            return "—"
        c = df.iloc[-1]
        if c["rsi"] > 50 and c["macd"] > c["signal"] and c["Close"] > c["mm200"]:
            return "COMPRAR"
        elif c["rsi"] < 50 and c["macd"] < c["signal"] and c["Close"] < c["mm200"]:
            return "VENDER"
        return "MANTER"
    except Exception:
        return "—"


@st.cache_data(show_spinner=False)
def rec_prophet_cached(ticker: str, data_ref_str: str) -> str:
    """Recomendação Prophet — cacheada por (ticker, data)."""
    try:
        from prophet import Prophet
        df_full = carregar_ticker(ticker)
        df_ate  = df_full[df_full.index <= pd.to_datetime(data_ref_str)].copy()
        if len(df_ate) < 60:
            return "—"
        df_p = df_ate[["Close"]].copy()
        df_p.reset_index(inplace=True)
        df_p.rename(columns={"Date": "ds", "Close": "y"}, inplace=True)
        df_p["ds"] = pd.to_datetime(df_p["ds"])
        modelo = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        modelo.fit(df_p)
        futuro = modelo.make_future_dataframe(periods=180)
        prev = modelo.predict(futuro)
        yhat  = float(prev.iloc[-1]["yhat"])
        atual = float(df_ate["Close"].iloc[-1])
        return "COMPRAR" if yhat > atual else "VENDER"
    except Exception:
        return "—"


def dias_ate_10pct(df_full: pd.DataFrame, data_ref: date, preco_ref: float):
    """Retorna dias até o preço subir ≥ 10% a partir de data_ref."""
    alvo = preco_ref * 1.10
    df_fut = df_full[df_full.index > pd.to_datetime(data_ref)]
    mask = df_fut["Close"] >= alvo
    if mask.any():
        data_lucro = df_fut[mask].index[0]
        return (data_lucro.date() - data_ref).days
    return None


# ── Loop de cálculo ───────────────────────────────────────────────────────────
total_ops = len(datas_sorteadas) * len(tickers)
progresso = st.progress(0, text="Iniciando cálculos…")
status_txt = st.empty()
resultados = []
op = 0

for data_ref in datas_sorteadas:
    data_str = str(data_ref)
    for tk in tickers:
        op += 1
        status_txt.markdown(
            f"<span style='color:#94a3b8;font-size:0.82rem'>⚙️ {tk.replace('.SA','')} · {data_ref.strftime('%d/%m/%Y')} ({op}/{total_ops})</span>",
            unsafe_allow_html=True,
        )
        progresso.progress(op / total_ops)

        try:
            df_full = carregar_ticker(tk)
            df_ate  = df_full[df_full.index <= pd.to_datetime(data_str)].copy()

            if df_ate.empty:
                continue

            preco_data  = float(df_ate["Close"].iloc[-1])
            preco_atual = float(df_full["Close"].iloc[-1])

            r_prophet = rec_prophet_cached(tk, data_str)
            r_series  = rec_series(df_ate)
            r_torch   = rec_torch(df_ate)

            # Dias até +10% — só calcula se ao menos uma rec for COMPRAR
            if "COMPRAR" in (r_prophet, r_series, r_torch):
                dias = dias_ate_10pct(df_full, data_ref, preco_data)
                dias_str = str(dias) if dias is not None else "Ainda não"
            else:
                dias_str = "N/A"

            resultados.append({
                "_data_ref":       data_ref,
                "_ticker_raw":     tk,
                "Ticker":          tk.replace(".SA", ""),
                "Data Previsão":   data_ref.strftime("%d/%m/%Y"),
                "Valor na Data":   preco_data,
                "Rec. Prophet":    r_prophet,
                "Rec. Séries":     r_series,
                "Rec. Torch":      r_torch,
                "Dias até +10%":   dias_str,
                "Valor Atual":     preco_atual,
            })

        except Exception as e:
            pass  # pula tickers com erro silenciosamente

progresso.empty()
status_txt.empty()

# ── Renderizar tabela ─────────────────────────────────────────────────────────
if not resultados:
    st.warning("Nenhum resultado gerado. Verifique os arquivos de cotações.")
    st.stop()

df_result = pd.DataFrame(resultados)

# CSS da tabela
st.markdown("""
<style>
.td-table { width:100%; border-collapse:collapse; font-family:'Segoe UI',sans-serif; font-size:0.84rem; }
.td-table thead th {
    background:#1e293b; color:#94a3b8;
    font-size:0.72rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.06em; padding:10px 12px;
    border-bottom:2px solid #334155; text-align:center; white-space:nowrap;
}
.td-table thead th:first-child, .td-table thead th:nth-child(2) { text-align:left; }
.td-table tbody tr { border-bottom:1px solid #1e293b; }
.td-table tbody tr:hover { background:rgba(255,255,255,0.025); }
.td-table tbody td { padding:8px 12px; color:#e2e8f0; text-align:center; }
.td-table tbody td:first-child, .td-table tbody td:nth-child(2) { text-align:left; }
.td-table .date-group { background:#0f172a; color:#475569;
    font-size:0.72rem; font-weight:700; letter-spacing:0.1em;
    text-transform:uppercase; padding:6px 12px; }
.tk { color:#93c5fd; font-weight:700; }
.comprar { color:#4ade80; font-weight:700; }
.vender  { color:#f87171; font-weight:700; }
.manter  { color:#fbbf24; font-weight:700; }
.neutro  { color:#6b7280; }
.dias-ok { color:#4ade80; font-weight:700; }
.dias-no { color:#f59e0b; }
.dias-na { color:#6b7280; }
.val     { font-variant-numeric: tabular-nums; }
</style>
""", unsafe_allow_html=True)


def _rec_cell(val: str) -> str:
    if val == "COMPRAR":
        return f"<td class='comprar'>📈 COMPRAR</td>"
    elif val == "VENDER":
        return f"<td class='vender'>📉 VENDER</td>"
    elif val == "MANTER":
        return f"<td class='manter'>⚖️ MANTER</td>"
    else:
        return f"<td class='neutro'>—</td>"


def _dias_cell(val: str) -> str:
    if val == "N/A":
        return "<td class='dias-na'>N/A</td>"
    elif val == "Ainda não":
        return "<td class='dias-no'>⏳ Ainda não</td>"
    else:
        return f"<td class='dias-ok'>✅ {val} dias</td>"


cabecalho = """
<table class="td-table">
  <thead>
    <tr>
      <th>Ticker</th>
      <th>Data Previsão</th>
      <th>Valor na Data</th>
      <th>Rec. Prophet</th>
      <th>Rec. Séries</th>
      <th>Rec. Torch</th>
      <th>Dias até +10%</th>
      <th>Valor Atual</th>
    </tr>
  </thead>
  <tbody>
"""

corpo = ""
ultima_data = None

for _, row in df_result.sort_values(["Data Previsão", "Ticker"]).iterrows():
    # Separador de data
    if row["Data Previsão"] != ultima_data:
        ultima_data = row["Data Previsão"]
        corpo += (
            f"<tr><td colspan='8' class='date-group'>"
            f"📅 &nbsp;{ultima_data}"
            f"</td></tr>"
        )

    var_pct = ((row["Valor Atual"] - row["Valor na Data"]) / row["Valor na Data"] * 100) if row["Valor na Data"] else 0
    var_cor = "comprar" if var_pct >= 0 else "vender"

    corpo += (
        f"<tr>"
        f"<td class='tk'>{row['Ticker']}</td>"
        f"<td>{row['Data Previsão']}</td>"
        f"<td class='val'>R$ {row['Valor na Data']:.2f}</td>"
        f"{_rec_cell(row['Rec. Prophet'])}"
        f"{_rec_cell(row['Rec. Séries'])}"
        f"{_rec_cell(row['Rec. Torch'])}"
        f"{_dias_cell(row['Dias até +10%'])}"
        f"<td class='val {var_cor}'>R$ {row['Valor Atual']:.2f} "
        f"<small>({'+' if var_pct>=0 else ''}{var_pct:.1f}%)</small></td>"
        f"</tr>"
    )

rodape = "</tbody></table>"

st.markdown(cabecalho + corpo + rodape, unsafe_allow_html=True)

# ── Resumo estatístico ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Resumo")

total_linhas = len(df_result)
dias_validos = df_result[df_result["Dias até +10%"].apply(lambda x: x not in ("N/A", "Ainda não", "—"))]
acertos      = len(dias_validos)
pct_acerto   = acertos / total_linhas * 100 if total_linhas else 0

if not dias_validos.empty:
    media_dias = dias_validos["Dias até +10%"].astype(int).mean()
    mediana_dias = dias_validos["Dias até +10%"].astype(int).median()
else:
    media_dias = mediana_dias = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de previsões", total_linhas)
col2.metric("Lucraram ≥ 10%", acertos, f"{pct_acerto:.0f}%")
col3.metric("Média de dias", f"{media_dias:.0f}" if media_dias else "—")
col4.metric("Mediana de dias", f"{mediana_dias:.0f}" if mediana_dias else "—")
