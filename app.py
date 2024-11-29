import arcgis
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import folium_static  
from arcgis.gis import GIS




# Traduções
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
st.title("Análise de Alertas do Waze - Minas Gerais")

try:
    user = st.secrets["GIS"]["user"]
    password = st.secrets["GIS"]["passoword"]
    
    # Conectar ao GIS
    gis = GIS("https://observatorio.infraestrutura.mg.gov.br/portal", user, password)
    st.success("Conexão com o GIS bem-sucedida!")
except Exception as e:
    st.error(f"Erro ao conectar ao GIS: {e}")
    st.stop()

# Conectar à camada de features
try:
    feature_layer = arcgis.features.FeatureLayer(
        "https://observatorio.infraestrutura.mg.gov.br/server/rest/services/00_PUBLICACOES/waze_alertas_transito/FeatureServer/0"
    )
    st.success("Camada de alertas carregada com sucesso!")
except Exception as e:
    st.error(f"Erro ao carregar a camada: {e}")
    st.stop()

# Consultar dados da camada
try:
    tabela = feature_layer.query(where="1=1", out_fields="*", return_geometry=True)
    dados = tabela.sdf  # Converter para DataFrame
    st.write("Dados Extraídos da Camada:")
    st.dataframe(dados)  # Exibir os dados na interface
except Exception as e:
    st.error(f"Erro ao consultar os dados da camada: {e}")

# Criando colunas de coordenadas X e Y a partir da geometria
dados['x'] = dados['SHAPE'].apply(lambda point: point.x if point else None)
dados['y'] = dados['SHAPE'].apply(lambda point: point.y if point else None)
dados['subtype'] = dados['subtype'].astype(str)
dados['regional'] = dados['regional'].astype(str)
dados['subtype'] = dados['subtype'].replace(traducao)
dados['type'] = dados['type'].replace(traducao_tipo)

# Seleção e renomeação de colunas
dados = dados[['objectid', 'type', 'roadtype', 'subtype', 'street', 'created_date', 'cod_regional', 'trecho', 'rodovia',
                'mesorregiao', 'municipio', 'regional', 'jurisdicao', 'x', 'y']].rename(
    columns={
        'objectid': 'Alerta', 'type': 'Tipo de Alerta', 'roadtype': 'Tipo de Rodovia', 'subtype': 'Subtipo de Alerta',
        'street': 'Via', 'created_date': 'Data da criação', 'cod_regional': 'Código da regional',
        'trecho': 'Trecho', 'rodovia': 'Rodovia', 'mesorregiao': 'Mesorregião', 'municipio': 'Município',
        'regional': 'Regional', 'jurisdicao': 'Jurisdição', 'x': 'Longitude', 'y': 'Latitude'})

dados = dados.drop(columns=['Código da regional', 'Tipo de Rodovia', 'Data da criação'])

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
        mapa = folium.Map(location=[-19.8157, -43.9542], zoom_start=6)  # Coordenadas iniciais de Minas Gerais
        
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
                    radius=3,
                    color="blue",
                    fill=True,
                    fill_opacity=0.5
                ).add_to(mapa)
        
        # Exibindo o mapa
        folium_static(mapa, width=1400, height=800)
