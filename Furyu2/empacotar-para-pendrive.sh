#!/usr/bin/env bash
# Gera um .tar.gz pronto para copiar no pendrive (sem .venv / caches).
# Uso:
#   bash empacotar-para-pendrive.sh
#   bash empacotar-para-pendrive.sh /caminho/destino
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${1:-$ROOT}"
STAMP="$(date +%Y%m%d)"
NAME="Furyu2-ubuntu-pendrive-${STAMP}.tar.gz"
OUT="${OUT_DIR}/${NAME}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/Furyu2"
if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.venv/' \
    --exclude '.pqa/' \
    --exclude 'testes/.pqa_eval/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache/' \
    --exclude '.coverage' \
    --exclude 'htmlcov/' \
    --exclude '.env' \
    --exclude 'documentos/*.pdf' \
    --exclude 'linux-env/' \
    --exclude 'linux-env.img' \
    --exclude '.git/' \
    --exclude 'Furyu2-ubuntu-pendrive*.tar.gz' \
    "$ROOT"/ "$TMP/Furyu2"/
else
  # Fallback sem rsync
  tar -C "$ROOT" \
    --exclude='.venv' \
    --exclude='.pqa' \
    --exclude='testes/.pqa_eval' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.coverage' \
    --exclude='htmlcov' \
    --exclude='.env' \
    --exclude='linux-env' \
    --exclude='linux-env.img' \
    --exclude='.git' \
    --exclude='Furyu2-ubuntu-pendrive*.tar.gz' \
    --exclude='documentos/*.pdf' \
    -cf - . | tar -C "$TMP/Furyu2" -xf -
fi

# Garante .env.example e pastas vazias
mkdir -p "$TMP/Furyu2/documentos"
touch "$TMP/Furyu2/documentos/.gitkeep"
[[ -f "$TMP/Furyu2/.env.example" ]] || true

tar -C "$TMP" -czf "$OUT" Furyu2
# Cópia “estável” sem data no nome (para atalhos/docs)
cp -f "$OUT" "${OUT_DIR}/Furyu2-ubuntu-pendrive.tar.gz"

echo ""
echo "Pacote gerado:"
echo "  $OUT"
echo "  ${OUT_DIR}/Furyu2-ubuntu-pendrive.tar.gz"
ls -lh "$OUT" "${OUT_DIR}/Furyu2-ubuntu-pendrive.tar.gz"
echo ""
echo "No pendrive (PC Ubuntu):"
echo "  1. Copie Furyu2-ubuntu-pendrive.tar.gz para o pendrive"
echo "  2. No outro PC: tar -xzf Furyu2-ubuntu-pendrive.tar.gz -C ~"
echo "  3. cd ~/Furyu2 && bash install-ubuntu.sh"
echo "  4. Siga INSTALAR-UBUNTU-LTS.txt"
