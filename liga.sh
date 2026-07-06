#!/bin/bash
cd "$(dirname "$0")"

echo "================================="
echo "Iniciando ambiente Streamlit"
echo "================================="

if [ ! -d "streamlit-env" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv streamlit-env
fi

source streamlit-env/bin/activate

echo "Atualizando pip..."
pip install --upgrade pip

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Atualizando yfinance..."
pip install yfinance --upgrade --no-cache-dir

echo "Iniciando Streamlit..."
python3 -m streamlit run app.py