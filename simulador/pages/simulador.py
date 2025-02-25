# FALTA FAZER
# qual ação minha que está dando mais lucro hoje
# qual ação minha que está dando mais preju hoje
# o valor que paguei foi x
# o valor máximo foi x em data tal
# mes com maior volume negociado, volume e média diária
# o mês com melhor mediana foi tal, mediana tal
# o mês com pior mediana foi tal, mediana tal
# se vale mostrar valor do minério
# se petrobras mostrar valor do petroleo
# média móvel com setinha para 1 mes
# média móvel com setinha para 3 meses


import streamlit as st
from streamlit_option_menu import option_menu
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objs as go
import os

st.title("Simulador de Investimentos")

def listar_tickers_disponiveis():
    if os.path.exists('cotacoes'):
        arquivos = [f.replace('.csv', '') for f in os.listdir('cotacoes') if f.endswith('.csv')]
        return sorted(arquivos)
    return []

def carregar_dados_acao(ticker):
    arquivo = f'cotacoes/{ticker}.csv'
    if os.path.exists(arquivo):
        try:
            df = pd.read_csv(arquivo)
            # Converter colunas numéricas para float
            for col in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception as e:
            st.error(f'Erro ao ler arquivo {arquivo}: {str(e)}')
            return None
    return None

# Lista de tickers disponíveis
tickers_disponiveis = listar_tickers_disponiveis()

# Seleção do ticker via combo box
ticker = st.selectbox('Selecione o ativo:', tickers_disponiveis)

# Link fixo para importação
st.markdown("Caso o ticker não esteja na lista, [clique aqui para importar](/importa_cotacoes)")

if ticker:
    df_valores = carregar_dados_acao(ticker)
    
    if df_valores is not None:
        # Interface do usuário para entrada de dados
        col1, col2 = st.columns(2)
        
        with col1:
            data_compra_sim = st.date_input("Data de Compra (Simulação)", 
                                          min_value=df_valores['Date'].min().date(),
                                          max_value=df_valores['Date'].max().date())
            valor_sim = st.number_input("Valor de investimento (R$):", value=1000.00, step=0.01)
            
        with col2:
            data_venda_sim = st.date_input("Data de Venda (Simulação)",
                                         min_value=data_compra_sim,
                                         max_value=df_valores['Date'].max().date())
        
        # Simular a compra
        dados_compra = df_valores[df_valores['Date'].dt.date == data_compra_sim]
        if dados_compra.empty:
            # Encontra a próxima data disponível
            proxima_data = df_valores[df_valores['Date'].dt.date > data_compra_sim]['Date'].min()
            if pd.isna(proxima_data):
                st.error(f"Não há dados disponíveis após {data_compra_sim}")
            else:
                dados_compra = df_valores[df_valores['Date'] == proxima_data]
                st.warning(f"Dados não disponíveis para {data_compra_sim}. Usando próxima data disponível: {proxima_data.date()}")
        
        if not dados_compra.empty:
            close_compra = dados_compra.iloc[0]['Close']
            quantidade_comprada = valor_sim / close_compra
            
            # Simular a venda
            dados_venda = df_valores[df_valores['Date'].dt.date == data_venda_sim]
            if dados_venda.empty:
                # Encontra a data anterior disponível
                data_anterior = df_valores[df_valores['Date'].dt.date < data_venda_sim]['Date'].max()
                if pd.isna(data_anterior):
                    st.error(f"Não há dados disponíveis antes de {data_venda_sim}")
                else:
                    dados_venda = df_valores[df_valores['Date'] == data_anterior]
                    st.warning(f"Dados não disponíveis para {data_venda_sim}. Usando data anterior disponível: {data_anterior.date()}")
            
            if not dados_venda.empty:
                close_venda = dados_venda.iloc[0]['Close']
                valor_vendido = quantidade_comprada * close_venda
                lucro_prejuizo = valor_vendido - valor_sim
                
                # Exibir resultados
                col3, col4, col5 = st.columns(3)
                
                with col3:
                    st.metric("Quantidade de ações", f"{quantidade_comprada:.2f}")
                
                with col4:
                    st.metric("Preço de compra", f"R$ {close_compra:.2f}")
                
                with col5:
                    st.metric("Preço de venda", f"R$ {close_venda:.2f}")
                
                # Exibir resultado final
                cor = "green" if lucro_prejuizo >= 0 else "red"
                st.markdown(
                    f"""
                    <div style='padding: 10px; border-radius: 5px; background-color: {cor}; color: white; text-align: center; margin: 10px 0;'>
                        <h3>Resultado: R$ {lucro_prejuizo:.2f} ({(lucro_prejuizo/valor_sim*100):.2f}%)</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Gráfico
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_valores['Date'],
                    y=df_valores['Close'],
                    name='Preço',
                    line=dict(color='blue')
                ))
                
                # Adicionar marcadores para compra e venda
                fig.add_trace(go.Scatter(
                    x=[dados_compra.iloc[0]['Date']],
                    y=[close_compra],
                    mode='markers',
                    name='Compra',
                    marker=dict(color='green', size=12)
                ))
                
                fig.add_trace(go.Scatter(
                    x=[dados_venda.iloc[0]['Date']],
                    y=[close_venda],
                    mode='markers',
                    name='Venda',
                    marker=dict(color='red', size=12)
                ))
                
                fig.update_layout(
                    title=f'Histórico de preços - {ticker}',
                    xaxis_title='Data',
                    yaxis_title='Preço (R$)',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig)
