import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Diccionario para mostrar fechas en español
MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def fecha_es(dt):
    if pd.isna(dt):
        return ""
    return f"{MESES_ES[dt.month]} de {dt.year}"


@st.cache_data
def cargar_datos():
    pob = pd.read_excel('datasets/Poblacion residente por fecha, sexo y edad1971.xlsx', skiprows=5)
    defun = pd.read_excel('datasets/Defunciones1975.xlsx', skiprows=6)
    naci = pd.read_excel('datasets/Nacimientos1975.xlsx', skiprows=6)
    inmig = pd.read_excel('datasets/Flujo de inmigracion procedente del extranjero por año, sexo y edad2008.xlsx', skiprows=5)
    return pob, defun, naci, inmig

pob_df_raw, defun_df_raw, naci_df_raw, inmig_df_raw = cargar_datos()

# ---------------------------
# TRATAMIENTO DE DATOS
# ---------------------------

# Defunciones
defun_df_raw = defun_df_raw.iloc[:, :50]
defun_df_raw.columns = defun_df_raw.iloc[0]
defun_df_raw = defun_df_raw.drop(index=0).reset_index(drop=True)
defun_df_raw_g = defun_df_raw.iloc[[0]].reset_index(drop=True)
valid_cols = [col for col in defun_df_raw_g.columns if str(col).strip().replace('.0', '').isdigit() and len(str(int(float(col)))) == 4]
defun_df_raw_g = defun_df_raw_g[valid_cols]
defun_df_raw_g.columns = pd.to_datetime([str(int(float(col))) for col in defun_df_raw_g.columns], format='%Y')
defun_df_raw_g = defun_df_raw_g.T
defun_df_raw_g.columns = ['Defunciones']
defun_df_raw_g.index.name = 'Años'

# Nacimientos
naci_df_raw = naci_df_raw.iloc[:, :50]
naci_df_raw.columns = naci_df_raw.iloc[0]
naci_df_raw = naci_df_raw.drop(index=0).reset_index(drop=True)
naci_df_raw_g = naci_df_raw.iloc[[0]].reset_index(drop=True)
valid_cols = [col for col in naci_df_raw_g.columns if str(col).strip().replace('.0', '').isdigit() and len(str(int(float(col)))) == 4]
naci_df_raw_g = naci_df_raw_g[valid_cols]
naci_df_raw_g.columns = pd.to_datetime([str(int(float(col))) for col in naci_df_raw_g.columns], format='%Y')
naci_df_raw_g = naci_df_raw_g.T
naci_df_raw_g.columns = ['Nacimientos']
naci_df_raw_g.index.name = 'Años'

# Inmigración
fechas = inmig_df_raw.iloc[0, 1:].tolist()
inmig_df_raw.columns = ['Sexo/Grupo de edad'] + fechas
inmig_df_raw = inmig_df_raw.drop(index=[0, 1]).reset_index(drop=True)
img_df_filtered_g = inmig_df_raw.iloc[0:1].copy()
img_df_transpuesto_g = img_df_filtered_g.set_index('Sexo/Grupo de edad').transpose().reset_index()
img_df_transpuesto_g.columns = ['Años', 'Inmigrantes']
img_df_transpuesto_g['Años'] = pd.to_datetime(img_df_transpuesto_g['Años'].astype(float).astype(int).astype(str), format='%Y')
img_df_transpuesto_g = img_df_transpuesto_g.set_index('Años')

# Población
fechas = pob_df_raw.iloc[0, 1:].tolist()
pob_df_raw.columns = ['Sexo/Grupo de edad'] + fechas
pob_df_raw = pob_df_raw.drop(index=[0, 1]).reset_index(drop=True)
pob_df_filtered_g = pob_df_raw.iloc[0:3].copy()
pob_df_transpuesto_g = pob_df_filtered_g.set_index('Sexo/Grupo de edad').transpose().reset_index()
pob_df_transpuesto_g.columns = ['Años', 'Ambos sexos', 'Hombres', 'Mujeres']
pob_df_transpuesto_g['Años'] = pd.to_datetime(pob_df_transpuesto_g['Años'], format='%d de %B de %Y', errors='coerce')
pob_df_transpuesto_g = pob_df_transpuesto_g.set_index('Años')

# Eliminar duplicados de índices
for df_temp in [naci_df_raw_g, defun_df_raw_g, img_df_transpuesto_g, pob_df_transpuesto_g]:
    df_temp.drop_duplicates(inplace=True)
    df_temp.dropna(inplace=True)

# Unión
df = pd.concat([naci_df_raw_g, defun_df_raw_g], axis=1)
df = pd.concat([df, img_df_transpuesto_g], axis=1)
df = pd.concat([df, pob_df_transpuesto_g[['Ambos sexos']]], axis=1)
df = df.rename(columns={'Ambos sexos': 'Población'})
df['Inmigrantes'] = df['Inmigrantes'].fillna(0)
df = df[df.index >= '1975']
df.index = pd.to_datetime(df.index)

# Relleno de valores
julio_mask = df.index.month == 7
df.loc[julio_mask, 'Nacimientos'] = df['Nacimientos'].shift(1)[julio_mask]
df.loc[julio_mask, 'Defunciones'] = df['Defunciones'].shift(1)[julio_mask]
df.iloc[-1, df.columns.get_loc('Población')] = df.iloc[-2]['Población']


# ---------------------------
# VISUALIZACIONES
# ---------------------------

st.title("📊 Indicadores Demográficos: Bubble Chart y Heatmap")

# Mostrar última fecha formateada
st.markdown(f"**Último dato disponible:** {fecha_es(df.index.max())}")

st.subheader("🔵 Bubble Chart: Población vs Año (Tamaño = Inmigración, Color = Saldo Natural)")
st.text("Este gráfico representa la población por año, el tamaño indica inmigración, y el color el saldo natural.")

df_bubble = df.copy()
df_bubble['Año'] = df_bubble.index.year
df_bubble = df_bubble.groupby('Año').mean().reset_index()
df_bubble['Saldo Natural'] = df_bubble['Nacimientos'] - df_bubble['Defunciones']
df_bubble = df_bubble.dropna(subset=['Año', 'Población', 'Inmigrantes', 'Saldo Natural'])

if not df_bubble.empty:
    fig_bubble = px.scatter(
        df_bubble,
        x='Año',
        y='Población',
        size='Inmigrantes',
        color='Saldo Natural',
        color_continuous_scale='RdBu',
        labels={'Saldo Natural': 'Saldo Natural'},
        title=''
    )
    fig_bubble.update_traces(marker=dict(line=dict(width=1, color='black')))
    st.plotly_chart(fig_bubble, use_container_width=True)
else:
    st.warning("⚠️ No hay datos para mostrar el bubble chart.")

st.subheader("🌡️ Heatmap de Indicadores Demográficos por Año (Normalizado)")
st.text("Este gráfico muestra la evolución normalizada de nacimientos, defunciones, inmigración y población por año.")

df_heatmap = df.copy().astype(float)
df_heatmap['Año'] = df_heatmap.index.year
df_heatmap = df_heatmap.groupby('Año').mean()

if not df_heatmap.empty:
    df_heatmap_T = df_heatmap.T
    df_heatmap_normalized = df_heatmap_T.apply(
        lambda row: (row - row.min()) / (row.max() - row.min()) if row.max() != row.min() else row * 0,
        axis=1
    ).dropna(how='all')

    if not df_heatmap_normalized.empty:
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=df_heatmap_normalized.values,
            x=df_heatmap_normalized.columns,
            y=df_heatmap_normalized.index,
            colorscale='YlOrBr',
            colorbar=dict(title='Valor Normalizado')
        ))
        fig_heatmap.update_layout(title='', height=600)
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.warning("⚠️ El heatmap quedó vacío tras normalizar.")
else:
    st.warning("⚠️ No hay datos suficientes para construir el heatmap.")
