#!/usr/bin/env bash
# Desmonta o volume ext4 do pendrive.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/config.sh"

if ! findmnt -n "$MNT" >/dev/null 2>&1; then
  echo "Não estava montado: $MNT"
  exit 0
fi

if [[ "$(id -u)" -eq 0 ]]; then
  umount "$MNT"
else
  sudo umount "$MNT"
fi

echo "Desmontado: $MNT"
