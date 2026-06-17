import streamlit as st
import pandas as pd
import os
import random
from datetime import timedelta

st.set_page_config(page_title="Jogo: Alta ou Baixa?", layout="wide")
st.title("🎲 Jogo: Alta ou Baixa?")
st.markdown("Você será transportado para uma data aleatória do passado. Com base no comportamento da ação nos meses anteriores, adivinhe: o preço subiu ou caiu nos próximos 2 meses?")

PASTA_COTACOES = "cotacoes"

def listar_tickers():
    if not os.path.exists(PASTA_COTACOES):
        return []
    return sorted([f.replace(".csv", "") for f in os.listdir(PASTA_COTACOES) if f.endswith(".csv")])

@st.cache_data
def carregar_dados(ticker: str) -> pd.DataFrame:
    caminho = os.path.join(PASTA_COTACOES, f"{ticker}.csv")
    if not os.path.exists(caminho):
        return pd.DataFrame()
    df = pd.read_csv(caminho)
    if "Date" not in df.columns or "Close" not in df.columns:
        return pd.DataFrame()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df

def inicializar_jogo():
    tickers = listar_tickers()
    if not tickers:
        st.error("Nenhum ticker disponível na pasta 'cotacoes'.")
        st.stop()
    
    # Tenta encontrar um cenário válido aleatoriamente
    for _ in range(50):
        ticker = random.choice(tickers)
        df = carregar_dados(ticker)
        
        if len(df) < 200:
            continue
            
        data_min = df["Date"].min() + timedelta(days=90)  # Pelo menos 3 meses de passado
        data_max = df["Date"].max() - timedelta(days=65)  # Pelo menos 2 meses de futuro
        
        if data_min >= data_max:
            continue
            
        datas_validas = df[(df["Date"] >= data_min) & (df["Date"] <= data_max)]["Date"].tolist()
        if not datas_validas:
            continue
            
        data_escolhida = random.choice(datas_validas)
        
        # Obter contexto (3 meses anteriores)
        df_passado = df[(df["Date"] >= data_escolhida - timedelta(days=90)) & (df["Date"] <= data_escolhida)]
        preco_atual = df_passado.iloc[-1]["Close"]
        
        # Obter futuro (1 e 2 meses)
        df_1_mes = df[df["Date"] >= data_escolhida + timedelta(days=30)]
        df_2_meses = df[df["Date"] >= data_escolhida + timedelta(days=60)]
        
        if df_1_mes.empty or df_2_meses.empty:
            continue
            
        linha_1m = df_1_mes.iloc[0]
        linha_2m = df_2_meses.iloc[0]
        
        st.session_state.game = {
            "ticker": ticker,
            "data_ref": data_escolhida,
            "preco_ref": preco_atual,
            "df_passado": df_passado,
            "data_1m": linha_1m["Date"],
            "preco_1m": linha_1m["Close"],
            "data_2m": linha_2m["Date"],
            "preco_2m": linha_2m["Close"],
            "status": "jogando",
            "escolha": None
        }
        return
        
    st.error("Não foi possível encontrar dados suficientes para gerar uma rodada do jogo.")

# ── Gerenciamento de Estado ──────────────────────────────────────────────────
if "game" not in st.session_state:
    inicializar_jogo()

game = st.session_state.game

# ── Interface Principal ──────────────────────────────────────────────────────
st.subheader(f"Ação Sorteada: **{game['ticker']}**")
st.write(f"📅 **Data de Referência:** {game['data_ref'].strftime('%d/%m/%Y')}")
st.write(f"💵 **Preço na época:** R$ {game['preco_ref']:.2f}")

st.divider()

# Contexto (Notícias simuladas pelo gráfico)
st.markdown("### Contexto Histórico (Últimos 3 meses)")
st.caption("Como a maioria das APIs de notícias gratuitas não fornece um catálogo histórico arbitrário para ações, o jogo fornece este gráfico com a tendência dos 3 meses antecedentes à data sorteada para simular o 'clima' de mercado e ajudar na sua aposta.")

# Renderizar gráfico
df_grafico = game["df_passado"][["Date", "Close"]].set_index("Date")
st.line_chart(df_grafico, y="Close", height=300)

st.divider()

if game["status"] == "jogando":
    st.markdown("### Qual a sua aposta para os próximos 2 meses?")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📈 Apostar na ALTA", use_container_width=True):
            st.session_state.game["escolha"] = "alta"
            st.session_state.game["status"] = "revelado"
            st.rerun()
    with col2:
        if st.button("📉 Apostar na BAIXA", use_container_width=True):
            st.session_state.game["escolha"] = "baixa"
            st.session_state.game["status"] = "revelado"
            st.rerun()

else:
    # ── Fase de Revelação ────────────────────────────────────────────────────
    escolha = game["escolha"]
    preco_ref = game["preco_ref"]
    preco_2m = game["preco_2m"]
    
    # Determinar vitória (baseado na variação de 2 meses)
    houve_alta = preco_2m > preco_ref
    acertou = (escolha == "alta" and houve_alta) or (escolha == "baixa" and not houve_alta)
    
    if acertou:
        st.success("🎉 **PARABÉNS! Você acertou!**")
    else:
        st.error("❌ **QUE PENA! Você errou!**")
        
    st.markdown(f"Sua aposta foi: **{'ALTA 📈' if escolha == 'alta' else 'BAIXA 📉'}**")
    
    # Construir tabela de resultados
    var_1m = ((game["preco_1m"] - preco_ref) / preco_ref) * 100
    var_2m = ((game["preco_2m"] - preco_ref) / preco_ref) * 100
    
    dados_tabela = [
        {"Período": "Data Inicial", "Data": game["data_ref"].strftime("%d/%m/%Y"), "Preço (R$)": f"{preco_ref:.2f}", "Variação (%)": "-"},
        {"Período": "Após 1 Mês", "Data": game["data_1m"].strftime("%d/%m/%Y"), "Preço (R$)": f"{game['preco_1m']:.2f}", "Variação (%)": f"{var_1m:+.2f}%"},
        {"Período": "Após 2 Meses", "Data": game["data_2m"].strftime("%d/%m/%Y"), "Preço (R$)": f"{game['preco_2m']:.2f}", "Variação (%)": f"{var_2m:+.2f}%"}
    ]
    
    st.table(pd.DataFrame(dados_tabela))
    
    if st.button("🔄 Jogar Novamente"):
        del st.session_state.game
        st.rerun()
