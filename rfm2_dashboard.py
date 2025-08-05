import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard RFM + Estrategias", layout="wide")

st.title("📊 Análisis RFM Avanzado + Estrategias de Marketing")

uploaded_file = st.file_uploader("Sube tu archivo Excel (con Transaction Data)", type=["xlsx"])

if uploaded_file:
    # ✅ Procesar archivo y crear tabla RFM
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Hr transacc'] = pd.to_datetime(df['Hr transacc'], format='%H:%M:%S', errors='coerce').dt.hour

    # ✅ Crear tabla RFM
    rfm = df.groupby('Customer ID').agg({
        'Order Date': lambda x: (pd.Timestamp.now() - x.max()).days,
        'Order ID': 'nunique',
        'Sales': 'sum'
    }).reset_index()
    rfm.columns = ['Customer ID', 'Recency', 'Frequency', 'Monetary']

    # ✅ Calcular puntajes RFM
    rfm['R_score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1])
    rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
    rfm['M_score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5])
    rfm['RFM_Score'] = rfm['R_score'].astype(str)+rfm['F_score'].astype(str)+rfm['M_score'].astype(str)

    # ✅ Segmentación
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

    # ✅ Mostrar RFM
    st.subheader("📌 Segmentación RFM")
    st.dataframe(rfm.head(20))

    csv_rfm = rfm.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Descargar Segmentación RFM", data=csv_rfm, file_name="segmentacion_rfm.csv", mime="text/csv")

    # ✅ Gráficos
    st.subheader("📊 Distribución por Segmento")
    fig, ax = plt.subplots()
    rfm['Segment'].value_counts().plot(kind='bar', ax=ax, color=['#3498db','#2ecc71','#f1c40f','#e74c3c'])
    st.pyplot(fig)

    df_merged = df.merge(rfm[['Customer ID','Segment']], on='Customer ID')

    st.subheader("🏪 Ventas por Segmento y Establecimiento")
    segment_establecimiento = df_merged.groupby(['Segment','Establecimiento'])['Sales'].sum().unstack(fill_value=0)
    st.bar_chart(segment_establecimiento.T)

    st.subheader("🕒 Ventas por Hora según Segmento")
    segment_hora = df_merged.groupby(['Segment','Hr transacc'])['Sales'].sum().unstack(fill_value=0)
    st.line_chart(segment_hora.T)

    # ✅ Estrategias automáticas
    st.subheader("📢 Estrategias de Marketing Basadas en RFM")

    segmentos = ['Champions', 'Leales', 'Potenciales', 'En riesgo']
    establecimientos = ['Grifos', 'Supermercados']
    horarios = {
        'Champions':'06:00 – 09:00',
        'Leales':'06:00 – 09:00',
        'Potenciales':'17:00 – 20:00',
        'En riesgo':'17:00 – 20:00'
    }
    ofertas = {
        ('Champions','Grifos'):'Café + snack gratis por carga > S/50',
        ('Champions','Supermercados'):'Acceso anticipado a promociones exclusivas',
        ('Leales','Grifos'):'Cada 5 cargas, 1 gratis',
        ('Leales','Supermercados'):'Cupones semanales en productos frecuentes',
        ('Potenciales','Grifos'):'Descuento en snacks con carga mínima',
        ('Potenciales','Supermercados'):'Promociones cruzadas en productos populares',
        ('En riesgo','Grifos'):'Oferta flash: -30% en snacks',
        ('En riesgo','Supermercados'):'Cupón de recuperación con vencimiento rápido'
    }
    canales = {
        'Champions':'Push + Email + WhatsApp Business',
        'Leales':'WhatsApp Business + SMS',
        'Potenciales':'Publicidad en redes + SMS',
        'En riesgo':'Email remarketing + SMS'
    }

    estrategias = []
    for seg in segmentos:
        for est in establecimientos:
            estrategias.append({
                'Segmento': seg,
                'Establecimiento': est,
                'Hora óptima': horarios[seg],
                'Oferta': ofertas[(seg, est)],
                'Canal recomendado': canales[seg],
                'Mensaje sugerido': f"¡Hola {seg}! {ofertas[(seg, est)]}. Disponible en {est}. ¡Aprovecha hoy!"
            })

    df_estrategias = pd.DataFrame(estrategias)
    st.dataframe(df_estrategias)

    csv_estrategias = df_estrategias.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Descargar Estrategias en CSV", data=csv_estrategias, file_name="estrategias_marketing.csv", mime="text/csv")
