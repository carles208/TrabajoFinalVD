from pydoc import text
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Pirámides Poblacionales España", layout="wide")
st.title("Pirámides Poblacionales de España (1971 vs 2024)")

@st.cache_data
def cargar_y_procesar_piramide(ruta_excel: str):
    raw = pd.read_excel(ruta_excel, sheet_name=0, skiprows=8)
    raw.columns = ['Edad', 'Hombres', 'Mujeres']
    raw = raw.fillna(0)
    raw['Hombres'] = pd.to_numeric(raw['Hombres'], errors='coerce').fillna(0)
    raw['Mujeres'] = pd.to_numeric(raw['Mujeres'], errors='coerce').fillna(0)

    # Filtrar solo filas donde 'Edad' contenga "año"
    df = raw[raw['Edad'].astype(str).str.contains('año')].copy()
    # Extraer parte numérica de la edad
    df['Edad_num'] = df['Edad'].str.extract(r'(\d+)').astype(float)
    # Calcular inicio de cada franja de 5 años
    df['Grupo_inicio'] = (df['Edad_num'] // 5 * 5).astype(int)
    df['Grupo'] = df['Grupo_inicio'].astype(str) + '-' + (df['Grupo_inicio'] + 4).astype(str)

    # Agrupar simultáneamente Hombres y Mujeres por 'Grupo'
    agrupado = df.groupby('Grupo', as_index=False).agg({
        'Hombres': 'sum',
        'Mujeres': 'sum',
        'Grupo_inicio': 'first'
    })

    # Ordenar por el valor numérico de inicio de franja y quitar esa columna auxiliar
    agrupado = agrupado.sort_values('Grupo_inicio').drop(columns=['Grupo_inicio']).reset_index(drop=True)
    return agrupado

ruta_1971 = "datasets/EdadPob1971-PAños.xlsx"
ruta_2024 = "datasets/EdadPob2024-PAños.xlsx"

st.subheader("Pirámide Poblacional 1971")
st.text("En cuanto a la pirámide poblacional del año 1971, se puede observar que se cuenta con una población muy " \
"joven concentrada en la franja de los 0 hasta los 29 años. Esto se puede deber a que, debido a la baja calidad de vida y " \
"la limitada esperanza de vida en ese periodo, era común que la mayor parte de la población estuviera compuesta por personas " \
"jóvenes. Además, las altas tasas de natalidad propias de mediados del siglo XX contribuían a una base ancha en la pirámide, " \
"reflejando una sociedad en crecimiento, aunque con una notable disminución de población conforme aumenta la edad. Esta forma " \
"piramidal clásica indica un modelo demográfico aún en transición, con una mortalidad elevada en edades avanzadas y un fuerte " \
"peso de las generaciones jóvenes.")
pir_1971 = cargar_y_procesar_piramide(ruta_1971)

hombres_1971 = -pir_1971["Hombres"]
mujeres_1971 = pir_1971["Mujeres"]
grupos_1971 = pir_1971["Grupo"]

fig1971 = go.Figure()
fig1971.add_trace(go.Bar(
    y=grupos_1971,
    x=hombres_1971,
    name="Hombres",
    orientation="h",
    marker=dict(color="steelblue"),
    hovertemplate="%{y}<br>Hombres: %{x:.0f}<extra></extra>"
))
fig1971.add_trace(go.Bar(
    y=grupos_1971,
    x=mujeres_1971,
    name="Mujeres",
    orientation="h",
    marker=dict(color="salmon"),
    hovertemplate="%{y}<br>Mujeres: %{x:.0f}<extra></extra>"
))
fig1971.update_layout(
    title_text="España - Pirámide Poblacional 1971",
    barmode="relative",
    xaxis=dict(
        title="Población",
        tickvals=[-2000000, -1000000, 0, 1000000, 2000000],
        ticktext=["2 M", "1 M", "0", "1 M", "2 M"]
    ),
    yaxis=dict(title="Rango de edad"),
    plot_bgcolor="white",
    template="simple_white",
    margin=dict(l=80, r=80, t=50, b=50)
)
st.plotly_chart(fig1971, use_container_width=True)

st.subheader("Pirámide Poblacional 2024")
st.text("En la pirámide del año 2024 se observa una clara inversión en la estructura demográfica en comparación " \
"con la de 1971. La base de la pirámide, correspondiente a las edades más jóvenes (0-14 años), es notablemente más estrecha, " \
"lo que indica una disminución sostenida de la natalidad en las últimas décadas. Esta tendencia puede deberse al encarecimiento " \
"general de la vida, que ha provocado un aplazamiento en la decisión de tener hijos por parte de muchas parejas, o incluso un " \
"rechazo directo a la procreación debido a la imposibilidad de mantener económicamente a la descendencia. En contraste, las " \
"franjas de edad comprendidas entre los 45 y los 59 años son las más anchas, reflejando el envejecimiento de las generaciones " \
"nacidas durante el baby boom de mediados del siglo XX.")
st.text("Además, se aprecia un ensanchamiento progresivo de los grupos de mayor " \
"edad, especialmente a partir de los 70 años, con una clara predominancia femenina, lo que evidencia una mayor esperanza de vida " \
"para las mujeres. Esta forma más parecida a un barril o un rombo que a una pirámide clásica refleja un país con baja natalidad, " \
"longevidad elevada y envejecimiento demográfico, típico de sociedades avanzadas.")
st.text("Este tipo de pirámides plantean una gran " \
"problemática a futuro, ya que la poca tasa de natalidad y la gran vejez de la población imposibilita el relevo generacional " \
"necesario para mantener el equilibrio entre cotizantes y beneficiarios de un sistema de bienestar como lo es el español.")
pir_2024 = cargar_y_procesar_piramide(ruta_2024)

hombres_2024 = -pir_2024["Hombres"]
mujeres_2024 = pir_2024["Mujeres"]
grupos_2024 = pir_2024["Grupo"]

fig2024 = go.Figure()
fig2024.add_trace(go.Bar(
    y=grupos_2024,
    x=hombres_2024,
    name="Hombres",
    orientation="h",
    marker=dict(color="steelblue"),
    hovertemplate="%{y}<br>Hombres: %{x:.0f}<extra></extra>"
))
fig2024.add_trace(go.Bar(
    y=grupos_2024,
    x=mujeres_2024,
    name="Mujeres",
    orientation="h",
    marker=dict(color="salmon"),
    hovertemplate="%{y}<br>Mujeres: %{x:.0f}<extra></extra>"
))
fig2024.update_layout(
    title_text="España - Pirámide Poblacional 2024",
    barmode="relative",
    xaxis=dict(
        title="Población",
        tickvals=[-2000000, -1000000, 0, 1000000, 2000000],
        ticktext=["2 M", "1 M", "0", "1 M", "2 M"]
    ),
    yaxis=dict(title="Rango de edad"),
    plot_bgcolor="white",
    template="simple_white",
    margin=dict(l=80, r=80, t=50, b=50)
)
st.plotly_chart(fig2024, use_container_width=True)
