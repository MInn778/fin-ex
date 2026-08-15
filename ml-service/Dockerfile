FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY artifacts ./artifacts

ENV MODEL_PATH=/app/artifacts/url_xgb.joblib
EXPOSE 8001
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8001"]

