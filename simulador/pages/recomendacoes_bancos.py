import streamlit as st
import pandas as pd
import yfinance as yf
import os

st.set_page_config(page_title="Recomendações de Bancos", layout="wide")
st.title("🏦 Recomendações de Agências e Bancos")
st.markdown("Consulte o histórico estruturado de revisões de mercado e indicações (Compra/Venda/Manter) feitas por grandes bancos de investimento e agências analíticas.")

# Obtém a lista de arquivos CSV da pasta cotacoes para facilitar a busca
pasta_cotacoes = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cotacoes')
if os.path.exists(pasta_cotacoes):
    arquivos_csv = sorted([f.replace('.csv', '') for f in os.listdir(pasta_cotacoes) if f.endswith('.csv')])
else:
    arquivos_csv = []

col1, col2 = st.columns([2, 1])

with col1:
    if arquivos_csv:
        ticker_selecionado = st.selectbox('Escolha o Ativo (cadastrados localmente):', arquivos_csv)
    else:
        ticker_selecionado = st.text_input("Digite o Ticker (ex: ITUB4.SA)", value="ITUB4.SA")

with col2:
    st.write("")
    st.write("")
    buscar = st.button("Buscar Recomendações", use_container_width=True)

if buscar or ticker_selecionado:
    with st.spinner(f"Buscando dados para {ticker_selecionado}..."):
        try:
            # Garante que o ticker termina com .SA se não for índice gringo, embora yfinance seja tolerante
            ticker_busca = ticker_selecionado
            if not ticker_busca.endswith(".SA") and not ticker_busca.endswith(".sa") and len(ticker_busca) >= 4:
                # Opcional: ajustar se quiser forçar mercado BR. 
                # Deixaremos como está para não quebrar tickers internacionais caso o usuário digite AAPL.
                pass

            ativo = yf.Ticker(ticker_busca)
            df_recomendacoes = ativo.get_recommendations()

            if df_recomendacoes is not None and not df_recomendacoes.empty:
                st.success(f"Foram encontradas {len(df_recomendacoes)} avaliações para {ticker_selecionado}.")
                
                # Exibe a tabela estruturada das recomendações
                st.dataframe(df_recomendacoes, use_container_width=True)
                
                # Adiciona um gráfico de barras simples para facilitar a visualização da última revisão
                st.markdown("### 📊 Visão Geral do Período Mais Recente")
                ultima_revisao = df_recomendacoes.iloc[0] if 'period' in df_recomendacoes.columns and not df_recomendacoes.empty else df_recomendacoes.tail(1).squeeze()
                
                # Filtra apenas as colunas numéricas de recomendação (buy, sell, etc)
                colunas_voto = [c for c in df_recomendacoes.columns if c.lower() in ['strongbuy', 'buy', 'hold', 'sell', 'strongsell']]
                
                if colunas_voto:
                    df_grafico = df_recomendacoes[colunas_voto].copy()
                    if 'period' in df_recomendacoes.columns:
                        df_grafico.index = df_recomendacoes['period']
                    st.bar_chart(df_grafico)
            else:
                st.warning(f"O Yahoo Finance não retornou nenhuma recomendação cadastrada para o ativo {ticker_selecionado}.")
                
        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar as recomendações: {str(e)}")
