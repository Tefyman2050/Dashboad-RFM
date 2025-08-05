import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Dashboard RFM Interactivo", layout="wide")
st.title("📊 Dashboard RFM Interactivo con Insights Estratégicos")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
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

    # ✅ Distribuciones R, F, M
    st.subheader("Distribuciones R, F, M")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(px.histogram(rfm_df, x='Recency', nbins=20, title="Recency"), use_container_width=True)
    with col2:
        st.plotly_chart(px.histogram(rfm_df, x='Frequency', nbins=20, title="Frequency"), use_container_width=True)
    with col3:
        st.plotly_chart(px.histogram(rfm_df, x='Monetary', nbins=20, title="Monetary"), use_container_width=True)

    # ✅ Ventas por Establecimiento
    st.subheader("🏪 Ventas por Establecimiento (%)")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum()
    ventas_pct = (ventas_est / ventas_est.sum()) * 100
    fig_est = px.bar(x=ventas_pct.index, y=ventas_pct.values, color=ventas_pct.index, text=ventas_pct.values.round(2),
                     title="Ventas por Establecimiento", labels={'x': 'Establecimiento', 'y': '% Ventas'})
    st.plotly_chart(fig_est, use_container_width=True)

    # ✅ Insight: Mapa Competitivo
    st.subheader("🔥 Insight: Mapa Competitivo")
    df_merged = df_filtered.merge(rfm_df, on="Customer ID")
    df_mapa = df_merged.groupby('Establecimiento').agg({'Monetary': 'sum', 'RFM Score': 'mean'}).reset_index()
    df_mapa['Margen Estimado'] = df_mapa['Monetary'] * 0.3
    fig_map = px.scatter(df_mapa, x='Monetary', y='Margen Estimado', size='RFM Score', color='Establecimiento',
                         title="Mapa Competitivo", labels={'Monetary': 'Ventas', 'Margen Estimado': 'Margen'},
                         hover_data=['Establecimiento'])
    st.plotly_chart(fig_map, use_container_width=True)

    # ✅ Ventas por Hora Global (en barras)
    st.subheader("📊 Ventas por Hora (Global)")
    ventas_hora = df_filtered.groupby(['Hr transacc', 'Establecimiento'])['Sales'].sum().reset_index()
    fig_hora = px.bar(ventas_hora, x='Hr transacc', y='Sales', color='Establecimiento', barmode='group',
                    title="Ventas por Hora por Establecimiento")
    fig_hora.update_xaxes(title_text="Hora")
    fig_hora.update_yaxes(title_text="Ventas")
    st.plotly_chart(fig_hora, use_container_width=True)

    # ✅ Estrategias
    estrategias = []
    for est in establecimientos:
        for hora in range(rango_hora[0], rango_hora[1]+1):
            estrategias.append({'Establecimiento': est, 'Hora': f"{hora}:00", 'Estrategia': f"Oferta en {est} durante {hora}:00"})
    df_estrategias = pd.DataFrame(estrategias)
    st.subheader("📢 Estrategias sugeridas")
    st.dataframe(df_estrategias)
    csv_estrategias = df_estrategias.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Descargar Estrategias", data=csv_estrategias, file_name="estrategias.csv", mime="text/csv")
