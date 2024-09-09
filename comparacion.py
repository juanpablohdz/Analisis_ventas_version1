
import pandas as pd
import plotly.express as px
import streamlit as st

# Cargar el archivo CSV
df_melted = pd.read_csv(r'datos_pivoteados_fecha.csv')

# Convertir la columna 'Mes' a formato de fecha
df_melted['Mes'] = pd.to_datetime(df_melted['Mes'])

# Convertir la columna 'Ventas' a numérico, forzando errores a NaN
df_melted['Ventas'] = pd.to_numeric(df_melted['Ventas'], errors='coerce')

# Eliminar la columna 'TABLA_VERDAD' si existe
if 'TABLA_VERDAD' in df_melted.columns:
    df_melted = df_melted.drop(columns=['TABLA_VERDAD'])

# Convertir la columna SKU a string
df_melted['SKU'] = df_melted['SKU'].astype(str)

# Título de la aplicación con la imagen
st.set_page_config(page_title="Análisis de Ventas", page_icon=":bar_chart:")
col1, col2 = st.columns([1, 6])  # Ajusta el tamaño de las columnas según sea necesario
with col1:
    st.image(r'Rfp.png', use_column_width=True)
with col2:
    st.title('ANÁLISIS DE VENTA')

# Selección de columnas a mostrar
columnas_disponibles = [
    'SUB_CADENA_NOMBRE', 'ID_MOTOR', 'ID_FARMACIA', 'SKU', 'COSTO_RFP_SYS', 
    'NOMBRE_FARMACIA', 'DESCRIPCION', 'ABCD_MOTOR', 'PVD_MOTOR', 'INVENTARIO_SUCURSAL', 
    'VENTA_30_DIAS', 'VENTA_90_DIAS', 'capacity', 'Mes', 'Ventas'
]
columnas_seleccionadas = st.multiselect('Selecciona las columnas a mostrar:', columnas_disponibles, default=['SUB_CADENA_NOMBRE', 'DESCRIPCION', 'Mes', 'Ventas'])

# Filtro de farmacias
farmacias = df_melted['SUB_CADENA_NOMBRE'].unique()
farmacia_seleccionada = st.selectbox('Selecciona una farmacia:', farmacias)

# Filtro de capacity
capacidades = df_melted['capacity'].unique()
capacity_seleccionada = st.selectbox('Selecciona un capacity:', capacidades)

# Sincronización de SKU y descripción
skus = df_melted['SKU'].unique()
descripciones = df_melted['DESCRIPCION'].unique()

df_filtrado_capacity = df_melted[df_melted['capacity'] == capacity_seleccionada]

# Crear un diccionario para mapear SKU a Descripción y viceversa
sku_to_desc = df_melted.set_index('SKU')['DESCRIPCION'].to_dict()
desc_to_sku = df_melted.set_index('DESCRIPCION')['SKU'].to_dict()

# Inicializar st.session_state si no está ya definido
if 'sku' not in st.session_state:
    st.session_state.sku = None
if 'descripcion' not in st.session_state:
    st.session_state.descripcion = None

# Combinar los filtros de SKU y Descripción
search_options = [f"{sku}: {desc}" for sku, desc in sku_to_desc.items()] + list(descripciones)
search_selection = st.selectbox('Selecciona un SKU o una Descripción:', search_options)

# Actualizar SKU y Descripción a partir de la selección combinada
if search_selection:
    if ':' in search_selection:  # Si la selección incluye un SKU
        sku_seleccionado = search_selection.split(':')[0]
        st.session_state.sku = sku_seleccionado
        st.session_state.descripcion = sku_to_desc.get(sku_seleccionado, '')
    else:  # Si la selección es solo una descripción
        st.session_state.descripcion = search_selection
        st.session_state.sku = desc_to_sku.get(search_selection, '')

# Filtrar datos por farmacia, SKU, y Descripción
df_filtrado = df_melted[
    (df_melted['SUB_CADENA_NOMBRE'] == farmacia_seleccionada) &
    (df_melted['SKU'] == st.session_state.sku) &
    (df_melted['DESCRIPCION'] == st.session_state.descripcion)
]

# Encontrar cadenas donde se encuentra el SKU o Descripción
cadenas_con_sku = df_melted[df_melted['SKU'] == st.session_state.sku]['SUB_CADENA_NOMBRE'].unique()
cadenas_con_desc = df_melted[df_melted['DESCRIPCION'] == st.session_state.descripcion]['SUB_CADENA_NOMBRE'].unique()

# Mostrar cadenas donde se encuentra el SKU y la Descripción
if st.session_state.sku and st.session_state.descripcion:
    st.write(f"El SKU {st.session_state.sku} se encuentra en las siguientes cadenas: {', '.join(cadenas_con_sku)}")
    st.write(f"La descripción '{st.session_state.descripcion}' se encuentra en las siguientes cadenas: {', '.join(cadenas_con_desc)}")

# Mostrar los datos filtrados
df_muestra = df_filtrado[columnas_seleccionadas]
st.write(f"Datos filtrados para la farmacia: {farmacia_seleccionada}, SKU: {st.session_state.sku}, Descripción: {st.session_state.descripcion}")

# Verificar si hay datos filtrados
if df_muestra.empty:
    st.write("No se encontraron datos para los filtros seleccionados.")

st.dataframe(df_muestra)

# Agrupar por mes para la farmacia seleccionada
df_grouped = df_filtrado.groupby('Mes').agg({'Ventas': 'sum'}).reset_index()

# Gráfica de ventas mensuales para la farmacia seleccionada
if 'Ventas' in columnas_seleccionadas:
    fig_ventas = px.line(df_grouped, x='Mes', y='Ventas', title=f'Ventas Mensuales para {st.session_state.descripcion}', labels={'Ventas': 'Ventas (Unidades)'})
    # Agregar anotaciones a cada punto
    fig_ventas.update_traces(mode='lines+markers+text', text=df_grouped['Ventas'], textposition='top center')
    # Ajustar diseño
    fig_ventas.update_layout(
        width=800, height=400,
        xaxis_title='Mes',
        yaxis_title='Ventas (Unidades)',
        xaxis_tickformat='%Y-%m',
        xaxis_dtick='M1'
    )

# Nueva gráfica: Ventas por Farmacia en línea
df_ventas_por_farmacia = df_melted[df_melted['SUB_CADENA_NOMBRE'] == farmacia_seleccionada]
df_ventas_por_farmacia_grouped = df_ventas_por_farmacia.groupby('Mes').agg({'Ventas': 'sum'}).reset_index()
fig_ventas_farmacia = px.line(df_ventas_por_farmacia_grouped, x='Mes', y='Ventas', title=f'Ventas por Farmacia: {farmacia_seleccionada}', labels={'Ventas': 'Ventas (Unidades)'})
# Agregar anotaciones a cada punto
fig_ventas_farmacia.update_traces(mode='lines+markers+text', text=df_ventas_por_farmacia_grouped['Ventas'], textposition='top center')
# Ajustar diseño
fig_ventas_farmacia.update_layout(
    width=800, height=400,
    xaxis_title='Mes',
    yaxis_title='Ventas (Unidades)',
    xaxis_tickformat='%Y-%m',
    xaxis_dtick='M1'
)

# Gráfica de ventas mensuales totales
df_grouped_total = df_melted.groupby('Mes').agg({'Ventas': 'sum'}).reset_index()
fig_ventas_total = px.line(df_grouped_total, x='Mes', y='Ventas', title='Ventas Mensuales Totales', labels={'Ventas': 'Ventas (Unidades)'})
# Agregar anotaciones a cada punto
fig_ventas_total.update_traces(mode='lines+markers+text', text=df_grouped_total['Ventas'], textposition='top center')
# Ajustar diseño
fig_ventas_total.update_layout(
    width=800, height=400,
    xaxis_title='Mes',
    yaxis_title='Ventas (Unidades)',
    xaxis_tickformat='%Y-%m',
    xaxis_dtick='M1'
)

# Mostrar gráficas juntas en 2 filas
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_ventas_farmacia, use_container_width=True)
with col2:
    st.plotly_chart(fig_ventas, use_container_width=True)

# Mostrar gráfica de ventas mensuales totales en una fila separada
st.plotly_chart(fig_ventas_total, use_container_width=True)

# Filtro de capacity
df_grouped_capacity = df_filtrado_capacity.groupby('Mes').agg({'Ventas': 'sum'}).reset_index()
df_muestra_capacity = df_filtrado_capacity[columnas_seleccionadas]

# Gráfica de ventas por capacity
fig_ventas_capacity = px.line(df_grouped_capacity, x='Mes', y='Ventas', title=f'Ventas Mensuales para Capacity {capacity_seleccionada}', labels={'Ventas': 'Ventas (Unidades)'})
# Agregar anotaciones a cada punto
fig_ventas_capacity.update_traces(mode='lines+markers+text', text=df_grouped_capacity['Ventas'], textposition='top center')
# Ajustar diseño
fig_ventas_capacity.update_layout(
    width=800, height=400,
    xaxis_title='Mes',
    yaxis_title='Ventas (Unidades)',
    xaxis_tickformat='%Y-%m',
    xaxis_dtick='M1'
)

# Mostrar gráfica de ventas por capacity
st.plotly_chart(fig_ventas_capacity, use_container_width=True)
