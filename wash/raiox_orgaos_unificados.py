"""
Painel em Streamlit para visualização dos órgãos/entidades unificados e
padronizados, superiores ou não, permitindo filtragens.

Para desenvolver:
    pip install streamlit

Para conectar, editar/criar o arquivo ".streamlit/secrets.toml" com os dados
entre <> preenchidos adequadamente:

[datalake]
dialect = "mssql"
username = "userSegesETL"
password = "gwxu8QhN"
host = "10.209.42.31"
port = "1533"
database = "PGG_DW.DW_APF_GERAL"

Para executar:
    streamlit run orgaos_unificados.py
"""

import locale
import pandas as pd
import sqlalchemy as sa
import streamlit as st


# locale.setlocale(locale.LC_ALL, 'pt_BR')
# locale.setlocale(locale.LC_ALL, 'pt_BR.utf-8')


@st.cache_resource
def connect_datalake():
    """Conecta no Datalake"""
    dialect = st.secrets["datalake"]["dialect"]
    username = st.secrets["datalake"]["username"]
    password = st.secrets["datalake"]["password"]
    host = st.secrets["datalake"]["host"]
    port = st.secrets["datalake"]["port"]
    database = st.secrets["datalake"]["database"]
    driver = "pyodbc"
    urldb = (
        f"{dialect}+{driver}://{username}:{password}@{host}:{port}/"
        f"{database}?driver=ODBC+Driver+17+for+SQL+Server"
    )
    engine = sa.create_engine(urldb)
    return engine


@st.cache_data
def load_orgaos(_engine) -> pd.DataFrame:
    """Carrega os órgãos para dataframe"""

    sql = """
        select  concat(vop.ORG_SUPER_PADR_NOME,
                    ' [', vop.ORG_SUPER_PADR_SIGLA, ']' ,
                    ' [', vop.ORG_SUPER_PADR_CODIGO, ']') as ORG_SUPER_BUSCA,
                vop.ORG_SUPER_PADR_NOME,
                concat(vop.ORG_PADR_NOME,
                            ' [', vop.ORG_PADR_SIGLA, ']' ,
                            ' [', vop.ORG_PADR_CODIGO, ']') as ORG_PADR_BUSCA,
                vop.ORG_PADR_NOME,
                vop.ORG_PADR_SIGLA,
                vop.ORG_PADR_CODIGO,
                concat(ou.ORGAO_UNIFICADO_NOME,
                    ' [', ou.ORGAO_UNIFICADO_SIGLA, ']' ,
                    ' [', ou.ORGAO_UNIFICADO_ID_ORIGEM, ']',
                    ' [', ou.ORGAO_UNIFICADO_FONTE, ']') as ORG_UNIF_BUSCA,
                vop.ORGAO_UNIFICADO_ID,
                ou.ORGAO_UNIFICADO_FONTE,
                ou.ORGAO_UNIFICADO_ID_ORIGEM,
                ou.ORGAO_UNIFICADO_NOME,
                ou.ORGAO_UNIFICADO_SIGLA,
                ou.ORGAO_UNIFICADO_SITUACAO,
                ou.ORGAO_UNIFICADO_COD_SIORG_ORIGEM,
                ou.ORG_PADR_ID,
                ou.ORGAO_UNIFICADO_DT_ATUALIZACAO
        from PGG_DW.DW_APF_GERAL.VW_DM_ORG_PADRONIZADO vop
        inner join PGG_DW.DW_APF_GERAL.DM_ORGAO_UNIFICADO ou
            on ou.ORGAO_UNIFICADO_ID = vop.ORGAO_UNIFICADO_ID
        order by 1, 2
    """
    df = pd.read_sql(sql=sa.text(sql), con=_engine.connect())
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
            "orgao_unificado_dt_atualizacao": "atualizacao",
        },
        axis=1,
        inplace=True,
    )
    df.padr_codigo = df.padr_codigo.astype("Int64").astype(str)
    df.unif_id = df.unif_id.astype("Int64").astype(str)
    df.id_origem = df.id_origem.astype("Int64").astype(str)
    df.cod_siorg = df.cod_siorg.astype("Int64").astype(str)
    df.padr_id = df.padr_id.astype("Int64").astype(str)
    return df


@st.cache_data
def lookup_siorg(_engine, uos: list) -> pd.DataFrame:
    """Consulta uma unidade organizacional no datamart Siorg"""

    sql = f"""
        select  ID_UNIDADE_ORGANIZACIONAL,
                CO_UNIDADE_ORGANIZACIONAL,
                NO_UNIDADE_ORGANIZACIONAL,
                SG_UNIDADE_ORGANIZACIONAL,
                IN_TIPO_UNIDADE_ORGANIZACIONAL,
                SN_ATIVO,
                DT_CRIACAO,
                DT_ALTERACAO,
                NO_CATEGORIA,
                NO_NATUREZA_JURIDICA,
                NO_SUBNATUREZA_JURIDICA
        from PGG_DW.DM_SIORG.DM_UNIDADE_SIORG
        where ID_TEMPO = (select max(ID_TEMPO) from PGG_DW.DM_SIORG.DM_CARGO_SIORG)
            and CO_UNIDADE_ORGANIZACIONAL in ({','.join(uos)})
    """
    df = pd.read_sql(sql=sa.text(sql), con=_engine.connect())
    df.columns = df.columns.str.lower()
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
        },
        axis=1,
        inplace=True,
    )
    df.id = df.id.astype("Int64").astype(str)
    df.cod_siorg = df.cod_siorg.astype("Int64").astype(str)
    return df


def create_dashboard(_engine, df: pd.DataFrame):
    """Cria o painel com visão dos órgãos"""

    with st.sidebar:
        st.sidebar.markdown("Filtre por código, sigla ou nome")

        SELECT_ALL = "<Todos>"

        orgao_sup_list = pd.unique(df["org_super_busca"]).tolist()
        orgao_sup_list.append(SELECT_ALL)
        filtro1 = st.selectbox("Órgão Padronizado Superior", sorted(orgao_sup_list))
        if filtro1 != SELECT_ALL:
            df = df[df["org_super_busca"] == filtro1]

        orgao_list = pd.unique(df["org_padr_busca"]).tolist()
        orgao_list.append(SELECT_ALL)
        filtro2 = st.selectbox("Órgão Padronizado", sorted(orgao_list))
        if filtro2 != SELECT_ALL:
            df = df[df["org_padr_busca"] == filtro2]

        orgao_unif_list = pd.unique(df["org_unif_busca"]).tolist()
        orgao_unif_list.append(SELECT_ALL)
        filtro3 = st.selectbox("Órgão Unificado", sorted(orgao_unif_list))
        if filtro3 != SELECT_ALL:
            df = df[df["org_unif_busca"] == filtro3]

    ind1, ind2 = st.columns(2)
    qtde_sup = df["super_padr_nome"].nunique()
    ind1.metric(label="Órgãos Superiores", value=qtde_sup)
    qtde_org = df["padr_nome"].nunique()
    ind2.metric(label="Órgãos/Entidades", value=qtde_org)

    if (filtro1 != SELECT_ALL) or (filtro2 != SELECT_ALL) or (filtro3 != SELECT_ALL):
        st.subheader("Padronizado")
        cols_padr = [
            "padr_id",
            "super_padr_nome",
            "padr_nome",
            "padr_sigla",
            "padr_codigo",
        ]
        st.dataframe(
            df.groupby(cols_padr, as_index=False)
            .count()[cols_padr]
            .set_index("padr_id"),
            use_container_width=True,
        )

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
            st.dataframe(df_siorg.set_index("unif_id"), use_container_width=True)
        with tab2:
            df_siafi = df.loc[df["fonte"] == "SIAFI", cols_unif]
            st.dataframe(df_siafi.set_index("unif_id"), use_container_width=True)
        with tab3:
            df_siape = df.loc[df["fonte"] == "SIAPE", cols_unif]
            st.dataframe(df_siape.set_index("unif_id"), use_container_width=True)
        with tab4:
            df_siasg = df.loc[df["fonte"] == "SIASG", cols_unif]
            st.dataframe(df_siasg.set_index("unif_id"), use_container_width=True)
        with tab5:
            uo_list = pd.unique(df_siorg["cod_siorg"]).tolist()
            if uo_list:
                df_dm_siorg = lookup_siorg(_engine, uo_list)
                st.dataframe(df_dm_siorg.set_index("id"), use_container_width=True)


st.set_page_config(
    page_title="Órgãos Unificados",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.header("Órgãos Unificados")
st.markdown(
    """
            Visualização dos órgãos e entidades da APF direta e indireta,
            unificados e padronizados pelos códigos das diversas fontes.
            """
)

sa_engine = connect_datalake()
df_org_ent = load_orgaos(sa_engine)
create_dashboard(sa_engine, df_org_ent)
