import pandas as pd
import os

def verifica_data_maxima(caminho_arquivo):
    # Verifica se o arquivo existe
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"O arquivo {caminho_arquivo} não foi encontrado.")

    # Lê o arquivo CSV
    df = pd.read_csv(caminho_arquivo)

    # Verifica se a coluna 'Date' existe no DataFrame
    if 'Date' not in df.columns:
        raise ValueError("A coluna 'Date' não está presente no arquivo CSV.")

    # Converte a coluna 'Date' para datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Encontra o valor máximo da coluna 'Date'
    data_maxima = df['Date'].max()

    return data_maxima

if __name__ == "__main__":
    caminho_arquivo = os.path.join('dados', 'cotacoes.csv')
    try:
        data_maxima = verifica_data_maxima(caminho_arquivo)
        print(f"O valor máximo da coluna 'Date' é: {data_maxima}")
    except (FileNotFoundError, ValueError) as e:
        print(e)
verifica_data_maxima(/dados/)