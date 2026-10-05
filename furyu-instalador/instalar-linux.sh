#!/bin/bash
# Instala a janela Furyu e registra amadeus-verbo no Ollama.
# O GGUF não vem no Git: ele fica no pendrive, na pasta Furyu-teste.
set -euo pipefail

PASTA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GGUF_NOME="Amadeus-Verbo-FI-Qwen2.5-0.5B-PT-BR-Instruct.Q4_K_M.gguf"
DEB_NOME="furyu_0.1.0_amd64.deb"

passo() {
    printf '\n==> %s\n' "$1"
}

montar_deb() {
    local saida="$1"
    local stage
    if [[ ! -f "$PASTA/packaging/DEBIAN/control" || ! -f "$PASTA/furyu_app.py" ]]; then
        echo "Falta packaging/ ou furyu_app.py para montar ${DEB_NOME}." >&2
        exit 1
    fi
    if ! command -v dpkg-deb >/dev/null 2>&1; then
        echo "Falta o comando dpkg-deb para montar ${DEB_NOME}." >&2
        exit 1
    fi
    stage="$(mktemp -d)"
    cp -a "$PASTA/packaging/." "$stage/"
    install -D -m 0755 "$PASTA/furyu_app.py" "$stage/usr/share/furyu/furyu_app.py"
    chmod 755 "$stage/DEBIAN/postinst" "$stage/usr/bin/furyu"
    rm -rf "$stage/usr/share/furyu/__pycache__"
    dpkg-deb --root-owner-group -Zxz --build "$stage" "$saida"
    rm -rf "$stage"
}

if ! command -v apt-get >/dev/null 2>&1; then
    echo "Este script é para Ubuntu. Nada foi instalado." >&2
    exit 1
fi

passo "Instalando python3, python3-gi e gir1.2-gtk-3.0."
sudo -v
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-gi \
    gir1.2-gtk-3.0

if [[ -f "$PASTA/$DEB_NOME" ]]; then
    DEB="$PASTA/$DEB_NOME"
else
    DEB="$PASTA/$DEB_NOME"
    passo "Montando ${DEB_NOME}."
    montar_deb "$DEB"
fi

passo "Instalando ${DEB_NOME}."
sudo DEBIAN_FRONTEND=noninteractive dpkg -i "$DEB"

if [[ ! -f "$PASTA/$GGUF_NOME" || ! -f "$PASTA/Modelfile" ]]; then
    echo "Falta ${GGUF_NOME} ao lado do Modelfile." >&2
    echo "Esse GGUF fica no pendrive, na pasta Furyu-teste, e não vai para o Git." >&2
    exit 1
fi

if ! curl -sf --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null; then
    echo "O Ollama não está em execução." >&2
    exit 1
fi

passo "Criando o modelo amadeus-verbo no Ollama."
cd "$PASTA"
ollama create amadeus-verbo -f Modelfile

echo
echo "Pronto. Abra o menu e clique em Furyu."
echo "No terminal, o comando é: furyu"
