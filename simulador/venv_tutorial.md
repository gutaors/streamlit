source venv/bin/activate
#   pip install -r requirements.txt
streamlit run app.py
deactivate






Crie o ambiente virtual utilizando a biblioteca [`venv`](https://docs.python.org/3/library/venv.html) do Python. Onde, `crawler-venv` será o nome do ambiente virtual.

    ```bash
    python3 -m venv crawler-env
    ```

3. Ative o ambiente virtual, caso ele ainda não tenha sido ativado.

    * *No linux:*

    ```bash
    source crawler-env/bin/activate
    ou
    source venv/bin/activate
    ```


4. Instale as bibliotecas que iremos utilizar nesse projeto (com o ambiente virtual ativado). Essas bibliotecas e as suas respectivas versões estão definidas no arquivo `requirements.txt`. No Python, para instalar bibliotecas a partir desse arquivo, executamos o comando:

    ```bash
    pip install -r requirements.txt
    ```

**PRONTO!** :tada: :confetti_ball: Conseguimos criar o nosso ambiente virtual e instalar as bibliotecas que vamos utilizar nesse projeto!

> Para desativar o ambiente virtual, execute: `deactivate`.

## Executando o crawler

Depois de ter criando o ambiente virtual e instalando as bibliotecas, ative o ambiente virtual (caso ele não esteja ativo):

* *No linux:*

```bash
source crawler-env/bin/activate
source venv/bin/activate
```


E execute o crawler que foi desenvolvido:

```bash
python3 app.py
streamlit run app.py

```
