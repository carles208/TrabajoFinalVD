import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import json
import locale
import altair as alt
from streamlit_folium import st_folium
from branca.colormap import linear, LinearColormap

# --- Función de limpieza ---
def limpiar_indices(df):
    df.columns.values[0] = 'Provincia'
    df['Provincia'] = df['Provincia'].str.replace(r'^\d+\s*', '', regex=True).str.strip()
    df.set_index('Provincia', inplace=True)
    df.index = df.index.str.strip()
    df.index = df.index.map(lambda x: '/'.join(x.split('/')[::-1]) if '/' in x else x)
    df.index = df.index.map(lambda x: ' '.join(x.split(', ')[::-1]) if ', ' in x else x)
    return df

# --- Cargar datos ---
provincias = gpd.read_file('datasets/recintos_provinciales_inspire_peninbal_etrs89.shp').to_crs("EPSG:4326")
provincias = provincias[['NAMEUNIT', 'geometry']].rename(columns={'NAMEUNIT': 'Provincia'})
gdf = gpd.GeoDataFrame(provincias, crs="EPSG:4326")

naci_homb_df = limpiar_indices(pd.read_excel('datasets/NaciHomb.xlsx', skiprows=6))
naci_homb_df.columns = naci_homb_df.columns.map(str)

naci_muj_df = limpiar_indices(pd.read_excel('datasets/NaciMuj.xlsx', skiprows=6))
naci_muj_df.columns = naci_muj_df.columns.map(str)

naci_tot_df = limpiar_indices(pd.read_excel('datasets/NaciTot.xlsx', skiprows=6))
naci_tot_df.columns = naci_tot_df.columns.map(str)
print(sorted(naci_tot_df.index.unique()))

# --- UI ---
st.title("🧑‍🍼 Análisis de natalidad")
st.subheader("1. Mapa de natalidad por provincia:")
st.text(
     "Como se puede apreciar mediante la diferenciación entre mapas de 1975 y 2023, "
    "la natalidad en España se concentra en las principales ciudades y comunidades económicas del país: Barcelona, Valencia, " \
    "Alicante, Madrid, Sevilla, Málaga y Murcia, mientras que en el resto de las provincias o, lo que actualmente se considera " \
    "España vacía, representa un decremento exponencial en orden canónico."
)
st.sidebar.header("Filtros")
data_columns = [str(col) for col in naci_tot_df.select_dtypes(include=['float64', 'int']).columns]
selected_column = st.sidebar.selectbox("Selecciona una fecha", sorted(data_columns, reverse=True))
genero = st.sidebar.radio("Selecciona grupo poblacional", ["Total", "Hombres", "Mujeres"], index=0)

# --- Dataset seleccionado ---
if genero == "Hombres":
    pob_df = naci_homb_df
elif genero == "Mujeres":
    pob_df = naci_muj_df
else:
    pob_df = naci_tot_df

# --- Unir y visualizar ---
gdf_gen = gdf.merge(pob_df, on='Provincia', how='left').fillna(1)
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

geojson = folium.GeoJson(
    data=json.loads(gdf_gen.to_json()),
    style_function=lambda feature: {
        "fillColor": colormap(feature["properties"].get(selected_column))
        if isinstance(feature["properties"].get(selected_column), (int, float))
        else "#ffffff",
        "color": "black",
        "weight": 1,
        "dashArray": "5, 5",
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(
    fields=["Provincia", str(selected_column)],
    aliases=["Provincia:", f"Población ({selected_column}):"],
    localize=True
)
)
geojson.add_to(m)

colormap.options = {"position": "bottomleft"}
colormap.add_to(m)
st_folium(m, use_container_width=True, height=600, returned_objects=[])

# --- Gráfica temporal ---
st.subheader("2. Gráfica de natalidad:")
st.text(
    "Como se puede apreciar en la siguiente gráfica natalidad en España presenta actualmente una tendencia altamente bajista. " \
    "Esta, desde el 1975 hasta el 2023 se ha llegado a reducir a la mitad y únicamente ha presentado un crecimiento hasta " \
    "un máximo local en la franja entre los años 1996 y el 2008 (antes del comienzo de la crisis económica). "
)

# Establecer locale español para que pandas reconozca meses en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux/Mac
except:
    locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Windows

if genero == "Total":
    # Gráfico apilado
    serie_h = naci_homb_df.sum(axis=0)
    serie_m = naci_muj_df.sum(axis=0)

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
    df_stacked["Fecha"] = pd.to_datetime(df_stacked["Fecha"], format="%Y", errors="coerce")
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

    df_evolucion["Fecha"] = pd.to_datetime(df_evolucion["Fecha"], format="%Y", errors="coerce")
    df_evolucion = df_evolucion.dropna().sort_values("Fecha").set_index("Fecha")

    st.line_chart(df_evolucion)
