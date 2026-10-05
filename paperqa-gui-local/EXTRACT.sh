#!/usr/bin/env bash
# Uso: bash EXTRACT.sh paperqa-gui-local-pack.txt
set -euo pipefail
PACK="${1:-paperqa-gui-local-pack.txt}"
OUT="paperqa-gui-local"
mkdir -p "$OUT"
awk -v out="$OUT" '
  /^########## FILE: / {
    name = $0
    sub(/^########## FILE: /, "", name)
    sub(/ ##########$/, "", name)
    file = out "/" name
    next
  }
  /^########## END ##########$/ {
    file = ""
    next
  }
  file != "" { print >> file }
' "$PACK"
echo "Arquivos extraídos em ./$OUT"
ls -la "$OUT"
