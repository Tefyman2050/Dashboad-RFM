# Dashboard RFM Dinámico - Interactivo

Este proyecto implementa un dashboard **interactivo** con Streamlit para análisis RFM y visualización gerencial.

## 🚀 Ejecutar localmente
1. Clona este repositorio:
   ```bash
   git clone https://github.com/tuusuario/dashboard_rfm.git
   cd dashboard_rfm/app
   ```
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta el dashboard:
   ```bash
   streamlit run dashboard_rfm_dinamico.py
   ```
Accede en: [http://localhost:8501](http://localhost:8501)

---

## 🐳 Ejecutar con Docker
1. Construir la imagen:
   ```bash
   docker build -t dashboard-rfm .
   ```
2. Ejecutar el contenedor:
   ```bash
   docker run -p 8501:8501 dashboard-rfm
   ```
Accede en: [http://localhost:8501](http://localhost:8501)

---

## 🌐 Desplegar en Streamlit Cloud
1. Sube este proyecto a GitHub.
2. Ve a [Streamlit Cloud](https://streamlit.io/cloud) y conecta tu repositorio.
3. Configura `app/dashboard_rfm_dinamico.py` como script principal.

---

### ✅ Visualizaciones incluidas
- Gráfico dinámico para Ventas por Hora (Línea, Barras, Burbujas)
- Gráfico dinámico para Ventas por Establecimiento (Barras, Pie, Sunburst)
- Gráfico dinámico para Mapa Competitivo (Burbujas, Barras)
- Distribuciones interactivas R, F, M
- Tabla de estrategias sugeridas descargable
