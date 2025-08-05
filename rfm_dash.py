import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="RFM Analysis", layout="wide")
st.title("📊 Análisis RFM con Segmentación y Visualización")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    transactions_df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')

    # Definir fecha de referencia
    current_date = pd.to_datetime('2015-12-31')

    # Calcular Recency, Frequency y Monetary
    rfm_df = transactions_df.groupby('Customer ID').agg({
        'Order Date': lambda x: (current_date - x.max()).days,
        'Customer ID': 'count',
        'Sales': 'sum'
    })
    rfm_df.rename(columns={
        'Order Date': 'Recency',
        'Customer ID': 'Frequency',
        'Sales': 'Monetary'
    }, inplace=True)
    rfm_df['Recency'] = rfm_df['Recency'].astype(int)

    st.subheader("📌 Datos RFM Calculados")
    st.write(rfm_df.head())

    # Calcular cuantiles
    quantiles = rfm_df.quantile(q=[0.20, 0.40, 0.60, 0.80]).to_dict()

    # Funciones para puntuar
    def r_score(x, p, d):
        if x <= d[p][0.20]:
            return 5
        elif x <= d[p][0.40]:
            return 4
        elif x <= d[p][0.60]:
            return 3
        elif x <= d[p][0.80]:
            return 2
        else:
            return 1

    def fm_score(x, p, d):
        if x <= d[p][0.20]:
            return 1
        elif x <= d[p][0.40]:
            return 2
        elif x <= d[p][0.60]:
            return 3
        elif x <= d[p][0.80]:
            return 4
        else:
            return 5

    # Asignar puntajes
    rfm_df['R'] = rfm_df['Recency'].apply(r_score, args=('Recency', quantiles,))
    rfm_df['F'] = rfm_df['Frequency'].apply(fm_score, args=('Frequency', quantiles,))
    rfm_df['M'] = rfm_df['Monetary'].apply(fm_score, args=('Monetary', quantiles,))
    rfm_df['RFM Score'] = rfm_df['R'] + rfm_df['F'] + rfm_df['M']

    st.subheader("📊 Tabla con Puntajes RFM")
    st.write(rfm_df.head())

    # Descargar CSV
    csv = rfm_df.to_csv().encode('utf-8')
    st.download_button("⬇ Descargar Segmentación RFM", data=csv, file_name="rfm_segmentacion.csv", mime="text/csv")

    # Gráficos
    st.subheader("📈 Distribución de R, F y M")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    sns.histplot(rfm_df['Recency'], bins=20, kde=True, color='skyblue', ax=axes[0])
    axes[0].set_title('Distribución de Recency')
    sns.histplot(rfm_df['Frequency'], bins=20, kde=True, color='salmon', ax=axes[1])
    axes[1].set_title('Distribución de Frequency')
    sns.histplot(rfm_df['Monetary'], bins=20, kde=True, color='green', ax=axes[2])
    axes[2].set_title('Distribución de Monetary')
    st.pyplot(fig)

    # Heatmap
    st.subheader("🔥 Correlación entre Recency, Frequency y Monetary")
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    sns.heatmap(rfm_df[['Recency', 'Frequency', 'Monetary']].corr(), annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=ax2)
    ax2.set_title('Correlación entre R, F, M')
    st.pyplot(fig2)
