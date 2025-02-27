import streamlit as st
import pandas as pd
from pyvis.network import Network
from sentence_transformers import SentenceTransformer, util
import torch

# Caminho do novo arquivo
file_dw_apf_geral = 'ORGAOS_DW_APF_GERAL.csv'
file_dwtg_siafi = 'ORGAOS_DWTG_SIAFI.csv'

# Função para carregar e mostrar os dados
def load_data():
    # Carregar o arquivo
    df_orgaos = pd.read_csv(file_dw_apf_geral)
    df_orgaos_siafi = pd.read_csv(file_dwtg_siafi)
    return df_orgaos, df_orgaos_siafi

# criar subdataframes
# de orgaos superiores : unique org_padr_id, org_padr_sigla e org_padr_nome
# de orgaos subordinados : unique org_id, org_sigla e org_nome
def subdataframes(df_orgaos):
    # criar subdataframes
    # de orgaos superiores : unique org_padr_id, org_padr_sigla e org_padr_nome
    df_orgaos_superiores = df_orgaos[['ORG_PADR_ID', 'ORG_PADR_SIGLA', 'ORG_PADR_NOME']].drop_duplicates()
    # de orgaos subordinados : unique org_id, org_sigla e org_nome
    df_orgaos_subordinados = df_orgaos[['ORG_PADR_ID', 'ORG_PADR_ID.1', 'ORG_PADR_SIGLA.1', 'ORG_PADR_NOME.1', 'ORGAO_UNIFICADO_ID_ORIGEM', 'ORGAO_UNIFICADO_NOME', 'ORGAO_UNIFICADO_FONTE']].drop_duplicates()
    return df_orgaos_superiores, df_orgaos_subordinados


# função para criar o menu de filtro de orgaos a partir do org_padr_sigla do dataframe
def menu(df_orgaos_superiores):
    orgao = st.sidebar.selectbox('Selecione o Órgão:', df_orgaos_superiores[['ORG_PADR_ID', 'ORG_PADR_SIGLA', 'ORG_PADR_NOME']].apply(lambda x: f"{x['ORG_PADR_ID']} - {x['ORG_PADR_SIGLA']} - {x['ORG_PADR_NOME']}", axis=1))
    # orgao_id = orgao.split(' - ')[0]
    return orgao


def plot_graph(df_superiores, df_subordinados):
    net = Network(notebook=True, directed=True)

    # Adicionar nós de órgãos superiores
    for _, row in df_superiores.iterrows():
        net.add_node(row['ORG_PADR_ID'], label=row['ORG_PADR_SIGLA'], title=row['ORG_PADR_NOME'], color='blue')

    # Adicionar nós de órgãos subordinados e arestas
    for _, row in df_subordinados.iterrows():
        net.add_node(row['ORG_PADR_ID.1'], label=row['ORG_PADR_SIGLA.1'], title=row['ORG_PADR_NOME.1'], color='green', fonte=row['ORGAO_UNIFICADO_FONTE'])
        net.add_edge(row['ORG_PADR_ID'], row['ORG_PADR_ID.1'], title=f"Fonte: {row['ORGAO_UNIFICADO_FONTE']}")

    net.show_buttons(filter_=['physics'])
    net.show("graph.html")
    st.components.v1.html(open("graph.html", 'r', encoding='utf-8').read(), height=600)

def treinar_modelo():
    # Carregar o modelo pré-treinado
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    # Forçar o uso da CPU
    model = model.to('cpu')

    return model

# Função para buscar dados no df_orgaos_siafi usando similaridade semântica
def buscar_semantica(df_orgaos_siafi, texto_busca, top_n=5, model=None):

    # Verifique qual coluna usar para a busca (substitua 'NOME_ORGAO' pelo nome correto)
    coluna_busca = 'NO_UO'  # Substitua pelo nome da coluna correta

    # Transformar o texto de busca em embedding
    embedding_busca = model.encode(texto_busca, convert_to_tensor=True)

    # Transformar todos os textos do DataFrame em embeddings
    df_orgaos_siafi['embedding'] = df_orgaos_siafi[coluna_busca].apply(
        lambda x: model.encode(str(x), convert_to_tensor=True).cpu().numpy()  # Converter para NumPy array
    )

    # Calcular a similaridade entre o texto de busca e os textos do DataFrame
    df_orgaos_siafi['similaridade'] = df_orgaos_siafi['embedding'].apply(
        lambda x: util.pytorch_cos_sim(embedding_busca, torch.tensor(x)).item()  # Usando CPU
    )

    # Ordenar o DataFrame pela similaridade
    df_ordenado = df_orgaos_siafi.sort_values(by='similaridade', ascending=False)

    # Retornar os top_n resultados
    return df_ordenado.head(top_n)


# Função principal do Streamlit
def main():
    st.title("Visualização dos Dados dos Órgãos")
    
    # Treinar o modelo
    model = treinar_modelo()
    
    # Carregar os dados
    df_orgaos, df_orgaos_siafi = load_data()
    # Subdataframes
    df_orgaos_superiores, df_orgaos_subordinados = subdataframes(df_orgaos)
    # KPIs totais de órgãos superiores e subordinados distintos
    st.subheader("Informações Gerais")
    qtd_orgaos_superiores = df_orgaos_superiores['ORG_PADR_ID'].nunique()
    qtd_orgaos_subordinados = df_orgaos_subordinados['ORG_PADR_ID.1'].nunique()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Quantidade de Órgãos Superiores", value=qtd_orgaos_superiores)
    with col2:
        st.metric(label="Quantidade de Órgãos Subordinados", value=qtd_orgaos_subordinados)
    
    # Menu de filtro
    orgao = menu(df_orgaos_superiores)
    st.write(f"Órgão selecionado: {orgao}")

    # Filtrar os dados pelo órgão selecionado
    orgao_id = orgao.split(' - ')[0]
    df_orgaos_superiores_filtrado = df_orgaos_superiores[df_orgaos_superiores['ORG_PADR_ID'] == int(orgao_id)]
    df_orgaos_subordinados_filtrado = df_orgaos_subordinados[df_orgaos_subordinados['ORG_PADR_ID'] == int(orgao_id)]

    # kpis
    # quantidade distinto de orgaos subordinados
    qtd_orgaos_subordinados = df_orgaos_subordinados_filtrado['ORG_PADR_ID.1'].nunique()    
    st.write(f"Quantidade de Órgãos Subordinados: {qtd_orgaos_subordinados}")
    # Lista única dos órgãos subordinados
    orgaos_subordinados_unicos = df_orgaos_subordinados_filtrado[['ORG_PADR_ID.1', 'ORG_PADR_SIGLA.1', 'ORG_PADR_NOME.1']].drop_duplicates()
    # orgaos_subordinados_lista = orgaos_subordinados_unicos.apply(lambda x: f"[{x['ORG_PADR_ID.1']}] {x['ORG_PADR_SIGLA.1']} - {x['ORG_PADR_NOME.1']}", axis=1).tolist()

    # criar menu lateral para escolher o orgao subordinado único, permitindo mais de uma seleção
    orgao_subordinado = st.sidebar.multiselect(
        'Selecione o Órgão Subordinado:',
        orgaos_subordinados_unicos[['ORG_PADR_ID.1', 'ORG_PADR_SIGLA.1', 'ORG_PADR_NOME.1']].apply(lambda x: f"{x['ORG_PADR_ID.1']} - {x['ORG_PADR_SIGLA.1']} - {x['ORG_PADR_NOME.1']}", axis=1),
        default=orgaos_subordinados_unicos[['ORG_PADR_ID.1', 'ORG_PADR_SIGLA.1', 'ORG_PADR_NOME.1']].apply(lambda x: f"{x['ORG_PADR_ID.1']} - {x['ORG_PADR_SIGLA.1']} - {x['ORG_PADR_NOME.1']}", axis=1).tolist()
    )

    # sugestão de comando insert into para inserir os orgaos subordinados selecionados na tabela DM_ORGAO_UNIFICADO_NOVO


    # Filtrar os dados pelos órgãos subordinados selecionados
    orgao_subordinado_ids = [int(org.split(' - ')[0]) for org in orgao_subordinado]
    df_orgaos_subordinados_filtrado = df_orgaos_subordinados_filtrado[df_orgaos_subordinados_filtrado['ORG_PADR_ID.1'].isin(orgao_subordinado_ids)]

   # criar 3 colunas ok siape, ok siape e OK SIAFI, OK SIORG e OK SIAPE na tabela de orgaos subordinados filtrados com valor original de negação
    orgaos_subordinados_unicos['OK_SIAPE'] = False
    orgaos_subordinados_unicos['OK_SIAFI'] = False
    orgaos_subordinados_unicos['OK_SIORG'] = False

    # ver se a sigla do orgao subordinado está na tabela de orgaos subordinados filtrados e se sim, setar o valor da coluna correspondente para True
    for index, row in orgaos_subordinados_unicos.iterrows():
        if row['ORG_PADR_SIGLA.1'] in df_orgaos_subordinados_filtrado[df_orgaos_subordinados_filtrado['ORGAO_UNIFICADO_FONTE'] == 'SIAPE']['ORG_PADR_SIGLA.1'].values:
            orgaos_subordinados_unicos.loc[index, 'OK_SIAPE'] = True
        if row['ORG_PADR_SIGLA.1'] in df_orgaos_subordinados_filtrado[df_orgaos_subordinados_filtrado['ORGAO_UNIFICADO_FONTE'] == 'SIAFI']['ORG_PADR_SIGLA.1'].values:
            orgaos_subordinados_unicos.loc[index, 'OK_SIAFI'] = True
        if row['ORG_PADR_SIGLA.1'] in df_orgaos_subordinados_filtrado[df_orgaos_subordinados_filtrado['ORGAO_UNIFICADO_FONTE'] == 'SIORG']['ORG_PADR_SIGLA.1'].values:
            orgaos_subordinados_unicos.loc[index, 'OK_SIORG'] = True
    
    # somente se estiver algum falso, mostrar a sugestão de comando insert into
    if not orgaos_subordinados_unicos['OK_SIAPE'].all() or not orgaos_subordinados_unicos['OK_SIAFI'].all() or not orgaos_subordinados_unicos['OK_SIORG'].all():
        inserts_siape = ',\n'.join(orgaos_subordinados_unicos[~orgaos_subordinados_unicos['OK_SIAPE']].apply(lambda x: f"(<MAX ORGAO_UNIDICADO_ID + 1>, <CODIGO_ORGAO_SIAPE>, '{x['ORG_PADR_NOME.1']}', '{x['ORG_PADR_SIGLA.1']}', 'ATIVO', 'SIAPE', 0, 0, {x['ORG_PADR_ID.1']}, GETDATE(), GETDATE())", axis=1).tolist())
        inserts_siafi = ',\n'.join(orgaos_subordinados_unicos[~orgaos_subordinados_unicos['OK_SIAFI']].apply(lambda x: f"(<MAX ORGAO_UNIDICADO_ID + 1>, <COGIDO_ORGAO_SIAFI>, '{x['ORG_PADR_NOME.1']}', '{x['ORG_PADR_SIGLA.1']}', 'ATIVO', 'SIAFI', 0, 0, {x['ORG_PADR_ID.1']}, GETDATE(), GETDATE())", axis=1).tolist())
        inserts_siorg = ',\n'.join(orgaos_subordinados_unicos[~orgaos_subordinados_unicos['OK_SIORG']].apply(lambda x: f"(<MAX ORGAO_UNIDICADO_ID + 1>, <CODIGO_ORGAO_SIORG>, '{x['ORG_PADR_NOME.1']}', '{x['ORG_PADR_SIGLA.1']}', 'ATIVO', 'SIORG', 0, 0, {x['ORG_PADR_ID.1']}, GETDATE(), GETDATE())", axis=1).tolist())
        
        st.write("Sugestão de Inserts para correção:")
        st.code(f"""
        INSERT INTO PGG_DW.DW_APF_GERAL.DM_ORGAO_UNIFICADO_NOVO
                    ( ORGAO_UNIFICADO_ID
                    , ORGAO_UNIFICADO_ID_ORIGEM
                    , ORGAO_UNIFICADO_NOME
                    , ORGAO_UNIFICADO_SIGLA
                    , ORGAO_UNIFICADO_SITUACAO
                    , ORGAO_UNIFICADO_FONTE
                    , ORGAO_UNIFICADO_COD_SIORG_ORIGEM
                    , ORGAO_PADRONIZADO_ID
                    , ORG_PADR_ID
                    , ORGAO_UNIFICADO_DT_ATUALIZACAO
                    , ORGAO_UNIFICADO_DT_INCLUSAO)
        VALUES
        {inserts_siape},
        {inserts_siafi},
        {inserts_siorg};
        """)

        # Busca semântica no df_orgaos_siafi para órgãos subordinados não OK SIAFI
        st.subheader("Busca Semântica no df_orgaos_siafi para Órgãos Subordinados não OK SIAFI")
        orgaos_nao_ok_siafi = orgaos_subordinados_unicos[~orgaos_subordinados_unicos['OK_SIAFI']]
        if not orgaos_nao_ok_siafi.empty:
            for index, row in orgaos_nao_ok_siafi.iterrows():
                st.write(f"Buscando por: {row['ORG_PADR_NOME.1']}")
                resultados = buscar_semantica(df_orgaos_siafi, row['ORG_PADR_NOME.1'] + ' ' + row['ORG_PADR_SIGLA.1'], top_n=3, model=model)
                st.write("Resultados da Busca Semântica:")
                st.dataframe(resultados)

    # Mostrar os dados
    st.subheader("Lista de Órgãos Subordinados Únicos")
    st.dataframe(orgaos_subordinados_unicos)
    
    # Escrever tabelas
    st.write("Dados do arquivo de Órgãos Superiores:")
    st.dataframe(df_orgaos_superiores_filtrado)
    st.write("Dados do arquivo de Órgãos Subordinados:")
    fontes = df_orgaos_subordinados_filtrado['ORGAO_UNIFICADO_FONTE'].unique()
    for fonte in fontes:
        st.write(f"Fonte: {fonte}")
        df_filtrado_por_fonte = df_orgaos_subordinados_filtrado[df_orgaos_subordinados_filtrado['ORGAO_UNIFICADO_FONTE'] == fonte]
        st.dataframe(df_filtrado_por_fonte)

    # Plotar o grafo
    plot_graph(df_orgaos_superiores_filtrado, df_orgaos_subordinados_filtrado)


if __name__ == '__main__':
    main()
