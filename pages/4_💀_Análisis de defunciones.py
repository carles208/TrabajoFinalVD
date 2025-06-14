import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import json
import altair as alt
from streamlit_folium import st_folium
from branca.colormap import linear, LinearColormap

def limpiar_indices(df):
    if df is None or df.empty:
        return df
    
    df.columns.values[0] = 'Provincia'
    df['Provincia'] = df['Provincia'].str.replace(r'^\d+\s*', '', regex=True).str.strip()
    df.set_index('Provincia', inplace=True)
    df.index = df.index.str.strip()
    df.index = df.index.map(lambda x: '/'.join(x.split('/')[::-1]) if '/' in x else x)
    df.index = df.index.map(lambda x: ' '.join(x.split(', ')[::-1]) if ', ' in x else x)
    return df

@st.cache_data
def cargar_datos():
    try:
        # Cargar datos geográficos
        provincias = gpd.read_file('datasets/recintos_provinciales_inspire_peninbal_etrs89.shp').to_crs("EPSG:4326")
        provincias = provincias[['NAMEUNIT', 'geometry']].rename(columns={'NAMEUNIT': 'Provincia'})
        gdf = gpd.GeoDataFrame(provincias, crs="EPSG:4326")
        
        # Cargar datos de defunciones
        naci_homb_df = limpiar_indices(pd.read_excel('datasets/DefunHomb.xlsx', skiprows=6))
        naci_homb_df.columns = naci_homb_df.columns.map(str)
        
        naci_muj_df = limpiar_indices(pd.read_excel('datasets/DefunMuj.xlsx', skiprows=6))
        naci_muj_df.columns = naci_muj_df.columns.map(str)
        
        naci_tot_df = limpiar_indices(pd.read_excel('datasets/DefunTot.xlsx', skiprows=6))
        naci_tot_df.columns = naci_tot_df.columns.map(str)
        
        return gdf, naci_homb_df, naci_muj_df, naci_tot_df
        
    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos: {e}")
        st.info("Asegúrate de que todos los archivos estén en la carpeta 'datasets':")
        st.code("""
        datasets/
        ├── recintos_provinciales_inspire_peninbal_etrs89.shp
        ├── DefunHomb.xlsx
        ├── DefunMuj.xlsx
        └── DefunTot.xlsx
        """)
        return None, None, None, None
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return None, None, None, None

# --- Cargar datos ---
datos = cargar_datos()
if datos[0] is None:
    st.stop()

gdf, naci_homb_df, naci_muj_df, naci_tot_df = datos

# Verificar que los datos se cargaron correctamente
if any(df is None or df.empty for df in [naci_homb_df, naci_muj_df, naci_tot_df]):
    st.error("Error: Algunos datasets están vacíos")
    st.stop()

# --- UI ---
st.title("💀 Análisis de defunciones")
st.subheader("1. Mapa de defunciones por provincia:")
st.text(
     "Como se puede apreciar mediante la diferenciación entre mapas de 1975 y 2023, la mortalidad por provincia representa una distribución mucho " \
     "más equilibrada que la natalidad. Esto se debe a que pese la baja natalidad en ciertas regiones, aún faltan varias " \
     "generaciones por fallecer hasta que en un futuro la bajada de la población afecte en un decremento de las defunciones. " \
     "Independientemente de este equilibrio a nivel general, se puede apreciar que en las provincias con mayor nacimiento " \
     "también se presenta una alta natalidad. Esto, se puede deber a la cantidad de población."
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
try:
    gdf_gen = gdf.merge(pob_df, on='Provincia', how='left').fillna(1)
    
    if selected_column not in gdf_gen.columns:
        st.warning(f"La columna '{selected_column}' no existe para {genero.lower()}.")
        st.stop()

    # Verificar que hay datos válidos
    if gdf_gen[selected_column].isna().all():
        st.warning("No hay datos válidos para mostrar en el mapa.")
    else:
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

        # Simplificar geometría para mejor rendimiento
        gdf_gen['geometry'] = gdf_gen['geometry'].simplify(0.001, preserve_topology=True)
        
        # Crear mapa
        m = folium.Map(zoom_start=6)
        
        # Ajustar bounds del mapa
        bounds = gdf_gen.total_bounds
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

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

except Exception as e:
    st.error(f"Error al crear el mapa: {e}")

# --- Gráfica temporal ---
st.subheader("2. Gráfica de defunciones:")
st.text(
    "Como se puede apreciar en la siguiente gráfica la mortalidad de la población ha seguido una linealidad creciente. " \
    "Este resultado refleja como poco a poco la cantidad de las defunciones de población ha ido elevándose, " \
    "partiendo de unas 300000 personas anuales en 1975 hasta las 430000 de 2023 y pasando por un máximo de casi 500000 " \
    "en 2020 (probablemente debido a la pandemia de COVID). Esta subida constante de la mortalidad de la población se puede " \
    "deber a un posible crecimiento de la misma."
)

try:
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

        if not df_stacked.empty:
            chart = alt.Chart(df_stacked).mark_area().encode(
                x=alt.X("Fecha:T", title="Fecha"),
                y=alt.Y("Población:Q", stack="zero"),
                color=alt.Color("Sexo:N", scale=alt.Scale(scheme='tableau10')),
                tooltip=["Fecha:T", "Sexo:N", "Población:Q"]
            ).properties(width=700, height=400).interactive()

            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para mostrar el gráfico apilado.")

    else:
        # Línea individual para hombres o mujeres
        serie_evolucion = pob_df.sum(axis=0)
        df_evolucion = pd.DataFrame({
            "Fecha": serie_evolucion.index.astype(str),
            "Población": serie_evolucion.values
        })

        df_evolucion["Fecha"] = pd.to_datetime(df_evolucion["Fecha"], format="%Y", errors="coerce")
        df_evolucion = df_evolucion.dropna().sort_values("Fecha").set_index("Fecha")

        if not df_evolucion.empty:
            st.line_chart(df_evolucion)
        else:
            st.warning("No hay datos suficientes para mostrar el gráfico.")

except Exception as e:
    st.error(f"Error al crear los gráficos: {e}")
    st.info("Verifica que los datos estén en el formato correcto.")