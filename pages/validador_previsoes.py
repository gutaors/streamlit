import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import date, timedelta

st.set_page_config(page_title='Validador de Previsoes', layout='wide')
st.title('🔍 Validador de Previsoes')
st.markdown(
    'Informe uma lista de tickers brasileiros e uma data de referencia. '
    'A ferramenta exibira o valor do ativo naquela data e sua evolucao ate hoje.'
)


def normalizar_ticker(ticker):
    ticker = ticker.strip().upper()
    if not ticker.endswith('.SA'):
        ticker += '.SA'
    return ticker


def preco_na_data(df, data_alvo, janela_dias=10):
    df = df.copy()
    df['_date'] = pd.to_datetime(df['Date']).dt.date
    from datetime import timedelta as td
    for delta in range(janela_dias):
        d = data_alvo - td(days=delta)
        row = df[df['_date'] == d]
        if not row.empty:
            return float(row['Close'].iloc[-1])
    return None


def variacao_str(preco_ref, preco_alvo):
    if preco_alvo is None or preco_ref is None:
        return ''
    pct = (preco_alvo / preco_ref - 1) * 100
    sinal = '+' if pct >= 0 else ''
    return f'{sinal}{pct:.1f}%'


@st.cache_data(show_spinner=False)
def buscar_historico(ticker, data_inicio, data_fim):
    try:
        df = yf.download(ticker, start=data_inicio, end=data_fim, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        return df
    except Exception:
        return pd.DataFrame()


col_inp1, col_inp2 = st.columns([3, 1])

with col_inp1:
    tickers_raw = st.text_input(
        '📋 Tickers (separados por virgula)',
        placeholder='Ex: PETR4, VALE3, ITUB4.SA',
        help='O sufixo .SA e adicionado automaticamente.',
    )

with col_inp2:
    data_referencia = st.date_input(
        '📅 Data de referencia',
        value=date.today() - timedelta(days=180),
        min_value=date(2009, 1, 1),
        max_value=date.today() - timedelta(days=1),
        help='Data a partir da qual a analise sera feita.',
    )

buscar = st.button('🔎 Analisar', type='primary')

if buscar and tickers_raw.strip():
    tickers_lista = [normalizar_ticker(t) for t in tickers_raw.split(',') if t.strip()]
    if not tickers_lista:
        st.warning('Nenhum ticker valido informado.')
        st.stop()

    data_hoje = date.today()
    data_1m = data_referencia + timedelta(days=30)
    data_3m = data_referencia + timedelta(days=90)
    data_6m = data_referencia + timedelta(days=180)

    historicos = {}
    erros = []

    bar = st.progress(0, text='Buscando cotacoes...')
    for i, ticker in enumerate(tickers_lista):
        df = buscar_historico(
            ticker,
            data_referencia.strftime('%Y-%m-%d'),
            (data_hoje + timedelta(days=1)).strftime('%Y-%m-%d'),
        )
        if df.empty:
            erros.append(ticker)
        else:
            historicos[ticker] = df
        bar.progress((i + 1) / len(tickers_lista), text=f'Carregando {ticker}...')
    bar.empty()

    if erros:
        st.warning('Nao foi possivel obter dados para: ' + ', '.join(erros))
    if not historicos:
        st.error('Nenhum dado disponivel para os tickers informados.')
        st.stop()

    st.subheader('📊 Tabela de Evolucao de Precos')
    registros = []
    for ticker, df in historicos.items():
        p_ref   = preco_na_data(df, data_referencia)
        p_1m    = preco_na_data(df, data_1m)  if data_1m  <= data_hoje else None
        p_3m    = preco_na_data(df, data_3m)  if data_3m  <= data_hoje else None
        p_6m    = preco_na_data(df, data_6m)  if data_6m  <= data_hoje else None
        p_atual = preco_na_data(df, data_hoje)

        def fmt(v, _ref=p_ref):
            if v is None:
                return '-'
            s = variacao_str(_ref, v)
            base = f'R$ {v:.2f}'
            return base + (f'  ({s})' if s else '')

        registros.append({
            'Ticker': ticker.replace('.SA', ''),
            'Preco em ' + data_referencia.strftime('%d/%m/%Y'): f'R$ {p_ref:.2f}' if p_ref else '-',
            '+1 mes': fmt(p_1m),
            '+3 meses': fmt(p_3m),
            '+6 meses': fmt(p_6m),
            'Preco Atual': fmt(p_atual),
        })

    st.dataframe(pd.DataFrame(registros), use_container_width=True, hide_index=True)
    st.markdown('---')
    st.subheader('📈 Serie Temporal por Ativo')

    cores_marcos = ['#FFD700', '#FF8C00', '#FF4500', '#00FF7F']

    for ticker, df in historicos.items():
        df_plot = df.copy()
        df_plot['Date'] = pd.to_datetime(df_plot['Date'])
        df_plot = df_plot.sort_values('Date')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_plot['Date'], y=df_plot['Close'],
            mode='lines', name=ticker.replace('.SA', ''),
            line=dict(color='#00C8FF', width=2),
            hovertemplate='%{x|%d/%m/%Y}<br>R$ %{y:.2f}<extra></extra>',
        ))

        marcos = [
            ('Ref. ' + data_referencia.strftime('%d/%m/%Y'), data_referencia),
            ('+1 mes ' + data_1m.strftime('%d/%m/%Y'), data_1m),
            ('+3 meses ' + data_3m.strftime('%d/%m/%Y'), data_3m),
            ('+6 meses ' + data_6m.strftime('%d/%m/%Y'), data_6m),
        ]

        for (label, d), cor in zip(marcos, cores_marcos):
            if d > data_hoje:
                continue
            preco = preco_na_data(df, d)
            if preco is None:
                continue
            fig.add_trace(go.Scatter(
                x=[pd.Timestamp(d)], y=[preco],
                mode='markers+text', name=label,
                marker=dict(color=cor, size=10, symbol='diamond'),
                text=[f'R$ {preco:.2f}'],
                textposition='top center',
            ))

        titulo = ticker.replace('.SA', '') + ' - Evolucao desde ' + data_referencia.strftime('%d/%m/%Y')
        fig.update_layout(
            title=dict(text=titulo, font=dict(size=16, color='#FFFFFF')),
            plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
            font=dict(color='#CCCCCC'),
            xaxis=dict(title='Data', gridcolor='#1F2937', showgrid=True, zeroline=False),
            yaxis=dict(title='Preco (R$)', gridcolor='#1F2937', showgrid=True, zeroline=False),
            legend=dict(bgcolor='rgba(0,0,0,0.4)', bordercolor='#333', borderwidth=1),
            hovermode='x unified',
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

elif buscar and not tickers_raw.strip():
    st.warning('Por favor, informe pelo menos um ticker.')
