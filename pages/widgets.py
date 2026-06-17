# widgets.py
import streamlit as st

def main():
    # 1. Botão
    st.header("1. Botão")
    if st.button('Clique aqui'):
        st.write('Você clicou no botão!')

    # 2. Checkbox
    st.header("2. Checkbox")
    if st.checkbox('Marque se você gosta de Python'):
        st.write('Você marcou a caixa!')

    # 3. Radio (Botões de rádio)
    st.header("3. Radio")
    option = st.radio('Escolha uma opção', ['Opção A', 'Opção B', 'Opção C'])
    st.write('Você escolheu:', option)

    # 4. Selectbox (Caixa suspensa)
    st.header("4. Selectbox")
    option = st.selectbox('Escolha uma opção', ['Opção A', 'Opção B', 'Opção C'])
    st.write('Você escolheu:', option)

    # 5. Multiselect (Seleção múltipla)
    st.header("5. Multiselect")
    options = st.multiselect('Escolha algumas opções', ['Opção A', 'Opção B', 'Opção C'])
    st.write('Você escolheu:', options)

    # 6. Slider
    st.header("6. Slider")
    value = st.slider('Escolha um valor', 0, 100, 50)
    st.write('Você escolheu o valor:', value)

    # 7. Text Input (Entrada de texto de uma linha)
    st.header("7. Text Input")
    name = st.text_input('Qual é o seu nome?')
    st.write('Olá', name)

    # 8. Text Area (Entrada de texto com várias linhas)
    st.header("8. Text Area")
    message = st.text_area('Deixe sua mensagem:')
    st.write('Você escreveu:', message)

    # 9. Number Input (Entrada de número)
    st.header("9. Number Input")
    age = st.number_input('Qual a sua idade?', min_value=0, max_value=120, value=30)
    st.write('Você tem', age, 'anos')

    # 10. Date Input (Seleção de data)
    st.header("10. Date Input")
    date = st.date_input('Escolha uma data')
    st.write('A data escolhida é', date)

    # 11. Time Input (Seleção de hora)
    st.header("11. Time Input")
    time = st.time_input('Escolha um horário', value="08:45")
    st.write('O horário escolhido é', time)

    # 12. File Uploader (Upload de arquivo)
    st.header("12. File Uploader")
    uploaded_file = st.file_uploader('Escolha um arquivo')
    if uploaded_file is not None:
        st.write('Arquivo carregado com sucesso!')

    # 13. Color Picker (Seleção de cor)
    st.header("13. Color Picker")
    color = st.color_picker('Escolha uma cor', '#00f900')
    st.write('Você escolheu a cor:', color)

    # 14. Image (Exibição de imagem)
    st.header("14. Image")
    st.image('https://www.streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.svg', caption="Logo do Streamlit", use_column_width=True)

    # 15. Video (Exibição de vídeo)
    st.header("15. Video")
    st.video('https://www.streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.svg')

    # 16. Markdown (Renderiza texto Markdown)
    st.header("16. Markdown")
    st.markdown('## Título em Markdown')
    st.markdown('Aqui está um **texto em negrito** e *texto em itálico*.')

if __name__ == "__main__":
    main()
