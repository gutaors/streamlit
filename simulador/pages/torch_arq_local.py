import streamlit as st
import os
import pandas as pd
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import matplotlib.pyplot as plt
import datetime as dt
import numpy as np

# Configuração da página
st.set_page_config(page_title="Stock Price Prediction with GPT", layout="wide")

# Título da página
st.title("Stock Price Prediction with GPT")
st.write("Previsão de preços históricos de ações usando GPT-2 e dados de arquivos CSV.")

# Obtém os tickers disponíveis na pasta "cotacoes"
cotacoes_dir = "cotacoes"
tickers = [f.replace('.csv', '') for f in os.listdir(cotacoes_dir) if f.endswith('.csv')]

if not tickers:
    st.error("No ticker CSV files found in the 'cotacoes' folder.")
else:
    ticker = st.selectbox("Select Ticker Symbol:", tickers)
    start_date = st.date_input("Start Date:", value=dt.date(2023, 1, 1))
    end_date = st.date_input("End Date:", value=dt.date(2023, 6, 8))

    if start_date >= end_date:
        st.error("Start date must be earlier than end date.")
    else:
        file_path = os.path.join(cotacoes_dir, f"{ticker}.csv")
        data = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
        data = data[(data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))]

        if data.empty:
            st.error("No data found for the given date range.")
        else:
            prices = data["Close"].values.tolist()
            st.write(f"Data for {ticker}:")
            st.dataframe(data)

            st.write("Loading GPT-2 model...")
            tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            model = GPT2LMHeadModel.from_pretrained("gpt2")

            # Codifica os preços convertendo-os em uma string. Utiliza truncation para não exceder o limite de tokens.
            prices_str = " ".join([str(price) for price in prices])
            encoded_prices = tokenizer.encode(
                prices_str,
                truncation=True,
                max_length=tokenizer.model_max_length,
                return_tensors="pt"
            )

            st.write("Generating predictions...")
            attention_mask = torch.ones(encoded_prices.shape, device=encoded_prices.device)
            generated = model.generate(
                encoded_prices,
                attention_mask=attention_mask,
                max_new_tokens=10,
                temperature=1.0,
                num_return_sequences=1
            )

            generated_text = tokenizer.decode(generated[0], skip_special_tokens=True).split()
            # Assumindo que a sequência gerada contenha os tokens originais seguidos dos novos tokens,
            # extraímos os tokens referentes às previsões.
            predicted_prices_tokens = generated_text[len(encoded_prices[0]):]
            try:
                predicted_prices = [float(token.strip('[]')) for token in predicted_prices_tokens]
                future_dates = data.index[-1] + pd.to_timedelta(np.arange(1, len(predicted_prices) + 1), 'D')
            except ValueError:
                st.error("Error parsing predicted prices.")
                predicted_prices = []

            # Plotagem do gráfico com os preços históricos e as previsões
            plt.figure(figsize=(12, 6))
            plt.plot(data.index, prices, label="Historical Prices")
            if predicted_prices:
                plt.plot(future_dates, predicted_prices, "g^", label="Predicted Prices")
            plt.xlabel("Date")
            plt.ylabel("Stock Price")
            plt.title(f"{ticker} - Historical and Predicted Stock Prices (GPT)")
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(plt)

            # --- Resumo dos Números Gerados pelo Modelo e Recomendações ---
            if predicted_prices:
                last_predicted_price = predicted_prices[-1]
                last_historical_price = float(prices[-1])

                st.markdown("## **Resumo dos Números Gerados pelo Modelo**")
                st.write("**Último Valor Histórico:**", f"{last_historical_price:.2f}")
                st.write("**Último Valor Previsto:**", f"{last_predicted_price:.2f}")

                if last_predicted_price > last_historical_price:
                    rec = "<span style='color: green; font-weight: bold;'>Recomendação: Tendência Altista - Recomenda-se manter ou aumentar posições de compra.</span>"
                else:
                    rec = "<span style='color: red; font-weight: bold;'>Recomendação: Tendência Baixista - Recomenda-se cautela ou redução de posições.</span>"

                st.markdown(rec, unsafe_allow_html=True)
            else:
                st.error("Previsões não geradas corretamente para exibir o resumo e a recomendação.")
