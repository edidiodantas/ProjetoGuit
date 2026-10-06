#!/usr/bin/env bash
# Compatibilidade: redireciona para o instalador na raiz
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$ROOT/install-ubuntu.sh"
