import streamlit as st
import os
import yfinance as yf
import pandas as pd
from datetime import datetime

def baixa_cotacoes(ticker):
    # Simulação de funcionalidade para baixar cotações
    st.info(f"Baixando cotações para o ticker: {ticker}...")
    # Aqui você pode adicionar a lógica real para baixar e salvar os dados.
    baixar_cotacoes(ticker)

def formatar_ticker(ticker):
    """Verifica e formata o ticker para garantir que termina com .sa."""
    ticker = ticker.strip()
    if not ticker.lower().endswith(".sa"):
        ticker += ".sa"
    return ticker

def verificar_arquivo_existente(ticker):
    """Verifica se o arquivo já existe no diretório 'cotacoes'."""
    #file_path = os.path.join("cotacoes", f"{ticker}.csv")
    file_path = os.path.join("cotacoes", f"{ticker.upper()}.csv")

    return os.path.exists(file_path)



def verificar_ticker_real(ticker: str) -> bool:
    """
    Verifica se um ticker é real, consultando dados no Yahoo Finance.

    Parâmetros:
        ticker (str): O código do ativo a ser verificado.

    Retorna:
        bool: True se o ticker for válido, False caso contrário.
    """
    try:
        # Tentar baixar apenas um período curto para validar
        df = yf.download(ticker, period="1d")
        return not df.empty  # Retorna True se o DataFrame não estiver vazio
    except Exception:
        return False


def baixar_cotacoes(ticker: str) -> pd.DataFrame:
    """
    Baixa um DataFrame de cotações para o ticker fornecido,
    com dados entre 01/01/2018 e o dia atual.

    Parâmetros:
        ticker (str): O código do ativo para buscar as cotações.

    Retorna:
        pd.DataFrame: Um DataFrame contendo as cotações do ativo.
    """
    # Definir a data inicial e final
    data_inicio = "2018-01-01"
    data_fim = datetime.today().strftime('%Y-%m-%d')

    # Baixar os dados
    #df = yf.download(ticker, start=data_inicio, end=data_fim)
    df = yf.download(ticker, start=data_inicio, end=data_fim).reset_index()


    # Verificar se os dados foram baixados com sucesso
    if df.empty:
        raise ValueError(f"Não foram encontrados dados para o ticker {ticker}.")
    else:
        salvar_dataframe(ticker, df)
    #return df

# Exemplo de uso:
# df_cotacoes = baixar_cotacoes("AAPL")
# print(df_cotacoes.head())
import pandas as pd
import os

def salvar_dataframe(ticker: str, df: pd.DataFrame):
    """
    Salva um DataFrame em um arquivo CSV com o nome do ticker em maiúsculas (exceto a extensão).

    Parâmetros:
        ticker (str): O código do ativo a ser usado no nome do arquivo.
        df (pd.DataFrame): O DataFrame a ser salvo.

    Retorna:
        None
    """
    # Nome do arquivo com o ticker em maiúsculas e extensão em minúsculas
    nome_arquivo = f"{ticker.upper()}.csv"

    # Certificar-se de que a pasta "cotacoes" existe e salvar o arquivo nela
    caminho_pasta = "cotacoes"
    os.makedirs(caminho_pasta, exist_ok=True)  # Cria a pasta se não existir


    # Caminho completo para salvar o arquivo
    caminho_arquivo = os.path.join(caminho_pasta, nome_arquivo)

    # Salvar o DataFrame no arquivo CSV
    df.to_csv(caminho_arquivo, index=False)
    print(f"Arquivo salvo como: {nome_arquivo}")

# Exemplo de uso:
# df_exemplo = pd.DataFrame({'Data': ['2023-01-01', '2023-01-02'], 'Preço': [100, 101]})

def importa_tickers(ticker):

            if ticker.strip():
                ticker = formatar_ticker(ticker)

                # Verificar se o arquivo já existe no diretório "cotacoes"
                if verificar_arquivo_existente(ticker):
                    st.warning(f"O arquivo '{ticker}.csv' já existe no diretório 'cotacoes'.")
                else:
                    if verificar_ticker_real(ticker):
                        baixa_cotacoes(ticker)
                        st.success(f"Ticker '{ticker}' enviado com sucesso!")
                    else:
                        st.warning(f"O ticker '{ticker}' não existe.")
            else:
                st.error("Por favor, insira um código de ticker válido.")

def preparar_lista_tickers_b3(arquivo_csv: str):
    """
    Prepara uma lista chamada tickers_b3 com todos os tickers da B3
    a partir de um arquivo CSV.

    Parâmetros:
        arquivo_csv (str): O caminho para o arquivo CSV contendo os tickers da B3.
    """
    global tickers_b3  # Define a lista como global
    tickers_b3 = []  # Inicializa a lista como vazia

    try:
        # Ler o arquivo CSV
        df = pd.read_csv(arquivo_csv)

        # Garantir que a coluna do ticker está presente
        if "Ticker" not in df.columns:
            raise ValueError("O arquivo CSV deve conter uma coluna chamada 'Ticker'.")

        # Criar a lista de tickers
        tickers_b3 = df["Ticker"].dropna().unique().tolist()

        print(f"Lista 'tickers_b3' preparada com sucesso! Total de tickers: {len(tickers_b3)}")
    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")

# Exemplo de uso:
# preparar_lista_tickers_b3("tickers_b3.csv")
# print(tickers_b3)

# Exemplo de uso:
# preparar_lista_tickers_b3("tickers_b3.csv")
# print(tickers_b3)

def main():
    # Configura o título da página
    st.set_page_config(page_title="Importa Cotações", layout="centered")

    # Título da página
    st.title("Importa Cotações")

    # Criar formulário
    with st.form("ticker_form"):
        st.subheader("Código do Ticker")
        ticker = st.text_input("Digite o código do ticker:", max_chars=10)

        # Botão para enviar
        submitted = st.form_submit_button("Importar")

        if submitted:
            #preparar_lista_tickers_b3('../dados/tickers_b3.csv')
            importa_tickers(ticker)


    # Botão para listar arquivos no diretório "cotacoes"
    if st.button("Listar Arquivos do Diretório 'cotacoes'"):
        directory = "cotacoes"
        if os.path.exists(directory):
            files = sorted(os.listdir(directory))
            if files:
                st.write("Arquivos no diretório 'cotacoes':")
                for file in files:
                    st.write(f"- {file}")
            else:
                st.info("O diretório 'cotacoes' está vazio.")
        else:
            st.error("O diretório 'cotacoes' não existe.")



    # atualizar cotacoes
    if st.button("Atualizar Cotações"):
        directory = "cotacoes"

        if os.path.exists(directory):
            files = sorted(os.listdir(directory))

            if files:
                st.write("Atualizando cotações com base nos arquivos no diretório 'cotacoes':")

                for file in files:
                    # Exibir o nome do arquivo
                    st.write(f"- Processando: {file}")

                    # Construir o caminho completo do arquivo
                    file_path = os.path.join(directory, file)

                    if os.path.isfile(file_path):
                        # Extrair o nome do arquivo sem a extensão como ticker
                        ticker = os.path.splitext(file)[0]

                        # Apagar o arquivo
                        os.remove(file_path)
                        st.write(f"  Arquivo '{file}' removido.")

                        # Chamar a função baixa_cotacoes
                        baixa_cotacoes(ticker)
            else:
                st.info("O diretório 'cotacoes' está vazio.")
        else:
            st.error("O diretório 'cotacoes' não existe.")


        # Botão para visualizar as últimas 3 linhas dos arquivos no diretório
    if st.button("Visualizar"):
        directory = "cotacoes"

        if os.path.exists(directory):
            files = sorted(os.listdir(directory))

            if files:
                st.write("Exibindo as últimas 3 linhas de cada arquivo no diretório 'cotacoes':")

                for file in files:
                    # Construir o caminho completo do arquivo
                    file_path = os.path.join(directory, file)

                    if os.path.isfile(file_path):
                        try:
                            # Ler o arquivo com pandas e exibir as últimas 3 linhas
                            df = pd.read_csv(file_path)
                            st.write(f"Arquivo: {file}")
                            st.write(df.head(2))
                            st.write(df.tail(2))
                        except Exception as e:
                            st.error(f"Erro ao ler o arquivo '{file}': {e}")
            else:
                st.info("O diretório 'cotacoes' está vazio.")
        else:
            st.error("O diretório 'cotacoes' não existe.")


if __name__ == "__main__":
    main()
