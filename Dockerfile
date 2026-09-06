FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
# serving needs a slim subset; install the full file for simplicity
RUN pip install --no-cache-dir fastapi==0.112.2 uvicorn==0.30.6 pydantic==2.8.2 \
    scikit-learn==1.5.1 pandas==2.2.2 numpy==1.26.4 joblib==1.4.2 prometheus-client==0.20.0
COPY src/serve.py src/serve.py
COPY models/ models/
EXPOSE 8080
ENV MODEL_DIR=models MODEL_VERSION=1.0.0
CMD ["uvicorn", "src.serve:app", "--host", "0.0.0.0", "--port", "8080"]
