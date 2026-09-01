"""
╔══════════════════════════════════════════════════════════════════╗
║      3 MELHORES — Análise Combinada: Prophet + PyTorch + Score   ║
║  Elege os 3 tickers com maior probabilidade de alta combinada    ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ──────────────────────────────────────────────────────────────
#  IMPORTS
# ──────────────────────────────────────────────────────────────
import os
import warnings
from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import torch
import torch.nn as nn
from prophet import Prophet

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="3 Melhores — Previsão Combinada",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────
#  CSS CUSTOMIZADO
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #060b14 0%, #0a1020 50%, #060b14 100%);
    color: #e8f0fe;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }

/* Header */
.page-header {
    background: linear-gradient(135deg, #0d1624 0%, #111d2e 100%);
    border: 1px solid rgba(0,229,160,0.2);
    border-left: 4px solid #00e5a0;
    border-radius: 14px;
    padding: 20px 28px;
    margin-bottom: 24px;
}

.page-title {
    font-size: 28px;
    font-weight: 800;
    color: #e8f0fe;
    margin: 0 0 4px 0;
}

.page-subtitle {
    font-size: 13px;
    color: #8899bb;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin-right: 6px;
    letter-spacing: 0.5px;
}
.badge-prophet  { background: rgba(245,200,66,0.15); color: #f5c842; border: 1px solid rgba(245,200,66,0.3); }
.badge-torch    { background: rgba(79,195,247,0.15); color: #4fc3f7; border: 1px solid rgba(79,195,247,0.3); }
.badge-score    { background: rgba(0,229,160,0.15); color: #00e5a0; border: 1px solid rgba(0,229,160,0.3); }
.badge-gold     { background: linear-gradient(135deg,#f5c842,#e8a800); color: #000; border: none; }

/* Top 3 Cards */
.top-card {
    background: linear-gradient(135deg, #0d1624, #111d2e);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.top-card-1 { border-top: 3px solid #f5c842; }
.top-card-2 { border-top: 3px solid #b0bec5; }
.top-card-3 { border-top: 3px solid #cd7f32; }

.ticker-big {
    font-family: 'JetBrains Mono', monospace;
    font-size: 26px;
    font-weight: 800;
    color: #e8f0fe;
}

.score-bar-bg {
    background: rgba(255,255,255,0.06);
    border-radius: 6px;
    height: 8px;
    margin: 4px 0 2px 0;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 6px;
}

/* Return table */
.ret-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ret-table th {
    background: #0a1520;
    color: #8899bb;
    padding: 10px 14px;
    text-align: center;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.ret-table td {
    padding: 10px 14px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}
.ret-table tr:hover td { background: rgba(255,255,255,0.02); }
.pos { color: #00e5a0; }
.neg { color: #ff5252; }
.neutral { color: #8899bb; }

/* Metric mini */
.mini-metric {
    background: #0a1520;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 12px;
    text-align: center;
}
.mini-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 20px;
    font-weight: 700;
}
.mini-label {
    font-size: 10px;
    color: #4a5a78;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 2px;
}

/* stButton */
.stButton > button {
    background: linear-gradient(135deg, #00e5a0, #00b880);
    color: #000;
    font-weight: 700;
    border: none;
    border-radius: 40px;
    padding: 12px 32px;
    font-size: 15px;
    transition: all 0.2s;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,229,160,0.3);
}

/* Progress area */
.progress-label {
    font-size: 12px;
    color: #8899bb;
    margin-bottom: 4px;
}

/* Alert */
.alert-box {
    background: rgba(255,183,77,0.06);
    border: 1px solid rgba(255,183,77,0.25);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 13px;
    color: #aabdd4;
}

.total-row td {
    background: rgba(0,229,160,0.04) !important;
    border-top: 1px solid rgba(0,229,160,0.2) !important;
    font-weight: 700;
    color: #e8f0fe !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
#  CONSTANTES
# ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COTACOES_DIR = os.path.join(os.path.dirname(BASE_DIR), "cotacoes")
HORIZONTE_DIAS = 30          # horizonte de previsão dos modelos
MIN_DIAS_LSTM = 60            # mínimo de dados para LSTM
MIN_DIAS_PROPHET = 30         # mínimo de dados para Prophet
SCORE_THRESHOLD = 50.0        # limiar para "aprovado" no modelo
INVESTIMENTO = 10_000.0       # R$ por ticker


# ──────────────────────────────────────────────────────────────
#  HELPERS DE DADOS
# ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def listar_csvs() -> list[str]:
    """Lista todos os arquivos CSV disponíveis no diretório cotacoes/."""
    if not os.path.exists(COTACOES_DIR):
        return []
    return sorted([f for f in os.listdir(COTACOES_DIR) if f.endswith(".csv")])


@st.cache_data(show_spinner=False)
def carregar_csv(nome_arquivo: str) -> pd.DataFrame:
    """Carrega e normaliza um CSV de cotações."""
    caminho = os.path.join(COTACOES_DIR, nome_arquivo)
    try:
        df = pd.read_csv(caminho)
        # Suporta múltiplos formatos de data (com ou sem horário, com ou sem timezone)
        df["Date"] = pd.to_datetime(df["Date"], infer_datetime_format=True, utc=False)
        # Remove timezone se existir
        if df["Date"].dt.tz is not None:
            df["Date"] = df["Date"].dt.tz_localize(None)
        df = df.sort_values("Date").reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()


def datas_disponiveis_globais(csvs: list[str]) -> list[date]:
    """
    Retorna uma lista de datas de negociação (union de todos os tickers),
    limitadas ao último ano, em ordem decrescente.
    """
    datas: set[date] = set()
    for csv in csvs[:10]:  # usa apenas primeiros 10 para ser rápido
        df = carregar_csv(csv)
        if df.empty or "Date" not in df.columns:
            continue
        datas.update(df["Date"].dt.date.tolist())
    # Filtra último ano
    hoje = date.today()
    um_ano_atras = hoje - timedelta(days=365)
    datas_filtradas = sorted(
        [d for d in datas if um_ano_atras <= d <= hoje - timedelta(days=90)],
        reverse=True,
    )
    return datas_filtradas


def preco_na_data(df: pd.DataFrame, data_alvo: date, janela: int = 10) -> float | None:
    """Retorna o preço de fechamento mais próximo da data_alvo (até `janela` dias antes)."""
    df = df.copy()
    df["_d"] = df["Date"].dt.date
    for delta in range(janela):
        d = data_alvo - timedelta(days=delta)
        row = df[df["_d"] == d]
        if not row.empty:
            return float(row["Close"].iloc[-1])
    return None


# ──────────────────────────────────────────────────────────────
#  MODELOS
# ──────────────────────────────────────────────────────────────

def score_prophet(df: pd.DataFrame, data_corte: date) -> float:
    """
    Treina Prophet com dados até data_corte e prevê HORIZONTE_DIAS.
    Score = porcentagem de dias previstos com yhat > preço atual.
    Retorna 0.0 se dados insuficientes.
    """
    df_cut = df[df["Date"].dt.date <= data_corte].copy()
    if len(df_cut) < MIN_DIAS_PROPHET:
        return 0.0

    preco_atual = float(df_cut["Close"].iloc[-1])
    df_treino = df_cut[["Date", "Close"]].rename(columns={"Date": "ds", "Close": "y"})

    try:
        modelo = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10,
        )
        modelo.fit(df_treino, algorithm="LBFGS")
        futuro = modelo.make_future_dataframe(periods=HORIZONTE_DIAS, freq="B")
        previsao = modelo.predict(futuro)
        previsao_futura = previsao.tail(HORIZONTE_DIAS)
        dias_alta = (previsao_futura["yhat"] > preco_atual).sum()
        return float(dias_alta / HORIZONTE_DIAS * 100)
    except Exception:
        return 0.0


# ── PyTorch LSTM ──────────────────────────────────────────────

class LSTMPredictor(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 64,
                 num_layers: int = 2, output_size: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True, dropout=0.1)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def score_pytorch(df: pd.DataFrame, data_corte: date) -> float:
    """
    Treina um LSTM simples com dados até data_corte e prevê HORIZONTE_DIAS.
    Score = porcentagem de dias previstos com preço > preço atual.
    Retorna 0.0 se dados insuficientes.
    """
    df_cut = df[df["Date"].dt.date <= data_corte].copy()
    if len(df_cut) < MIN_DIAS_LSTM + HORIZONTE_DIAS:
        return 0.0

    precos = df_cut["Close"].values.astype(np.float32)
    preco_atual = float(precos[-1])

    # Normalização MinMax
    p_min, p_max = precos.min(), precos.max()
    if p_max == p_min:
        return 0.0
    precos_norm = (precos - p_min) / (p_max - p_min)

    SEQ_LEN = MIN_DIAS_LSTM

    # Montar sequências
    X, y = [], []
    for i in range(len(precos_norm) - SEQ_LEN):
        X.append(precos_norm[i:i + SEQ_LEN])
        y.append(precos_norm[i + SEQ_LEN])

    X = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)  # (N, SEQ, 1)
    y = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(-1)  # (N, 1)

    modelo = LSTMPredictor()
    otimizador = torch.optim.Adam(modelo.parameters(), lr=0.005)
    criterio = nn.MSELoss()

    modelo.train()
    for _ in range(40):  # epochs rápidas
        otimizador.zero_grad()
        saida = modelo(X)
        loss = criterio(saida, y)
        loss.backward()
        otimizador.step()

    # Previsão recursiva
    modelo.eval()
    janela = precos_norm[-SEQ_LEN:].tolist()
    previsoes_norm = []
    with torch.no_grad():
        for _ in range(HORIZONTE_DIAS):
            entrada = torch.tensor(janela[-SEQ_LEN:], dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
            pred = modelo(entrada).item()
            pred = max(0.0, min(1.0, pred))
            previsoes_norm.append(pred)
            janela.append(pred)

    # Desnormalizar
    previsoes = [v * (p_max - p_min) + p_min for v in previsoes_norm]
    dias_alta = sum(1 for p in previsoes if p > preco_atual)
    return float(dias_alta / HORIZONTE_DIAS * 100)


# ── Score de Precificação ─────────────────────────────────────

def score_precificacao(df: pd.DataFrame, data_corte: date) -> float:
    """
    Score de sobrevendido/barato baseado em:
      - RSI(14) < 40  → +40 pts
      - Preço abaixo da Banda Bollinger inferior(20) → +30 pts
      - Kairi(200) < -10%  → +30 pts
    Retorna 0.0 se dados insuficientes.
    """
    df_cut = df[df["Date"].dt.date <= data_corte].copy()
    if len(df_cut) < 20:
        return 0.0

    closes = df_cut["Close"]
    score = 0.0

    # RSI(14)
    if len(closes) >= 15:
        delta = closes.diff().dropna()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = float((100 - 100 / (1 + rs)).iloc[-1])
        if rsi < 40:
            score += 40.0
        elif rsi < 50:
            score += 20.0  # parcial

    # Bollinger(20)
    if len(closes) >= 20:
        ma20 = closes.rolling(20).mean().iloc[-1]
        std20 = closes.rolling(20).std().iloc[-1]
        banda_inf = ma20 - 2 * std20
        preco = float(closes.iloc[-1])
        if preco < banda_inf:
            score += 30.0
        elif preco < ma20:
            score += 10.0  # parcial (abaixo da média)

    # Kairi(200)
    if len(closes) >= 200:
        ma200 = float(closes.rolling(200).mean().iloc[-1])
        kairi = (float(closes.iloc[-1]) - ma200) / ma200 * 100
        if kairi < -10:
            score += 30.0
        elif kairi < -5:
            score += 15.0  # parcial

    return min(score, 100.0)


# ──────────────────────────────────────────────────────────────
#  ANÁLISE COMBINADA
# ──────────────────────────────────────────────────────────────

def analisar_ticker(
    csv_nome: str,
    data_corte: date,
) -> dict | None:
    """
    Roda os três modelos para um ticker e retorna um dicionário
    com os scores e o score combinado.
    Retorna None se o ticker não tiver dados suficientes ou se
    não passar pelo menos em 2 dos 3 modelos com score >= SCORE_THRESHOLD.
    """
    df = carregar_csv(csv_nome)
    if df.empty:
        return None

    ticker = csv_nome.replace(".csv", "")

    sp = score_prophet(df, data_corte)
    st_ = score_pytorch(df, data_corte)
    sc = score_precificacao(df, data_corte)

    # Elegibilidade: todos os três modelos aprovam (>= threshold)
    aprovados = sum([sp >= SCORE_THRESHOLD, st_ >= SCORE_THRESHOLD, sc >= SCORE_THRESHOLD])
    if aprovados < 3:
        return None  # não elegível

    score_total = (sp + st_ + sc) / 3.0

    return {
        "ticker": ticker,
        "score_prophet": sp,
        "score_torch": st_,
        "score_preco": sc,
        "score_total": score_total,
        "df": df,
    }


# ──────────────────────────────────────────────────────────────
#  TABELA DE RETORNO
# ──────────────────────────────────────────────────────────────

def calcular_retorno(df: pd.DataFrame, data_corte: date, investimento: float) -> dict:
    """Calcula o retorno hipotético para +15, +30, +60 e +90 dias."""
    p0 = preco_na_data(df, data_corte)
    if p0 is None or p0 == 0:
        return {}

    qtde = investimento / p0
    prazos = {15: None, 30: None, 60: None, 90: None}

    for dias, _ in prazos.items():
        data_alvo = data_corte + timedelta(days=dias)
        p = preco_na_data(df, data_alvo)
        prazos[dias] = p

    resultado = {"ticker": "", "p0": p0, "qtde": qtde, "investimento": investimento}
    for dias, preco in prazos.items():
        if preco is not None:
            valor = qtde * preco
            variacao = (preco / p0 - 1) * 100
            resultado[f"+{dias}d_valor"] = valor
            resultado[f"+{dias}d_pct"] = variacao
        else:
            resultado[f"+{dias}d_valor"] = None
            resultado[f"+{dias}d_pct"] = None

    return resultado


# ──────────────────────────────────────────────────────────────
#  RENDERIZAÇÃO HTML
# ──────────────────────────────────────────────────────────────

def fmt_valor(v: float | None) -> str:
    if v is None:
        return "<span class='neutral'>—</span>"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v: float | None) -> str:
    if v is None:
        return "<span class='neutral'>—</span>"
    sinal = "+" if v >= 0 else ""
    css = "pos" if v >= 0 else "neg"
    return f"<span class='{css}'>{sinal}{v:.1f}%</span>"


def barra_score(score: float, cor: str) -> str:
    w = min(max(int(score), 0), 100)
    return (
        f"<div class='score-bar-bg'>"
        f"<div class='score-bar-fill' style='width:{w}%;background:{cor};'></div>"
        f"</div>"
        f"<span style='font-size:11px;color:#8899bb;'>{score:.1f}%</span>"
    )


def card_rank(rank: int, info: dict) -> str:
    medalhas = {1: "🥇", 2: "🥈", 3: "🥉"}
    classes = {1: "top-card-1", 2: "top-card-2", 3: "top-card-3"}
    m = medalhas.get(rank, "")
    cls = classes.get(rank, "top-card-1")
    t = info["ticker"].replace(".SA", "")

    return f"""
    <div class='top-card {cls}'>
        <div style='display:flex;align-items:center;gap:12px;margin-bottom:16px;'>
            <span style='font-size:32px;'>{m}</span>
            <div>
                <div class='ticker-big'>{t}</div>
                <div style='font-size:12px;color:#8899bb;'>Score Combinado: <b style='color:#e8f0fe;'>{info['score_total']:.1f}%</b></div>
            </div>
        </div>
        <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;'>
            <div>
                <span class='badge badge-prophet'>Prophet</span>
                {barra_score(info['score_prophet'], '#f5c842')}
            </div>
            <div>
                <span class='badge badge-torch'>PyTorch</span>
                {barra_score(info['score_torch'], '#4fc3f7')}
            </div>
            <div>
                <span class='badge badge-score'>Precificação</span>
                {barra_score(info['score_preco'], '#00e5a0')}
            </div>
        </div>
    </div>
    """


# ──────────────────────────────────────────────────────────────
#  INTERFACE PRINCIPAL
# ──────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class='page-header'>
    <div class='page-title'>🏆 3 Melhores</div>
    <div class='page-subtitle'>
        Análise combinada de Prophet · PyTorch LSTM · Precificação Técnica<br>
        Elege os 3 tickers com maior probabilidade de alta e simula R$ 10.000 investidos em cada um.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Verificar CSVs disponíveis ─────────────────────────────────
csvs_disponiveis = listar_csvs()

if not csvs_disponiveis:
    st.markdown("""
    <div class='alert-box'>
        ⚠️ <b>Nenhum arquivo CSV encontrado</b> no diretório <code>cotacoes/</code>.<br>
        Use a página <b>Importa Cotações</b> para baixar e salvar as cotações dos tickers desejados.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Seleção de Data ────────────────────────────────────────────
st.markdown("### ⚙️ Configuração da Análise")
col_cfg1, col_cfg2, col_cfg3 = st.columns([2, 2, 1])

with col_cfg1:
    datas_combo = datas_disponiveis_globais(csvs_disponiveis)

    if not datas_combo:
        st.error("Não foi possível determinar datas disponíveis a partir dos CSVs.")
        st.stop()

    opcoes_data = {str(d): d for d in datas_combo}
    data_sel_str = st.selectbox(
        "📅 Data de corte (análise até esta data)",
        options=list(opcoes_data.keys()),
        index=0,
        help="A análise usará apenas dados anteriores ou iguais a esta data. "
             "A tabela de retorno mostrará o que aconteceu nos 15, 30, 60 e 90 dias seguintes.",
    )
    data_corte: date = opcoes_data[data_sel_str]

with col_cfg2:
    st.markdown(f"""
    <div class='mini-metric' style='margin-top:28px;'>
        <div class='mini-val'>{len(csvs_disponiveis)}</div>
        <div class='mini-label'>Tickers Disponíveis</div>
    </div>
    """, unsafe_allow_html=True)

with col_cfg3:
    st.markdown("<div style='margin-top:28px;'>", unsafe_allow_html=True)
    botao = st.button("🚀 Analisar 3 Melhores", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div class='alert-box' style='margin-top:12px;'>
    <b>Critério de elegibilidade:</b> O ticker precisa ter score ≥ 50% nos <b>três</b> modelos
    simultaneamente (Prophet, PyTorch LSTM e Score de Precificação) para ser considerado.
    O ranking final é pelo score médio combinado dos três.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── EXECUÇÃO ───────────────────────────────────────────────────
if botao:
    st.markdown("### 🔄 Processando Tickers…")

    resultados = []
    erros = []
    n = len(csvs_disponiveis)

    barra = st.progress(0, text="Iniciando análise…")
    status_txt = st.empty()

    for idx, csv_nome in enumerate(csvs_disponiveis):
        ticker_nome = csv_nome.replace(".csv", "").replace(".SA", "")
        status_txt.markdown(f"<p class='progress-label'>🔍 Analisando <b>{ticker_nome}</b>…</p>",
                            unsafe_allow_html=True)
        barra.progress((idx + 1) / n, text=f"{idx+1}/{n} — {ticker_nome}")

        try:
            r = analisar_ticker(csv_nome, data_corte)
            if r is not None:
                resultados.append(r)
        except Exception as e:
            erros.append(f"{ticker_nome}: {e}")

    barra.empty()
    status_txt.empty()

    # ── Resultados ────────────────────────────────────────────
    if erros:
        with st.expander(f"⚠️ {len(erros)} ticker(s) com erro"):
            for err in erros:
                st.write(f"- {err}")

    if not resultados:
        st.markdown("""
        <div class='alert-box'>
            ❌ <b>Nenhum ticker passou em todos os três critérios</b> para a data selecionada.<br>
            Tente uma data diferente ou verifique se os CSVs têm dados suficientes (mínimo 200 dias).
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Ordenar e pegar top 3
    resultados.sort(key=lambda x: x["score_total"], reverse=True)
    top3 = resultados[:3]

    # ── Exibir Top 3 Cards ────────────────────────────────────
    st.markdown(f"### 🏆 Top {len(top3)} — Elegíveis com os 3 critérios")
    st.markdown(
        f"De **{n}** tickers analisados, **{len(resultados)}** passaram nos 3 critérios. "
        f"Mostrando o Top {len(top3)}."
    )

    for rank, info in enumerate(top3, 1):
        st.markdown(card_rank(rank, info), unsafe_allow_html=True)

    st.markdown("---")

    # ── Tabela de Retorno ─────────────────────────────────────
    st.markdown("### 💰 Simulação: R$ 10.000 investidos em cada ticker na data da recomendação")
    st.markdown(
        f"Data de entrada: **{data_corte.strftime('%d/%m/%Y')}** · "
        f"Investimento por ticker: **R$ {INVESTIMENTO:,.0f}** · "
        f"Total investido: **R$ {INVESTIMENTO * len(top3):,.0f}**"
    )

    # Construir dados da tabela
    retornos = []
    for info in top3:
        ret = calcular_retorno(info["df"], data_corte, INVESTIMENTO)
        ret["ticker"] = info["ticker"].replace(".SA", "")
        retornos.append(ret)

    # Colunas de prazo
    prazos_cols = [15, 30, 60, 90]
    labels = {15: "+15 dias", 30: "+30 dias", 60: "+60 dias", 90: "+90 dias"}

    # Cabeçalho
    cabecalho_html = "<tr>"
    cabecalho_html += "<th style='text-align:left;'>Ticker</th>"
    cabecalho_html += f"<th>Preço em {data_corte.strftime('%d/%m/%Y')}</th>"
    cabecalho_html += "<th>Qtde Papéis</th>"
    for d in prazos_cols:
        cabecalho_html += f"<th>{labels[d]}</th>"
    cabecalho_html += "</tr>"

    # Linhas dos tickers
    linhas_html = ""
    totais = {d: 0.0 for d in prazos_cols}
    totais_validos = {d: True for d in prazos_cols}

    for ret in retornos:
        linha = f"<tr><td style='text-align:left;font-weight:700;font-family:JetBrains Mono,monospace;'>{ret['ticker']}</td>"
        linha += f"<td>{fmt_valor(ret.get('p0'))}</td>"
        qtde = ret.get('qtde')
        linha += f"<td>{f'{qtde:.2f}' if qtde else '—'}</td>"
        for d in prazos_cols:
            val = ret.get(f"+{d}d_valor")
            pct = ret.get(f"+{d}d_pct")
            if val is not None:
                totais[d] += val
            else:
                totais_validos[d] = False
            linha += f"<td>{fmt_valor(val)}<br><small>{fmt_pct(pct)}</small></td>"
        linha += "</tr>"
        linhas_html += linha

    # Linha totais
    total_investido = INVESTIMENTO * len(top3)
    linha_total = "<tr class='total-row'>"
    linha_total += f"<td style='text-align:left;'>TOTAL ({len(top3)} tickers)</td>"
    linha_total += f"<td>R$ {total_investido:,.2f}</td>".replace(",", "X").replace(".", ",").replace("X", ".")
    linha_total += "<td>—</td>"
    for d in prazos_cols:
        if totais_validos[d] and len(top3) > 0:
            total_val = totais[d]
            total_pct = (total_val / total_investido - 1) * 100
            linha_total += f"<td>{fmt_valor(total_val)}<br><small>{fmt_pct(total_pct)}</small></td>"
        else:
            linha_total += "<td><span class='neutral'>—</span></td>"
    linha_total += "</tr>"

    # Render tabela
    tabela_html = f"""
    <div style='overflow-x:auto;margin-top:12px;'>
        <table class='ret-table'>
            <thead>{cabecalho_html}</thead>
            <tbody>{linhas_html}{linha_total}</tbody>
        </table>
    </div>
    """
    st.markdown(tabela_html, unsafe_allow_html=True)

    st.markdown("---")

    # ── Gráfico de evolução dos Top 3 ─────────────────────────
    st.markdown("### 📈 Evolução de Preços — Top 3 (a partir da data de recomendação)")

    cores_tickers = ["#f5c842", "#4fc3f7", "#00e5a0"]

    fig = go.Figure()

    for i, info in enumerate(top3):
        df_plot = info["df"].copy()
        df_plot["Date"] = pd.to_datetime(df_plot["Date"])

        # Mostrar 90 dias antes e 90 dias depois da data de corte
        dt_corte = pd.Timestamp(data_corte)
        df_janela = df_plot[
            (df_plot["Date"] >= dt_corte - pd.Timedelta(days=90)) &
            (df_plot["Date"] <= dt_corte + pd.Timedelta(days=100))
        ]

        if df_janela.empty:
            continue

        ticker_label = info["ticker"].replace(".SA", "")
        cor = cores_tickers[i % len(cores_tickers)]

        # Normalizar para base 100 na data de corte
        p_base = preco_na_data(info["df"], data_corte)
        if p_base is None or p_base == 0:
            continue

        df_janela = df_janela.copy()
        df_janela["Close_norm"] = df_janela["Close"] / p_base * 100

        fig.add_trace(go.Scatter(
            x=df_janela["Date"],
            y=df_janela["Close_norm"],
            mode="lines",
            name=ticker_label,
            line=dict(color=cor, width=2),
            hovertemplate=f"<b>{ticker_label}</b><br>%{{x|%d/%m/%Y}}<br>Base 100: %{{y:.1f}}<extra></extra>",
        ))

    # Linha vertical na data de corte
    fig.add_vline(
        x=pd.Timestamp(data_corte),
        line_dash="dash",
        line_color="rgba(255,255,255,0.3)",
        annotation_text=f"Recomendação {data_corte.strftime('%d/%m/%Y')}",
        annotation_font_color="#8899bb",
        annotation_font_size=11,
    )

    # Linhas de +15, +30, +60, +90 dias
    for dias, cor_linha in zip([15, 30, 60, 90], ["#ff9800", "#ff5252", "#7c4dff", "#00bfa5"]):
        dt_alvo = pd.Timestamp(data_corte + timedelta(days=dias))
        fig.add_vline(
            x=dt_alvo,
            line_dash="dot",
            line_color=f"rgba({','.join(str(int(cor_linha.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.3)",
            annotation_text=f"+{dias}d",
            annotation_font_color="#4a5a78",
            annotation_font_size=10,
        )

    fig.update_layout(
        title=dict(
            text="Evolução Normalizada (Base 100 = preço na data de recomendação)",
            font=dict(size=14, color="#e8f0fe"),
        ),
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0a1020",
        font=dict(color="#CCCCCC"),
        xaxis=dict(
            title="Data",
            gridcolor="#1F2937",
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            title="Preço Normalizado (Base 100)",
            gridcolor="#1F2937",
            showgrid=True,
            zeroline=False,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor="#333",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        height=450,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Disclaimer ─────────────────────────────────────────────
    st.markdown("""
    <div class='alert-box' style='margin-top:16px;font-size:11px;color:#4a5a78;'>
        ⚠️ <b>Aviso legal:</b> Esta análise é puramente educacional e informativa. Modelos de machine learning
        e análise técnica não garantem resultados futuros. Passado não é garantia de futuro.
        Não constitui recomendação de investimento. Consulte um profissional certificado antes de investir.
    </div>
    """, unsafe_allow_html=True)

else:
    # Estado inicial — antes de clicar no botão
    st.markdown(f"""
    <div style='text-align:center;padding:60px 20px;color:#4a5a78;'>
        <div style='font-size:64px;margin-bottom:16px;'>🏆</div>
        <div style='font-size:20px;font-weight:700;color:#8899bb;margin-bottom:8px;'>
            {len(csvs_disponiveis)} tickers prontos para análise
        </div>
        <div style='font-size:13px;'>
            Selecione a data de corte acima e clique em <b style='color:#00e5a0;'>Analisar 3 Melhores</b> para começar.
        </div>
        <div style='font-size:12px;margin-top:12px;color:#2a3a58;'>
            Tickers: {', '.join([f.replace('.csv','').replace('.SA','') for f in csvs_disponiveis[:15]])}{'…' if len(csvs_disponiveis) > 15 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
