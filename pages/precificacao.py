import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import requests
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Precificação", layout="wide")

st.title("Precificação & Análise Fundamentalista")

# Sidebar inputs
st.sidebar.header("Parâmetros")
ticker_input = st.sidebar.text_input("Ticker da Ação (ex: WEGE3, PETR4)", value="PETR4").strip().upper()
comparacao_input = st.sidebar.text_input("Ticker Comparativo (opcional)", value="").strip().upper()
data_input = st.sidebar.date_input("Data de Referência (Apenas para o preço)", value=datetime.today())

def format_ticker(ticker):
    if not ticker.endswith(".SA") and ticker != "":
        return ticker + ".SA"
    return ticker

ticker_sa = format_ticker(ticker_input)
comp_sa = format_ticker(comparacao_input) if comparacao_input else ""

@st.cache_data(ttl=86400)
def fetch_fundamental_data(ticker):
    """
    Tenta buscar dados do Status Invest por web scraping. 
    Faz o fallback para yfinance se bloqueado (muito comum devido ao Cloudflare).
    """
    data = {}
    # Tentativa com yfinance primeiro por ser muito mais estavel
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # Coleta de dados
        data['preco'] = info.get('currentPrice', info.get('previousClose', 0))
        data['p_l'] = info.get('trailingPE', 0)
        data['p_vp'] = info.get('priceToBook', 0)
        data['ev_ebitda'] = info.get('enterpriseToEbitda', 0)
        data['roe'] = info.get('returnOnEquity', 0)
        data['roic'] = info.get('returnOnAssets', 0) # Aproximação se ROIC não estiver disp.
        
        data['margem_bruta'] = info.get('grossMargins', 0)
        data['margem_operacional'] = info.get('operatingMargins', 0)
        data['margem_liquida'] = info.get('profitMargins', 0)
        
        data['divida_liquida'] = info.get('totalDebt', 0) - info.get('totalCash', 0)
        data['ebitda'] = info.get('ebitda', 0)
        data['divida_ebitda'] = data['divida_liquida'] / data['ebitda'] if data['ebitda'] else 0
        
        data['dy'] = info.get('dividendYield', 0)
        
        data['receita'] = info.get('totalRevenue', 0)
        data['lucro_liquido'] = info.get('netIncomeToCommon', 0)
        data['fcl'] = info.get('freeCashflow', 0)
        data['num_acoes'] = info.get('sharesOutstanding', 1)
        data['lpa'] = info.get('trailingEps', 0)
        data['vpa'] = info.get('bookValue', 0)
        
        # Históricos
        data['financials'] = t.financials
        data['cashflow'] = t.cashflow
        data['dividends'] = t.dividends
        
    except Exception as e:
        st.error(f"Erro ao buscar dados para {ticker} no yfinance: {e}")
        
    return data

if ticker_sa:
    with st.spinner(f"Buscando dados para {ticker_sa}..."):
        dados_principais = fetch_fundamental_data(ticker_sa)
        
    if not dados_principais or dados_principais.get('preco') == 0:
        st.error(f"Não foi possível encontrar dados para {ticker_input}.")
    else:
        st.header(f"Análise de {ticker_input}")
        
        # Pega preco historico se necessário
        try:
            t = yf.Ticker(ticker_sa)
            hist = t.history(start=data_input, end=data_input + pd.Timedelta(days=5))
            if not hist.empty:
                preco_ref = hist.iloc[0]['Close']
                st.write(f"**Preço de Fechamento na data {data_input.strftime('%d/%m/%Y')}:** R$ {preco_ref:.2f}")
            else:
                st.write(f"**Preço Atual:** R$ {dados_principais['preco']:.2f}")
        except:
            st.write(f"**Preço Atual:** R$ {dados_principais['preco']:.2f}")
            
        st.markdown("---")
        st.subheader("Indicadores de Valuation e Rentabilidade")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("P/L", f"{dados_principais['p_l']:.2f}", help="Preço/Lucro: Tempo em anos para reaver o capital investido considerando o lucro atual.")
            st.metric("P/VP", f"{dados_principais['p_vp']:.2f}", help="Preço/Valor Patrimonial: Quanto o mercado paga por cada R$ 1 de patrimônio da empresa.")
        with col2:
            st.metric("EV/EBITDA", f"{dados_principais['ev_ebitda']:.2f}", help="Valor da Firma / EBITDA: Mede quanto custaria comprar a empresa e pagar suas dívidas, gerando seu caixa operacional.")
            st.metric("Dividend Yield", f"{dados_principais['dy']*100:.2f}%", help="Rendimento de dividendos sobre o preço atual da ação.")
        with col3:
            st.metric("ROE", f"{dados_principais['roe']*100:.2f}%", help="Return on Equity: Rentabilidade que a empresa gera sobre o dinheiro dos acionistas.")
            st.metric("ROIC", f"{dados_principais['roic']*100:.2f}%", help="Return on Invested Capital: Rentabilidade sobre todo o capital investido na operação (próprio + terceiros). Onde pegar: Status Invest.")
        with col4:
            st.metric("Margem Líquida", f"{dados_principais['margem_liquida']*100:.2f}%", help="Percentual de lucro que sobra após todos os custos e despesas. Onde pegar: Status Invest.")
            st.metric("Dívida Líq / EBITDA", f"{dados_principais['divida_ebitda']:.2f}", help="Mede em quantos anos a empresa pagaria sua dívida usando sua geração de caixa operacional.")
            
        st.markdown("---")
        st.subheader("Dados Absolutos")
        colA, colB, colC, colD = st.columns(4)
        with colA:
            st.metric("Receita", f"R$ {dados_principais['receita']/1e9:.2f} B", help="Onde pegar: Status Invest")
        with colB:
            st.metric("Lucro Líquido", f"R$ {dados_principais['lucro_liquido']/1e9:.2f} B", help="Onde pegar: Status Invest")
        with colC:
            st.metric("Fluxo de Caixa Livre", f"R$ {dados_principais['fcl']/1e9:.2f} B", help="Onde pegar: RI / Investidor10")
        with colD:
            st.metric("Número de Ações", f"{dados_principais['num_acoes']/1e9:.2f} B", help="Onde pegar: RI")
            
        st.markdown("---")
        st.subheader("Histórico de Resultados")
        
        tab1, tab2, tab3 = st.tabs(["Evolução Financeira (DRE)", "Fluxo de Caixa", "Histórico de Dividendos"])
        
        with tab1:
            st.write("Evolução de Receita e Lucro (Anual)")
            df_fin = dados_principais['financials']
            if not df_fin.empty:
                df_fin = df_fin.T
                # Filter useful columns
                if 'Total Revenue' in df_fin.columns and 'Net Income' in df_fin.columns:
                    fig_dre = go.Figure()
                    fig_dre.add_trace(go.Bar(x=df_fin.index.year, y=df_fin['Total Revenue'], name='Receita Total'))
                    fig_dre.add_trace(go.Bar(x=df_fin.index.year, y=df_fin['Net Income'], name='Lucro Líquido'))
                    fig_dre.update_layout(barmode='group')
                    st.plotly_chart(fig_dre, use_container_width=True)
                else:
                    st.info("Dados de DRE indisponíveis para plotar.")
            else:
                st.info("Dados históricos indisponíveis.")
                
        with tab2:
            st.write("Fluxo de Caixa Operacional vs Livre")
            df_cf = dados_principais['cashflow']
            if not df_cf.empty:
                df_cf = df_cf.T
                if 'Operating Cash Flow' in df_cf.columns and 'Free Cash Flow' in df_cf.columns:
                    fig_cf = go.Figure()
                    fig_cf.add_trace(go.Bar(x=df_cf.index.year, y=df_cf['Operating Cash Flow'], name='Fluxo de Caixa Operacional'))
                    fig_cf.add_trace(go.Bar(x=df_cf.index.year, y=df_cf['Free Cash Flow'], name='Fluxo de Caixa Livre'))
                    fig_cf.update_layout(barmode='group')
                    st.plotly_chart(fig_cf, use_container_width=True)
                else:
                    st.info("Dados de Fluxo de Caixa indisponíveis para plotar.")
            else:
                st.info("Dados históricos indisponíveis.")
                
        with tab3:
            st.write("Dividendos pagos ao longo do tempo")
            df_div = dados_principais['dividends']
            if not df_div.empty:
                # Group by year
                df_div_yearly = df_div.resample('Y').sum()
                fig_div = go.Figure()
                fig_div.add_trace(go.Bar(x=df_div_yearly.index.year, y=df_div_yearly.values, name='Dividendos (R$)'))
                st.plotly_chart(fig_div, use_container_width=True)
            else:
                st.info("Histórico de dividendos não encontrado.")
                
        # --- COMPARAÇÃO ---
        if comp_sa:
            st.markdown("---")
            st.subheader(f"Comparação: {ticker_input} vs {comparacao_input}")
            with st.spinner(f"Buscando dados para {comp_sa}..."):
                dados_comp = fetch_fundamental_data(comp_sa)
            
            if dados_comp and dados_comp.get('preco') != 0:
                comp_df = pd.DataFrame({
                    'Indicador': ['P/L', 'P/VP', 'EV/EBITDA', 'ROE', 'Margem Líquida', 'Div. Liq / EBITDA', 'Dividend Yield'],
                    ticker_input: [
                        f"{dados_principais['p_l']:.2f}",
                        f"{dados_principais['p_vp']:.2f}",
                        f"{dados_principais['ev_ebitda']:.2f}",
                        f"{dados_principais['roe']*100:.2f}%",
                        f"{dados_principais['margem_liquida']*100:.2f}%",
                        f"{dados_principais['divida_ebitda']:.2f}",
                        f"{dados_principais['dy']*100:.2f}%"
                    ],
                    comparacao_input: [
                        f"{dados_comp['p_l']:.2f}",
                        f"{dados_comp['p_vp']:.2f}",
                        f"{dados_comp['ev_ebitda']:.2f}",
                        f"{dados_comp['roe']*100:.2f}%",
                        f"{dados_comp['margem_liquida']*100:.2f}%",
                        f"{dados_comp['divida_ebitda']:.2f}",
                        f"{dados_comp['dy']*100:.2f}%"
                    ]
                })
                st.table(comp_df.set_index('Indicador'))
            else:
                st.error(f"Não foi possível buscar os dados do ticker comparativo {comparacao_input}.")
                
        # --- PRECIFICAÇÃO ---
        st.markdown("---")
        st.subheader("Modelos de Precificação (Valuation)")
        st.write("Abaixo estão dois modelos simples e amplamente utilizados para determinar o **Preço Justo** de uma ação baseando-se em seus dados fundamentalistas.")
        
        # Graham
        st.markdown("#### 1. Fórmula de Benjamin Graham")
        st.write("A fórmula de Graham encontra o valor justo de uma empresa partindo do princípio de que um P/L aceitável é 15 e um P/VP aceitável é 1.5 (15 * 1.5 = 22.5).")
        st.latex(r"Valor Justo = \sqrt{22.5 \times LPA \times VPA}")
        
        lpa = dados_principais.get('lpa', 0)
        vpa = dados_principais.get('vpa', 0)
        
        if lpa > 0 and vpa > 0:
            preco_justo_graham = np.sqrt(22.5 * lpa * vpa)
            margem_graham = ((preco_justo_graham / dados_principais['preco']) - 1) * 100
            
            st.write(f"**LPA (Lucro por Ação):** R$ {lpa:.2f}")
            st.write(f"**VPA (Valor Patrimonial da Ação):** R$ {vpa:.2f}")
            st.success(f"**Preço Justo (Graham): R$ {preco_justo_graham:.2f}**")
            
            if margem_graham > 0:
                st.info(f"**Margem de Segurança:** {margem_graham:.2f}% (Potencial de Valorização)")
            else:
                st.warning(f"**Margem de Segurança:** {margem_graham:.2f}% (Ação sendo negociada acima do Preço Justo de Graham)")
        else:
            st.error("A empresa possui LPA ou VPA negativo/nulo. A fórmula de Graham não se aplica a empresas com prejuízo ou patrimônio líquido negativo.")
            
        # Decio Bazin
        st.markdown("#### 2. Modelo de Décio Bazin (Dividendos)")
        st.write("Décio Bazin considerava que uma boa pagadora de dividendos deve remunerar, no mínimo, 6% ao ano. O Preço Justo é aquele onde o Yield mínimo exigido é de 6%.")
        st.latex(r"Valor Justo = \frac{Dividendo Médio (3 anos)}{0.06}")
        
        df_div = dados_principais['dividends']
        if not df_div.empty:
            df_div_yearly = df_div.resample('YE').sum()
            # Pegar ultimos 3 anos fechados ou ultimos 3 registros
            ultimos_3_anos = df_div_yearly.tail(3)
            div_medio = ultimos_3_anos.mean()
            
            if div_medio > 0:
                preco_justo_bazin = div_medio / 0.06
                margem_bazin = ((preco_justo_bazin / dados_principais['preco']) - 1) * 100
                
                st.write(f"**Dividendo Médio Anual (Últimos 3 anos):** R$ {div_medio:.2f}")
                st.success(f"**Preço Teto (Bazin): R$ {preco_justo_bazin:.2f}**")
                
                if margem_bazin > 0:
                    st.info(f"**Margem de Segurança:** {margem_bazin:.2f}% (Ação pagando mais de 6% ao ano a este preço)")
                else:
                    st.warning(f"**Margem de Segurança:** {margem_bazin:.2f}% (Ação muito cara para pagar os 6% de dividendo)")
            else:
                 st.error("Empresa não pagou dividendos consistentes nos últimos 3 anos.")
        else:
             st.error("Histórico de dividendos não encontrado para calcular o modelo de Bazin.")
