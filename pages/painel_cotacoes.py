import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import date, timedelta

st.set_page_config(page_title="Painel de Cotações", layout="wide")

@st.cache_data(ttl=900)
def get_commodity_prices():
    try:
        brent = yf.Ticker("BZ=F").fast_info['lastPrice']
    except Exception:
        brent = None
    try:
        # Minério de Ferro 62% Fe CFR China
        iron = yf.Ticker("TIO=F").fast_info['lastPrice']
    except Exception:
        iron = None
    return brent, iron

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0e1117; }

    /* Tabela customizada */
    .cotacao-table { width: 100%; border-collapse: collapse; font-family: 'Segoe UI', sans-serif; }
    .cotacao-table thead th {
        background: #1a1d27;
        color: #a0aec0;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 12px 16px;
        border-bottom: 1px solid #2d3748;
        text-align: left;
    }
    .cotacao-table tbody tr {
        border-bottom: 1px solid #1a1d27;
        transition: background 0.15s;
    }
    .cotacao-table tbody tr:hover { background: #1a1d27; }
    .cotacao-table tbody td {
        padding: 10px 16px;
        font-size: 0.92rem;
        color: #e2e8f0;
    }
    .ticker-badge {
        font-weight: 700;
        font-size: 0.88rem;
        letter-spacing: 0.05em;
        color: #90cdf4;
    }
    .alta  { color: #68d391; font-weight: 600; }
    .queda { color: #fc8181; font-weight: 600; }
    .neutro { color: #a0aec0; }
    .arrow-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .arrow-alta  { background: rgba(72,187,120,0.15); color: #68d391; }
    .arrow-queda { background: rgba(252,129,129,0.15); color: #fc8181; }
    .arrow-neutro { background: rgba(160,174,192,0.1); color: #a0aec0; }

    /* Seção de gráficos */
    .charts-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #e2e8f0;
        margin: 32px 0 8px 0;
        border-left: 4px solid #4299e1;
        padding-left: 12px;
    }
    div[data-testid="stDateInput"] label { color: #a0aec0 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("## 📊 Painel de Cotações")
st.markdown("Visão consolidada de todos os ativos da carteira.")

brent_price, iron_price = get_commodity_prices()
col_c1, col_c2, _ = st.columns([1, 1, 2])
if brent_price is not None:
    col_c1.metric("🛢️ Petróleo Brent Futuros", f"US$ {brent_price:.2f}")
if iron_price is not None:
    col_c2.metric("⛏️ Minério de Ferro", f"US$ {iron_price:.2f}")

st.markdown("---")


# ─── Diretório de cotações ─────────────────────────────────────────────────────
PASTA_COTACOES = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cotacoes')

arquivos = sorted([f for f in os.listdir(PASTA_COTACOES) if f.endswith('.csv')])
tickers  = [f.replace('.csv', '') for f in arquivos]

if not tickers:
    st.error("Nenhum arquivo CSV encontrado no diretório 'cotacoes'.")
    st.stop()

# ─── Filtro de data ────────────────────────────────────────────────────────────
col_date, col_space = st.columns([1, 3])
with col_date:
    data_corte = st.date_input(
        "📅 Data de referência",
        value=date.today(),
        help="Selecione a data para calcular os valores e variações."
    )

st.markdown("---")

# ─── Funções auxiliares ────────────────────────────────────────────────────────
def carregar_df(ticker: str) -> pd.DataFrame:
    caminho = os.path.join(PASTA_COTACOES, ticker + '.csv')
    df = pd.read_csv(caminho)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
    if 'Close' in df.columns:
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    return df


def calcular_resumo(df: pd.DataFrame, data_ref: date) -> dict:
    """Retorna valor atual, variação do dia, % variação e média histórica."""
    df_filtrado = df[df.index <= pd.to_datetime(data_ref)].dropna(subset=['Close'])
    if df_filtrado.empty:
        return None

    valor_atual = df_filtrado['Close'].iloc[-1]
    media       = df_filtrado['Close'].mean()

    # Variação em relação ao dia anterior disponível
    if len(df_filtrado) >= 2:
        valor_anterior = df_filtrado['Close'].iloc[-2]
        var_valor = valor_atual - valor_anterior
        var_pct   = (var_valor / valor_anterior) * 100 if valor_anterior != 0 else 0.0
    else:
        var_valor = 0.0
        var_pct   = 0.0

    return {
        'valor_atual':   valor_atual,
        'var_valor':     var_valor,
        'var_pct':       var_pct,
        'media':         media,
    }


def arrow_badge(valor: float) -> str:
    if valor > 0:
        return f'<span class="arrow-badge arrow-alta">▲ Alta</span>'
    elif valor < 0:
        return f'<span class="arrow-badge arrow-queda">▼ Queda</span>'
    else:
        return f'<span class="arrow-badge arrow-neutro">— Neutro</span>'


def fmt_pct(v: float) -> str:
    cls = "alta" if v > 0 else ("queda" if v < 0 else "neutro")
    sinal = "+" if v > 0 else ""
    return f'<span class="{cls}">{sinal}{v:.2f}%</span>'


def fmt_val(v: float) -> str:
    cls = "alta" if v > 0 else ("queda" if v < 0 else "neutro")
    sinal = "+" if v > 0 else ""
    return f'<span class="{cls}">{sinal}R$ {v:.2f}</span>'


# ─── Coleta dos dados ──────────────────────────────────────────────────────────
dados_dfs = {}
resumos   = []

for ticker in tickers:
    try:
        df = carregar_df(ticker)
        resumo = calcular_resumo(df, data_corte)
        if resumo:
            resumo['ticker'] = ticker
            resumos.append(resumo)
            dados_dfs[ticker] = df
    except Exception as e:
        st.warning(f"Erro ao carregar {ticker}: {e}")

if not resumos:
    st.error("Nenhum dado disponível para a data selecionada.")
    st.stop()

# ─── Tabela de resumo ──────────────────────────────────────────────────────────
st.markdown("### 📋 Resumo dos Ativos")

header = """
<table class="cotacao-table">
  <thead>
    <tr>
      <th>Ticker</th>
      <th>Status</th>
      <th>% Variação ↑↓</th>
      <th>Valor Variação ↑↓</th>
      <th>Valor Atual</th>
      <th>Média Histórica</th>
    </tr>
  </thead>
  <tbody>
"""
rows = ""
for r in resumos:
    ticker_nome = r['ticker'].replace('.SA', '')
    rows += f"""<tr>
  <td><span class="ticker-badge">{ticker_nome}</span></td>
  <td>{arrow_badge(r['var_pct'])}</td>
  <td>{fmt_pct(r['var_pct'])}</td>
  <td>{fmt_val(r['var_valor'])}</td>
  <td>R$ {r['valor_atual']:.2f}</td>
  <td>R$ {r['media']:.2f}</td>
</tr>
"""

footer = "</tbody></table>"
st.markdown(header + rows + footer, unsafe_allow_html=True)

# ─── Gráficos SMA 50 × SMA 200 ────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📈 Gráficos com Médias Móveis (SMA 50 × SMA 200)")

for ticker in tickers:
    if ticker not in dados_dfs:
        continue

    df = dados_dfs[ticker].copy()
    df_filtrado = df[df.index <= pd.to_datetime(data_corte)].dropna(subset=['Close'])

    if df_filtrado.empty:
        continue

    # Calcula SMAs
    df_filtrado['SMA50']  = df_filtrado['Close'].rolling(window=50,  min_periods=1).mean()
    df_filtrado['SMA200'] = df_filtrado['Close'].rolling(window=200, min_periods=1).mean()

    # Título do gráfico
    ticker_nome   = ticker.replace('.SA', '')
    ultimo        = df_filtrado['Close'].iloc[-1]
    resumo_ticker = next((r for r in resumos if r['ticker'] == ticker), None)
    var_pct_g     = resumo_ticker['var_pct'] if resumo_ticker else 0.0
    sinal_g       = "▲" if var_pct_g > 0 else ("▼" if var_pct_g < 0 else "—")
    cor_g         = "#68d391" if var_pct_g > 0 else ("#fc8181" if var_pct_g < 0 else "#a0aec0")

    st.markdown(
        f'<div class="charts-title">{ticker_nome} &nbsp;|&nbsp; R$ {ultimo:.2f} '
        f'&nbsp;<span style="color:{cor_g};font-size:0.9rem">{sinal_g} {var_pct_g:+.2f}%</span></div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure()

    # Preço de fechamento
    fig.add_trace(go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['Close'],
        name='Fechamento',
        line=dict(color='#90cdf4', width=1),
        opacity=0.6,
        hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Fechamento: R$ %{y:.2f}<extra></extra>',
    ))

    # SMA 50
    fig.add_trace(go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['SMA50'],
        name='SMA 50',
        line=dict(color='#f6e05e', width=2, dash='solid'),
        hovertemplate='<b>%{x|%d/%m/%Y}</b><br>SMA 50: R$ %{y:.2f}<extra></extra>',
    ))

    # SMA 200
    fig.add_trace(go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['SMA200'],
        name='SMA 200',
        line=dict(color='#fc8181', width=2, dash='solid'),
        hovertemplate='<b>%{x|%d/%m/%Y}</b><br>SMA 200: R$ %{y:.2f}<extra></extra>',
    ))

    # Área de cruzamento (golden/death cross shading)
    crossover = (df_filtrado['SMA50'] - df_filtrado['SMA200'])
    golden = crossover > 0  # SMA50 acima de SMA200

    fig.update_layout(
        height=380,
        margin=dict(l=0, r=0, t=20, b=20),
        paper_bgcolor='#0e1117',
        plot_bgcolor='#131720',
        font=dict(family='Segoe UI', color='#a0aec0', size=12),
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='right', x=1,
            font=dict(size=12),
            bgcolor='rgba(0,0,0,0)',
        ),
        xaxis=dict(
            showgrid=True, gridcolor='#1a1d27', gridwidth=1,
            zeroline=False, tickformat='%b/%Y',
            color='#a0aec0',
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#1a1d27', gridwidth=1,
            zeroline=False, tickprefix='R$ ',
            color='#a0aec0',
        ),
        hovermode='x unified',
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
