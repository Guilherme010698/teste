import requests
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import folium_static


traducao = {
    'ACIDENT_MINOR': 'Acidente Menor',
    'ACCIDENT_MAJOR': 'Acidente Maior',
    'NO_SUBTYPE': 'Sem Subtipo',
    'JAM_MODERATE_TRAFFIC': 'Tráfego Moderado',
    'JAM_HEAVY_TRAFFIC': 'Tráfego Intenso',
    'JAM_STAND_STILL_TRAFFIC': 'Tráfego Parado',
    'JAM_LIGHT_TRAFFIC': 'Tráfego Leve',
    'HAZARD_ON_ROAD': 'Perigo na Estrada',
    'HAZARD_ON_SHOULDER': 'Perigo no Acostamento',
    'HAZARD_WEATHER': 'Condições Climáticas Adversas',
    'HAZARD_ON_ROAD_OBJECT': 'Objeto na Estrada',
    'HAZARD_ON_ROAD_POT_HOLE': 'Buraco na Estrada',
    'HAZARD_ON_ROAD_ROAD_KILL': 'Animal Morto na Estrada',
    'HAZARD_ON_SHOULDER_CAR_STOPPED': 'Carro Parado no Acostamento',
    'HAZARD_ON_SHOULDER_ANIMALS': 'Animais no Acostamento',
    'HAZARD_ON_SHOULDER_MISSING_SIGN': 'Placa Faltando no Acostamento',
    'HAZARD_WEATHER_FOG': 'Nevoeiro',
    'HAZARD_WEATHER_HAIL': 'Granizo',
    'HAZARD_WEATHER_HEAVY_RAIN': 'Chuva Intensa',
    'HAZARD_WEATHER_HEAVY_SNOW': 'Neve Intensa',
    'HAZARD_WEATHER_FLOOD': 'Enchente',
    'HAZARD_WEATHER_MONSOON': 'Monção',
    'HAZARD_WEATHER_TORNADO': 'Tornado',
    'HAZARD_WEATHER_HEAT_WAVE': 'Onda de Calor',
    'HAZARD_WEATHER_HURRICANE': 'Furacão',
    'HAZARD_WEATHER_FREEZING_RAIN': 'Chuva Congelante',
    'HAZARD_ON_ROAD_LANE_CLOSED': 'Faixa Fechada na Estrada',
    'HAZARD_ON_ROAD_OIL': 'Óleo na Estrada',
    'HAZARD_ON_ROAD_ICE': 'Gelo na Estrada',
    'HAZARD_ON_ROAD_CONSTRUCTION': 'Obra na Estrada',
    'HAZARD_ON_ROAD_CAR_STOPPED': 'Carro Parado na Estrada',
    'HAZARD_ON_ROAD_TRAFFIC_LIGHT_FAULT': 'Semáforo com Defeito',
    'ROAD_CLOSED_HAZARD': 'Via Fechada por Perigo',
    'ROAD_CLOSED_CONSTRUCTION': 'Via Fechada por Obras',
    'ROAD_CLOSED_EVENT': 'Via Fechada por Evento'
}

traducao_tipo = {
    'JAM': 'Engarrafamento',
    'ACCIDENT': 'Acidente',
    'ROAD_CLOSED': 'Estrada Fechada',
    'HAZARD': 'Perigo'
}
st.set_page_config(layout="wide")

# Filtro - PAGINA
pagina = st.sidebar.selectbox("Escolha a Página", ["Página 1: Geral", "Página 2: Engarrafamentos"])
if pagina == "Página 1: Geral":
    # HTML para personalizar o título
    st.markdown(
        """
        <style>
        .custom-title {
            background-color: #002231;
            color: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-size: 36px; /* Tamanho da fonte */
        }
        </style>
        <div class="custom-title">
            Análise de Alertas do Waze - Minas Gerais
        </div>
        """,
        unsafe_allow_html=True
    )
    

    fields = [
        'objectid', 'type', 'subtype', 'rodovia', 'mesorregiao', 'municipio',
        'regional', 'jurisdicao', 'x', 'y'
    ]

    # URLs do serviço e do endpoint de token
    token_url = "https://observatorio.infraestrutura.mg.gov.br/portal/sharing/rest/generateToken"
    feature_layer_url = "https://observatorio.infraestrutura.mg.gov.br/server/rest/services/00_PUBLICACOES/waze_tempo_real/FeatureServer/1/query"
    
    # Credenciais de login
    user = st.secrets["API"]["user"]
    password = st.secrets["API"]["password"]

    # Parâmetros para obter o token
    token_params = {
        "username": user,
        "password": password,
        "referer": "https://observatorio.infraestrutura.mg.gov.br/portal",
        "f": "json",
    }

    # Solicitar o token
    token_response = requests.post(token_url, data=token_params)
    if token_response.status_code == 200:
        token_data = token_response.json()
        if "token" in token_data:
            token = token_data["token"]
            print("Token obtido com sucesso!")
        else:
            print("Erro ao obter o token:", token_data)
            exit()
    else:
        print(f"Erro na requisição do token: {token_response.status_code}")
        print(token_response.text)
        exit()

    # Parâmetros para consultar o FeatureLayer
    query_params = {
        "where": "1=1",  # Consulta para retornar todos os dados
        "outFields": ",".join(fields),  # Retornar todos os campos
        "returnGeometry": "true",  # Incluir geometria dos objetos
        "f": "json",  # Formato da resposta (JSON)
        "token": token,  # Token de autenticação
        "resultRecordCount": 2000,  # Máximo de registros por página
        "resultOffset": 0  # Offset inicial (começa no primeiro registro)
    }

    all_data = []  # Lista para armazenar todos os dados

    # Paginação para obter todos os dados
    while True:
        response = requests.get(feature_layer_url, params=query_params)
        if response.status_code == 200:
            data = response.json()  # Parse do JSON
            features = data.get("features", [])
            
            if not features:
                break  # Se não houver mais dados, parar o loop
            
            # Extrair atributos e adicionar à lista all_data
            attributes = [feature["attributes"] for feature in features]
            all_data.extend(attributes)
            
            # Atualizar o offset para a próxima página
            query_params["resultOffset"] += query_params["resultRecordCount"]
        else:
            print(f"Erro na requisição dos dados: {response.status_code}")
            break

    # Transformar os dados em DataFrame
    dados = pd.DataFrame(all_data)

    dados['subtype'] = dados['subtype'].astype(str)
    dados['regional'] = dados['regional'].astype(str)
    dados['subtype'] = dados['subtype'].replace(traducao)
    dados['type'] = dados['type'].replace(traducao_tipo)

    # Seleção e renomeação de colunas
    dados = dados[['objectid', 'type', 'subtype', 'rodovia', 'mesorregiao', 'municipio', 'regional', 'jurisdicao', 'x', 'y']].rename(
        columns={
            'objectid': 'Alerta', 'type': 'Tipo de Alerta', 'subtype': 'Subtipo de Alerta',
            'rodovia': 'Rodovia', 'mesorregiao': 'Mesorregião', 'municipio': 'Município',
            'regional': 'Regional', 'jurisdicao': 'Jurisdição', 'x': 'Longitude', 'y': 'Latitude'})

    

    # Filtros - Sidebar
    st.sidebar.header("Filtros")
    type_filter = st.sidebar.selectbox(
        "Filtro por Tipo",
        options=["Todos"] + list(dados['Tipo de Alerta'].dropna().unique())
    )
    subtype_filter = st.sidebar.selectbox(
        "Filtro por Subtipo",
        options=["Todos"] + list(dados['Subtipo de Alerta'].dropna().unique())
    )
    regional_filter = st.sidebar.selectbox(
        "Filtro por Regional",
        options=["Todos"] + list(dados['Regional'].dropna().unique())
    )

    # Aplicando os filtros
    filtered_data = dados.copy()
    if type_filter != "Todos":
        filtered_data = filtered_data[filtered_data['Tipo de Alerta'] == type_filter]
    if subtype_filter != "Todos":
        filtered_data = filtered_data[filtered_data['Subtipo de Alerta'] == subtype_filter]
    if regional_filter != "Todos":
        filtered_data = filtered_data[filtered_data['Regional'] == regional_filter]

    # Cálculo das métricas
    if not filtered_data.empty:
        # Rodovia com maior número de buracos
        rodovia_com_mais_ocorrencias = (
            filtered_data['Rodovia']
            .value_counts()
            .idxmax() if not filtered_data.empty else "N/A"
        )
        total_ocorrencias_rodovia = (
            filtered_data['Rodovia']
            .value_counts()
            .max() if not filtered_data.empty else 0
        )
        # Regional com maior número de ocorrências
        regional_com_mais_ocorrencias = (
            filtered_data['Regional']
            .value_counts()
            .idxmax() if not filtered_data.empty else "N/A"
        )
        total_ocorrencias_regional = (
            filtered_data['Regional']
            .value_counts()
            .max() if not filtered_data.empty else 0
        )
        # Municipio com maior número de ocorrências
        municipio_com_mais_ocorrencias = (
            filtered_data['Município']
            .value_counts()
            .idxmax() if not filtered_data.empty else "N/A"
        )
        total_ocorrencias_municipio = (
            filtered_data['Município']
            .value_counts()
            .max() if not filtered_data.empty else 0
        )
        # Jurisdição com maior número de ocorrências
        jurisdicao_com_mais_ocorrencias = (
            filtered_data['Jurisdição']
            .value_counts()
            .idxmax() if not filtered_data.empty else "N/A"
        )
        total_ocorrencias_jurisdicao = (
            filtered_data['Jurisdição']
            .value_counts()
            .max() if not filtered_data.empty else 0
        )
        # Mesorregião com maior número de ocorrências
        mesorregiao_com_mais_ocorrencias = (
            filtered_data['Mesorregião']
            .value_counts()
            .idxmax() if not filtered_data.empty else "N/A"
        )
        total_ocorrencias_mesorregiao = (
            filtered_data['Mesorregião']
            .value_counts()
            .max() if not filtered_data.empty else 0
        )


        # Total de alertas no filtro
        total_alertas = len(filtered_data)


        
        # Exibindo os cards
        st.subheader("Resumo das Ocorrências")
        col1, col2, col3 = st.columns(3)

        st.write(
        """
        <style>
        [data-testid="stMetricDelta"] svg {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
        )
        
        with col1:
            st.metric(
                label="Total de Alertas",
                value=f"{total_alertas} ocorrências ⚠️"
            )
        with col2:
            st.metric(
                label="Regional com Mais Ocorrências",
                value=f"{regional_com_mais_ocorrencias} 📝",
                delta=f"{total_ocorrencias_regional} ocorrências",
                delta_color='inverse'
            )
        with col3:
            st.metric(
                label="Mesorregião com Mais Ocorrências",
                value=f"{mesorregiao_com_mais_ocorrencias} 🗺️",
                delta=f"{total_ocorrencias_mesorregiao} ocorrências",
                delta_color='inverse'
            )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Rodovia com Mais Ocorrências",
                value=f"{rodovia_com_mais_ocorrencias} 🛣️",
                delta=f"{total_ocorrencias_rodovia} Ocorrências",
                delta_color='inverse'
            )

        with col2:
            st.metric(
                label="Município com Mais Ocorrências",
                value=f"{municipio_com_mais_ocorrencias} 🏙️",
                delta=f"{total_ocorrencias_municipio} Ocorrências",
                delta_color='inverse'
            )

        with col3:
            st.metric(
                label="Jurisdição com Mais Ocorrências",
                value=f"{jurisdicao_com_mais_ocorrencias} 🏛️",
                delta=f"{total_ocorrencias_jurisdicao} Ocorrências",
                delta_color='inverse'
            )    


    # Gráficos1
    if not filtered_data.empty:
        st.subheader("Gráficos")

    # Calcular as contagens de "Subtipo de Alerta" e ordenar pelo maior valor
        subtipo_counts = (
            filtered_data.groupby(["Subtipo de Alerta", "Tipo de Alerta"])
            .size()
            .reset_index(name="counts")
            .sort_values(by="counts", ascending=False)
        )

        # Criar o gráfico ordenado
        fig = px.histogram(
            subtipo_counts,
            x="Subtipo de Alerta",
            y="counts",
            color="Tipo de Alerta",
            title="Distribuição por Subtipos de Alertas",
            text_auto=True
        )

        # Atualizar layout para melhorar visualização
        fig.update_layout(
            xaxis_categoryorder="total descending",  
            xaxis_title="Subtipo de Alerta",
            yaxis_title="Contagem"
        )

        st.plotly_chart(fig)

    # Gráfico

    st.subheader("Gráfico de Ocorrências")
    columns_available = [col for col in filtered_data.columns if col not in ["Alerta", "Latitude", "Longitude"]]
    xaxis_column = st.selectbox("Eixo X", options=columns_available)

    # Agrupar os dados
    plot_data = filtered_data.groupby(xaxis_column)['Alerta'].count().reset_index()

    # Ordenar os dados do maior para o menor
    plot_data = plot_data.sort_values(by='Alerta', ascending=False)

    # Filtro para Top N
    top_n_filter = st.selectbox("Mostrar:", options=["Todos", "Top 5", "Top 10"], index=0, help="Selecione a quantidade de dados do ranking:")

    if top_n_filter == "Top 5":
        plot_data = plot_data.head(5)
    elif top_n_filter == "Top 10":
        plot_data = plot_data.head(10)

    # Seletor para tipo de gráfico (Barras ou Pizza)
    chart_type = st.radio("Escolha o Tipo de Gráfico:", options=["Gráfico de Barras", "Gráfico de Pizza"])

    # Exibir o gráfico com base na escolha do usuário
    if not plot_data.empty:
        if chart_type == "Gráfico de Barras":
            fig = px.bar(
                plot_data,
                x=xaxis_column,
                y='Alerta',
                title="Ocorrências por Categoria",
                text_auto=True
            )
        elif chart_type == "Gráfico de Pizza":
            fig = px.pie(
                plot_data,
                names=xaxis_column,
                values='Alerta',
                title="Distribuição de Ocorrências por Categoria"
            )

        st.plotly_chart(fig)


        # Mapa de Calor ou Mapa de Pontos
        st.subheader("Escolha o Tipo de Mapa")

        # Criando duas colunas para as opções ficarem lado a lado
        col1, col2 = st.columns(2)

        with col1:
            mapa_tipo = st.radio(
                "Selecione o tipo de mapa",
                options=["Mapa de Calor", "Mapa de Pontos"],
                index=0  # Valor inicial
            )

        # Criando o mapa com base na escolha do usuário
        with st.container():
            mapa = folium.Map(location=[-19.8157, -43.9542], zoom_start=6, tiles=None)  # Coordenadas iniciais de Minas Gerais

            folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr='CartoDB © <a href="https://carto.com/">CartoDB</a>',
            name="CartoDB.DarkMatter"
                ).add_to(mapa)
            
            # Preparando os dados para o mapa
            heat_data = filtered_data[['Latitude', 'Longitude']].dropna().values.tolist()
            
            if mapa_tipo == "Mapa de Calor":
                # Adicionando o Mapa de Calor
                HeatMap(heat_data, radius=10).add_to(mapa)
            elif mapa_tipo == "Mapa de Pontos":
                # Adicionando os pontos no Mapa
                for lat, lon in heat_data:
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=10,
                        color="blue",
                        fill=True,
                        fill_opacity=1
                    ).add_to(mapa)
            
            # Exibindo o mapa
            folium_static(mapa, width=1400, height=800)

if pagina == "Página 2: Engarrafamentos":
    # HTML para personalizar o título
    st.markdown(
        """
        <style>
        .custom-title {
            background-color: #002231;
            color: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-size: 36px; /* Tamanho da fonte */
        }
        </style>
        <div class="custom-title">
            Análise de Engarrafamentos do Waze - Minas Gerais
        </div>
        """,
        unsafe_allow_html=True
    )

    # URLs do serviço e do endpoint de token
    token_url = "https://observatorio.infraestrutura.mg.gov.br/portal/sharing/rest/generateToken"
    feature_layer_url = "https://observatorio.infraestrutura.mg.gov.br/server/rest/services/00_PUBLICACOES/waze_tempo_real/FeatureServer/2/query"

    # Credenciais de login
    user = st.secrets["API"]["user"]
    password = st.secrets["API"]["password"]

    # Parâmetros para obter o token
    token_params = {
        "username": user,
        "password": password,
        "referer": "https://observatorio.infraestrutura.mg.gov.br/portal",
        "f": "json",
    }

    # Solicitar o token
    token_response = requests.post(token_url, data=token_params)
    if token_response.status_code == 200:
        token_data = token_response.json()
        if "token" in token_data:
            token = token_data["token"]
            print("Token obtido com sucesso!")
        else:
            print("Erro ao obter o token:", token_data)
            exit()
    else:
        print(f"Erro na requisição do token: {token_response.status_code}")
        print(token_response.text)
        exit()


    fields_engarrafamentos = ['objectid', 'level', 'city',
        'line', 'speedkmh', 'length', 'speed', 'roadtype', 'delay', 'street', 'id',
        'pubmillis', 'startnode', 'id_dash', 'cod_regional', 'cd_mun', 'nm_mun',
        'trecho', 'sremg', 'rodovia', 'mesorregiao', 'created_user',
        'created_date', 'last_edited_user', 'last_edited_date', 'jurisdicao',
        'municipio', 'regional', 'altitude', 'declividade', 'pub',
        'Shape__Length']
    
    traducao_level = {'1': 'Fluxo Livre',
                      '2': 'Leve',
                      '3': 'Moderado',
                      '4': 'Alto',
                      '5': 'Bloqueado'}



    # Parâmetros para consultar o FeatureLayer
    query_params = {
        "where": "1=1",  # Consulta para retornar todos os dados
        "outFields": ",".join(fields_engarrafamentos),  # Retornar todos os campos
        "returnGeometry": "true",  # Incluir geometria dos objetos
        "f": "json",  # Formato da resposta (JSON)
        "token": token,  # Token de autenticação
        "resultRecordCount": 2000,  # Máximo de registros por página
        "resultOffset": 0  # Offset inicial (começa no primeiro registro)
    }

    all_data = []  # Lista para armazenar todos os dados

    # Paginação para obter todos os dados
    while True:
        response = requests.get(feature_layer_url, params=query_params)
        if response.status_code == 200:
            data = response.json()  # Parse do JSON
            features = data.get("features", [])
            
            if not features:
                break 
            
            # Extrair atributos e adicionar à lista all_data
            attributes = [feature["attributes"] for feature in features]
            all_data.extend(attributes)
            
            # Atualizar o offset para a próxima página
            query_params["resultOffset"] += query_params["resultRecordCount"]
        else:
            print(f"Erro na requisição dos dados: {response.status_code}")
            break

    # Transformar os dados em DataFrame
    dados_engarrafamentos = pd.DataFrame(all_data)

    dados_engarrafamentos['regional'] = dados_engarrafamentos['regional'].astype(str)
    dados_engarrafamentos['level'] = dados_engarrafamentos['level'].astype(str)
    dados_engarrafamentos['level'] = dados_engarrafamentos['level'].replace(traducao_level)
    
    print(dados_engarrafamentos['line'].apply(type).unique())  # Deve mostrar <class 'list'> para cada célula

    # Caso algum valor não seja uma lista de dicionários
    dados_engarrafamentos['line'] = dados_engarrafamentos['line'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    
    
    # Filtros
    
    regional_filter = st.sidebar.selectbox(
            "Filtro por Regional",
            options=["Todos"] + list(dados_engarrafamentos['regional'].dropna().unique())
        )
    level_filter = st.sidebar.selectbox(
            "Filtro por Nível de Engarrafamento",
            options=["Todos"] + list(dados_engarrafamentos['level'].dropna().unique())
        )
    rodovia_filter = st.sidebar.selectbox(
            "Filtro por Rodovia",
            options=['Todos'] + list(dados_engarrafamentos['rodovia'].dropna().unique())
        )

    # Aplicando os filtros
    filtered_data_jam = dados_engarrafamentos.copy()
    if regional_filter != "Todos":
            filtered_data_jam = filtered_data_jam[filtered_data_jam['regional'] == regional_filter]
    if level_filter != "Todos":
            filtered_data_jam = filtered_data_jam[filtered_data_jam['level'] == level_filter]
    if rodovia_filter != "Todos":
            filtered_data_jam = filtered_data_jam[filtered_data_jam['rodovia'] == rodovia_filter]   

    # Cálculo das métricas
    if not filtered_data_jam.empty:
        # Rodovia com maior número de engarrafamentos
        rodovia_com_mais_engarrafamentos = (
            filtered_data_jam['rodovia']
            .value_counts()
            .idxmax() if not filtered_data_jam.empty else "N/A"
        )
        total_engarrafamentos_rodovia = (
                filtered_data_jam['rodovia']
                .value_counts()
                .max() if not filtered_data_jam.empty else 0
            )
        # Regional com maior número de ocorrências
        regional_com_mais_engarrafamentos = (
            filtered_data_jam['regional']
            .value_counts()
            .idxmax() if not filtered_data_jam.empty else "N/A"
        )
        total_engarrafamentos_regional = (
            filtered_data_jam['regional']
            .value_counts()
            .max() if not filtered_data_jam.empty else 0
        )
        # Municipio com maior número de ocorrências
        municipio_com_mais_engarrafamentos = (
            filtered_data_jam['municipio']
            .value_counts()
            .idxmax() if not filtered_data_jam.empty else "N/A"
        )
        total_engarrafamentos_municipio = (
            filtered_data_jam['municipio']
            .value_counts()
            .max() if not filtered_data_jam.empty else 0
        )
        # Jurisdição com maior número de ocorrências
        jurisdicao_com_mais_engarrafamentos = (
            filtered_data_jam['jurisdicao']
            .value_counts()
            .idxmax() if not filtered_data_jam.empty else "N/A"
        )
        total_engarrafamentos_jurisdicao = (
            filtered_data_jam['jurisdicao']
            .value_counts()
            .max() if not filtered_data_jam.empty else 0
        )
        # Mesorregião com maior número de ocorrências
        mesorregiao_com_mais_engarrafamentos = (
            filtered_data_jam['mesorregiao']
            .value_counts()
            .idxmax() if not filtered_data_jam.empty else "N/A"
        )
        total_engarrafamentos_mesorregiao = (
            filtered_data_jam['mesorregiao']
            .value_counts()
            .max() if not filtered_data_jam.empty else 0
        )

    total_alertas_jam = len(filtered_data_jam)
    
    
    # Exibindo os cards
    st.subheader("Resumo das Ocorrências")
    col1, col2, col3 = st.columns(3)

    st.write(
    """
    <style>
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )


# CSS personalizado para ajustar o espaçamento
    st.markdown(
        """
        <style>
        .custom-text {
            margin-top: -20px; /* Ajuste o valor para controlar o espaçamento */
            color: red; /* Cor do texto */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    
    with col1:
        st.metric(
            label="Total de Engarrafamentos",
            value=f"{total_alertas_jam} Engarrafamentos ⚠️"
        )
        comprimento_total = filtered_data_jam['length'].sum() / 1000
        st.markdown(f'<p class="custom-text"><b>Comprimento total dos engarrafamentos:</b> {int(comprimento_total)} km</p>',
        unsafe_allow_html=True)
    
    with col2:
        st.metric(
            label="Regional com Mais Engarrafamentos",
            value=f"{regional_com_mais_engarrafamentos} 📝",
            delta=f"{total_engarrafamentos_regional} Engarrafamentos",
            delta_color='inverse'
        )
    
    with col3:
        st.metric(
            label="Mesorregião com Mais Engarrafamentos",
            value=f"{mesorregiao_com_mais_engarrafamentos} 🗺️",
            delta=f"{total_engarrafamentos_mesorregiao} Engarrafamentos",
            delta_color='inverse'
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Rodovia com Mais Engarrafamentos",
            value=f"{rodovia_com_mais_engarrafamentos} 🛣️",
            delta=f"{total_engarrafamentos_rodovia} Engarrafamentos",
            delta_color='inverse'
        )

    with col2:
        st.metric(
            label="Município com Mais Engarrafamentos",
            value=f"{municipio_com_mais_engarrafamentos} 🏙️",
            delta=f"{total_engarrafamentos_municipio} Engarrafamentos",
            delta_color='inverse'
        )

    with col3:
        st.metric(
            label="Jurisdição com Mais Engarrafamentos",
            value=f"{jurisdicao_com_mais_engarrafamentos} 🏛️",
            delta=f"{total_engarrafamentos_jurisdicao} Engarrafamentos",
            delta_color='inverse'
        )

    
    # Gráfico de categorias
    
    # Convertendo m para km
    filtered_data_jam['length'] = filtered_data_jam['length'] / 1000
    
    # Categorizando
    bins = [0, 1, 2, 4, 10, 20]
    labels = ['0-1 km', '1-2 km', '2-4 km', '4-10 km', '10-20 km']
    filtered_data_jam['categoria'] = pd.cut(filtered_data_jam['length'], bins=bins, labels=labels, right=False)

    # Contagem de engarrafamentos por categoria
    categoria_count = filtered_data_jam['categoria'].value_counts().sort_index()

   

    # Criando gráfico de barras

    fig_jam = px.bar(
                categoria_count,
                x=categoria_count.index,
                y=categoria_count.values,
                title="Engarrafamentos por comprimento",
                text_auto=True)
    
    st.plotly_chart(fig_jam)
    
    
    # Gráfico

    st.subheader("Gráfico de Engarrafamentos")
    columns_available = [col for col in filtered_data_jam.columns if col not in ['objectid', 'roadtype', 'street', 'id',
        'pubmillis', 'startnode', 'id_dash', 'cd_mun', 'nm_mun', 'trecho', 'sremg', 'created_user', 'created_date', 'last_edited_user', 'last_edited_date', 'jurisdicao', 'pub',
        'Shape__Length']]
    xaxis_column = st.selectbox("Eixo X", options=columns_available)

    # Agrupar os dados
    plot_data = filtered_data_jam.groupby(xaxis_column)['objectid'].count().reset_index()

    # Ordenar os dados do maior para o menor
    plot_data = plot_data.sort_values(by='objectid', ascending=False)

    # Filtro para Top N
    top_n_filter = st.selectbox("Mostrar:", options=["Todos", "Top 5", "Top 10"], index=0, help="Selecione a quantidade de dados do ranking:")

    if top_n_filter == "Top 5":
        plot_data = plot_data.head(5)
    elif top_n_filter == "Top 10":
        plot_data = plot_data.head(10)

    # Seletor para tipo de gráfico (Barras ou Pizza)
    chart_type = st.radio("Escolha o Tipo de Gráfico:", options=["Gráfico de Barras", "Gráfico de Pizza"])

    # Exibir o gráfico com base na escolha do usuário
    if not plot_data.empty:
        if chart_type == "Gráfico de Barras":
            fig = px.bar(
                plot_data,
                x=xaxis_column,
                y='objectid',
                title="Ocorrências por Categoria",
                text_auto=True
            )
        elif chart_type == "Gráfico de Pizza":
            fig = px.pie(
                plot_data,
                names=xaxis_column,
                values='objectid',
                title="Distribuição de Ocorrências por Categoria"
            )

        st.plotly_chart(fig)
    
    # Função para determinar os estilos de linha
    def get_line_style(level):
        colors = {'Fluxo Livre': 'blue', 'Leve': 'green', 'Moderado': 'yellow', 'Alto': 'orange', 'Bloqueado': 'red'}
        thickness = {'Fluxo Livre': 2, 'Leve': 3, 'Moderado': 4, 'Alto': 5, 'Bloqueado': 6}
        return colors.get(level, 'black'), thickness.get(level, 2)

    # Inicializar o mapa
    m = folium.Map(location=[-19.965, -44.740], zoom_start=6, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='CartoDB © <a href="https://carto.com/">CartoDB</a>',
        name="CartoDB.DarkMatter"
            ).add_to(m)
    
    # Coletar todos os pontos para ajustar os limites do mapa
    all_coords = []

    for idx, row in filtered_data_jam.iterrows():
        print(f"Adicionando linha {idx + 1} com level {row['level']}: {row['line']}")
        
        # Converter coordenadas
        line_coords = [(point['y'], point['x']) for point in row['line']]
        all_coords.extend(line_coords)  # Adicionar todas as coordenadas à lista

        print(f"Coordenadas da linha {idx + 1}: {line_coords}")
        
        # Obter estilo da linha
        color, thickness = get_line_style(row['level'])
        print(f"Cor e espessura da linha {idx + 1}: {color}, {thickness}")
        
        # Criar o conteúdo do pop-up
        popup_content = f"""
        <b>Detalhes do Engarrafamento</b><br>
        Nível: {row['level']}<br>
        Comprimento: {row['length']} km<br>
        Velocidade: {row['speedkmh']} km/h<br>
        Rodovia: {row['rodovia']} <br>
        Município: {row['municipio']} <br>
        Regional: {row['regional']} <br>
        Jurisdição: {row['jurisdicao']}
        """
        popup = folium.Popup(popup_content, max_width=300)
        
        # Adicionar a linha ao mapa com pop-up
        folium.PolyLine(line_coords, color=color, weight=thickness, opacity=0.6, popup=popup).add_to(m)

    # Ajustar o zoom para os dados filtrados
    if all_coords:  # Verificar se há coordenadas
        bounds = [[min(coord[0] for coord in all_coords), min(coord[1] for coord in all_coords)], 
                [max(coord[0] for coord in all_coords), max(coord[1] for coord in all_coords)]]
        m.fit_bounds(bounds)  # Ajustar o zoom para os limites
        
        
        
        st.sidebar.markdown("### Níveis de Engarrafamentos")

        # Estilos da legenda com as cores
        st.sidebar.markdown("""
            <div style="display: flex; flex-direction: column;">
                <div><span style="color:blue;">&#11044;</span> Fluxo Livre</div>
                <div><span style="color:green;">&#11044;</span> Leve</div>
                <div><span style="color:yellow;">&#11044;</span> Moderado</div>
                <div><span style="color:orange;">&#11044;</span> Alto</div>
                <div><span style="color:red;">&#11044;</span> Bloqueado</div>
            </div>
        """, unsafe_allow_html=True)

        folium_static(m, width=1400, height=800)


