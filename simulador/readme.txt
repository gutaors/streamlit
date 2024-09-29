VENV
STREAMLIT
python3 -m venv streamlit-env
source streamlit-env/bin/activate
pip install -r requirements.txt

pip install streamlit
streamlit run app.py
http://127.0.0.1:8501/
deactivate

DOCKER
docker build -t <imagename and tagname> -f Dockerfile
docker build -t simulador -f Dockerfile