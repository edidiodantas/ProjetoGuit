# MVP: Streamlit + PaperQA2 (embeddings locais). Ollama fica em outro serviço.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONNOUSERSITE=1 \
    HF_HOME=/app/.cache/hf \
    TRANSFORMERS_CACHE=/app/.cache/hf \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/hf

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY constraints-cpu.txt requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -c constraints-cpu.txt \
        -r requirements.txt

COPY app.py docker/entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /app/documentos /app/.pqa /app/.cache/hf

EXPOSE 8501
ENTRYPOINT ["/app/entrypoint.sh"]
