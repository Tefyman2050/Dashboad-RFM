import pandas as pd
import streamlit as st
import plotly.express as px
from scipy.cluster.hierarchy import linkage, dendrogram
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Dashboard RFM Gerencial", layout="wide")
st.title("📊 Dashboard RFM Gerencial - Análisis Estratégico")

# ✅ Subir archivo
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # ✅ Cargar datos
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Hr transacc'] = pd.to_datetime(df['Hr transacc'], format='%H:%M:%S', errors='coerce').dt.hour

    # ✅ Filtros dinámicos
    st.sidebar.header("Filtros")
    establecimientos = st.sidebar.multiselect("Establecimientos", df['Establecimiento'].unique(), default=list(df['Establecimiento'].unique()))
    rango_hora = st.sidebar.slider("Rango Horario", 0, 23, (0, 23))

    df_filtered = df[(df['Establecimiento'].isin(establecimientos)) & (df['Hr transacc'].between(rango_hora[0], rango_hora[1]))]

    # ✅ Cálculo RFM
    current_date = pd.to_datetime('2015-12-31')
    rfm_df = df_filtered.groupby('Customer ID').agg({
        'Order Date': lambda x: (current_date - x.max()).days,
        'Customer ID': 'count',
        'Sales': 'sum'
    }).rename(columns={'Order Date': 'Recency', 'Customer ID': 'Frequency', 'Sales': 'Monetary'})
    rfm_df['Recency'] = rfm_df['Recency'].astype(int)

    # ✅ Gráficos Interactivos
    st.subheader("📊 Visualizaciones Gerenciales")

    # 1. Barras agrupadas (Ventas por Hora y Establecimiento)
    st.markdown("### Ventas por Hora por Establecimiento")
    ventas_hora_det = df_filtered.groupby(['Hr transacc', 'Establecimiento'])['Sales'].sum().reset_index()
    fig_bar = px.bar(ventas_hora_det, x='Hr transacc', y='Sales', color='Establecimiento', barmode='group',
                     title="Ventas por Hora por Establecimiento")
    st.plotly_chart(fig_bar, use_container_width=True)

    # 2. Pie Chart (Participación por Establecimiento)
    st.markdown("### Participación de Ventas por Establecimiento")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum().reset_index()
    fig_pie = px.pie(ventas_est, names='Establecimiento', values='Sales', title="Participación por Establecimiento", hole=0.3)
    st.plotly_chart(fig_pie, use_container_width=True)

    # 3. Mapa Competitivo (Scatter Burbujas)
    st.markdown("### Mapa Competitivo: Ventas vs Margen vs RFM Score")
    df_merged = df_filtered.merge(rfm_df, on="Customer ID")
    df_mapa = df_merged.groupby('Establecimiento').agg({'Monetary': 'sum', 'RFM Score': 'mean'}).reset_index()
    df_mapa['Margen Estimado'] = df_mapa['Monetary'] * 0.3
    fig_scatter = px.scatter(df_mapa, x='Monetary', y='Margen Estimado', size='RFM Score', color='Establecimiento',
                             hover_name='Establecimiento', size_max=60,
                             title="Mapa Competitivo (Ventas vs Margen vs RFM Score)")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # 4. Sunburst (Jerarquía)
    st.markdown("### Ventas por Jerarquía: Establecimiento → Categoría")
    if 'Categoria' in df_filtered.columns:
        fig_sunburst = px.sunburst(df_filtered, path=['Establecimiento','Categoria'], values='Sales',
                                   title="Ventas por Jerarquía")
        st.plotly_chart(fig_sunburst, use_container_width=True)

    # 5. Heatmap (Horas vs Establecimiento)
    st.markdown("### Mapa de Calor: Ventas por Hora y Establecimiento")
    fig_heatmap = px.density_heatmap(df_filtered, x='Hr transacc', y='Establecimiento', z='Sales', nbinsx=24,
                                     title='Mapa de Calor: Horas vs Establecimiento', color_continuous_scale='Viridis')
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # ✅ Insight: Horas Pico vs Valle
    st.subheader("🔥 Insight: Horas de Mayor y Menor Venta")
    ventas_hora = df_filtered.groupby('Hr transacc')['Sales'].sum()
    horas_pico = ventas_hora.sort_values(ascending=False).head(3)
    horas_valle = ventas_hora.sort_values(ascending=True).head(3)
    st.write(f"**Horas Pico (Mayor Venta):** {', '.join(str(h)+':00' for h in horas_pico.index)}")
    st.write(f"**Horas Valle (Menor Venta):** {', '.join(str(h)+':00' for h in horas_valle.index)}")
    st.info("💡 Estrategia: Refuerza inventario y personal en horas pico. Lanza promociones en horas valle.")

    # ✅ Estrategias dinámicas
    st.subheader("📢 Estrategias sugeridas")
    estrategias = []
    for est in establecimientos:
        for hora in range(rango_hora[0], rango_hora[1]+1):
            estrategias.append({'Establecimiento': est, 'Hora': f"{hora}:00", 'Estrategia': f"Promoción activa en {est} durante {hora}:00"})
    df_estrategias = pd.DataFrame(estrategias)
    st.dataframe(df_estrategias)
    csv_estrategias = df_estrategias.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Descargar Estrategias", data=csv_estrategias, file_name="estrategias.csv", mime="text/csv")
