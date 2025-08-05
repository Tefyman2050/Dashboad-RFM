import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, dendrogram

st.set_page_config(page_title="Dashboard RFM Estático", layout="wide")
st.title("📊 Dashboard RFM Estático con Insights Estratégicos")

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

    # ✅ Calcular RFM
    current_date = pd.to_datetime('2015-12-31')
    rfm_df = df_filtered.groupby('Customer ID').agg({
        'Order Date': lambda x: (current_date - x.max()).days,
        'Customer ID': 'count',
        'Sales': 'sum'
    }).rename(columns={'Order Date': 'Recency', 'Customer ID': 'Frequency', 'Sales': 'Monetary'})
    rfm_df['Recency'] = rfm_df['Recency'].astype(int)

    # ✅ Generar puntajes RFM
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

    # ✅ Panel 2x2: Correlación, Dendrograma, Ventas por Establecimiento y Ventas por Hora
    st.subheader("🔥 Panel Integrado: Correlación, Clusters y Ventas")
    fig_combined, axes2 = plt.subplots(2, 2, figsize=(14, 10))

    # [0,0] Heatmap correlación
    sns.heatmap(rfm_df[['Recency', 'Frequency', 'Monetary']].corr(), annot=True, cmap='coolwarm', ax=axes2[0, 0])
    axes2[0, 0].set_title('Mapa de Correlación (R, F, M)')

    # [0,1] Dendrograma
    linkage_matrix = linkage(rfm_df[['Recency', 'Frequency', 'Monetary']], method='ward')
    dendrogram(linkage_matrix, truncate_mode='lastp', p=12, leaf_rotation=45, leaf_font_size=10, show_contracted=True, ax=axes2[0, 1])
    axes2[0, 1].set_title('Clusters Jerárquicos (RFM)')

    # [1,0] Ventas por Establecimiento
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum()
    ventas_pct = (ventas_est / ventas_est.sum()) * 100
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
    st.subheader("🔥 Insight: Comparativa de Horas de Mayor y Menor Venta")
    horas_pico = ventas_hora.sort_values(ascending=False).head(3)
    horas_valle = ventas_hora.sort_values(ascending=True).head(3)

    fig_pico, ax_pico = plt.subplots(1, 2, figsize=(12, 5))
    horas_pico.plot(kind='bar', color='orange', ax=ax_pico[0])
    ax_pico[0].set_title('Horas de Mayor Venta (Pico)')
    horas_valle.plot(kind='bar', color='gray', ax=ax_pico[1])
    ax_pico[1].set_title('Horas de Menor Venta (Valle)')
    st.pyplot(fig_pico)

    st.markdown(f"""
    **Definiciones:**
    - **Horas de Mayor Venta (Pico):** {', '.join(str(h)+':00' for h in horas_pico.index)}.
    - **Horas de Menor Venta (Valle):** {', '.join(str(h)+':00' for h in horas_valle.index)}.

    💡 **Acción:** Refuerza inventario en horas pico y lanza promociones en horas valle.
    """)

    # ✅ Gráficos por Establecimiento (máximo 4)
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
