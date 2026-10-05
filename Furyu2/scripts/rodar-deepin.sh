#!/usr/bin/env bash
# Sobe a GUI no Deepin usando só o volume ext4 do pendrive.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
cd "$PROJECT_ROOT"

if [[ ! -f "$IMG" || ! -x "$MNT/venv/bin/python" ]]; then
  echo "Ambiente ainda não instalado. Rode: bash scripts/setup-deepin.sh"
  exit 1
fi

bash "$SCRIPT_DIR/montar-linux-env.sh"

export PIP_CACHE_DIR="$MNT/pip-cache"
export HF_HOME="$MNT/hf-cache"
export TRANSFORMERS_CACHE="$MNT/hf-cache"
export SENTENCE_TRANSFORMERS_HOME="$MNT/hf-cache"
export XDG_CACHE_HOME="$MNT/xdg-cache"
export XDG_DATA_HOME="$MNT/xdg-data"
export TMPDIR="$MNT/tmp"
export OLLAMA_MODELS="$MNT/ollama-models"
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"

# shellcheck disable=SC1091
source "$MNT/venv/bin/activate"

if ! curl -fsS --max-time 2 "http://${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; then
  echo "Ollama não está em http://${OLLAMA_HOST}."
  echo "Em outro terminal (modelos no pendrive):"
  echo "  export OLLAMA_MODELS=\"$OLLAMA_MODELS\""
  echo "  ollama serve"
  exit 1
fi

exec streamlit run "$PROJECT_ROOT/app.py"
