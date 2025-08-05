import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import scipy
from scipy.cluster.hierarchy import linkage, dendrogram

st.set_page_config(page_title="Dashboard RFM Avanzado", layout="wide")
st.title("📊 Dashboard Interactivo: RFM + Estrategias + Insights")

uploaded_file = st.file_uploader("Sube tu archivo Excel (con Transaction Data)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Hr transacc'] = pd.to_datetime(df['Hr transacc'], format='%H:%M:%S', errors='coerce').dt.hour

    st.subheader("📌 Vista previa de datos")
    st.dataframe(df.head())

    # Filtros
    st.sidebar.header("🔍 Filtros")
    establecimientos = st.sidebar.multiselect("Selecciona Establecimientos", options=df['Establecimiento'].unique(), default=list(df['Establecimiento'].unique()))
    rango_hora = st.sidebar.slider("Selecciona Rango de Horas", 0, 23, (0, 23))

    df_filtered = df[(df['Establecimiento'].isin(establecimientos)) & (df['Hr transacc'].between(rango_hora[0], rango_hora[1]))]

    # RFM
    current_date = pd.to_datetime('2015-12-31')
    rfm_df = df_filtered.groupby('Customer ID').agg({
        'Order Date': lambda x: (current_date - x.max()).days,
        'Customer ID': 'count',
        'Sales': 'sum'
    })
    rfm_df.rename(columns={'Order Date': 'Recency', 'Customer ID': 'Frequency', 'Sales': 'Monetary'}, inplace=True)
    rfm_df['Recency'] = rfm_df['Recency'].astype(int)

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

    csv = rfm_df.to_csv().encode('utf-8')
    st.download_button("⬇ Descargar Segmentación RFM", data=csv, file_name="rfm_segmentacion.csv", mime="text/csv")

    # Distribuciones
    st.subheader("📈 Distribución de R, F y M")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    sns.histplot(rfm_df['Recency'], bins=20, kde=True, color='skyblue', ax=axes[0])
    axes[0].set_title('Recency')
    sns.histplot(rfm_df['Frequency'], bins=20, kde=True, color='salmon', ax=axes[1])
    axes[1].set_title('Frequency')
    sns.histplot(rfm_df['Monetary'], bins=20, kde=True, color='green', ax=axes[2])
    axes[2].set_title('Monetary')
    st.pyplot(fig)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔥 Heatmap de Correlación")
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        sns.heatmap(rfm_df[['Recency', 'Frequency', 'Monetary']].corr(), annot=True, cmap='coolwarm', ax=ax2)
        st.pyplot(fig2)

    with col2:
        st.subheader("🔗 Dendrograma")
        linkage_matrix = linkage(rfm_df[['Recency', 'Frequency', 'Monetary']], method='ward')
        fig3, ax3 = plt.subplots(figsize=(5, 4))
        dendrogram(linkage_matrix, truncate_mode='lastp', p=10, leaf_rotation=45, leaf_font_size=10, show_contracted=True)
        st.pyplot(fig3)

    # Ventas por Establecimiento
    st.subheader("🏪 Ventas por Establecimiento")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum()
    ventas_pct = (ventas_est / ventas_est.sum()) * 100
    fig4, ax4 = plt.subplots(figsize=(8, 5))
    sns.barplot(x=ventas_pct.index, y=ventas_pct.values, palette='viridis', ax=ax4)
    ax4.set_ylabel('% Ventas')
    st.pyplot(fig4)

    # Ventas por Hora y Establecimiento
    st.subheader("🕒 Ventas por Hora y Establecimiento")
    pivot_heat = df_filtered.pivot_table(index='Hr transacc', columns='Establecimiento', values='Sales', aggfunc='sum').fillna(0)
    fig5, ax5 = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot_heat, cmap='YlGnBu', ax=ax5)
    st.pyplot(fig5)

    # Estrategias
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
