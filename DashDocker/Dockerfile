FROM python:3.10
WORKDIR /app
COPY ./app /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "dashboard_rfm_dinamico.py", "--server.port=8501", "--server.address=0.0.0.0"]
