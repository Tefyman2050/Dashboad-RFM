import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, dendrogram

st.set_page_config(page_title="Dashboard RFM Estático", layout="wide")
st.title("📊 Dashboard RFM Estático con Insights Estratégicos")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # ✅ Cargar y procesar datos
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Hr transacc'] = pd.to_datetime(df['Hr transacc'], format='%H:%M:%S', errors='coerce').dt.hour

    # ✅ Filtros
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

    # ✅ Scores RFM
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
    st.subheader("Distribuciones R, F, M")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    sns.histplot(rfm_df['Recency'], bins=20, kde=True, color='blue', ax=axes[0])
    axes[0].set_title("Recency")
    sns.histplot(rfm_df['Frequency'], bins=20, kde=True, color='red', ax=axes[1])
    axes[1].set_title("Frequency")
    sns.histplot(rfm_df['Monetary'], bins=20, kde=True, color='green', ax=axes[2])
    axes[2].set_title("Monetary")
    st.pyplot(fig)

    # ✅ Heatmap correlación
    st.subheader("🔥 Correlación entre R, F, M")
    fig_corr, ax_corr = plt.subplots(figsize=(5, 4))
    sns.heatmap(rfm_df[['Recency', 'Frequency', 'Monetary']].corr(), annot=True, cmap='coolwarm', ax=ax_corr)
    st.pyplot(fig_corr)

    # ✅ Insight: Horas de Mayor y Menor Venta
    st.subheader("🔥 Insight: Comparativa de Horas de Mayor y Menor Venta")
    ventas_hora = df_filtered.groupby('Hr transacc')['Sales'].sum()
    horas_pico = ventas_hora.sort_values(ascending=False).head(3)
    horas_valle = ventas_hora.sort_values(ascending=True).head(3)

    fig_pico, ax_pico = plt.subplots(1, 2, figsize=(12, 5))
    horas_pico.plot(kind='bar', color='orange', ax=ax_pico[0])
    ax_pico[0].set_title('Horas de Mayor Venta (Pico)')
    ax_pico[0].set_xlabel('Hora')
    ax_pico[0].set_ylabel('Ventas')

    horas_valle.plot(kind='bar', color='gray', ax=ax_pico[1])
    ax_pico[1].set_title('Horas de Menor Venta (Valle)')
    ax_pico[1].set_xlabel('Hora')
    ax_pico[1].set_ylabel('Ventas')

    st.pyplot(fig_pico)

    st.markdown(f"""
    **Definiciones:**
    - **Horas de Mayor Venta (Pico):** Horas con más ventas. Detectadas: {', '.join(str(h)+':00' for h in horas_pico.index)}.
    - **Horas de Menor Venta (Valle):** Horas con menos ventas. Detectadas: {', '.join(str(h)+':00' for h in horas_valle.index)}.

    💡 **Consejo:** Refuerza inventario en horas pico y lanza promociones agresivas en horas valle.
    """)

    # ✅ Dendrograma
    st.subheader("Clusters Jerárquicos")
    linkage_matrix = linkage(rfm_df[['Recency', 'Frequency', 'Monetary']], method='ward')
    fig_dendo, ax_dendo = plt.subplots(figsize=(8, 5))
    dendrogram(linkage_matrix, truncate_mode='lastp', p=12, leaf_rotation=45, leaf_font_size=10, show_contracted=True, ax=ax_dendo)
    st.pyplot(fig_dendo)

    # ✅ Ventas por Establecimiento (%)
    st.subheader("🏪 Ventas por Establecimiento (%)")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum()
    ventas_pct = (ventas_est / ventas_est.sum()) * 100
    fig_est, ax_est = plt.subplots(figsize=(8, 5))
    sns.barplot(x=ventas_pct.index, y=ventas_pct.values, palette='viridis', ax=ax_est)
    ax_est.set_ylabel('% Ventas')
    st.pyplot(fig_est)

    # ✅ 4 gráficos por hora
    st.subheader("📊 Distribución de Ventas por Hora (por Establecimiento)")
    est_seleccionados = establecimientos[:4]
    fig_dist, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()
    for i, est in enumerate(est_seleccionados):
        data_est = df_filtered[df_filtered['Establecimiento'] == est].groupby('Hr transacc')['Sales'].sum()
        axes[i].bar(data_est.index, data_est.values, color=sns.color_palette("viridis", len(est_seleccionados))[i])
        axes[i].set_title(f"Ventas por Hora - {est}")
        axes[i].set_xticks(range(0, 24, 2))
    for j in range(i+1, 4):
        fig_dist.delaxes(axes[j])
    plt.tight_layout()
    st.pyplot(fig_dist)
