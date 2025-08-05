# rfm_dashboard.py

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.title("📊 Análisis RFM y Segmentación de Clientes")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')

    rfm = df.groupby('Customer ID').agg({
        'Order Date': lambda x: (pd.Timestamp.now() - x.max()).days,
        'Order ID': 'nunique',
        'Sales': 'sum'
    }).reset_index()
    rfm.columns = ['Customer ID', 'Recency', 'Frequency', 'Monetary']

    rfm['R_score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1])
    rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
    rfm['M_score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5])
    rfm['RFM_Score'] = rfm['R_score'].astype(str)+rfm['F_score'].astype(str)+rfm['M_score'].astype(str)

    def segment(row):
        if row['RFM_Score'] in ['555','554','545','544']:
            return 'Champions'
        elif row['RFM_Score'] in ['543','444','433']:
            return 'Leales'
        elif row['RFM_Score'] in ['111','112','121']:
            return 'En riesgo'
        else:
            return 'Potenciales'
    rfm['Segment'] = rfm.apply(segment, axis=1)

    recommendations = {
        'Champions': 'Ofrecer acceso exclusivo, preventas y programas de fidelización.',
        'Leales': 'Recompensar su fidelidad con descuentos o beneficios adicionales.',
        'Potenciales': 'Enviar campañas atractivas y descuentos iniciales.',
        'En riesgo': 'Lanzar ofertas agresivas y recordatorios personalizados.'
    }
    rfm['Recommendation'] = rfm['Segment'].map(recommendations)

    st.subheader("Vista previa de la segmentación")
    st.dataframe(rfm.head(20))

    st.download_button("Descargar Segmentación", data=rfm.to_csv(index=False).encode('utf-8'),
                       file_name="segmentacion_rfm.csv", mime="text/csv")

    st.subheader("Distribución por Segmento")
    fig, ax = plt.subplots()
    rfm['Segment'].value_counts().plot(kind='bar', ax=ax)
    st.pyplot(fig)

    st.subheader("Valor Monetario Promedio por Segmento")
    fig2, ax2 = plt.subplots()
    rfm.groupby('Segment')['Monetary'].mean().sort_values().plot(kind='bar', ax=ax2)
    st.pyplot(fig2)
