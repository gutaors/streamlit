VENV
STREAMLIT
python3 -m venv streamlit-env
source streamlit-env/bin/activate
pip install -r requirements.txt

DOCKER
docker build -t <imagename and tagname> -f Dockerfile
docker build -t simulador -f Dockerfile