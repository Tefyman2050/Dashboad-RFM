import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, dendrogram

# Configuración de la página
st.set_page_config(page_title="Dashboard RFM Dinámico", layout="wide")
st.title("📊 Dashboard RFM Dinámico con Gráficos Interactivos")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # ✅ Cargar datos
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Hr transacc'] = pd.to_datetime(df['Hr transacc'], format='%H:%M:%S', errors='coerce').dt.hour

    # ✅ Filtros en la barra lateral
    st.sidebar.header("Filtros")
    establecimientos = st.sidebar.multiselect("Establecimientos", df['Establecimiento'].unique(),
                                              default=list(df['Establecimiento'].unique()))
    rango_hora = st.sidebar.slider("Rango Horario", 0, 23, (0, 23))

    # Selectores para tipos de gráficos
    chart_type_hora = st.sidebar.selectbox("Gráfico para Ventas por Hora", ["Línea", "Barras", "Burbujas"])
    chart_type_est = st.sidebar.selectbox("Gráfico para Ventas por Establecimiento", ["Barras", "Pie", "Sunburst"])
    chart_type_map = st.sidebar.selectbox("Gráfico para Mapa Competitivo", ["Burbujas", "Barras"])

    # Filtrar dataset
    df_filtered = df[(df['Establecimiento'].isin(establecimientos)) &
                     (df['Hr transacc'].between(rango_hora[0], rango_hora[1]))]

    # ✅ Cálculo de RFM
    current_date = pd.to_datetime('2015-12-31')
    rfm_df = df_filtered.groupby('Customer ID').agg({
        'Order Date': lambda x: (current_date - x.max()).days,
        'Customer ID': 'count',
        'Sales': 'sum'
    }).rename(columns={'Order Date': 'Recency', 'Customer ID': 'Frequency', 'Sales': 'Monetary'})

    rfm_df['Recency'] = rfm_df['Recency'].astype(int)

    # Calcular puntuaciones RFM
    quantiles = rfm_df.quantile(q=[0.20, 0.40, 0.60, 0.80]).to_dict()
    def r_score(x, p, d): return 5 if x <= d[p][0.20] else (4 if x <= d[p][0.40] else (3 if x <= d[p][0.60] else (2 if x <= d[p][0.80] else 1)))
    def fm_score(x, p, d): return 1 if x <= d[p][0.20] else (2 if x <= d[p][0.40] else (3 if x <= d[p][0.60] else (4 if x <= d[p][0.80] else 5)))

    rfm_df['R'] = rfm_df['Recency'].apply(r_score, args=('Recency', quantiles,))
    rfm_df['F'] = rfm_df['Frequency'].apply(fm_score, args=('Frequency', quantiles,))
    rfm_df['M'] = rfm_df['Monetary'].apply(fm_score, args=('Monetary', quantiles,))
    rfm_df['RFM Score'] = rfm_df['R'] + rfm_df['F'] + rfm_df['M']

    st.subheader("📌 Segmentación RFM")
    st.dataframe(rfm_df)

    # ✅ Distribuciones R, F, M
    st.subheader("📊 Distribuciones R, F, M")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(px.histogram(rfm_df, x='Recency', nbins=20, title="Distribución Recency"), use_container_width=True)
    with col2:
        st.plotly_chart(px.histogram(rfm_df, x='Frequency', nbins=20, title="Distribución Frequency"), use_container_width=True)
    with col3:
        st.plotly_chart(px.histogram(rfm_df, x='Monetary', nbins=20, title="Distribución Monetary"), use_container_width=True)

    # ✅ Ventas por Establecimiento (Dinámico)
    st.subheader("🏪 Ventas por Establecimiento")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum().reset_index()

    if chart_type_est == "Barras":
        fig_est = px.bar(ventas_est, x='Establecimiento', y='Sales', color='Establecimiento', text='Sales', title="Ventas por Establecimiento")
    elif chart_type_est == "Pie":
        fig_est = px.pie(ventas_est, names='Establecimiento', values='Sales', title="Participación por Establecimiento", hole=0.3)
    elif chart_type_est == "Sunburst" and 'Categoria' in df_filtered.columns:
        fig_est = px.sunburst(df_filtered, path=['Establecimiento', 'Categoria'], values='Sales', title="Ventas por Jerarquía")
    else:
        fig_est = px.bar(ventas_est, x='Establecimiento', y='Sales', color='Establecimiento', title="Ventas por Establecimiento")

    st.plotly_chart(fig_est, use_container_width=True)

    # ✅ Mapa Competitivo (Dinámico)
    st.subheader("🔥 Mapa Competitivo")
    df_merged = df_filtered.merge(rfm_df, on="Customer ID")
    df_mapa = df_merged.groupby('Establecimiento').agg({'Monetary': 'sum', 'RFM Score': 'mean'}).reset_index()
    df_mapa['Margen Estimado'] = df_mapa['Monetary'] * 0.3

    if chart_type_map == "Burbujas":
        fig_map = px.scatter(df_mapa, x='Monetary', y='Margen Estimado', size='RFM Score', color='Establecimiento',
                             hover_name='Establecimiento', title="Mapa Competitivo (Burbujas)")
    else:  # Barras
        fig_map = px.bar(df_mapa, x='Establecimiento', y='Monetary', color='Establecimiento', text='Margen Estimado',
                         title="Mapa Competitivo (Barras)")

    st.plotly_chart(fig_map, use_container_width=True)

    # ✅ Ventas por Hora (Dinámico)
    st.subheader("📊 Ventas por Hora por Establecimiento")
    ventas_hora_det = df_filtered.groupby(['Hr transacc', 'Establecimiento'])['Sales'].sum().reset_index()

    if chart_type_hora == "Línea":
        fig_hora = px.line(ventas_hora_det, x='Hr transacc', y='Sales', color='Establecimiento', title="Ventas por Hora (Línea)")
    elif chart_type_hora == "Barras":
        fig_hora = px.bar(ventas_hora_det, x='Hr transacc', y='Sales', color='Establecimiento', barmode='group', title="Ventas por Hora (Barras)")
    else:  # Burbujas
        fig_hora = px.scatter(ventas_hora_det, x='Hr transacc', y='Sales', color='Establecimiento', size='Sales',
                              hover_name='Establecimiento', title="Ventas por Hora (Burbujas)")
        fig_hora.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))

    fig_hora.update_layout(xaxis_title="Hora", yaxis_title="Ventas", legend_title="Establecimiento")
    st.plotly_chart(fig_hora, use_container_width=True)

    # ✅ Insight: Horas Pico vs Valle
    st.subheader("🔥 Insight: Horas Pico y Horas Valle")
    ventas_hora = df_filtered.groupby('Hr transacc')['Sales'].sum()
    horas_pico = ventas_hora.sort_values(ascending=False).head(3)
    horas_valle = ventas_hora.sort_values(ascending=True).head(3)
    st.write(f"Horas Pico: {', '.join(str(h)+':00' for h in horas_pico.index)}")
    st.write(f"Horas Valle: {', '.join(str(h)+':00' for h in horas_valle.index)}")
    st.info("💡 Estrategia: Refuerza inventario en horas pico y lanza promociones en horas valle.")

    # ✅ Estrategias dinámicas
    st.subheader("📢 Estrategias sugeridas")
    estrategias = []
    for est in establecimientos:
        for hora in range(rango_hora[0], rango_hora[1]+1):
            estrategias.append({'Establecimiento': est, 'Hora': f"{hora}:00", 'Estrategia': f"Promoción en {est} durante {hora}:00"})
    df_estrategias = pd.DataFrame(estrategias)
    st.dataframe(df_estrategias)
    st.download_button("⬇ Descargar Estrategias", data=df_estrategias.to_csv(index=False).encode('utf-8'),
                       file_name="estrategias.csv", mime="text/csv")
