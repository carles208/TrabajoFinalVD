import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go



# Función para parsear fechas en español sin locale
def parse_spanish_date(date_str):
    """Parsea fechas en formato español sin usar locale"""
    if pd.isna(date_str):
        return pd.NaT
    
    months_es = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    try:
        # Formato esperado: "1 de enero de 2020"
        parts = str(date_str).lower().split(' de ')
        if len(parts) == 3:
            day = parts[0].strip()
            month = months_es.get(parts[1].strip(), '01')
            year = parts[2].strip()
            return pd.to_datetime(f"{year}-{month}-{day.zfill(2)}")
    except:
        pass
    
    return pd.NaT

@st.cache_data
def cargar_datos():
    try:
        pob = pd.read_excel('datasets/Poblacion residente por fecha, sexo y edad1971.xlsx', skiprows=5)
        defun = pd.read_excel('datasets/Defunciones1975.xlsx', skiprows=6)
        naci = pd.read_excel('datasets/Nacimientos1975.xlsx', skiprows=6)
        inmig = pd.read_excel('datasets/Flujo de inmigracion procedente del extranjero por año, sexo y edad2008.xlsx', skiprows=5)
        return pob, defun, naci, inmig
    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos: {e}")
        st.info("Asegúrate de que la carpeta 'datasets' esté en el directorio raíz de tu repositorio")
        return None, None, None, None

# Verificar que los datos se carguen correctamente
data_loaded = cargar_datos()
if data_loaded[0] is None:
    st.stop()

pob_df_raw, defun_df_raw, naci_df_raw, inmig_df_raw = data_loaded

# ---------------------------
# TRATAMIENTO DE DATOS
# ---------------------------

try:
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

    # Población - usando función personalizada para fechas en español
    fechas = pob_df_raw.iloc[0, 1:].tolist()
    pob_df_raw.columns = ['Sexo/Grupo de edad'] + fechas
    pob_df_raw = pob_df_raw.drop(index=[0, 1]).reset_index(drop=True)
    pob_df_filtered_g = pob_df_raw.iloc[0:3].copy()
    pob_df_transpuesto_g = pob_df_filtered_g.set_index('Sexo/Grupo de edad').transpose().reset_index()
    pob_df_transpuesto_g.columns = ['Años', 'Ambos sexos', 'Hombres', 'Mujeres']
    
    # Aplicar la función personalizada para parsear fechas
    pob_df_transpuesto_g['Años'] = pob_df_transpuesto_g['Años'].apply(parse_spanish_date)
    pob_df_transpuesto_g = pob_df_transpuesto_g.set_index('Años')

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
    if julio_mask.any():
        df.loc[julio_mask, 'Nacimientos'] = df['Nacimientos'].shift(1)[julio_mask]
        df.loc[julio_mask, 'Defunciones'] = df['Defunciones'].shift(1)[julio_mask]
    
    # Verificar que hay datos antes de acceder al último elemento
    if len(df) > 1:
        df.iloc[-1, df.columns.get_loc('Población')] = df.iloc[-2]['Población']

    # ---------------------------
    # VISUALIZACIONES
    # ---------------------------

    st.title("📊 Indicadores Demográficos: Bubble Chart y Heatmap")
    st.subheader("🔵 Bubble Chart: Población vs Año (Tamaño = Inmigración, Color = Saldo Natural)")
    st.text("La primera gráfica (Bubble Chart) muestra de forma más sencilla este estancamiento y leve crecimiento a través de la representación de la inmigración mediante el tamaño de las burbujas y la diferencia entre nacimiento y defunciones (Saldo Natural) mediante su color.")
    
    # Bubble Chart
    df_bubble = df.copy()
    df_bubble['Año'] = df_bubble.index.year
    df_bubble = df_bubble.groupby('Año').mean().reset_index()
    df_bubble = df_bubble[df_bubble['Año'] >= 2005]
    df_bubble['Saldo Natural'] = df_bubble['Nacimientos'] - df_bubble['Defunciones']

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
        st.warning("⚠️ No hay datos suficientes para el Bubble Chart.")

    st.subheader("🌡️ Heatmap de Indicadores Demográficos por Año (Normalizado)")
    st.text("La segunda gráfica muestra mediante un heatmap como las defunciones y la inmigración aumentan a " \
    "lo largo del tiempo, como la natalidad decrementa y, como se ha comentado a lo largo del trabajo, como estas variables " \
    "afectan al aumento y estancamiento de la población.")

    # Heatmap
    df_heatmap = df.copy().astype(float)
    df_heatmap['Año'] = df_heatmap.index.year
    df_heatmap = df_heatmap.groupby('Año').mean()

    if not df_heatmap.empty:
        df_heatmap_T = df_heatmap.T

        df_heatmap_normalized = df_heatmap_T.apply(
            lambda row: (row - row.min()) / (row.max() - row.min()) if row.max() != row.min() else row * 0,
            axis=1
        )

        df_heatmap_normalized = df_heatmap_normalized.dropna(how='all')

        if not df_heatmap_normalized.empty:
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=df_heatmap_normalized.values,
                x=df_heatmap_normalized.columns,
                y=df_heatmap_normalized.index,
                colorscale='YlOrBr',
                colorbar=dict(title='Valor Normalizado')
            ))
            fig_heatmap.update_layout(
                title='',
                height=600
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.warning("⚠️ El heatmap quedó vacío tras normalizar.")
    else:
        st.warning("⚠️ No hay datos suficientes para construir el heatmap.")

except Exception as e:
    st.error(f"Error en el procesamiento de datos: {e}")
    st.info("Verifica que los archivos Excel tengan el formato esperado.")