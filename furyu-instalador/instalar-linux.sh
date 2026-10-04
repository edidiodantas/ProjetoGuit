#!/bin/bash
# Instala o aplicativo de teste Furyu neste Ubuntu.
# A janela não é o editor completo: ela conversa em português com o Amadeus Verbo.
set -euo pipefail

PASTA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GGUF_NOME="Amadeus-Verbo-FI-Qwen2.5-0.5B-PT-BR-Instruct.Q4_K_M.gguf"
DEB_NOME="furyu_0.1.0_amd64.deb"
LLAMA_DIR="/usr/lib/furyu"
SRC="$HOME/.local/src/furyu-llama.cpp"

passo() {
    printf '\n==> %s\n' "$1"
}

achar() {
    local nome="$1"
    local candidato
    for candidato in "$PASTA/$nome" "$PASTA/../$nome"; do
        if [[ -f "$candidato" ]]; then
            printf '%s\n' "$(cd "$(dirname "$candidato")" && pwd)/$(basename "$candidato")"
            return 0
        fi
    done
    return 1
}

if ! GGUF_ORIGEM="$(achar "$GGUF_NOME")"; then
    echo "Falta o arquivo ${GGUF_NOME} nesta pasta." >&2
    exit 1
fi

bytes="$(stat -c '%s' "$GGUF_ORIGEM")"
if [[ "$bytes" -lt 100000000 ]]; then
    echo "O arquivo ${GGUF_NOME} está incompleto." >&2
    exit 1
fi

montar_deb() {
    local saida="$1"
    local stage
    if [[ ! -f "$PASTA/packaging/DEBIAN/control" || ! -f "$PASTA/furyu_app.py" ]]; then
        echo "Falta o pacote ${DEB_NOME} e também a pasta packaging/." >&2
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

if DEB_ORIGEM="$(achar "$DEB_NOME")"; then
    :
else
    if [[ -w "$PASTA" ]]; then
        DEB_ORIGEM="$PASTA/$DEB_NOME"
    else
        DEB_ORIGEM="/tmp/$DEB_NOME"
    fi
    passo "Montando ${DEB_NOME} a partir do código em packaging/."
    montar_deb "$DEB_ORIGEM"
fi

DESTINO_MODELO="/usr/share/furyu/$GGUF_NOME"

passo "Furyu de teste, não o editor completo"
echo "Este script instala a janela Furyu no menu do Ubuntu."
echo "Ela conversa offline, em português do Brasil, com o Amadeus Verbo na CPU."
echo "PC alvo: Intel Core i5 de 3ª geração (cerca de 2,9 GHz), 8 GB de RAM, SSD de 128 GB."
echo "Esse processador tem AVX e não tem AVX2."
echo "As versões oficiais do Ollama em geral exigem AVX2 e saem com \"illegal instruction\"."
echo "Se precisar, o llama.cpp é compilado aqui com AVX e sem AVX2."

if ! command -v apt-get >/dev/null 2>&1; then
    echo "Este script é para Ubuntu. Nada foi instalado." >&2
    exit 1
fi

passo "Instalando pacotes do sistema. O Ubuntu pode pedir a sua senha."
sudo -v
sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    cmake \
    git \
    libcurl4-openssl-dev \
    python3 \
    python3-gi \
    gir1.2-gtk-3.0 \
    desktop-file-utils

passo "Instalando ${DEB_NOME}."
if ! sudo DEBIAN_FRONTEND=noninteractive dpkg -i "$DEB_ORIGEM"; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -f -y
    sudo DEBIAN_FRONTEND=noninteractive dpkg -i "$DEB_ORIGEM"
fi

passo "Copiando o modelo para ${DESTINO_MODELO}."
sudo install -d -m 0755 /usr/share/furyu "$LLAMA_DIR"
sudo install -m 0644 "$GGUF_ORIGEM" "$DESTINO_MODELO"

precisa_compilar=1
if [[ -x "$LLAMA_DIR/llama-server" ]]; then
    set +e
    "$LLAMA_DIR/llama-server" --version >/dev/null 2>&1
    rc=$?
    set -e
    if [[ "$rc" -eq 0 ]]; then
        precisa_compilar=0
        passo "O llama-server já roda neste processador."
    else
        passo "O llama-server atual não roda neste processador. Vou compilar com AVX, sem AVX2."
    fi
else
    passo "Compilando o llama.cpp com AVX, sem AVX2."
fi

if [[ "$precisa_compilar" -eq 1 ]]; then
    flags="$(grep -m1 '^flags' /proc/cpuinfo || true)"
    if ! grep -qw avx <<<"$flags"; then
        echo "Este processador não tem AVX. A compilação foi interrompida." >&2
        exit 1
    fi

    f16c="OFF"
    if grep -qw f16c <<<"$flags"; then
        f16c="ON"
        echo "F16C encontrado (comum no i5 de 3ª geração). AVX2 e FMA ficam desligados."
    else
        echo "Sem F16C. AVX fica ligado. AVX2 e FMA ficam desligados."
    fi

    mem_kb="$(awk '/MemTotal:/ {print $2}' /proc/meminfo)"
    jobs=4
    if [[ "$mem_kb" -lt 11000000 ]]; then
        jobs=2
    fi
    echo "Memória: ${mem_kb} kB. A compilação usa ${jobs} tarefas para caber em 8 GB."

    mkdir -p "$(dirname "$SRC")"
    if [[ ! -d "$SRC/.git" ]]; then
        rm -rf "$SRC"
        git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$SRC"
    fi

    cmake -S "$SRC" -B "$SRC/build-avx" \
        -DCMAKE_BUILD_TYPE=Release \
        -DGGML_NATIVE=OFF \
        -DGGML_CUDA=OFF \
        -DGGML_VULKAN=OFF \
        -DGGML_BLAS=OFF \
        -DGGML_SSE42=ON \
        -DGGML_AVX=ON \
        -DGGML_AVX2=OFF \
        -DGGML_AVX_VNNI=OFF \
        -DGGML_BMI2=OFF \
        -DGGML_FMA=OFF \
        -DGGML_F16C="$f16c" \
        -DGGML_AVX512=OFF \
        -DGGML_AVX512_VBMI=OFF \
        -DGGML_AVX512_VNNI=OFF \
        -DGGML_AVX512_BF16=OFF \
        -DGGML_AMX_TILE=OFF \
        -DGGML_AMX_INT8=OFF \
        -DGGML_AMX_BF16=OFF

    cmake --build "$SRC/build-avx" --config Release -j "$jobs" --target llama-server llama-cli

    if [[ ! -x "$SRC/build-avx/bin/llama-server" || ! -x "$SRC/build-avx/bin/llama-cli" ]]; then
        echo "A compilação não gerou llama-server e llama-cli." >&2
        exit 1
    fi

    sudo install -m 0755 \
        "$SRC/build-avx/bin/llama-server" \
        "$SRC/build-avx/bin/llama-cli" \
        "$LLAMA_DIR/"

    set +e
    "$LLAMA_DIR/llama-server" --version >/dev/null 2>&1
    rc=$?
    set -e
    if [[ "$rc" -ne 0 ]]; then
        echo "O llama-server compilado não rodou neste processador." >&2
        exit 1
    fi
    echo "llama-server instalado em ${LLAMA_DIR}/llama-server."
fi

passo "Atualizando o menu de aplicativos."
if command -v update-desktop-database >/dev/null 2>&1; then
    sudo update-desktop-database /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    sudo gtk-update-icon-cache -f /usr/share/icons/hicolor || true
fi

echo
echo "Pronto. Abra o menu do Ubuntu e clique em Furyu."
echo "No terminal, o comando é: furyu"
echo "Modelo: ${DESTINO_MODELO}"
echo "Licença do modelo: Apache 2.0. A base é o Qwen2.5-0.5B."
echo "O editor completo ainda não se instala. Esta janela é o teste em português."
