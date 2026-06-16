import streamlit as st
import os
import pandas as pd
from datetime import date
import numpy as np

st.title("Coleta Preço de Ativo")
st.header("Informações a respeito de fechamento, volume e Médias Móveis")

# Define a pasta onde estão os arquivos CSV
pasta_cotacoes = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cotacoes')
arquivos_csv = [f.replace('.csv', '') for f in os.listdir(pasta_cotacoes) if f.endswith('.csv')]
arquivos_csv.sort()

# Permite a escolha do ativo pelo usuário
ticker_simbolo = st.selectbox('Escolha o Ativo', arquivos_csv)

# Monta o caminho para o arquivo CSV correspondente
caminho_csv = os.path.join(pasta_cotacoes, ticker_simbolo + '.csv')

# Lê o arquivo CSV
tickerDF = pd.read_csv(caminho_csv)

# Se existir a coluna 'Date', converte para datetime, define como índice e ordena
if 'Date' in tickerDF.columns:
    tickerDF['Date'] = pd.to_datetime(tickerDF['Date'], errors='coerce')
    tickerDF = tickerDF.dropna(subset=['Date'])
    tickerDF.set_index('Date', inplace=True)
    tickerDF.sort_index(inplace=True)

# Campo Data de Corte (pré-preenchido com a data atual)
cut_date = st.date_input("Data de Corte", value=date.today())

# Cria um novo dataframe filtrado até a data de corte
df_cut = tickerDF[tickerDF.index <= pd.to_datetime(cut_date)]

# Converte a coluna 'Close' para numérico e remove valores nulos
if 'Close' in df_cut.columns:
    df_cut['Close'] = pd.to_numeric(df_cut['Close'], errors='coerce')
    df_cut = df_cut.dropna(subset=['Close'])
    if 'Volume' in df_cut.columns:
        df_cut['Volume'] = pd.to_numeric(df_cut['Volume'], errors='coerce')

# Exibe apenas os dados mais recentes
st.subheader("Dados mais recentes até a data de corte")
ultimos_dados = df_cut.tail(1)
if not ultimos_dados.empty:
    col1, col2 = st.columns(2)

    # Último preço
    ultimo_preco = float(ultimos_dados['Close'].iloc[0])
    col1.metric("Último Preço", f"R$ {ultimo_preco:.2f}")
    col1.write(f"Data: {ultimos_dados.index[0].strftime('%d/%m/%Y')}")

    # Máximo e Mínimo
    max_idx = df_cut['Close'].idxmax()
    min_idx = df_cut['Close'].idxmin()
    max_val = float(df_cut.loc[max_idx, 'Close'])
    min_val = float(df_cut.loc[min_idx, 'Close'])

    col1.markdown(f'<div style="color: #0f9d58;"><b>Valor Máximo:</b> R$ {max_val:.2f}</div>', unsafe_allow_html=True)
    col1.markdown(f'<div style="color: #0f9d58;">Data: {max_idx.strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
    col1.markdown(f'<div style="color: #0f9d58;"><b>Valor Mínimo:</b> R$ {min_val:.2f}</div>', unsafe_allow_html=True)
    col1.markdown(f'<div style="color: #0f9d58;">Data: {min_idx.strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)

    # Volume
    if 'Volume' in ultimos_dados.columns and pd.notna(ultimos_dados['Volume'].iloc[0]):
        ultimo_volume = int(ultimos_dados['Volume'].iloc[0])
        col2.metric("Volume", f"{ultimo_volume:,}")
        col2.write("Último volume negociado")




if not df_cut.empty:
    # Cálculo das Médias Móveis
    df_cut['MM50'] = df_cut['Close'].rolling(window=50).mean()
    df_cut['MM200'] = df_cut['Close'].rolling(window=200).mean()

    # Gráfico de Fechamento com MM50 e MM200
    st.header("Gráfico de Fechamento com MM50 e MM200")
    chart_data = df_cut[['Close', 'MM50', 'MM200']].dropna()
    st.line_chart(chart_data)

    # Identifica os pontos de cruzamento
    cross = df_cut['MM50'] > df_cut['MM200']
    sinal = cross.ne(cross.shift())
    cross_df = df_cut[sinal].copy()

    # Prepara a tabela de cruzamentos
    if not cross_df.empty:
        st.subheader("Pontos de Cruzamento das Médias Móveis")
        cross_df['Recomendacao'] = cross_df.apply(
            lambda x: 'COMPRA' if x['MM50'] > x['MM200'] else 'VENDA',
            axis=1
        )

        # Formata a tabela de cruzamentos
        tabela_cruzamentos = pd.DataFrame({
            'Nº': range(1, len(cross_df) + 1),
            'Data': cross_df.index.strftime('%d/%m/%Y'),
            'Preço': [f"R$ {price:.2f}" for price in cross_df['Close']],
            'Recomendação': cross_df['Recomendacao']
        })

        # CSS para ajustar colunas
        st.markdown("""
            <style>
            .stTable td:first-child {
                width: 40px !important;
                min-width: 40px !important;
                max-width: 40px !important;
            }
            .stTable td:nth-child(2) {
                min-width: 120px;
            }
            </style>
        """, unsafe_allow_html=True)

        # Ordena colunas
        tabela_cruzamentos = tabela_cruzamentos[['Nº', 'Data', 'Preço', 'Recomendação']]

        # Mostra tabela
        st.table(tabela_cruzamentos)

        # >>> NOVO DATAFRAME FINAL <<<
        df_cruzamentos = tabela_cruzamentos.copy()

        



        if "df_cruzamentos" in st.session_state:

            df_cruzamentos = st.session_state["df_cruzamentos"].copy()

            # Garantir ordem cronológica
            df_cruzamentos = df_cruzamentos.sort_values(by="Data")

            # Extrair preços em formato numérico
            df_cruzamentos["Preco_num"] = (
                df_cruzamentos["Preço"]
                .str.replace("R$", "", regex=False)
                .str.replace(",", ".", regex=False)
                .astype(float)
            )

            # Variáveis iniciais
            valor = 10000.0
            quantidade = 0.0
            comprado = False

            # Loop pelas linhas do DataFrame
            for idx, row in df_cruzamentos.iterrows():

                preco = row["Preco_num"]
                recomendacao = row["Recomendação"]

                # Primeira compra ou compra após venda
                if recomendacao == "COMPRA" and not comprado:
                    quantidade = valor / preco
                    comprado = True

                # Venda
                elif recomendacao == "VENDA" and comprado:
                    valor = quantidade * preco
                    quantidade = 0
                    comprado = False

            # Se terminar comprado, valor permanece o mesmo (a pedido do usuário)
            preco_ultimo = df_cruzamentos["Preco_num"].iloc[-1]

            st.write("### Resultado Final")
            st.write(f"**Valor final:** R$ {valor:,.2f}")
            st.write(f"**Quantidade final:** {quantidade}")
            st.write(f"**Preço da última linha:** R$ {preco_ultimo:.2f}")

        else:
            st.warning("df_cruzamentos ainda não foi gerado.")




        # Análise de concretização das recomendações
        st.subheader("Data da Concretização")

        dados_concretizacao = []
        numero = 1

        for idx, row in cross_df.iterrows():
            preco_ref = row['Close']
            data_ref = idx
            recomendacao = row['Recomendacao']

            # Pega todos os preços após a data de referência
            precos_futuros = df_cut.loc[df_cut.index > data_ref, 'Close']

            if recomendacao == 'COMPRA':
                # Procura quando atingiu +10%
                preco_alvo = preco_ref * 1.10
                mask = precos_futuros >= preco_alvo
            else:  # VENDA
                # Procura quando atingiu -10%
                preco_alvo = preco_ref * 0.90
                mask = precos_futuros <= preco_alvo

            if mask.any():
                # Encontrou o objetivo
                data_concretizacao = precos_futuros[mask].index[0]
                preco_concretizacao = precos_futuros[mask].iloc[0]
                dias_passados = (data_concretizacao - data_ref).days

                dados_concretizacao.append({
                    'Nº': numero,
                    'Data Sinal': data_ref.strftime('%d/%m/%Y'),
                    'Preço Sinal': f"R$ {preco_ref:.2f}",
                    'Recomendação': recomendacao,
                    'Data Concretização': data_concretizacao.strftime('%d/%m/%Y'),
                    'Dias Passados': dias_passados,
                    'Preço Concretização': f"R$ {preco_concretizacao:.2f}"
                })
                numero += 1

        if dados_concretizacao:
            df_concretizacao = pd.DataFrame(dados_concretizacao)

            # Aplica cores diferentes para compra e venda e ajusta largura da coluna
            def color_recomendacao(val):
                color = '#0f9d58' if val == 'COMPRA' else '#dc3545'
                return f'color: {color}'

            def style_df(df):
                return df.style.apply(
                    lambda x: [color_recomendacao(x['Recomendação'])] * len(x),
                    axis=1
                ).set_properties(**{
                    'Data Sinal': 'min-width: 120px',
                    'Nº': 'width: 40px'
                })

            # Adiciona CSS global para ajustar a largura da coluna Nº
            st.markdown("""
                <style>
                .stTable td:first-child {
                    width: 40px !important;
                    min-width: 40px !important;
                    max-width: 40px !important;
                }
                </style>
            """, unsafe_allow_html=True)

            st.table(style_df(df_concretizacao))

            # Seção de Resumo
            st.subheader("Resumo *vender quando recomendação é compra parece funcionar melhor*")

            # Calcula as médias e medianas de dias para cada tipo de recomendação
            df_compras = df_concretizacao[df_concretizacao['Recomendação'] == 'COMPRA']
            df_vendas = df_concretizacao[df_concretizacao['Recomendação'] == 'VENDA']

            media_dias_compra = df_compras['Dias Passados'].mean() if not df_compras.empty else 0
            media_dias_venda = df_vendas['Dias Passados'].mean() if not df_vendas.empty else 0
            mediana_dias_compra = df_compras['Dias Passados'].median() if not df_compras.empty else 0
            mediana_dias_venda = df_vendas['Dias Passados'].median() if not df_vendas.empty else 0

            # Exibe as médias e medianas com cores diferentes
            col1, col2 = st.columns(2)

            # Média e Mediana de dias para Compra (Verde)
            col1.markdown(
                f'<div style="color: #0f9d58; font-size: 16px;"><b>Dias para Valorização de 10%:</b></div>',
                unsafe_allow_html=True
            )
            col1.markdown(
                f'<div style="color: #0f9d58; font-size: 24px;"><b>Média: {media_dias_compra:.0f} dias</b></div>',
                unsafe_allow_html=True
            )
            col1.markdown(
                f'<div style="color: #0f9d58; font-size: 24px;"><b>Mediana: {mediana_dias_compra:.0f} dias</b></div>',
                unsafe_allow_html=True
            )

            # Média e Mediana de dias para Venda (Vermelho)
            col2.markdown(
                f'<div style="color: #dc3545; font-size: 16px;"><b>Dias para Desvalorização de 10%:</b></div>',
                unsafe_allow_html=True
            )
            col2.markdown(
                f'<div style="color: #dc3545; font-size: 24px;"><b>Média: {media_dias_venda:.0f} dias</b></div>',
                unsafe_allow_html=True
            )
            col2.markdown(
                f'<div style="color: #dc3545; font-size: 24px;"><b>Mediana: {mediana_dias_venda:.0f} dias</b></div>',
                unsafe_allow_html=True
            )

            # Seção de Pesquisa por Data
            st.markdown("---")
            st.subheader("Pesquisa de Preços por Data")

            col1, col2 = st.columns([2, 1])

            # Campo de data
            data_pesquisa = col1.date_input(
                "Selecione uma data para pesquisar",
                value=date.today(),
                format="DD/MM/YYYY"
            )

            # Botão de pesquisa
            if col2.button("Pesquisar 20 dias"):
                # Converte a data para datetime
                data_inicio = pd.to_datetime(data_pesquisa)

                # Filtra os dados para a data selecionada e os próximos 20 dias
                mask = (df_cut.index >= data_inicio)
                df_periodo = df_cut[mask].head(21)  # 21 para incluir o dia inicial

                if not df_periodo.empty:
                    # Cria DataFrame com as colunas desejadas
                    df_resultado = pd.DataFrame({
                        'Data': df_periodo.index.strftime('%d/%m/%Y'),
                        'Preço de Fechamento': [f"R$ {price:.2f}" for price in df_periodo['Close']]
                    })

                    # Exibe a tabela
                    st.table(df_resultado)
                else:
                    st.warning("Não foram encontrados dados para o período selecionado.")

        else:
            st.info("Não foram encontradas concretizações de recomendações no período analisado.")
    else:
        st.info("Não foram encontrados pontos de cruzamento no período selecionado.")




# Footer
st.markdown("---")
st.write("Desenvolvido por Gustavo")