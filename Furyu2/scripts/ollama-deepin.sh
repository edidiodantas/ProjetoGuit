#!/usr/bin/env bash
# Inicia o Ollama no Deepin com modelos no pendrive (sem sudo).
# Uso: bash scripts/ollama-deepin.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
cd "$PROJECT_ROOT"

# Adiciona ollama local ao PATH se existir
if [ -d "$HOME/.local/ollama/bin" ]; then
    export PATH="$HOME/.local/ollama/bin:$PATH"
fi

if ! command -v ollama &> /dev/null; then
    echo "ERRO: ollama não encontrado."
    echo "Instale primeiro com:"
    echo "  mkdir -p ~/.local/ollama"
    echo "  curl -L -o /tmp/ollama-linux-amd64.tar.zst https://github.com/ollama/ollama/releases/download/v0.34.4/ollama-linux-amd64.tar.zst"
    echo "  tar --zstd -xf /tmp/ollama-linux-amd64.tar.zst -C ~/.local/ollama"
    exit 1
fi

# Modelos ficam no pendrive, não no SSD
export OLLAMA_MODELS="/media/Edidio/8662-B4492/ollama-models"
mkdir -p "$OLLAMA_MODELS"

MODEL="${1:-$(grep -E '^OLLAMA_MODEL=' "$PROJECT_ROOT/.env" | cut -d= -f2- || true)}"
MODEL="${MODEL:-qwen3.5:2b}"

echo "== Ollama Deepin =="
echo "Binário: $(command -v ollama)"
echo "Modelos: $OLLAMA_MODELS"
echo "Modelo : $MODEL"
echo

if pgrep -x "ollama" > /dev/null; then
    echo "Ollama já está rodando."
else
    echo "Iniciando ollama serve..."
    nohup ollama serve > /tmp/ollama-serve.log 2>&1 &
    sleep 3
fi

if ollama list | grep -q "^${MODEL}"; then
    echo "Modelo $MODEL já baixado."
else
    echo "Baixando modelo $MODEL..."
    echo "(Isso pode levar vários minutos; aperte Ctrl+C se quiser interromper)"
    ollama pull "$MODEL"
fi

echo
echo "Pronto. Teste com:"
echo "  ollama run $MODEL"
echo
echo "Para rodar o Furyu:"
echo "  bash scripts/rodar-deepin.sh"
