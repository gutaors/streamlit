import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Subi/Dez", layout="wide")
st.title("📊 Subiu? — Valorização e Desvalorização de 10%")
st.markdown("Selecione uma data de referência para identificar quais ativos **subiram** ou **desceram** 10% ou mais a partir daquela data.")

# ── Configuração ──────────────────────────────────────────────────────────────
PASTA_COTACOES = "cotacoes"
LIMIAR = 0.10  # 10%


def listar_tickers_disponiveis():
    """Retorna lista de tickers disponíveis na pasta cotacoes."""
    if not os.path.exists(PASTA_COTACOES):
        return []
    return sorted(
        [f.replace(".csv", "") for f in os.listdir(PASTA_COTACOES) if f.endswith(".csv")]
    )


@st.cache_data
def carregar_cotacoes(ticker: str) -> pd.DataFrame:
    """Carrega e retorna o DataFrame de cotações de um ticker."""
    caminho = os.path.join(PASTA_COTACOES, f"{ticker}.csv")
    if not os.path.exists(caminho):
        return pd.DataFrame()
    df = pd.read_csv(caminho)
    if "Date" not in df.columns or "Close" not in df.columns:
        return pd.DataFrame()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def encontrar_cruzamento(df: pd.DataFrame, preco_ref: float, data_ref, direcao: str):
    """
    Busca a primeira data APÓS data_ref onde o preço cruzou o limiar.

    direcao: 'alta' para valorização ≥ +10%, 'baixa' para desvalorização ≥ -10%.

    Retorna (data_cruzamento, preco_cruzamento) ou (None, None).
    """
    df_futuro = df[df["Date"] > data_ref].copy()
    if df_futuro.empty:
        return None, None

    if direcao == "alta":
        alvo = preco_ref * (1 + LIMIAR)
        mask = df_futuro["Close"] >= alvo
    else:
        alvo = preco_ref * (1 - LIMIAR)
        mask = df_futuro["Close"] <= alvo

    hits = df_futuro[mask]
    if hits.empty:
        return None, None

    primeira = hits.iloc[0]
    return primeira["Date"], primeira["Close"]


# ── Interface ─────────────────────────────────────────────────────────────────
tickers = listar_tickers_disponiveis()

if not tickers:
    st.warning("Nenhum ticker encontrado na pasta 'cotacoes'. Importe cotações primeiro.")
    st.stop()

# Data de referência
data_referencia = st.date_input(
    "📅 Data de Referência",
    value=datetime(2025, 1, 2),
    help="Selecione a data a partir da qual será analisada a variação de 10%.",
)

data_ref_ts = pd.Timestamp(data_referencia)

# ── Processamento ─────────────────────────────────────────────────────────────
resultados_alta = []
resultados_baixa = []

barra = st.progress(0, text="Analisando tickers...")

for i, ticker in enumerate(tickers):
    barra.progress((i + 1) / len(tickers), text=f"Analisando {ticker}...")
    df = carregar_cotacoes(ticker)
    if df.empty:
        continue

    # Encontrar o preço de fechamento na data de referência (ou a mais próxima posterior)
    df_ref = df[df["Date"] >= data_ref_ts]
    if df_ref.empty:
        continue

    linha_ref = df_ref.iloc[0]
    preco_ref = linha_ref["Close"]
    data_efetiva = linha_ref["Date"]
    preco_atual = df.iloc[-1]["Close"]

    # Buscar valorização ≥ +10%
    data_alta, preco_alta = encontrar_cruzamento(df, preco_ref, data_efetiva, "alta")
    if data_alta is not None:
        variacao_alta = ((preco_alta - preco_ref) / preco_ref) * 100
        dias_alta = (data_alta - data_efetiva).days
        resultados_alta.append({
            "Ticker": ticker,
            "Data Ref.": data_efetiva.strftime("%d/%m/%Y"),
            "Preço Ref. (R$)": round(preco_ref, 2),
            "Data Valorização": data_alta.strftime("%d/%m/%Y"),
            "Preço Valoriz.(R$)": round(preco_alta, 2),
            "Variação (%)": round(variacao_alta, 2),
            "Dias": dias_alta,
            "Preço Atual (R$)": round(preco_atual, 2),
        })

    # Buscar desvalorização ≥ -10%
    data_baixa, preco_baixa = encontrar_cruzamento(df, preco_ref, data_efetiva, "baixa")
    if data_baixa is not None:
        variacao_baixa = ((preco_baixa - preco_ref) / preco_ref) * 100
        dias_baixa = (data_baixa - data_efetiva).days
        resultados_baixa.append({
            "Ticker": ticker,
            "Data Ref.": data_efetiva.strftime("%d/%m/%Y"),
            "Preço Ref. (R$)": round(preco_ref, 2),
            "Data Desvaloriz.": data_baixa.strftime("%d/%m/%Y"),
            "Preço Desvaloriz.(R$)": round(preco_baixa, 2),
            "Variação (%)": round(variacao_baixa, 2),
            "Dias": dias_baixa,
            "Preço Atual (R$)": round(preco_atual, 2),
        })

barra.empty()

# ── Exibição ──────────────────────────────────────────────────────────────────
col_alta, col_baixa = st.columns(2)

with col_alta:
    st.subheader("🟢 Valorização ≥ +10%")
    if resultados_alta:
        df_alta = pd.DataFrame(resultados_alta)
        df_alta = df_alta.sort_values("Dias")
        st.dataframe(df_alta, use_container_width=True, hide_index=True)
        st.caption(f"{len(df_alta)} de {len(tickers)} tickers atingiram +10% após a data de referência.")
    else:
        st.info("Nenhum ticker atingiu valorização de +10% após a data selecionada.")

with col_baixa:
    st.subheader("🔴 Desvalorização ≥ -10%")
    if resultados_baixa:
        df_baixa = pd.DataFrame(resultados_baixa)
        df_baixa = df_baixa.sort_values("Dias")
        st.dataframe(df_baixa, use_container_width=True, hide_index=True)
        st.caption(f"{len(df_baixa)} de {len(tickers)} tickers atingiram -10% após a data de referência.")
    else:
        st.info("Nenhum ticker atingiu desvalorização de -10% após a data selecionada.")

# ── Resumo ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""
**Resumo da análise a partir de {data_referencia.strftime('%d/%m/%Y')}:**
- Tickers analisados: **{len(tickers)}**
- Valorizaram ≥ +10%: **{len(resultados_alta)}**
- Desvalorizaram ≥ -10%: **{len(resultados_baixa)}**
""")
