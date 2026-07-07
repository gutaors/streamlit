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

# CSS estrutural da tabela (cores via inline style nas células)
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
</style>
""", unsafe_allow_html=True)


def _rec_cell(val: str) -> str:
    if val == "COMPRAR":
        return "<td style='color:#4ade80;font-weight:700;text-align:center'>📈 COMPRAR</td>"
    elif val == "VENDER":
        return "<td style='color:#f87171;font-weight:700;text-align:center'>📉 VENDER</td>"
    elif val == "MANTER":
        return "<td style='color:#fbbf24;font-weight:700;text-align:center'>⚖️ MANTER</td>"
    else:
        return "<td style='color:#6b7280;text-align:center'>—</td>"


def _dias_cell(val: str) -> str:
    if val == "N/A":
        return "<td style='color:#6b7280;text-align:center'>N/A</td>"
    elif val == "Ainda não":
        return "<td style='color:#f59e0b;text-align:center'>⏳ Ainda não</td>"
    else:
        return f"<td style='color:#4ade80;font-weight:700;text-align:center'>✅ {val} dias</td>"


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

# ── Análise de acertos por algoritmo ─────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Análise de Desempenho dos Algoritmos")

# Classificar cada linha por algoritmo
# "Acerto" = a coluna Dias até +10% tem um número (ou seja, houve lucro ≥ 10%)
def _lucrou(dias_str) -> bool:
    try:
        int(dias_str)
        return True
    except (ValueError, TypeError):
        return False

df_result["_lucrou"] = df_result["Dias até +10%"].apply(_lucrou)

# Apenas linhas onde cada algoritmo recomendou COMPRAR
stats = {}
for algo, col in [("Prophet", "Rec. Prophet"), ("Séries", "Rec. Séries"), ("Torch", "Rec. Torch")]:
    sub = df_result[df_result[col] == "COMPRAR"]
    total_compras = len(sub)
    acertos       = sub["_lucrou"].sum()
    erros         = total_compras - acertos
    pct           = (acertos / total_compras * 100) if total_compras > 0 else 0.0
    stats[algo]   = {"total": total_compras, "acertos": acertos, "erros": erros, "pct": pct}

# Ranking
ranking = sorted(stats.items(), key=lambda x: x[1]["pct"], reverse=True)
melhor_algo, melhor_stat = ranking[0]

# ── Métricas rápidas ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
for col, (algo, s) in zip([col1, col2, col3], ranking):
    medal = "🥇" if algo == melhor_algo else ("🥈" if ranking.index((algo, s)) == 1 else "🥉")
    col.metric(
        label=f"{medal} {algo}",
        value=f"{s['pct']:.0f}% de acerto",
        delta=f"{s['acertos']} acertos de {s['total']} compras",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabela detalhada por algoritmo ────────────────────────────────────────────
def _cor_pct(pct: float) -> str:
    if pct >= 60:   return "#4ade80"
    elif pct >= 40: return "#fbbf24"
    else:           return "#f87171"

def _barra(pct: float, cor: str) -> str:
    w = int(pct)
    return (
        f"<div style='background:#1e293b;border-radius:4px;height:10px;width:100%;overflow:hidden'>"
        f"<div style='background:{cor};height:10px;width:{w}%;border-radius:4px'></div></div>"
    )

html_det = (
    "<table style='width:100%;border-collapse:collapse;font-family:Segoe UI,sans-serif;font-size:0.86rem'>"
    "<thead><tr>"
    "<th style='background:#1e293b;color:#94a3b8;padding:10px 14px;text-align:left;"
    "font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #334155'>Algoritmo</th>"
    "<th style='background:#1e293b;color:#94a3b8;padding:10px 14px;text-align:center;"
    "font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #334155'>Compras sinalizadas</th>"
    "<th style='background:#1e293b;color:#94a3b8;padding:10px 14px;text-align:center;"
    "font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #334155'>✅ Acertos</th>"
    "<th style='background:#1e293b;color:#94a3b8;padding:10px 14px;text-align:center;"
    "font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #334155'>❌ Erros</th>"
    "<th style='background:#1e293b;color:#94a3b8;padding:10px 14px;text-align:center;"
    "font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #334155'>% Acerto</th>"
    "<th style='background:#1e293b;color:#94a3b8;padding:10px 14px;text-align:left;"
    "font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #334155'>Barra</th>"
    "</tr></thead><tbody>"
)

for i, (algo, s) in enumerate(ranking):
    medal = ["🥇", "🥈", "🥉"][i]
    cor   = _cor_pct(s["pct"])
    html_det += (
        f"<tr style='border-bottom:1px solid #1e293b'>"
        f"<td style='padding:10px 14px;color:#e2e8f0;font-weight:700'>{medal} {algo}</td>"
        f"<td style='padding:10px 14px;text-align:center;color:#94a3b8'>{s['total']}</td>"
        f"<td style='padding:10px 14px;text-align:center;color:#4ade80;font-weight:700'>{s['acertos']}</td>"
        f"<td style='padding:10px 14px;text-align:center;color:#f87171;font-weight:700'>{s['erros']}</td>"
        f"<td style='padding:10px 14px;text-align:center;color:{cor};font-weight:800'>{s['pct']:.1f}%</td>"
        f"<td style='padding:10px 14px;min-width:160px'>{_barra(s['pct'], cor)}</td>"
        f"</tr>"
    )

html_det += "</tbody></table>"
st.markdown(html_det, unsafe_allow_html=True)

# ── Consenso: todos os três recomendam COMPRAR ────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 🤝 Consenso — quando os três algoritmos recomendam COMPRAR")

df_consenso = df_result[
    (df_result["Rec. Prophet"] == "COMPRAR") &
    (df_result["Rec. Séries"]  == "COMPRAR") &
    (df_result["Rec. Torch"]   == "COMPRAR")
].copy()

n_consenso  = len(df_consenso)
n_acerto_c  = df_consenso["_lucrou"].sum()
n_erro_c    = n_consenso - n_acerto_c
pct_c       = (n_acerto_c / n_consenso * 100) if n_consenso > 0 else 0.0
cor_c       = _cor_pct(pct_c)

if n_consenso == 0:
    st.info("Nenhuma linha com os três algoritmos recomendando COMPRAR ao mesmo tempo nesta amostra.")
else:
    dias_consenso_validos = df_consenso[df_consenso["_lucrou"]]["Dias até +10%"].astype(int)
    media_c   = dias_consenso_validos.mean()   if not dias_consenso_validos.empty else 0
    mediana_c = dias_consenso_validos.median() if not dias_consenso_validos.empty else 0

    cc1, cc2, cc3, cc4, cc5 = st.columns(5)
    cc1.metric("Casos de consenso", n_consenso)
    cc2.metric("✅ Lucraram ≥ 10%", n_acerto_c)
    cc3.metric("❌ Não lucraram", n_erro_c)
    cc4.metric("% Acerto consenso", f"{pct_c:.0f}%")
    cc5.metric("Média dias (consenso)", f"{media_c:.0f}" if media_c else "—")

    # Veredicto final
    if pct_c >= 60:
        v_bg, v_bord, v_cor, v_icon = "#052e16", "#16a34a", "#4ade80", "🏆"
        v_msg = f"Quando os três algoritmos concordam em COMPRAR, o acerto é de <b>{pct_c:.0f}%</b> — sinal forte e confiável."
    elif pct_c >= 40:
        v_bg, v_bord, v_cor, v_icon = "#1c1400", "#d97706", "#fbbf24", "⚖️"
        v_msg = f"Consenso de compra com <b>{pct_c:.0f}%</b> de acerto — razoável, mas use com outros critérios."
    else:
        v_bg, v_bord, v_cor, v_icon = "#2d0a0a", "#dc2626", "#f87171", "⚠️"
        v_msg = f"Consenso de compra com apenas <b>{pct_c:.0f}%</b> de acerto nesta amostra — sinais conflitantes."

    st.markdown(
        f"<div style='background:{v_bg};border:1px solid {v_bord};border-radius:12px;"
        f"padding:16px 20px;margin-top:12px'>"
        f"<div style='font-size:1.1rem;font-weight:800;color:{v_cor};margin-bottom:6px'>{v_icon} Veredicto do Consenso</div>"
        f"<div style='font-size:0.9rem;color:#cbd5e1;line-height:1.6'>{v_msg}</div>"
        f"<div style='font-size:0.8rem;color:#94a3b8;margin-top:8px'>"
        f"Média de {media_c:.0f} dias · Mediana de {mediana_c:.0f} dias para atingir +10% nos casos de acerto."
        f"</div></div>",
        unsafe_allow_html=True,
    )

# ── Melhor algoritmo ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
cor_m = _cor_pct(melhor_stat["pct"])
st.markdown(
    f"<div style='background:#0f172a;border:1px solid #334155;border-radius:12px;"
    f"padding:16px 20px'>"
    f"<div style='font-size:0.72rem;color:#94a3b8;text-transform:uppercase;"
    f"letter-spacing:0.1em;margin-bottom:6px'>🏅 Melhor algoritmo desta amostra</div>"
    f"<div style='font-size:1.4rem;font-weight:900;color:{cor_m}'>"
    f"🥇 {melhor_algo} — {melhor_stat['pct']:.0f}% de acerto</div>"
    f"<div style='font-size:0.85rem;color:#94a3b8;margin-top:6px'>"
    f"{melhor_stat['acertos']} acertos · {melhor_stat['erros']} erros · "
    f"{melhor_stat['total']} sinais de compra nesta amostra de {len(df_result)} previsões.</div>"
    f"</div>",
    unsafe_allow_html=True,
)

