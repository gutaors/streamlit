import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os

st.title('Importar Cotações')

# Criar diretório de cotações se não existir
if not os.path.exists('cotacoes'):
    os.makedirs('cotacoes')

# Função para listar tickers já importados
def listar_tickers_importados():
    if os.path.exists('cotacoes'):
        return [f.replace('.csv', '') for f in os.listdir('cotacoes') if f.endswith('.csv')]
    return []

# Função para baixar dados do Yahoo Finance
def baixar_dados_yahoo(ticker, data_inicio, data_fim):
    try:
        ticker_yf = ticker if ticker.endswith('.SA') else f'{ticker}.SA'
        df = yf.download(ticker_yf, start=data_inicio, end=data_fim)
        if df.empty:
            return None, "Nenhum dado encontrado para este ticker"
        df.reset_index(inplace=True)
        return df, None
    except Exception as e:
        return None, f"Erro ao baixar dados: {str(e)}"

# Função para validar formato do ticker
def validar_ticker(ticker):
    if not ticker:
        return False, "Digite um ticker"
    if len(ticker) < 4:
        return False, "Ticker deve ter pelo menos 4 caracteres"
    return True, ""

# Interface principal
col1, col2 = st.columns([2, 1])

with col1:
    # Input do ticker
    ticker = st.text_input('Digite o código do ativo (ex: PETR4):', '').upper()
    
    # Datas
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=5*365)  # 5 anos de dados
    
    col_data1, col_data2 = st.columns(2)
    with col_data1:
        data_inicio = st.date_input('Data Início:', value=data_inicio)
    with col_data2:
        data_fim = st.date_input('Data Fim:', value=data_fim)

    if st.button('Importar Dados'):
        # Validar ticker
        valido, mensagem = validar_ticker(ticker)
        
        if not valido:
            st.error(mensagem)
        else:
            with st.spinner('Baixando dados...'):
                df, erro = baixar_dados_yahoo(ticker, data_inicio, data_fim)
                
                if erro:
                    st.error(erro)
                else:
                    # Salvar dados
                    salvar_dataframe(ticker, df)
                    
                    # Mostrar preview
                    st.success(f'Dados do ticker {ticker} importados com sucesso!')
                    st.write('Preview dos dados:')
                    st.dataframe(df.head())

with col2:
    # Lista de tickers já importados
    st.subheader('Tickers Importados')
    tickers_importados = listar_tickers_importados()
    
    if st.button('Visualizar'):
        if tickers_importados:
            # Lista para armazenar os heads e tails
            all_data = []
            
            # Ler todos os arquivos
            for ticker in sorted(tickers_importados):
                try:
                    df = pd.read_csv(f'cotacoes/{ticker}.csv')
                    df['Ticker'] = ticker  # Adiciona coluna com nome do ticker
                    
                    # Pegar a primeira e última linha
                    df_head = df.head(1)
                    df_tail = df.tail(1)
                    
                    # Combinar head e tail para este ticker
                    all_data.append(pd.concat([df_head, df_tail]))
                    
                except Exception as e:
                    st.error(f"Erro ao ler dados do ticker {ticker}: {str(e)}")
            
            if all_data:
                # Combinar todos os dataframes
                df_combined = pd.concat(all_data, ignore_index=True)
                df_combined['Date'] = pd.to_datetime(df_combined['Date'])
                
                # Ordenar por ticker e data
                df_combined = df_combined.sort_values(['Ticker', 'Date'])
                
                st.subheader("Primeira e última linha de todos os ativos:")
                st.dataframe(df_combined, use_container_width=True)
        else:
            st.info('Nenhum ticker importado ainda')
    else:
        # Mostrar lista simples de tickers
        if tickers_importados:
            for t in sorted(tickers_importados):
                st.markdown(f"- {t}")
        else:
            st.info('Nenhum ticker importado ainda')
