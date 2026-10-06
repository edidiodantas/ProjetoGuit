# Furyu

Pesquisa e leitura de artigos científicos no seu computador.

Interface gráfica para [PaperQA2](https://github.com/Future-House/paper-qa) usando **somente IA local via Ollama** — custo zero, sem OpenAI.

O **mesmo** `app.py` roda no Windows 11 e no Ubuntu LTS. Só o jeito de instalar muda.

> Esta pasta se chama **Furyu2** (para não misturar com a pasta `Furyu` que você já tem no pendrive).

## Levar no pendrive → outro PC

1. Copie a pasta **inteira** `Furyu2` para o pendrive.
2. No PC de destino, **copie do pendrive para o disco interno** (SSD/HD). Não rode o `.venv` de dentro do pendrive se ele estiver em exFAT.
3. Siga o guia do sistema:
   - **Ubuntu LTS:** [INSTALAR-UBUNTU.md](INSTALAR-UBUNTU.md)
   - **Windows 11:** [INSTALAR-WINDOWS.md](INSTALAR-WINDOWS.md)
   - **Deepin (opcional):** [INSTALAR-DEEPIN.md](INSTALAR-DEEPIN.md)

Funções da tela: [FUNCOES.txt](FUNCOES.txt)

## Instalação rápida — Ubuntu LTS (22.04 / 24.04)

```bash
# 1) Copie Furyu2 para o home, por exemplo:
cp -a /media/SEU_USUARIO/PENDRIVE/Furyu2 ~/Furyu2
cd ~/Furyu2

# 2) Instale dependências do sistema + ambiente Python
bash install-ubuntu.sh

# 3) Instale o Ollama (se ainda não tiver) e baixe o modelo
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.5:4b

# 4) Edite o .env (e-mail real da escola para Unpaywall)
nano .env

# 5) Abra a interface
bash rodar-ubuntu.sh
```

Abra http://localhost:8501

## Instalação rápida — Windows 11

Copie `Furyu2` para `C:\Furyu2` → Python 3.12 → Ollama → `install-windows.bat` → `ollama pull qwen3.5:4b` → `rodar-windows.bat`.

## Hardware sugerido

- **Windows 11:** i7, 8 GB RAM, RTX ~6 GB VRAM → `qwen3.5:9b` (ou 4b se lento)
- **Ubuntu LTS:** 8 GB RAM ou mais → comece com `qwen3.5:4b`
- Alternativa leve: `qwen3.5:2b` no `.env`

## Por que `llm="ollama/..."` sozinho não basta

O PaperQA2 usa **quatro** papéis de LLM. O padrão de todos é OpenAI GPT-4o:

| Papel | Setting | Uso |
| --- | --- | --- |
| Resposta + metadados | `llm` + `llm_config` | Indexar e responder |
| Resumos de evidência | `summary_llm` + `summary_llm_config` | `gather_evidence` |
| Agente (ferramentas) | `agent.agent_llm` + `agent_llm_config` | Escolher ferramentas |
| Enrichment multimodal | `parsing.enrichment_llm` + `enrichment_llm_config` | Figuras/tabelas |

Este app configura os quatro + `api_base` do Ollama. Embeddings usam `st-*` (sentence-transformers), sem API paga.

**Não defina `OPENAI_API_KEY`.**

## Uso

1. Faça upload de PDFs **ou** busque um artigo aberto (seção 2 da tela).
2. Aguarde a indexação (status na tela — será lento no 9B).
3. Digite a pergunta e clique em **Perguntar**.
4. Veja a resposta com citações e abra **Mostrar fontes**.
5. Use **Limpar sessão** na barra lateral para recomeçar.

A busca acadêmica **não pede login**. Começa no **Oasisbr (IBICT)**. Se falhar, usa Semantic Scholar/Crossref. Unpaywall só entra para PDF aberto. No `.env`: `CONTACT_EMAIL`.

## Latência esperada

Com pouca VRAM, ~2 tokens/s é esperado; uma resposta curta pode levar 1–2 minutos. Se ficar lento, no `.env`:

```bash
OLLAMA_MODEL=qwen3.5:4b
```

Depois: `ollama pull qwen3.5:4b`

## Troubleshooting

| Problema | Solução |
| --- | --- |
| Erro pedindo OpenAI / GPT-4o | Confirme os quatro papéis + `*_config` apontando para Ollama (já no `app.py`) |
| `Connection refused :11434` | Inicie o Ollama e teste `ollama list` |
| Modelo não encontrado | `ollama pull qwen3.5:4b` (ou o nome no `.env`) |
| Python antigo | Use 3.11+ (Ubuntu 22.04/24.04 já atendem) |
| Embedding lento no 1º run | Download do modelo HuggingFace na 1ª indexação |
| Timeout do agente | O app usa 1800s; se ainda estourar, use `qwen3.5:4b` ou `2b` |

## Arquitetura

- **LLM / summary / agent / enrichment:** Ollama (`ollama/<modelo>` via LiteLLM)
- **Embeddings:** `st-multi-qa-MiniLM-L6-cos-v1` (local)
- **UI:** Streamlit
- **Índice:** `agent.index.paper_directory` e `index_directory`
