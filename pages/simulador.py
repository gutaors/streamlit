import streamlit as st
from datetime import date
import pandas as pd
import plotly.graph_objs as go
import os

st.title("Simulador de Investimentos")

def listar_tickers_disponiveis():
    if os.path.exists('cotacoes'):
        return sorted([f.replace('.csv', '') for f in os.listdir('cotacoes') if f.endswith('.csv')])
    return []

def carregar_dados_acao(ticker):
    arquivo = f'cotacoes/{ticker}.csv'
    if os.path.exists(arquivo):
        try:
            df = pd.read_csv(arquivo)
            for col in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception as e:
            st.error(f'Erro ao ler arquivo {arquivo}: {str(e)}')
    return None

tickers_disponiveis = listar_tickers_disponiveis()
ticker = st.selectbox('Selecione o ativo:', tickers_disponiveis)
st.markdown("Caso o ticker não esteja na lista, [clique aqui para importar](/importa_cotacoes)")
st.markdown("Para consultar na mão: https://www.infomoney.com.br/cotacoes/b3/acao/petrobras-petr4/historico/")
if ticker:
    df_valores = carregar_dados_acao(ticker)

    if df_valores is not None:
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

        # Simulação de compra
        dados_compra = df_valores[df_valores['Date'].dt.date == data_compra_sim]
        if dados_compra.empty:
            proxima_data = df_valores[df_valores['Date'].dt.date > data_compra_sim]['Date'].min()
            if pd.isna(proxima_data):
                st.error(f"Não há dados disponíveis após {data_compra_sim}")
            else:
                dados_compra = df_valores[df_valores['Date'] == proxima_data]
                st.warning(f"Usando próxima data disponível: {proxima_data.date()}")

        if not dados_compra.empty:
            close_compra = dados_compra.iloc[0]['Close']
            quantidade_comprada = valor_sim / close_compra
            data_compra_real = dados_compra.iloc[0]['Date'].date()

            # Simulação de venda
            dados_venda = df_valores[df_valores['Date'].dt.date == data_venda_sim]
            if dados_venda.empty:
                data_anterior = df_valores[df_valores['Date'].dt.date < data_venda_sim]['Date'].max()
                if pd.isna(data_anterior):
                    st.error(f"Não há dados disponíveis antes de {data_venda_sim}")
                else:
                    dados_venda = df_valores[df_valores['Date'] == data_anterior]
                    st.warning(f"Usando data anterior disponível: {data_anterior.date()}")

            if not dados_venda.empty:
                close_venda = dados_venda.iloc[0]['Close']
                data_venda_real = dados_venda.iloc[0]['Date'].date()
                valor_vendido = quantidade_comprada * close_venda
                lucro_prejuizo = valor_vendido - valor_sim

                # Cálculo do período entre compra e venda
                df_periodo = df_valores[
                    (df_valores['Date'].dt.date >= data_compra_real) &
                    (df_valores['Date'].dt.date <= data_venda_real)
                ]

                # Exibição dos resultados
                col3, col4, col5 = st.columns(3)
                with col3: st.metric("Quantidade", f"{quantidade_comprada:.2f}")
                with col4: st.metric("Preço compra", f"R$ {close_compra:.2f}")
                with col5: st.metric("Preço venda", f"R$ {close_venda:.2f}")

                # Valores extremos no período
                if not df_periodo.empty:
                    max_periodo = df_periodo['Close'].max()
                    data_max = df_periodo[df_periodo['Close'] == max_periodo]['Date'].iloc[0].strftime('%d/%m/%Y')

                    min_periodo = df_periodo['Close'].min()
                    data_min = df_periodo[df_periodo['Close'] == min_periodo]['Date'].iloc[0].strftime('%d/%m/%Y')

                    col6, col7 = st.columns(2)
                    with col6:
                        st.metric("Maior valor no período",
                                f"R$ {max_periodo:.2f}",
                                f"Em {data_max}")
                    with col7:
                        st.metric("Menor valor no período",
                                f"R$ {min_periodo:.2f}",
                                f"Em {data_min}")
                else:
                    st.warning("Não há dados para o período selecionado")

                # Resultado final
                cor = "green" if lucro_prejuizo >= 0 else "red"
                st.markdown(f"""
                    <div style='padding:10px; border-radius:5px; background-color:{cor}; color:white; text-align:center; margin:10px 0;'>
                        <h3>Resultado: R$ {lucro_prejuizo:.2f} ({(lucro_prejuizo/valor_sim*100):.2f}%)</h3>
                    </div>""", unsafe_allow_html=True)

                # Gráfico
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_valores['Date'],
                    y=df_valores['Close'],
                    name='Preço',
                    line=dict(color='blue')
                ))
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