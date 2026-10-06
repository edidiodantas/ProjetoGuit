#!/usr/bin/env bash
# Compatibilidade: redireciona para o launcher na raiz
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$ROOT/rodar-ubuntu.sh"
