



python3 -m venv streamlit-env
source streamlit-env/bin/activate
pip install -r requirements.txt
pip install yfinance --upgrade --no-cache-dir
pip install streamlit
streamlit run app.py
http://127.0.0.1:8501/
ou
http://localhost:8501
deactivate