from datetime import datetime
import pandas_datareader.data as web
import json
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os
data_atual = datetime.now().strftime('%Y-%m-%d')
df_csv = pd.read_csv('dados/cotacoes.csv', sep=',')
data_do_arquivo = max(df_csv['Date'])
if data_do_arquivo == data_atual:
    print("Arquivo já está atualizado para a data atual.")
    #sys.exit(0) # Interrompe o script com sucesso
else:
    print("nao atualizado",data_do_arquivo)
    from carga import carregar_dados