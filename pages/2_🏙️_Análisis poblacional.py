import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import json
import locale
import altair as alt
import datetime                            # ← Se añade esta línea
from streamlit_folium import st_folium
from branca.colormap import linear, LinearColormap

# --- Función de limpieza ---
def limpiar_indices(df):
    df.columns.values[0] = 'Provincia'
    df['Provincia'] = df['Provincia'].str.replace(r'^\d+\s*', '', regex=True).str.strip()
    df.set_index('Provincia', inplace=True)
    df.index = df.index.str[3:]
    df.index = df.index.map(lambda x: '/'.join(x.split('/')[::-1]) if '/' in x else x)
    df.index = df.index.map(lambda x: ' '.join(x.split(', ')[::-1]) if ', ' in x else x)
    return df

# --- Cargar datos ---
provincias = gpd.read_file('datasets/recintos_provinciales_inspire_peninbal_etrs89.shp').to_crs("EPSG:4326")
provincias = provincias[['NAMEUNIT', 'geometry']].rename(columns={'NAMEUNIT': 'Provincia'})
gdf = gpd.GeoDataFrame(provincias, crs="EPSG:4326")

pob_homb_df = limpiar_indices(pd.read_excel('datasets/PobHomb.xlsx', skiprows=6))
pob_muj_df = limpiar_indices(pd.read_excel('datasets/PobMuj.xlsx', skiprows=6))
pob_tot_df  = limpiar_indices(pd.read_excel('datasets/PobTot.xlsx',  skiprows=6))

# --- UI ---
st.title("🏙️ Análisis poblacional general")
st.subheader("1. Mapa de población por provincia:")
st.text(
    "Como se puede observar mediante la comparación de los períodos de 1971 frente al 2022 en el "
    "mapa, la evolución de la población de España presenta un gran crecimiento. No obstante, este "
    "crecimiento no se reparte de forma equilibrada sino que se ha distribuido entre las diferentes "
    "comunidades autónomas de Andalucía, Madrid y la Comunidad Valenciana. También se puede observar "
    "cómo las comunidades adyacentes han ido perdiendo población a un ritmo alarmante. A este "
    "fenómeno poblacional se le suele conocer como la “España vacía”. Se explica porque la población "
    "busca mejores condiciones laborales, nivel de vida y posibilidad de estudios superiores, "
    "desplazándose desde zonas más “rurales” hacia las ciudades más grandes."
)
st.sidebar.header("Filtros")

data_columns = pob_tot_df.select_dtypes(include=['float64', 'int']).columns.tolist()
selected_column = st.sidebar.selectbox("Selecciona una fecha", data_columns)
genero = st.sidebar.radio("Selecciona grupo poblacional", ["Total", "Hombres", "Mujeres"], index=0)

# --- Dataset seleccionado ---
if genero == "Hombres":
    pob_df = pob_homb_df
elif genero == "Mujeres":
    pob_df = pob_muj_df
else:
    pob_df = pob_tot_df

# ← Antes de hacer el merge, devolvemos 'Provincia' como columna en lugar de índice:
pob_df_reset = pob_df.reset_index()  # 'Provincia' pasa a ser columna otra vez

# --- Unir y visualizar ---
gdf_gen = gdf.merge(pob_df_reset, on='Provincia', how='left').fillna(1)
if selected_column not in gdf_gen.columns:
    st.warning(f"La columna '{selected_column}' no existe para {genero.lower()}.")
    st.stop()

vmin = float(gdf_gen[selected_column].min())
vmax = float(gdf_gen[selected_column].max())
caption = f"Población de {genero.lower()} en {selected_column}"

colormap = LinearColormap(
    colors=linear.viridis.colors,
    vmin=vmin,
    vmax=vmax,
    caption=caption,
    tick_labels=[vmin, vmax]
)

gdf_gen['geometry'] = gdf_gen['geometry'].simplify(0.001, preserve_topology=True)
m = folium.Map(zoom_start=6)
m.fit_bounds([[*gdf_gen.total_bounds[1::-1]], [*gdf_gen.total_bounds[3:1:-1]]])

folium.GeoJson(
    json.loads(gdf_gen.to_json()),
    style_function=lambda feature: {
        "fillColor": colormap(feature["properties"][selected_column]) if feature["properties"][selected_column] else "#ffffff",
        "color": "black",
        "weight": 1,
        "dashArray": "5, 5",
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["Provincia", selected_column],
        aliases=["Provincia:", "Población:"],
        localize=True
    )
).add_to(m)

colormap.options = {"position": "bottomleft"}
colormap.add_to(m)
st_folium(m, use_container_width=True, height=600, returned_objects=[])

# --- Gráfica temporal ---
st.subheader("2. Gráfica de población:")

st.text(
    "Como se puede observar en la siguiente gráfica, la evolución de la población de España a partir "
    "del año 1971 presenta un crecimiento constante hasta la entrada de los 2000 donde, posiblemente "
    "por la mejora de la economía y la situación social, se percibe un mayor aumento. Esto termina en 2008 "
    "donde, tras la crisis surgida, se crea un estancamiento que se mantiene hasta la actualidad. En esta "
    "figura también se puede ver que a lo largo del crecimiento de la población se mantiene cierta paridad "
    "entre mujeres y hombres."
)

# Establecer locale español - con manejo de errores para Streamlit Cloud
def set_spanish_locale():
    locales_to_try = [
        'es_ES.UTF-8',        # Linux/Mac
        'Spanish_Spain.1252', # Windows
        'es_ES',              # Alternativa
        'C.UTF-8'             # Fallback
    ]
    for loc in locales_to_try:
        try:
            locale.setlocale(locale.LC_TIME, loc)
            return True
        except:
            continue
    return False

# Función para parsear fechas en español sin depender del locale
def parse_date_safe(date_str):
    months = {
        'enero': 1, 'febrero': 2, 'marzo': 3,   'abril': 4,   'mayo': 5,   'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9,'octubre': 10,'noviembre': 11,'diciembre': 12
    }
    try:
        # Intentar con locale primero
        if set_spanish_locale():
            return pd.to_datetime(date_str, format="%d de %B de %Y", errors="coerce")
        else:
            # Fallback: parseo manual
            parts = date_str.split(' de ')
            if len(parts) == 3:
                day = int(parts[0])
                month = months.get(parts[1].lower())
                year = int(parts[2])
                if month:
                    return datetime.datetime(year, month, day)  # ← Se usa datetime.datetime en lugar de pd.datetime
    except:
        pass
    return pd.NaT

if genero == "Total":
    # Stacked area chart
    serie_h = pob_homb_df.sum(axis=0)
    serie_m = pob_muj_df.sum(axis=0)

    df_h = pd.DataFrame({
        "Fecha": serie_h.index.astype(str),
        "Población": serie_h.values,
        "Sexo": "Hombres"
    })

    df_m = pd.DataFrame({
        "Fecha": serie_m.index.astype(str),
        "Población": serie_m.values,
        "Sexo": "Mujeres"
    })

    df_stacked = pd.concat([df_h, df_m])
    df_stacked["Fecha"] = df_stacked["Fecha"].apply(parse_date_safe)
    df_stacked = df_stacked.dropna().sort_values("Fecha")

    chart = alt.Chart(df_stacked).mark_area().encode(
        x=alt.X("Fecha:T", title="Fecha"),
        y=alt.Y("Población:Q", stack="zero"),
        color=alt.Color("Sexo:N", scale=alt.Scale(scheme='tableau10')),
        tooltip=["Fecha:T", "Sexo:N", "Población:Q"]
    ).properties(width=700, height=400).interactive()

    st.altair_chart(chart, use_container_width=True)

else:
    # Línea individual para hombres o mujeres
    serie_evolucion = pob_df.sum(axis=0)
    df_evolucion = pd.DataFrame({
        "Fecha": serie_evolucion.index.astype(str),
        "Población": serie_evolucion.values
    })

    df_evolucion["Fecha"] = df_evolucion["Fecha"].apply(parse_date_safe)
    df_evolucion = df_evolucion.dropna().sort_values("Fecha").set_index("Fecha")

    st.line_chart(df_evolucion)
