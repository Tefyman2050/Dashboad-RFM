import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Dashboard RFM Interactivo", layout="wide")
st.title("📊 Dashboard RFM con Gráficos Interactivos")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name='Transaction Data')
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Hr transacc'] = pd.to_datetime(df['Hr transacc'], format='%H:%M:%S', errors='coerce').dt.hour

    st.subheader("Vista previa de datos")
    st.dataframe(df.head())

    st.sidebar.header("Filtros")
    establecimientos = st.sidebar.multiselect("Establecimientos", df['Establecimiento'].unique(), default=list(df['Establecimiento'].unique()))
    rango_hora = st.sidebar.slider("Rango horario", 0, 23, (0, 23))

    df_filtered = df[(df['Establecimiento'].isin(establecimientos)) & (df['Hr transacc'].between(rango_hora[0], rango_hora[1]))]

    # Ventas por Establecimiento
    st.subheader("🏪 Ventas por Establecimiento (%)")
    ventas_est = df_filtered.groupby('Establecimiento')['Sales'].sum()
    ventas_pct = (ventas_est / ventas_est.sum()) * 100
    fig = px.bar(x=ventas_pct.index, y=ventas_pct.values, color=ventas_pct.index,
                 title="Ventas por Establecimiento (%)", labels={'x': 'Establecimiento', 'y': '% Ventas'})
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap Hora vs Establecimiento
    st.subheader("🕒 Ventas por Hora y Establecimiento")
    pivot = df_filtered.pivot_table(index='Hr transacc', columns='Establecimiento', values='Sales', aggfunc='sum').fillna(0)
    fig2 = px.imshow(pivot, text_auto=True, color_continuous_scale='Viridis', aspect="auto",
                     title="Mapa de calor: Hora vs Establecimiento")
    st.plotly_chart(fig2, use_container_width=True)
