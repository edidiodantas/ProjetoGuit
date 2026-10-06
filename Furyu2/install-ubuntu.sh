#!/usr/bin/env bash
# Instala o Furyu no Ubuntu LTS (22.04 / 24.04)
# Uso: bash install-ubuntu.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo ""
echo "== Furyu · instalação Ubuntu LTS =="
echo "Pasta: $ROOT"
echo ""

# Recusa pendrive exFAT/vfat como destino do .venv
fstype="$(df -T "$ROOT" 2>/dev/null | awk 'NR==2 {print $2}')"
case "${fstype:-}" in
  exfat|vfat|msdos)
    echo "ERRO: a pasta está em filesystem ${fstype} (provável pendrive)."
    echo "Copie Furyu2 para o disco interno, ex.: ~/Furyu2"
    echo "e rode este script LÁ."
    exit 1
    ;;
esac

if [[ ! -f "app.py" || ! -f "academic_search.py" || ! -f "requirements.txt" ]]; then
  echo "ERRO: arquivos do Furyu não encontrados."
  echo "Copie a pasta INTEIRA Furyu2 (app.py, academic_search.py, requirements.txt…)."
  exit 1
fi

need_apt=0
for cmd in python3 curl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    need_apt=1
  fi
done
if ! python3 -c "import venv" 2>/dev/null; then
  need_apt=1
fi

if [[ "$need_apt" -eq 1 ]]; then
  echo "Instalando pacotes do sistema (pode pedir senha)…"
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip python3-dev build-essential curl
fi

PY=python3
if ! "$PY" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
then
  if command -v python3.12 >/dev/null 2>&1; then
    PY=python3.12
  elif command -v python3.11 >/dev/null 2>&1; then
    PY=python3.11
  else
    echo "ERRO: Python 3.11+ obrigatório."
    echo "No Ubuntu 22.04, instale python3.12 (veja INSTALAR-UBUNTU.md)."
    exit 1
  fi
fi

echo "Usando: $($PY --version)"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Criando ambiente virtual (.venv)…"
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip

echo "Instalando PyTorch CPU…"
pip install torch --index-url https://download.pytorch.org/whl/cpu

echo "Instalando PaperQA + Streamlit…"
if [[ -f "constraints-cpu.txt" ]]; then
  pip install -c constraints-cpu.txt --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
else
  pip install -r requirements.txt
fi

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Criado .env a partir de .env.example"
elif grep -qE '/media/|pqa-linux' .env 2>/dev/null; then
  cp .env.example .env
  echo "Substituído .env antigo (caminhos de outro sistema) pelo .env.example"
fi

echo ""
echo "Pronto. Agora:"
echo "  1. Instale o Ollama (se faltar): curl -fsSL https://ollama.com/install.sh | sh"
echo "  2. Baixe o modelo: ollama pull qwen3.5:4b"
echo "  3. Edite o .env: CONTACT_EMAIL=seu.email@escola.edu.br"
echo "  4. Rode: bash rodar-ubuntu.sh"
echo ""
echo "Opcional — validar instalação:"
echo "  pip install -r requirements-dev.txt && pytest"
echo "  pip install -r testes/requirements-avaliacao.txt && python testes/run_avaliacao.py"
echo ""
echo "Guia completo: INSTALAR-UBUNTU-LTS.txt / INSTALAR-UBUNTU.md"
echo ""
