#!/usr/bin/env bash
# Instalação no Deepin 23 — NÃO usa o SSD para venv, cache nem modelos.
# Rode só quando for instalar de verdade:
#   bash scripts/setup-deepin.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
cd "$PROJECT_ROOT"

echo "== Furyu · setup Deepin =="
echo "Projeto: $PROJECT_ROOT"
echo "Volume Linux: $IMG  (${IMG_SIZE_GB}G, ext4, no pendrive)"
echo

if [[ ! "$PROJECT_ROOT" =~ ^/media/ ]]; then
  echo "AVISO: o projeto não parece estar no pendrive ($PROJECT_ROOT)."
  echo "Nada deve ser instalado no SSD. Continue só se isso for intencional."
fi

fstype="$(df -T "$PROJECT_ROOT" | awk 'NR==2 {print $2}')"
echo "Filesystem do projeto: $fstype"

if [[ "$fstype" == "exfat" || "$fstype" == "vfat" || "$fstype" == "fuseblk" ]]; then
  echo "Pendrive em $fstype: .venv nativo aqui quebra. Usando imagem ext4."
fi

command -v python3 >/dev/null || { echo "Instale python3 (já vem no Deepin 23)."; exit 1; }
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11+ obrigatório, achou {sys.version}")
print(f"Python {sys.version.split()[0]} ok")
PY

if [[ ! -f "$IMG" ]]; then
  echo "Criando imagem esparsa ${IMG_SIZE_GB}G (não preenche o pendrive de imediato)…"
  truncate -s "${IMG_SIZE_GB}G" "$IMG"
  mkfs.ext4 -F -L pqa-linux "$IMG"
fi

bash "$SCRIPT_DIR/montar-linux-env.sh"

mkdir -p \
  "$MNT/venv" \
  "$MNT/hf-cache" \
  "$MNT/pip-cache" \
  "$MNT/xdg-cache" \
  "$MNT/ollama-models" \
  "$MNT/pqa" \
  "$MNT/tmp"

if [[ "$(stat -c '%u' "$MNT")" != "$(id -u)" ]]; then
  sudo chown -R "$(id -u):$(id -g)" "$MNT"
fi

export PIP_CACHE_DIR="$MNT/pip-cache"
export HF_HOME="$MNT/hf-cache"
export TRANSFORMERS_CACHE="$MNT/hf-cache"
export SENTENCE_TRANSFORMERS_HOME="$MNT/hf-cache"
export XDG_CACHE_HOME="$MNT/xdg-cache"
export TMPDIR="$MNT/tmp"
export OLLAMA_MODELS="$MNT/ollama-models"
# Impede pip/huggingface de cair em ~/.cache no SSD
export XDG_DATA_HOME="$MNT/xdg-data"

if [[ ! -x "$MNT/venv/bin/python" ]]; then
  echo "Criando venv em $MNT/venv …"
  python3 -m venv "$MNT/venv"
fi

# shellcheck disable=SC1091
source "$MNT/venv/bin/activate"
python -m pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"

if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
  if [[ -f "$PROJECT_ROOT/.env.deepin.example" ]]; then
    cp "$PROJECT_ROOT/.env.deepin.example" "$PROJECT_ROOT/.env"
    echo "Copiado .env.deepin.example → .env (modelo 4B, adequado à GTX 750)."
  else
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  fi
fi

# Garante PQA_HOME no volume ext4 (não no exFAT / SSD)
if grep -q '^PQA_HOME=' "$PROJECT_ROOT/.env"; then
  sed -i "s|^PQA_HOME=.*|PQA_HOME=$MNT/pqa|" "$PROJECT_ROOT/.env"
else
  echo "PQA_HOME=$MNT/pqa" >> "$PROJECT_ROOT/.env"
fi

echo
echo "== Ollama =="
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama ainda não está no PATH. Para instalar o binário no sistema (pequeno):"
  echo "  curl -fsSL https://ollama.com/install.sh | sh"
  echo "O binário vai para /usr/local (sistema). Os MODELOS ficam no pendrive:"
  echo "  OLLAMA_MODELS=$OLLAMA_MODELS"
else
  echo "Ollama já instalado: $(command -v ollama)"
fi

MODEL="$(grep -E '^OLLAMA_MODEL=' "$PROJECT_ROOT/.env" | cut -d= -f2- || true)"
MODEL="${MODEL:-qwen3.5:4b}"
echo
echo "Quando for baixar o modelo (vai para o pendrive, não para ~/.ollama):"
echo "  export OLLAMA_MODELS=\"$MNT/ollama-models\""
echo "  sudo systemctl stop ollama 2>/dev/null || true"
echo "  ollama serve &"
echo "  ollama pull $MODEL"
echo
echo "Pronto. Para abrir a UI:"
echo "  bash scripts/rodar-deepin.sh"
echo
echo "Nada de venv/cache/modelos foi colocado no SSD deste setup."
