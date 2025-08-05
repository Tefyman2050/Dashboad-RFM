import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Dashboard RFM Interactivo", layout="wide")

st.title("📊 Dashboard Interactivo: RFM + Insights por Establecimiento y Hora")

# 📌 Subida de archivo
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

    # Aplicar filtros
    df_filtered = df[(df['Establecimiento'].isin(establecimientos)) & (df['Hr transacc'].between(rango_hora[0], rango_hora[1]))]

    # ✅ Calcular RFM
    current_date = pd.to_datetime('2015-12-31')
    rfm_df = df_filtered.groupby('Customer ID').agg({
        'Order Date': lambda x: (current_date - x.max()).days,
        'Customer ID': 'count',
        'Sales': 'sum'
    })
    rfm_df.rename(columns={'Order Date': 'Recency','Customer ID': 'Frequency','Sales': 'Monetary'}, inplace=True)
    rfm_df['Recency'] = rfm_df['Recency'].astype(int)

    # Cuantiles
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

    # ✅ Gráficos interactivos
    st.subheader("📈 Distribución de R, F y M")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    sns.histplot(rfm_df['Recency'], bins=20, kde=True, color='skyblue', ax=axes[0])
    axes[0].set_title('Recency')
    sns.histplot(rfm_df['Frequency'], bins=20, kde=True, color='salmon', ax=axes[1])
    axes[1].set_title('Frequency')
    sns.histplot(rfm_df['Monetary'], bins=20, kde=True, color='green', ax=axes[2])
    axes[2].set_title('Monetary')
    st.pyplot(fig)

    # ✅ Heatmap
    st.subheader("🔥 Correlación entre R, F, M")
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    sns.heatmap(rfm_df[['Recency', 'Frequency', 'Monetary']].corr(), annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=ax2)
    st.pyplot(fig2)

    # ✅ Ventas por Establecimiento
    st.subheader("🏪 Ventas por Establecimiento (filtradas)")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum().sort_values(ascending=False)
    st.bar_chart(ventas_est)

    # ✅ Ventas por Hora
    st.subheader("🕒 Ventas por Hora (filtradas)")
    ventas_hora = df_filtered.groupby('Hr transacc')['Sales'].sum()
    st.line_chart(ventas_hora)

    # ✅ Filtro dinámico de columnas visibles
    st.sidebar.header("🛠 Configuración de Vista")
    columnas_seleccionadas = st.sidebar.multiselect("Selecciona columnas a mostrar en la tabla", options=list(rfm_df.columns), default=list(rfm_df.columns))
    st.subheader("📋 Tabla personalizada")
    st.dataframe(rfm_df[columnas_seleccionadas])
