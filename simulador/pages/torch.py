import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import matplotlib.pyplot as plt
import datetime as dt

# Configuração da página
st.set_page_config(page_title="Stock Price Prediction with GPT", layout="wide")

# Título da página
st.title("Stock Price Prediction with GPT")
st.write("Previsão de preços históricos de ações usando GPT-2 e dados do Yahoo Finance.")

# Entradas do usuário
ticker = st.text_input("Enter Ticker Symbol:", value="^NSEI")
start_date = st.date_input("Start Date:", value=dt.date(2023, 1, 1))
end_date = st.date_input("End Date:", value=dt.date(2023, 6, 8))

# Verifica se as datas estão corretas
if start_date >= end_date:
    st.error("Start date must be earlier than end date.")
else:
    # Download dos dados
    st.write("Downloading data...")
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.error("No data found for the given ticker and date range.")
    else:
        prices = data["Close"].values.tolist()

        # Exibe os dados
        st.write(f"Data for {ticker}:")
        st.dataframe(data)

        # Carrega o modelo e o tokenizador GPT-2
        st.write("Loading GPT-2 model...")
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        model = GPT2LMHeadModel.from_pretrained("gpt2")

        # Codifica os preços
        encoded_prices = tokenizer.encode(" ".join([str(price) for price in prices]), return_tensors="pt")

        # Configura o modelo para treino
        model.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=5e-5)
        model.resize_token_embeddings(len(tokenizer))

        st.write("Training the model...")
        for _ in range(3):
            model.zero_grad()
            outputs = model(encoded_prices, labels=encoded_prices)
            loss = outputs.loss
            loss.backward()
            optimizer.step()

        # Gera os preços previstos
        st.write("Generating predictions...")
        generated = model.generate(encoded_prices, max_new_tokens=10, temperature=1.0, num_return_sequences=1)
        generated_prices = tokenizer.decode(generated[0], skip_special_tokens=True).split()

        # Conversão e plotagem
        plt.figure(figsize=(12, 6))
        plt.plot(data.index, prices, label="Historical Prices")
        try:
            predicted_prices = [float(price.strip('[]')) for price in generated_prices[len(prices):]]
            future_dates = data.index[-1] + pd.to_timedelta(np.arange(1, len(predicted_prices) + 1), 'D')
            plt.plot(future_dates, predicted_prices, "g^", label="Predicted Prices")
        except ValueError:
            st.error("Error parsing predicted prices.")
            predicted_prices = []

        plt.xlabel("Date")
        plt.ylabel("Stock Price")
        plt.title(f"{ticker} - Historical and Predicted Stock Prices (GPT)")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Exibe o gráfico no Streamlit
        st.pyplot(plt)
