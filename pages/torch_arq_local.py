import streamlit as st
import os
import pandas as pd
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import matplotlib.pyplot as plt
import datetime as dt
import numpy as np
import re

# Configuração da página
st.set_page_config(page_title="Stock Price Prediction with GPT", layout="wide")

# Título e descrição da página
st.title("Stock Price Prediction with GPT")
st.write("Previsão de preços históricos de ações usando GPT-2 e dados de arquivos CSV.")

# Obtém os tickers disponíveis na pasta "cotacoes"
cotacoes_dir = "cotacoes"
tickers = [f.replace('.csv', '') for f in os.listdir(cotacoes_dir) if f.endswith('.csv')]

if not tickers:
    st.error("No ticker CSV files found in the 'cotacoes' folder.")
else:
    ticker = st.selectbox("Select Ticker Symbol:", tickers)

    # O usuário informa apenas a data final
    end_date = st.date_input("End Date:", value=dt.date(2023, 6, 8))
    # Define automaticamente o período de 1 ano para predições
    start_date = end_date - dt.timedelta(days=365)
    st.write(f"Data de início automaticamente definida para: {start_date}")

    if start_date >= end_date:
        st.error("A data de início calculada deve ser anterior à data final.")
    else:
        file_path = os.path.join(cotacoes_dir, f"{ticker}.csv")
        # Lê todos os dados disponíveis do CSV
        data_full = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")

        # Função para obter o preço de fechamento para uma data alvo ou o próximo disponível,
        # garantindo que o valor retornado seja um float.
        def get_price_for_date(target_date, data):
            target_date = pd.to_datetime(target_date)
            future_data = data[data.index >= target_date]
            if not future_data.empty:
                return float(future_data.iloc[0]["Close"])
            else:
                return None

        # Guarda os preços para 7, 15 e 30 dias após a data final
        price_7d = get_price_for_date(end_date + dt.timedelta(days=7), data_full)
        price_15d = get_price_for_date(end_date + dt.timedelta(days=15), data_full)
        price_30d = get_price_for_date(end_date + dt.timedelta(days=30), data_full)

        # Exibe os valores encontrados para os preços futuros
        st.write("Preço 7 dias após a data final:", price_7d)
        st.write("Preço 15 dias após a data final:", price_15d)
        st.write("Preço 30 dias após a data final:", price_30d)

        # Filtra os dados históricos com base no intervalo definido (1 ano)
        data = data_full[(data_full.index >= pd.to_datetime(start_date)) &
                         (data_full.index <= pd.to_datetime(end_date))]

        if data.empty:
            st.error("No data found for the given date range.")
        else:
            prices = data["Close"].tolist()
            st.write(f"Data for {ticker}:")
            st.dataframe(data)

            # Preço na data final (último valor do período)
            purchase_price = float(prices[-1])
            st.write("Preço na data final:", purchase_price)

            st.write("Loading GPT-2 model...")
            tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            model = GPT2LMHeadModel.from_pretrained("gpt2")

            # Definindo o número de tokens que serão gerados e ajustando o comprimento máximo de entrada
            max_new_tokens = 20
            max_input_length = tokenizer.model_max_length - max_new_tokens

            # Cria um prompt com os preços históricos e o marcador "Predicted:"
            prompt = "Historical Prices: " + " ".join([str(price) for price in prices]) + "\nPredicted: "
            encoded_prompt = tokenizer.encode(
                prompt,
                truncation=True,
                max_length=max_input_length,
                return_tensors="pt"
            )

            st.write("Generating predictions...")
            attention_mask = torch.ones(encoded_prompt.shape, device=encoded_prompt.device)
            generated = model.generate(
                encoded_prompt,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                num_return_sequences=1
            )

            # Extraindo os tokens gerados após o prompt
            generated_tokens = generated[0]
            predicted_tokens = generated_tokens[encoded_prompt.shape[1]:]
            predicted_text = tokenizer.decode(predicted_tokens, skip_special_tokens=True)
            st.write("Texto gerado para previsão:", predicted_text)

            # Separa os tokens da previsão e converte para números
            predicted_prices_tokens = predicted_text.split()
            predicted_prices = []
            for token in predicted_prices_tokens:
                try:
                    token_clean = re.sub(r"[^\d\.]+", "", token)
                    if token_clean:
                        predicted_prices.append(float(token_clean))
                except ValueError:
                    continue

            if predicted_prices:
                future_dates = data.index[-1] + pd.to_timedelta(np.arange(1, len(predicted_prices) + 1), 'D')
            else:
                st.error("Previsões não geradas corretamente para exibir o resumo e a recomendação.")

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

            # Cálculo do lucro/prejuízo para vendas em 7, 15 e 30 dias após a data final
            st.markdown("## **Análise de Lucro/Prejuízo**")
            if price_7d is not None:
                profit_7d = price_7d - purchase_price
                st.write(f"Lucro/Prejuízo (7 dias após): {profit_7d:.2f}")
            else:
                st.write("Preço 7 dias após não disponível para cálculo.")

            if price_15d is not None:
                profit_15d = price_15d - purchase_price
                st.write(f"Lucro/Prejuízo (15 dias após): {profit_15d:.2f}")
            else:
                st.write("Preço 15 dias após não disponível para cálculo.")

            if price_30d is not None:
                profit_30d = price_30d - purchase_price
                st.write(f"Lucro/Prejuízo (30 dias após): {profit_30d:.2f}")
            else:
                st.write("Preço 30 dias após não disponível para cálculo.")

            # --- Resumo dos Números Gerados pelo Modelo e Recomendações ---
            if predicted_prices:
                last_predicted_price = predicted_prices[-1]
                last_historical_price = purchase_price

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
