#!/usr/bin/env bash
# Caminhos comuns dos scripts Deepin. Sempre use: source "$(dirname "$0")/config.sh"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMG="${PROJECT_ROOT}/linux-env.img"
IMG_SIZE_GB="${LINUX_ENV_GB:-16}"

# Preferir o mount do udisks (não precisa de senha no Deepin).
if findmnt -n /media/Edidio/pqa-linux >/dev/null 2>&1; then
  MNT="/media/Edidio/pqa-linux"
else
  MNT="${PROJECT_ROOT}/linux-env"
fi

export PROJECT_ROOT IMG MNT IMG_SIZE_GB
