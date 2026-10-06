#!/bin/sh
set -eu
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3.5:4b}"

echo "Aguardando Ollama em ${OLLAMA_BASE_URL} …"
i=0
until curl -fsS --max-time 2 "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 90 ]; then
    echo "Ollama não respondeu a tempo."
    exit 1
  fi
  sleep 2
done

if ! curl -fsS --max-time 5 "${OLLAMA_BASE_URL}/api/tags" | grep -q "${OLLAMA_MODEL}"; then
  echo "Baixando modelo ${OLLAMA_MODEL} (só na 1ª subida)…"
  curl -fsS --max-time 0 "${OLLAMA_BASE_URL}/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${OLLAMA_MODEL}\",\"stream\":false}" >/dev/null
fi

exec streamlit run /app/app.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.headless true
