#!/usr/bin/env bash
# Copia a pasta Furyu2 (sem .venv) para o pendrive plugado.
# Uso no Ubuntu (no PC com o pendrive):
#   bash copiar-para-pendrive.sh
#   bash copiar-para-pendrive.sh /media/$USER/NOME_DO_PENDRIVE
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_BASE="${1:-}"

if [[ -z "$DEST_BASE" ]]; then
  mapfile -t mounts < <(find /media/"$USER" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort)
  if [[ ${#mounts[@]} -eq 0 ]]; then
    echo "Nenhum pendrive em /media/$USER/"
    echo "Plugue o pendrive e rode de novo, ou passe o caminho:"
    echo "  bash copiar-para-pendrive.sh /media/\$USER/NOME"
    exit 1
  fi
  if [[ ${#mounts[@]} -eq 1 ]]; then
    DEST_BASE="${mounts[0]}"
  else
    echo "Vários volumes em /media/$USER/ — escolha um:"
    select m in "${mounts[@]}"; do
      DEST_BASE="$m"
      break
    done
  fi
fi

if [[ ! -d "$DEST_BASE" ]]; then
  echo "ERRO: destino não existe: $DEST_BASE"
  exit 1
fi

DEST="$DEST_BASE/Furyu2"
echo "Origem: $ROOT"
echo "Destino: $DEST"
echo ""

mkdir -p "$DEST"
rsync -a --delete \
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
  "$ROOT"/ "$DEST"/

# Garante o guia TXT no pendrive
if [[ -f "$DEST/INSTALAR-UBUNTU-LTS.txt" ]]; then
  echo "OK: INSTALAR-UBUNTU-LTS.txt no pendrive (pode imprimir)."
fi
if [[ -f "$DEST/LEIA-ME-PENDRIVE.txt" ]]; then
  echo "OK: LEIA-ME-PENDRIVE.txt no pendrive."
fi

echo ""
echo "Cópia concluída."
echo "No outro PC Ubuntu:"
echo "  1. cp -a /media/\$USER/*/Furyu2 ~/Furyu2"
echo "  2. Siga INSTALAR-UBUNTU-LTS.txt (imprimir/acompanhar)"
echo "  3. cd ~/Furyu2 && bash install-ubuntu.sh"
echo "  4. bash rodar-ubuntu.sh"
echo ""
echo "Dica: se preferir um único arquivo, rode também:"
echo "  bash empacotar-para-pendrive.sh"
echo "e copie Furyu2-ubuntu-pendrive.tar.gz para o pendrive."
