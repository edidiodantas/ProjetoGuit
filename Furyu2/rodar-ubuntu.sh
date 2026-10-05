#!/usr/bin/env bash
# Abre a interface Furyu no Ubuntu
# Uso: bash rodar-ubuntu.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "ERRO: ambiente virtual não encontrado."
  echo "Rode primeiro: bash install-ubuntu.sh"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Furyu — Ollama precisa estar rodando (localhost:11434)."
echo "Abrindo http://localhost:8501 …"
exec streamlit run app.py
