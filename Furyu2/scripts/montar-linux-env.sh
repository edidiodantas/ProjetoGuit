#!/usr/bin/env bash
# Monta o volume ext4 do pendrive (venv, cache HuggingFace, modelos Ollama).
# Preferimos udisksctl (sem senha). sudo só como fallback.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/config.sh"

if findmnt -n /media/Edidio/pqa-linux >/dev/null 2>&1; then
  echo "Já montado: /media/Edidio/pqa-linux"
  df -h /media/Edidio/pqa-linux
  exit 0
fi

if findmnt -n "$MNT" >/dev/null 2>&1; then
  echo "Já montado: $MNT"
  df -h "$MNT"
  exit 0
fi

if [[ ! -f "$IMG" ]]; then
  echo "Imagem ainda não existe: $IMG"
  echo "Rode primeiro: bash scripts/setup-deepin.sh"
  exit 1
fi

# Reusa loop já mapeado, se existir
LOOP_DEV=""
while read -r loop backing; do
  if [[ "$backing" == "$IMG" ]]; then
    LOOP_DEV="$loop"
    break
  fi
done < <(losetup -O NAME,BACK-FILE --noheadings 2>/dev/null || true)

if [[ -z "$LOOP_DEV" ]]; then
  echo "Anexando imagem via udisksctl…"
  map_out="$(udisksctl loop-setup -f "$IMG")"
  echo "$map_out"
  LOOP_DEV="$(echo "$map_out" | grep -oE '/dev/loop[0-9]+' | head -1)"
fi

if [[ -n "$LOOP_DEV" ]]; then
  if ! findmnt -n "$LOOP_DEV" >/dev/null 2>&1; then
    udisksctl mount -b "$LOOP_DEV"
  fi
  echo "Montado $IMG em $(findmnt -n -o TARGET "$LOOP_DEV")"
  df -h "$LOOP_DEV"
  exit 0
fi

mkdir -p "$MNT"
if [[ "$(id -u)" -eq 0 ]]; then
  mount -o loop "$IMG" "$MNT"
else
  sudo mount -o loop "$IMG" "$MNT"
fi
echo "Montado $IMG em $MNT"
df -h "$MNT"
