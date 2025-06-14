import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
from branca.colormap import linear, LinearColormap

# --- UI ---
st.title("🗺️ Análisis poblacional de España")
st.markdown(
    ":blue-badge[Carles Carbonell Sales] :green-badge[:material/home: UPV] :orange-badge[:material/star: MUIARFID] :gray-badge[📊 VD] :red-badge[🗺️ España]"
)

st.image("images/image1.jpg","")

st.header("Descripción del proyecto:")
st.text("En este trabajo de análisis perteneciente a la asignatura de Visualización de datos de el Máster de Inteligencia Artificial" \
", Reconocimiento de Formas y Imagen Digital se pretende realizar una investigación realizar una investigación de la evolución de la distribución provincial de población española a lo largo del tiempo y como ha sido afectada por diferentes factores como la tasa de natalidad, la inmigración, defunción o la media de la vejez. Para ello, se ha hecho uso de una serie de datasets provenientes de la página web del Instituto nacional de estadística. ")
st.header("Datasets empleados:")
st.markdown("""
1. **Defunciones 2022**: Dataset de 51 filas que contiene la cantidad de defunciones organizada por provincias en el año 2022.  
2. **Edad 1971**: Dataset de 51 filas y 100 columnas que contiene la cifra de personas con cierta edad en 1971 diferenciada por provincias.  
3. **Edad 2022**: Dataset de 51 filas y 100 columnas que contiene la cifra de personas con cierta edad en 2022 diferenciada por provincias.  
4. **Nacimientos 2022**: Dataset de 51 filas que contiene la cantidad de nacimientos organizada por provincias en el año 2022.  
5. **Población residente por provincia en 1971**: Dataset con 51 filas con la población española clasificada por provincia en 1971.  
6. **Población residente por provincia en 2022**: Dataset con 51 filas con la población española clasificada por provincia en 2022.
7. **Defunciones1975**: Dataset de 147 columnas y 54 filas que contiene la cantidad de defunciones organizada por provincias y sexos desde el 1975 hasta el 2023.
8. **EdadPob1971-PAños**: Dataset de 107 filas y 2 columnas que contiene la cifra de personas con cierta edad en el 1971 diferenciando entre hombres y mujeres.
9. **EdadPob2024-PAños**: Dataset de 107 filas y 2 columnas que contiene la cifra de personas con cierta edad en el 2024 diferenciando entre hombres y mujeres.
10. **Flujo de inmigración procedente del extranjero por año, sexo y edad2008**: Dataset con 276 filas y 14 columnas que representa la cantidad de inmigración clasificada por edad y sexo desde el 2008 hasta el 2021.
11. **Nacimientos1975**: Dataset de 147 columnas y 54 filas que contiene la cantidad de nacimientos organizada por provincias y sexos desde el 1975 hasta el 2023.
12. **Población residente por fecha, sexo y edad1971**: Dataset de 104 columnas y 327 filas con la población española clasificada por sexo y edad desde el 1971 hasta el 2022.
""")



