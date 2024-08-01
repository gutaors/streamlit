from datetime import datetime
import json
import pandas_datareader.data as web
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os



def carregar_dados():

# Função para ler a data do arquivo JSON

    # Lê todas cotacoes históricas gravadas no csv
    #df_csv = pd.read_csv('codigo/quant/dados/cotacoes.csv', sep=',')
    df_csv = pd.read_csv('/home/gutao/dev/venv/streamlit/simulador/dados/cotacoes.csv', sep=',')
    #compara proveniente do csv com o dataframe que acabamos de baixar de cotações históricas

    datainicio = '2015-01-01'
    datafim = datetime.now()
    #datafim = '2023-11-14'
    # Lista de TICKERS
    #tickers = ['PETR4.SA','VALE3.SA','B3SA3.SA','RAIL3.SA','CARD3.SA','SHUL4.SA','ITUB4.SA','JBSS3.SA']
    # Lê arquivo csv com dados das minhas compras (não são dados históricos)
    #df_tickers = pd.read_csv('codigo/quant/dados/tickers.csv', sep=';')
    df_tickers = pd.read_csv('/home/gutao/dev/venv/streamlit/simulador/dados/tickers.csv', sep=';')
    # Remover a linha onde o campo ticker é igual a "ENBR3.SA"
    df_tickers = df_tickers[df_tickers['ticker'] != 'ENBR3.SA']
    #df_tickers.head(10)
    tickers = df_tickers['ticker'].tolist()

    # Dataframe para preencher
    df_resumo = pd.DataFrame(columns=['ticker', 'datain', 'datafim', 'acao', 'valor_maximo_ticker','data_valor_maximo', 'valor_minimo_ticker', 'data_valor_minimo', 'valor_atual_ticker', 'valor_atual_total'])

    #função para obter valor atual
    def valor_atual(ticker):
        try:
            acao = yf.Ticker(ticker)
            valor_atual_ticker = acao.info["currentPrice"]
            return valor_atual_ticker
        except KeyError:
            return "Informação de preço atual não disponível para o ticker fornecido."
        except Exception as e:
            return f"Ocorreu um erro: {e}"


    for ticker in tickers:
        datafim = datetime.now()
        datainicio = df_tickers.loc[df_tickers['ticker'] == ticker, 'data'].values[0]
        datainicio = datetime.strptime(datainicio, '%d/%m/%Y')
        #@#
        # print(ticker,datainicio, datafim)
        acao = yf.download(ticker, start = datainicio, end = datafim)
        valor_maximo_ticker = acao['High'].max()
        if not acao[acao['High'] == valor_maximo_ticker].empty:
            data_valor_maximo = acao[acao['High'] == valor_maximo_ticker].index[0].date()
        else:
            data_valor_maximo = "null"  # ou um valor padrão, caso não haja valores
            # Filtrar valores acima de zero
        valores_acima_de_zero = acao['Low'][acao['Low'] > 0]
        if not valores_acima_de_zero.empty:
                valor_minimo_ticker = valores_acima_de_zero.min()
        else:
                valor_minimo_ticker = None  # ou um valor padrão, caso não haja valores acima de zero

        #data_valor_minimo = acao['Low'].idxmin().date()
        if not acao[acao['Low'] == valor_minimo_ticker].empty:
            data_valor_minimo = acao[acao['Low'] == valor_minimo_ticker].index[0].date()
        else:
            data_valor_minimo = "null"  # ou um valor padrão, caso não haja valores
            # Filtrar valores acima de zero
        acao = yf.Ticker(ticker)
        #  valor_atual_ticker = acao.info["currentPrice"]


    # current value of the ticker
    valor_atual_ticker = valor_atual(ticker)


    valor_atual_total = df_tickers.loc[df_tickers['ticker'] == ticker, 'quantidade'].values[0] * valor_atual(ticker)

    nova_linha = pd.DataFrame([[ticker, datainicio, datafim, acao, valor_maximo_ticker, data_valor_maximo, valor_minimo_ticker,data_valor_minimo, valor_atual_ticker, valor_atual_total]], columns=df_resumo.columns)

    df_resumo = pd.concat([df_resumo, nova_linha], ignore_index=True)

    # Junta com uma analise e escreve no analise.csv
    df_analise = df_resumo.merge(df_tickers, on='ticker', how='inner')
    df_analise['lucro_prej'] = df_analise['valor_atual_total'] - df_analise['investi']
    df_analise['lucro_prej_max'] = (df_analise['valor_maximo_ticker'] * df_analise['quantidade']) - df_analise['investi']
    df_analise['lucro_prej_min'] = (df_analise['valor_minimo_ticker'] * df_analise['quantidade']) - df_analise['investi']
    # update the field valor_atual_ticker with the value of the ticker now

    path_csv = "/home/gutao/dev/venv/streamlit/simulador/dados/analise.csv"

    df_analise.to_csv(path_csv)

    #df_analise
    df_analise[['ticker', 'datain', 'datafim', 'valor_maximo_ticker', 'data_valor_maximo', 'valor_minimo_ticker', 'data_valor_minimo', 'valor_atual_ticker', 'valor_atual_total', 'quantidade', 'paguei', 'investi', 'data', 'lucro_prej']]


    #obter valor máximo
    def obter_valor_maximo(ticker, periodo):
        # Obtém os dados históricos do ticker
        dados = yf.download(ticker, period=periodo)

    # Obtém o valor máximo e a data correspondente
        valor_maximo = dados['Close'].max()
        data_valor_maximo = dados[dados['Close'] == valor_maximo].index[0].strftime('%Y-%m-%d')

        return valor_maximo, data_valor_maximo

    #@#
    #print(f'O valor máximo do ticker {ticker} foi de {valor_max} em {data_max}.')

    nomes_colunas =  df_tickers.columns

    # Imprimir os nomes das colunas
    #@#
    #print(nomes_colunas)

    # Obter a data atual
    data_atual = datetime.today().strftime("%Y%m%d")

    # Definir o caminho antigo e novo
    #caminho_antigo = 'dados/cotacoes.csv'
    #caminho_novo = f'dados/cotacoes_{data_atual}.csv'

    # Renomear o arquivo
    #os.rename(caminho_antigo, caminho_novo)
    #path_csv = "codigo/quant/dados/cotacoes.csv"
    #path_csv = "dados/cotacoes.csv"

    #df_cotacoes.to_csv(path_csv)

    # Download de Dados históricos dos tickers
    #!pip install yfinance --upgrade --no-cache-dir
    tickers = df_tickers['ticker'].tolist()
    # Crie uma lista vazia para armazenar os DataFrames de cotações
    df_list = []
    for ticker in tickers:
        datafim = datetime.now()
        datain = df_tickers.loc[df_tickers['ticker'] == ticker, 'data'].values[0]
        datain = datetime.strptime(datain, '%d/%m/%Y')
        acao = yf.download(ticker, start = datain, end = datafim)
        acao['Ticker'] = ticker  # Adicione uma coluna para identificar o ticker
        acao.reset_index(inplace=True)  # Resetar o índice, removendo a data como índice
        df_list.append(acao)

        # Concatene os DataFrames de cotações em um único DataFrame
        df_cotacoes = pd.concat(df_list)
        df_cotacoes.head(10)
        #compara_historico(df_cotacoes, df_tickers)

    #aqui embaixo no get estava dando erro TypeError: string indices must be integers
    #é porque eu fiz import pandas_datareader as web ao inves de
    #fazer o certo   import pandas_datareader.data as web
    #Filtrando data na fonte
    datainicio = '2015-01-01'
    datafim = datetime.now()
    #datafim = '2023-11-14'
    # Lista de TICKERS
    #tickers = ['PETR4.SA','VALE3.SA','B3SA3.SA','RAIL3.SA','CARD3.SA','SHUL4.SA','ITUB4.SA','JBSS3.SA']
    tickers = df_tickers['ticker'].tolist()

    # Dataframe para preencher
    df_resumo = pd.DataFrame(columns=['ticker', 'datain', 'datafim', 'acao', 'valor_maximo_ticker','data_valor_maximo', 'valor_minimo_ticker', 'data_valor_minimo', 'valor_atual_ticker', 'valor_atual_total'])

    #função para obter valor atual
    def valor_atual(ticker):
        try:
            acao = yf.Ticker(ticker)
            valor_atual_ticker = acao.info["currentPrice"]
            return valor_atual_ticker
        except KeyError:
            return "Informação de preço atual não disponível para o ticker fornecido."
        except Exception as e:
            return f"Ocorreu um erro: {e}"



    for ticker in tickers:
        datafim = datetime.now()
        datainicio = df_tickers.loc[df_tickers['ticker'] == ticker, 'data'].values[0]
        datainicio = datetime.strptime(datainicio, '%d/%m/%Y')
        #@#
        # print(ticker,datainicio, datafim)
        acao = yf.download(ticker, start = datainicio, end = datafim)
        valor_maximo_ticker = acao['High'].max()
        if not acao[acao['High'] == valor_maximo_ticker].empty:
            data_valor_maximo = acao[acao['High'] == valor_maximo_ticker].index[0].date()
        else:
            data_valor_maximo = "null"  # ou um valor padrão, caso não haja valores
            # Filtrar valores acima de zero
        valores_acima_de_zero = acao['Low'][acao['Low'] > 0]
        if not valores_acima_de_zero.empty:
                valor_minimo_ticker = valores_acima_de_zero.min()
        else:
                valor_minimo_ticker = None  # ou um valor padrão, caso não haja valores acima de zero

        #data_valor_minimo = acao['Low'].idxmin().date()
        if not acao[acao['Low'] == valor_minimo_ticker].empty:
            data_valor_minimo = acao[acao['Low'] == valor_minimo_ticker].index[0].date()
        else:
            data_valor_minimo = "null"  # ou um valor padrão, caso não haja valores
            # Filtrar valores acima de zero
        acao = yf.Ticker(ticker)
        #  valor_atual_ticker = acao.info["currentPrice"]


        # current value of the ticker
        valor_atual_ticker = valor_atual(ticker)


        valor_atual_total = df_tickers.loc[df_tickers['ticker'] == ticker, 'quantidade'].values[0] * valor_atual(ticker)

        nova_linha = pd.DataFrame([[ticker, datainicio, datafim, acao, valor_maximo_ticker, data_valor_maximo, valor_minimo_ticker,data_valor_minimo, valor_atual_ticker, valor_atual_total]], columns=df_resumo.columns)

        df_resumo = pd.concat([df_resumo, nova_linha], ignore_index=True)

    # Verificar se os DataFrames são iguais
    if len(df_csv) == len(df_cotacoes) and pd.to_datetime(df_csv["Date"].max()).date() == pd.to_datetime(df_cotacoes["Date"].max()).date() and set(df_csv['Ticker']) == set(df_cotacoes['Ticker']) :
        print("DATAFRAMES IGUAIS, O número de linhas e a data de atualização é igual nos dois DataFrames e ambos tem os mesmos tickers.")
        print("Data do último registro: "+df_csv["Date"].max())
        print("Data hoje: " + datafim.strftime('%Y-%m-%d'))
    # Se o dataframe atual é maior que o csv e tem data máxima mais recente, então renomeia o csv e substitui o csv pelo dataframe atual
    elif len(df_csv) < len(df_cotacoes) and pd.to_datetime(df_csv["Date"].max()).date() < pd.to_datetime(df_cotacoes["Date"].max()).date():
        print("DATAFRAMES DIFERENTES.")
        print(df_csv["Date"].max())
        print(df_cotacoes["Date"].max().date())
        print(len(df_csv))
        print(len(df_cotacoes))

    def compara_historico(df_cotacoes, df_tickers):
        import os
        try:
            # Lê todas cotacoes históricas gravadas no csv
            df_csv = pd.read_csv('/home/gutao/dev/venv/streamlit/simulador/dados/cotacoes.csv', sep=',')

            # Verificar se os DataFrames são iguais
            if not df_csv.empty and not df_cotacoes.empty and df_csv.equals(df_cotacoes):
                #@#
                print("DATAFRAMES IGUAIS, O número de linhas e a data de atualização é igual nos dois DataFrames e ambos tem os mesmos tickers.")
                print("Data do último registro: " + str(df_csv["Date"].max()))
                print("Data hoje: " + str(datetime.now().date()))
            else:
                # Se o dataframe atual é maior que o csv e tem data máxima mais recente, então renomeia o csv e substitui o csv pelo dataframe atual
                if not df_csv.empty and not df_cotacoes.empty and len(df_csv) < len(df_cotacoes) and pd.to_datetime(df_csv["Date"].max()).date() < pd.to_datetime(df_cotacoes["Date"].max()).date():
                    # Obter a data atual
                    data_atual = datetime.today().strftime("%Y%m%d")
                    # Definir o caminho antigo e novo
                    caminho_antigo = '/home/gutao/dev/venv/streamlit/simulador/dados/cotacoes.csv'
                    caminho_novo = f'/home/gutao/dev/venv/streamlit/simulador/dados/cotacoes_{data_atual}.csv'
                    # Renomear o arquivo
                    os.rename(caminho_antigo, caminho_novo)
                    # Substituir o arquivo pelo dataframe atual
                    df_cotacoes.to_csv(caminho_antigo, index=False)
                    # Faz uma análise dos tickers, joga tudo em df_resumo
                    import requests
        except FileNotFoundError:
            print("Arquivo de cotacoes.csv não encontrado.")
        except Exception as e:
            print(f"Erro inesperado: {str(e)}")


    compara_historico(df_cotacoes, df_tickers)

    # Certifique-se de que a coluna 'Date' esteja no formato datetime
    df_cotacoes['Date'] = pd.to_datetime(df_cotacoes['Date'])

    # Ordene o DataFrame pela coluna 'Date' em ordem decrescente
    df_cotacoes_sorted = df_cotacoes.sort_values(by='Date', ascending=False)

    # Imprima o DataFrame ordenado
    df_cotacoes_sorted.head(40)

    df_cotacoes_sorted.to_csv('/home/gutao/dev/venv/streamlit/simulador/dados/cotacoes.csv', index=False)



carregar_dados()






















#cotacao atual de um ticker B3
'''
import yfinance as yf
ticker = "B3SA3.SA"
acao = yf.Ticker(ticker)
valor_atual_ticker = acao.info["currentPrice"]
print(f"Cotação atual de B3SA3: {valor_atual_ticker}")
'''

#Cotação de um ticker para uma data informada:
'''
import yfinance as yf
from datetime import datetime, timedelta

ticker = "B3SA3.SA"
#data_ontem = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
data_desejada = "2023-08-14"
acao = yf.Ticker(ticker)
historico = acao.history(period="1d", interval="1d", start=data_desejada)
valor_cotacao = historico["Close"].values[0] if not historico.empty else None

if valor_cotacao is not None:
    print(f"Cotação de {ticker} em ({data_desejada}): {valor_cotacao:.2f}")
else:
    print(f"Não há dados de cotação disponíveis para {ticker} em ({data_desejada}).")
    '''

