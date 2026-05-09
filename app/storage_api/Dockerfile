FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --progress-bar off -r requirements.txt

COPY app ./app
COPY s3_lib ./s3_lib

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.storage_api.main:app", "--host", "0.0.0.0", "--port", "8000"]