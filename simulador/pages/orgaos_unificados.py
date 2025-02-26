import locale
import pandas as pd
import streamlit as st
from typing import Optional, List

# Configuração da página deve ser a primeira chamada Streamlit
st.set_page_config(
    page_title="Órgãos Unificados",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tenta configurar o locale pt_BR.UTF-8, se falhar usa o locale padrão do sistema
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')  # Windows fallback
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')  # Usa o locale padrão do sistema

@st.cache_resource(ttl=3600)  # Cache por 1 hora
def connect_datalake() -> None:
    """
    Função mantida por compatibilidade, não é mais utilizada pois os dados vêm de CSV.
    
    Returns:
        None
    """
    return None

@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_orgaos(_conn: None = None) -> Optional[pd.DataFrame]:
    """
    Carrega os órgãos do arquivo CSV.
    
    Args:
        _conn (None): Parâmetro mantido por compatibilidade, não é mais utilizado
        
    Returns:
        Optional[pd.DataFrame]: DataFrame com os dados dos órgãos ou None em caso de erro
    """
    try:
        # Lê o arquivo CSV
        df = pd.read_csv('dados/query1.csv')
        
        # Converte as colunas para o formato correto
        df.columns = df.columns.str.lower()
        df.rename(
                    {
                    "org_super_padr_nome": "super_padr_nome",
                    "org_padr_nome": "padr_nome",
                    "org_padr_sigla": "padr_sigla",
                    "org_padr_codigo": "padr_codigo",
                    "orgao_unificado_id": "unif_id",
                    "orgao_unificado_fonte": "fonte",
                    "orgao_unificado_id_origem": "id_origem",
                    "orgao_unificado_nome": "nome",
                    "orgao_unificado_sigla": "sigla",
                    "orgao_unificado_situacao": "situacao",
                    "orgao_unificado_cod_siorg_origem": "cod_siorg",
                    "org_padr_id": "padr_id",
                    "orgao_unificado_dt_atualizacao": "atualizacao"
                    }, axis=1, inplace=True
                  )
        
        # Converte tipos de dados
        df.padr_codigo = df.padr_codigo.astype("Int64").astype(str)
        df.unif_id = df.unif_id.astype("Int64").astype(str)
        df.id_origem = df.id_origem.astype("Int64").astype(str)
        df.cod_siorg = df.cod_siorg.astype("Int64").astype(str)
        df.padr_id = df.padr_id.astype("Int64").astype(str)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados dos órgãos do arquivo CSV: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache por 1 hora
def lookup_siorg(_conn: None, uos: List[str]) -> Optional[pd.DataFrame]:
    """
    Consulta unidades organizacionais nos arquivos CSV.
    
    Args:
        _conn (None): Parâmetro mantido por compatibilidade, não é mais utilizado
        uos (List[str]): Lista de códigos das unidades organizacionais
        
    Returns:
        Optional[pd.DataFrame]: DataFrame com os dados do SIORG ou None em caso de erro
    """
    try:
        # Lista de arquivos para concatenar
        csv_files = [
            'dados/query2_1.csv',
            'dados/query2_2.csv',
            'dados/query2_3.csv',
            'dados/query2_4.csv'
        ]
        
        # Lê e concatena todos os arquivos
        dfs = []
        for file in csv_files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        # Concatena todos os dataframes
        df = pd.concat(dfs, ignore_index=True)
        
        # Filtra pelos códigos das unidades organizacionais
        df = df[df['CO_UNIDADE_ORGANIZACIONAL'].astype(str).isin(uos)]
        
        # Converte as colunas para lowercase
        df.columns = df.columns.str.lower()
        
        # Renomeia as colunas
        df.rename(
                    {
                    "id_unidade_organizacional": "id",
                    "co_unidade_organizacional": "cod_siorg",
                    "no_unidade_organizacional": "nome",
                    "sg_unidade_organizacional": "sigla",
                    "in_tipo_unidade_organizacional": "tipo",
                    "sn_ativo": "ativo",
                    "dt_criacao": "criacao",
                    "dt_alteracao": "alteracao",
                    "no_categoria": "categoria",
                    "no_natureza_juridica": "natureza",
                    "no_subnatureza_juridica": "subnatureza",
                    }, axis=1, inplace=True
                  )
        
        # Converte tipos de dados
        df.id = df.id.astype("Int64").astype(str)
        df.cod_siorg = df.cod_siorg.astype("Int64").astype(str)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do SIORG dos arquivos CSV: {str(e)}")
        return None

def create_dashboard(_conn: None, df: pd.DataFrame) -> None:
    """
    Cria o painel com visão dos órgãos.
    
    Args:
        _conn (None): Parâmetro mantido por compatibilidade, não é mais utilizado
        df (pd.DataFrame): DataFrame com os dados dos órgãos
    """
    try:
        with st.sidebar:
            st.sidebar.markdown("Filtre por código, sigla ou nome")

            SELECT_ALL = "<Todos>"

            orgao_sup_list = pd.unique(df["org_super_busca"]).tolist()
            orgao_sup_list.append(SELECT_ALL)
            filtro1 = st.selectbox("Órgão Padronizado Superior",
                                   sorted(orgao_sup_list))
            if filtro1 != SELECT_ALL:
                df = df[df["org_super_busca"] == filtro1]

            orgao_list = pd.unique(df["org_padr_busca"]).tolist()
            orgao_list.append(SELECT_ALL)
            filtro2 = st.selectbox("Órgão Padronizado",
                                   sorted(orgao_list))
            if filtro2 != SELECT_ALL:
                df = df[df["org_padr_busca"] == filtro2]

            orgao_unif_list = pd.unique(df["org_unif_busca"]).tolist()
            orgao_unif_list.append(SELECT_ALL)
            filtro3 = st.selectbox("Órgão Unificado",
                                   sorted(orgao_unif_list))
            if filtro3 != SELECT_ALL:
                df = df[df["org_unif_busca"] == filtro3]

        ind1, ind2 = st.columns(2)
        qtde_sup = df["super_padr_nome"].nunique()
        ind1.metric(label="Órgãos Superiores", value=qtde_sup)
        qtde_org = df["padr_nome"].nunique()
        ind2.metric(label="Órgãos/Entidades", value=qtde_org)

        if ((filtro1 != SELECT_ALL)
            or (filtro2 != SELECT_ALL)
            or (filtro3 != SELECT_ALL)):

            st.subheader("Padronizado")
            cols_padr = [
                "padr_id",
                "super_padr_nome",
                "padr_nome",
                "padr_sigla",
                "padr_codigo",
            ]
            st.dataframe(df.groupby(cols_padr, as_index=False)
                         .count()[cols_padr].set_index("padr_id"),
                         use_container_width=True)

            st.subheader("Unificado")
            cols_unif = [
                "unif_id",
                "id_origem",
                "nome",
                "sigla",
                "situacao",
                "cod_siorg",
                "padr_id",
                "atualizacao",
            ]
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["SIORG", "SIAFI", "SIAPE", "SIASG", "Datamart SIORG"]
                )
            with tab1:
                df_siorg = df.loc[df["fonte"] == "SIORG", cols_unif]
                st.dataframe(df_siorg.set_index("unif_id"),
                             use_container_width=True)
            with tab2:
                df_siafi = df.loc[df["fonte"] == "SIAFI", cols_unif]
                st.dataframe(df_siafi.set_index("unif_id"),
                             use_container_width=True)
            with tab3:
                df_siape = df.loc[df["fonte"] == "SIAPE", cols_unif]
                st.dataframe(df_siape.set_index("unif_id"),
                             use_container_width=True)
            with tab4:
                df_siasg = df.loc[df["fonte"] == "SIASG", cols_unif]
                st.dataframe(df_siasg.set_index("unif_id"),
                             use_container_width=True)
            with tab5:
                uo_list = pd.unique(df_siorg["cod_siorg"]).tolist()
                if uo_list:
                    df_dm_siorg = lookup_siorg(None, uo_list)
                    st.dataframe(df_dm_siorg.set_index("id"),
                                 use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao criar dashboard: {str(e)}")

def main():
    """Função principal do aplicativo"""
    st.header("Órgãos Unificados")
    st.markdown("""
                Visualização dos órgãos e entidades da APF direta e indireta,
                unificados e padronizados pelos códigos das diversas fontes.
                """)

    # Carrega os dados do arquivo CSV
    df_org_ent = load_orgaos(None)  # Passa None já que a conexão não é mais necessária
    if df_org_ent is None:
        st.error("Não foi possível carregar os dados dos órgãos.")
        return

    create_dashboard(None, df_org_ent)  # Passa None já que a conexão não é mais necessária

if __name__ == "__main__":
    main()
