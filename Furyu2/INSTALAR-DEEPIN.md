# Instalação do Furyu no Deepin 23.1 (este PC)

O **Furyu** é o **mesmo** `app.py` do Windows. Aqui só muda *onde* instalar, para **não usar o SSD**.

Detectado neste Deepin:

- Deepin 23.1, Python 3.12 (já ok)
- Ryzen 5 4500, 16 GB RAM
- GeForce GTX 750 **4 GB** (Maxwell) — GPU antiga; o Ollama quase certamente roda em **CPU**
- Pendrive em **exFAT** — não dá para criar `.venv` nele; por isso os scripts usam uma imagem **ext4** no próprio pendrive

**Não instale agora** se ainda não for a hora. Quando for:

## 1. Deixe o projeto no pendrive

```bash
cd /media/Edidio/8662-B449/Furyu2
```

(Se clonar do GitHub, clone **para o pendrive**, nunca para `~/Projects`.)

```bash
cd /media/Edidio/8662-B449
git clone https://github.com/edidiodantas/Furyu2.git
cd Furyu2
```

Repositório **privado**: faça `gh auth login` antes, se o `git clone` pedir senha.

## 2. Ambiente Python + caches no pendrive

```bash
bash scripts/setup-deepin.sh
```

Isso cria `linux-env.img` (ext4, 16 G esparso), monta em `linux-env/` e instala o venv **lá dentro**.  
`~/.cache` e `~/.ollama` do SSD não são usados.

O script pede `sudo` só para `mount` da imagem.

## 3. Ollama (binário no sistema, modelos no pendrive)

O instalador oficial grava o programa em `/usr/local` (é o SO; são poucos MB). Os **pesos do modelo** vão para o pendrive.

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl stop ollama 2>/dev/null || true
sudo systemctl disable ollama 2>/dev/null || true

export OLLAMA_MODELS="/media/Edidio/8662-B449/Furyu2/linux-env/ollama-models"
ollama serve
```

Em **outro** terminal:

```bash
export OLLAMA_MODELS="/media/Edidio/8662-B449/Furyu2/linux-env/ollama-models"
ollama pull qwen3.5:4b
ollama run qwen3.5:4b "Olá"
```

Neste PC use **4b** (ou `qwen3.5:2b` se ainda ficar pesado). O 9B no Windows com RTX 6 GB já era limite; na GTX 750 4 GB + CPU não vale.

## 4. Abrir a interface

```bash
cd /media/Edidio/8662-B449/Furyu2
bash scripts/rodar-deepin.sh
```

Abra http://localhost:8501

Antes de ejetar o pendrive:

```bash
bash scripts/desmontar-linux-env.sh
```

## O que não vai para o SSD

| Item | Onde fica |
| --- | --- |
| Código | pendrive + GitHub privado |
| `.venv`, pip, HuggingFace, `.pqa` | `linux-env.img` no pendrive |
| Modelos Ollama | `linux-env/ollama-models` no pendrive |
| PDFs enviados | `documentos/` no pendrive |
| Binário `ollama` / `python3` do sistema | Deepin (`/usr`) — inevitável e pequeno |

## Troubleshooting Deepin

| Problema | Solução |
| --- | --- |
| `mount: failed to setup loop device` | plugue o pendrive, rode `bash scripts/montar-linux-env.sh` |
| `Permission denied` no venv | a imagem precisa estar montada; não use `.venv` no exFAT |
| Ollama grava em `~/.ollama` | `systemctl stop ollama` e suba com `OLLAMA_MODELS=... ollama serve` |
| Pedido de OpenAI / GPT-4o | já tratado no `app.py` (llm + summary + agent + enrichment) |
| Muito lento | `OLLAMA_MODEL=qwen3.5:2b` no `.env` e `ollama pull qwen3.5:2b` |
| Unpaywall sem PDF | coloque um e-mail real da escola em `CONTACT_EMAIL` no `.env` |
