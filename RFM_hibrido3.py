import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, dendrogram

st.set_page_config(page_title="Dashboard RFM Híbrido", layout="wide")
st.title("📊 Dashboard RFM Híbrido (Interactivo + Estático)")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # ✅ Cargar datos
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Hr transacc'] = pd.to_datetime(df['Hr transacc'], format='%H:%M:%S', errors='coerce').dt.hour

    # ✅ Filtros
    st.sidebar.header("Filtros")
    establecimientos = st.sidebar.multiselect("Establecimientos", df['Establecimiento'].unique(), default=list(df['Establecimiento'].unique()))
    rango_hora = st.sidebar.slider("Rango Horario", 0, 23, (0, 23))

    df_filtered = df[(df['Establecimiento'].isin(establecimientos)) & (df['Hr transacc'].between(rango_hora[0], rango_hora[1]))]

    # ✅ RFM
    current_date = pd.to_datetime('2015-12-31')
    rfm_df = df_filtered.groupby('Customer ID').agg({
        'Order Date': lambda x: (current_date - x.max()).days,
        'Customer ID': 'count',
        'Sales': 'sum'
    }).rename(columns={'Order Date': 'Recency', 'Customer ID': 'Frequency', 'Sales': 'Monetary'})
    rfm_df['Recency'] = rfm_df['Recency'].astype(int)

    # ✅ Scores
    quantiles = rfm_df.quantile(q=[0.20, 0.40, 0.60, 0.80]).to_dict()
    def r_score(x, p, d): return 5 if x <= d[p][0.20] else (4 if x <= d[p][0.40] else (3 if x <= d[p][0.60] else (2 if x <= d[p][0.80] else 1)))
    def fm_score(x, p, d): return 1 if x <= d[p][0.20] else (2 if x <= d[p][0.40] else (3 if x <= d[p][0.60] else (4 if x <= d[p][0.80] else 5)))
    rfm_df['R'] = rfm_df['Recency'].apply(r_score, args=('Recency', quantiles,))
    rfm_df['F'] = rfm_df['Frequency'].apply(fm_score, args=('Frequency', quantiles,))
    rfm_df['M'] = rfm_df['Monetary'].apply(fm_score, args=('Monetary', quantiles,))
    rfm_df['RFM Score'] = rfm_df['R'] + rfm_df['F'] + rfm_df['M']

    st.subheader("📌 Segmentación RFM")
    st.dataframe(rfm_df)

    # ✅ Distribuciones interactivas R, F, M
    st.subheader("📊 Distribuciones R, F, M (Interactivas)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(px.histogram(rfm_df, x='Recency', nbins=20, title="Recency"), use_container_width=True)
    with col2:
        st.plotly_chart(px.histogram(rfm_df, x='Frequency', nbins=20, title="Frequency"), use_container_width=True)
    with col3:
        st.plotly_chart(px.histogram(rfm_df, x='Monetary', nbins=20, title="Monetary"), use_container_width=True)

    # ✅ Ventas por Establecimiento interactivo
    st.subheader("🏪 Ventas por Establecimiento (%)")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum()
    ventas_pct = (ventas_est / ventas_est.sum()) * 100
    fig_est = px.bar(x=ventas_pct.index, y=ventas_pct.values, color=ventas_pct.index, text=ventas_pct.values.round(2),
                     title="Ventas por Establecimiento", labels={'x': 'Establecimiento', 'y': '% Ventas'})
    st.plotly_chart(fig_est, use_container_width=True)

    # ✅ Insight: Mapa Competitivo
    st.subheader("🔥 Insight: Mapa Competitivo (Ventas vs Margen vs RFM Score)")
    df_merged = df_filtered.merge(rfm_df, on="Customer ID")
    df_mapa = df_merged.groupby('Establecimiento').agg({'Monetary': 'sum', 'RFM Score': 'mean'}).reset_index()
    df_mapa['Margen Estimado'] = df_mapa['Monetary'] * 0.3
    fig_map = px.scatter(df_mapa, x='Monetary', y='Margen Estimado', size='RFM Score', color='Establecimiento',
                         title="Mapa Competitivo", labels={'Monetary': 'Ventas', 'Margen Estimado': 'Margen'},
                         hover_data=['Establecimiento'])
    st.plotly_chart(fig_map, use_container_width=True)

    # ✅ Panel Estático 2x2
    st.subheader("🔥 Panel 2x2: Correlación, Clusters y Ventas")
    fig_combined, axes2 = plt.subplots(2, 2, figsize=(14, 10))

    # [0,0] Heatmap correlación
    sns.heatmap(rfm_df[['Recency', 'Frequency', 'Monetary']].corr(), annot=True, cmap='coolwarm', ax=axes2[0, 0])
    axes2[0, 0].set_title('Mapa de Correlación (R, F, M)')

    # [0,1] Dendrograma
    linkage_matrix = linkage(rfm_df[['Recency', 'Frequency', 'Monetary']], method='ward')
    dendrogram(linkage_matrix, truncate_mode='lastp', p=12, leaf_rotation=45, leaf_font_size=10, show_contracted=True, ax=axes2[0, 1])
    axes2[0, 1].set_title('Clusters Jerárquicos (RFM)')

    # [1,0] Ventas por Establecimiento
    axes2[1, 0].bar(ventas_pct.index, ventas_pct.values, color=sns.color_palette("viridis", len(ventas_pct)))
    axes2[1, 0].set_title('Ventas por Establecimiento (%)')
    axes2[1, 0].set_ylabel('% Ventas')

    # [1,1] Ventas por Hora (Global)
    ventas_hora = df_filtered.groupby('Hr transacc')['Sales'].sum()
    axes2[1, 1].plot(ventas_hora.index, ventas_hora.values, marker='o', color='orange')
    axes2[1, 1].set_title('Ventas por Hora (Global)')
    axes2[1, 1].set_xlabel('Hora')
    axes2[1, 1].set_ylabel('Ventas')
    axes2[1, 1].set_xticks(range(0, 24, 2))

    plt.tight_layout()
    st.pyplot(fig_combined)

    # ✅ Insight: Horas Pico vs Valle
    st.subheader("🔥 Insight: Horas de Mayor y Menor Venta")
    horas_pico = ventas_hora.sort_values(ascending=False).head(3)
    horas_valle = ventas_hora.sort_values(ascending=True).head(3)

    st.write(f"Horas de Mayor Venta (Pico): {', '.join(str(h)+':00' for h in horas_pico.index)}")
    st.write(f"Horas de Menor Venta (Valle): {', '.join(str(h)+':00' for h in horas_valle.index)}")
    st.info("💡 Acción: Refuerza inventario en horas pico y lanza promociones en horas valle.")

    # ✅ Ventas por Hora (Scatter solo burbujas)
    st.subheader("📊 Ventas por Hora por Establecimiento (Burbujas)")
    ventas_hora_det = df_filtered.groupby(['Hr transacc', 'Establecimiento'])['Sales'].sum().reset_index()

    fig_hora = px.scatter(
        ventas_hora_det,
        x='Hr transacc',
        y='Sales',
        color='Establecimiento',
        size='Sales',  # Tamaño de burbuja proporcional a ventas
        hover_name='Establecimiento',
        title="Ventas por Hora por Establecimiento"
    )

    # Ajustes estéticos para burbujas
    fig_hora.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
    fig_hora.update_layout(xaxis_title="Hora", yaxis_title="Ventas", legend_title="Establecimiento")

    st.plotly_chart(fig_hora, use_container_width=True)



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
