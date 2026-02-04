import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide", page_title="BI - Entre Hierro y Carbono")

st.title("📊 Reporte Interactivo de Envejecimiento de Inventario")
st.write("Haz clic en las barras para ver el detalle de los SKUs.")

# --- Generar Datos Hipotéticos (Simulación de 500 SKUs) ---
@st.cache_data
def generate_data(num_skus=500):
    np.random.seed(42)
    data = {
        'SKU': [f'SKU-{i:04d}' for i in range(num_skus)],
        'Dias_Ultima_Factura': np.random.randint(0, 730, size=num_skus),
        'Existencia_Actual': np.random.randint(0, 500, size=num_skus),
        'Costo_Unitario': np.round(np.random.uniform(10, 500, size=num_skus), 2),
        'Precio_Venta_Unitario': np.round(np.random.uniform(15, 750, size=num_skus), 2),
        'Cliente_Mas_Reciente': np.random.choice([f'Cliente_{chr(65+i)}' for i in range(10)], size=num_skus),
        'Fecha_Ultima_Compra': pd.to_datetime('2023-01-01') + pd.to_timedelta(np.random.randint(0, 365*2, size=num_skus), unit='D')
    }
    df = pd.DataFrame(data)
    df['Utilidad_Unitaria'] = df['Precio_Venta_Unitario'] - df['Costo_Unitario']
    df['Margen_Utilidad_Porcentaje'] = np.round((df['Utilidad_Unitaria'] / df['Precio_Venta_Unitario']) * 100, 2)
    return df

df_inventario = generate_data()

# --- Definir los rangos (Buckets) de Antigüedad ---
bins = [0, 90, 180, 365, 730, float('inf')]
labels = ['0-3 Meses (Activo)', '3-6 Meses (Monitoreo)', '6-12 Meses (Riesgo)', '12-24 Meses (Obsoleto)', '+24 Meses (Crítico)']

df_inventario['Categoria_Antiguedad'] = pd.cut(
    df_inventario['Dias_Ultima_Factura'], 
    bins=bins, 
    labels=labels, 
    include_lowest=True,
    right=False
)

# --- Preparar datos para el histograma ---
df_conteo = df_inventario['Categoria_Antiguedad'].value_counts().reset_index()
df_conteo.columns = ['Categoria_Antiguedad', 'Cantidad_SKUs']
df_conteo['Categoria_Antiguedad'] = pd.Categorical(df_conteo['Categoria_Antiguedad'], categories=labels, ordered=True)
df_conteo = df_conteo.sort_values('Categoria_Antiguedad')

# --- Colores Semáforo ---
colores_semaforo = {
    '0-3 Meses (Activo)': '#2ECC71',
    '3-6 Meses (Monitoreo)': '#F1C40F',
    '6-12 Meses (Riesgo)': '#E67E22',
    '12-24 Meses (Obsoleto)': '#E74C3C',
    '+24 Meses (Crítico)': '#C0392B'
}

# --- Histograma con Plotly ---
fig = px.bar(
    df_conteo, 
    x='Categoria_Antiguedad', 
    y='Cantidad_SKUs',
    title='Distribución de Antigüedad de Inventario (Aging Report)',
    labels={'Categoria_Antiguedad': 'Tiempo desde la última factura', 'Cantidad_SKUs': 'Cantidad de SKUs'},
    color='Categoria_Antiguedad',
    color_discrete_map=colores_semaforo,
    text='Cantidad_SKUs',
    height=500
)

fig.update_traces(texttemplate='%{text}', textposition='outside')
fig.update_layout(
    xaxis_tickangle=-45,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white')
)

# --- MOSTRAR GRÁFICO Y CAPTURAR EVENTO (CORRECCIÓN AQUÍ) ---
# Usamos on_select="rerun" para que Streamlit detecte la selección
event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="aging_chart")

# --- LÓGICA DE DETALLE ---
if event and "selection" in event and event["selection"]["points"]:
    # Extraemos el valor del eje X del punto seleccionado
    categoria_seleccionada = event["selection"]["points"][0]["x"]
    
    st.divider()
    st.subheader(f"🔍 Detalle Maestro: {categoria_seleccionada}")
    
    df_detalle = df_inventario[df_inventario['Categoria_Antiguedad'] == categoria_seleccionada].copy()
    
    columnas_display = [
        'SKU', 'Existencia_Actual', 'Costo_Unitario', 'Precio_Venta_Unitario',
        'Utilidad_Unitaria', 'Margen_Utilidad_Porcentaje',
        'Dias_Ultima_Factura', 'Fecha_Ultima_Compra', 'Cliente_Mas_Reciente'
    ]
    
    if not df_detalle.empty:
        # Métricas rápidas arriba de la tabla
        c1, c2, c3 = st.columns(3)
        c1.metric("SKUs en Categoría", len(df_detalle))
        c2.metric("Inversión Total", f"${(df_detalle['Existencia_Actual'] * df_detalle['Costo_Unitario']).sum():,.2f}")
        c3.metric("Margen Promedio", f"{df_detalle['Margen_Utilidad_Porcentaje'].mean():.2f}%")

        st.dataframe(
            df_detalle[columnas_display].sort_values('Dias_Ultima_Factura', ascending=False), 
            use_container_width=True,
            hide_index=True
        )
        
        # Insights condicionales
        if "Crítico" in categoria_seleccionada:
            st.error("⚠️ **Acción Comercial Requerida:** Productos con nula rotación. Se recomienda remate o devolución a proveedor para liberar flujo.")
        elif "Activo" in categoria_seleccionada:
            st.success("✅ **Estado Óptimo:** Productos con alta rotación. Revisar que los puntos de reorden estén actualizados.")
    else:
        st.info("No hay datos para esta selección.")
else:
    st.info("👆 Selecciona una barra del gráfico para desplegar el análisis de SKUs, utilidad y existencias.")