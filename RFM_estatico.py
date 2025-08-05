import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, dendrogram
import numpy as np

st.set_page_config(page_title="Dashboard RFM Avanzado", layout="wide")
st.title("📊 Dashboard RFM Avanzado con Insights y Estrategias")

uploaded_file = st.file_uploader("Sube tu archivo Excel (con Transaction Data)", type=["xlsx"])

if uploaded_file:
    # ✅ Cargar y preparar datos
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Hr transacc'] = pd.to_datetime(df['Hr transacc'], format='%H:%M:%S', errors='coerce').dt.hour

    st.subheader("📌 Vista previa de datos")
    st.dataframe(df.head())

    # ✅ Filtros dinámicos
    st.sidebar.header("🔍 Filtros")
    establecimientos = st.sidebar.multiselect("Selecciona Establecimientos", options=df['Establecimiento'].unique(), default=list(df['Establecimiento'].unique()))
    rango_hora = st.sidebar.slider("Selecciona Rango de Horas", 0, 23, (0, 23))

    df_filtered = df[(df['Establecimiento'].isin(establecimientos)) & (df['Hr transacc'].between(rango_hora[0], rango_hora[1]))]

    # ✅ Calcular RFM
    current_date = pd.to_datetime('2015-12-31')
    rfm_df = df_filtered.groupby('Customer ID').agg({
        'Order Date': lambda x: (current_date - x.max()).days,
        'Customer ID': 'count',
        'Sales': 'sum'
    })
    rfm_df.rename(columns={'Order Date': 'Recency', 'Customer ID': 'Frequency', 'Sales': 'Monetary'}, inplace=True)
    rfm_df['Recency'] = rfm_df['Recency'].astype(int)

    # ✅ Calcular cuantiles
    quantiles = rfm_df.quantile(q=[0.20, 0.40, 0.60, 0.80]).to_dict()

    def r_score(x, p, d):
        if x <= d[p][0.20]: return 5
        elif x <= d[p][0.40]: return 4
        elif x <= d[p][0.60]: return 3
        elif x <= d[p][0.80]: return 2
        else: return 1

    def fm_score(x, p, d):
        if x <= d[p][0.20]: return 1
        elif x <= d[p][0.40]: return 2
        elif x <= d[p][0.60]: return 3
        elif x <= d[p][0.80]: return 4
        else: return 5

    rfm_df['R'] = rfm_df['Recency'].apply(r_score, args=('Recency', quantiles,))
    rfm_df['F'] = rfm_df['Frequency'].apply(fm_score, args=('Frequency', quantiles,))
    rfm_df['M'] = rfm_df['Monetary'].apply(fm_score, args=('Monetary', quantiles,))
    rfm_df['RFM Score'] = rfm_df['R'] + rfm_df['F'] + rfm_df['M']

    st.subheader("📊 Tabla RFM con Puntajes")
    st.dataframe(rfm_df.head())

    # ✅ Botón de descarga
    csv = rfm_df.to_csv().encode('utf-8')
    st.download_button("⬇ Descargar Segmentación RFM", data=csv, file_name="rfm_segmentacion.csv", mime="text/csv")

    rfm_por_est = df_filtered.merge(rfm_df, on="Customer ID").groupby("Establecimiento")['RFM Score'].mean().sort_values()

    # ✅ 4 Gráficos: R, F, M y RFM Score por Establecimiento
    st.subheader("📈 Distribución de R, F, M y RFM Score por Establecimiento")
    fig, axes = plt.subplots(1, 4, figsize=(24, 5))

    sns.histplot(rfm_df['Recency'], bins=20, kde=True, color='skyblue', ax=axes[0])
    axes[0].set_title('Recency')

    sns.histplot(rfm_df['Frequency'], bins=20, kde=True, color='salmon', ax=axes[1])
    axes[1].set_title('Frequency')

    sns.histplot(rfm_df['Monetary'], bins=20, kde=True, color='green', ax=axes[2])
    axes[2].set_title('Monetary')

    # Nuevo: RFM Score promedio por Establecimiento
    rfm_por_est = df_filtered.merge(rfm_df, on="Customer ID").groupby("Establecimiento")['RFM Score'].mean().sort_values()
    axes[3].bar(rfm_por_est.index, rfm_por_est.values, color=sns.color_palette("magma", len(rfm_por_est)))
    axes[3].set_title('RFM Score Promedio por Establecimiento')
    axes[3].set_xticklabels(rfm_por_est.index, rotation=45)
    axes[3].set_ylabel('Score Promedio')

    st.pyplot(fig)

    # ✅ Heatmap de correlación
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔥 Heatmap de Correlación")
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        sns.heatmap(rfm_df[['Recency', 'Frequency', 'Monetary']].corr(), annot=True, cmap='coolwarm', ax=ax2)
        st.pyplot(fig2)

    # ✅ Dendrograma Normal
    with col2:
        st.subheader("🔗 Dendrograma (Clusters RFM)")
        linkage_matrix = linkage(rfm_df[['Recency', 'Frequency', 'Monetary']], method='ward')
        fig_dendo, ax_dendo = plt.subplots(figsize=(6, 5))
        dendrogram(linkage_matrix, truncate_mode='lastp', p=12, leaf_rotation=45, leaf_font_size=10, show_contracted=True, ax=ax_dendo)
        ax_dendo.set_title("Clusters Jerárquicos de Clientes")
        st.pyplot(fig_dendo)

    # ✅ Ventas por Establecimiento (en %)
    st.subheader("🏪 Ventas por Establecimiento (%)")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum()
    ventas_pct = (ventas_est / ventas_est.sum()) * 100
    fig4, ax4 = plt.subplots(figsize=(8, 5))
    sns.barplot(x=ventas_pct.index, y=ventas_pct.values, palette='viridis', ax=ax4)
    ax4.set_ylabel('% Ventas')
    st.pyplot(fig4)

    # ✅ 4 gráficos individuales por Establecimiento (Ventas por Hora)
    st.subheader("🕒 Distribución de Ventas por Hora (por Establecimiento)")
    est_seleccionados = establecimientos[:4]
    fig_dist, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for i, est in enumerate(est_seleccionados):
        data_est = df_filtered[df_filtered['Establecimiento'] == est].groupby('Hr transacc')['Sales'].sum()
        axes[i].bar(data_est.index, data_est.values, color=sns.color_palette("viridis", len(est_seleccionados))[i])
        axes[i].set_title(f"Ventas por Hora - {est}")
        axes[i].set_xlabel("Hora")
        axes[i].set_ylabel("Ventas")
        axes[i].set_xticks(range(0, 24, 2))

    for j in range(i + 1, 4):
        fig_dist.delaxes(axes[j])

    plt.tight_layout()
    st.pyplot(fig_dist)

    # ✅ Estrategias dinámicas
    st.subheader("📢 Estrategias Generadas")
    estrategias = []
    for est in establecimientos:
        for hora in range(rango_hora[0], rango_hora[1]+1):
            estrategias.append({
                'Establecimiento': est,
                'Hora': f"{hora}:00",
                'Estrategia': f"Promoción especial en {est} durante {hora}:00 para clientes VIP"
            })
    df_estrategias = pd.DataFrame(estrategias)
    st.dataframe(df_estrategias)

    csv_estrategias = df_estrategias.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Descargar Estrategias", data=csv_estrategias, file_name="estrategias_marketing.csv", mime="text/csv")
