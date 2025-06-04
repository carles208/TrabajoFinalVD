import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import json
import locale
import altair as alt
from streamlit_folium import st_folium
from branca.colormap import linear, LinearColormap

inmig_file_path = 'datasets/Flujo de inmigracion procedente del extranjero por año, sexo y edad2008.xlsx'

inmig_df_raw = pd.read_excel(inmig_file_path, sheet_name=0, skiprows=5)

''' 2.1.3. Tabla de inmigraciones '''

# Extraer fechas de la fila 0
fechas = inmig_df_raw.iloc[0, 1:].tolist()
inmig_df_raw.columns = ['Sexo/Grupo de edad'] + fechas

fechas_inmg = inmig_df_raw.iloc[0, 1:].tolist()

inmig_df_raw.columns = ['Sexo/Grupo de edad'] + fechas_inmg

# Eliminar las filas de encabezado innecesarias
inmig_df_raw = inmig_df_raw.drop(index=[0, 1]).reset_index(drop=True)

# Extraer filas por posición (Ambos sexos, Hombres, Mujeres)
img_df_filtered_g = inmig_df_raw.iloc[0:1].copy()

# Transponer y renombrar
img_df_transpuesto_g = img_df_filtered_g.set_index('Sexo/Grupo de edad').transpose().reset_index()
img_df_transpuesto_g.columns = ['Años', 'Inmigrantes']

# Intentar convertir la columna de fecha a datetime
img_df_transpuesto_g['Años'] = pd.to_datetime(img_df_transpuesto_g['Años'].astype(float).astype(int).astype(str), format='%Y')

# Establecer 'Años' como índice
img_df_transpuesto_g = img_df_transpuesto_g.set_index('Años')

# --- UI ---
st.title("🎎 Análisis de inmigración")
st.subheader("1. Inmigración externa:")
st.text(
     "La gran causa de que no haya un gran decremento en la población española se sitúa en la inmigración de países exteriores"
     ". Esta, en el período de inversión de natalidad y mortalidad anteriormente comentado, ha presentado un gran aumento, " \
     "llegando en 2019 hasta una cantidad de más de 700000 personas."
)

img_df_transpuesto_g = img_df_transpuesto_g.copy()
img_df_transpuesto_g.index = pd.to_datetime(img_df_transpuesto_g.index)
img_df_transpuesto_g["Año"] = img_df_transpuesto_g.index.year
img_df_transpuesto_g["Década"] = (img_df_transpuesto_g["Año"] // 10) * 10

bar_chart = alt.Chart(img_df_transpuesto_g.reset_index()).mark_bar().encode(
    x=alt.X("Año:O", title="Año", sort="ascending"),
    y=alt.Y("Inmigrantes:Q", title="Número de Inmigrantes"),
    tooltip=["Año", "Inmigrantes"]
).properties(width=700, height=400)

st.altair_chart(bar_chart, use_container_width=True)

st.subheader("2. Inmigración interna:")

st.text(
    " Por lo que hace inmigración interior del país, resulta muy importante ya que permite entender cómo, " \
    "al ir el país evolucionando y avanzando hacia una economía más madura, se han movilizado la población hacia áreas más " \
    "desarrolladas. Además, una posible inferencia del descenso porcentual de la tasa de nacimiento a lo largo del tiempo, " \
    "puede ser resultante de la aglomeración poblacional en pocos puntos del país; cuanto mayor densidad de individuos en " \
    "una misma locación, mayor coste de vida, menos oportunidades laborales y mayor atrasamiento o negación a la reproducción."
)

col1, col2 = st.columns(2)

with col1:
    st.image("images/Poblacion_1971.png", caption="Figura 1. Población por provincia en 1971", width=400)

with col2:
    st.image("images/Poblacion_2022.png", caption="Figura 2. Población por provincia en 2022", width=400)