"""
Furyu — pesquisa e leitura de artigos científicos no PC
(PaperQA2 + Streamlit + Ollama, 100% local, custo zero).

Importante:
- Configure llm, summary_llm, agent_llm E enrichment_llm para ollama/...
- Sem agent_llm_config, o PaperQA2 tenta OpenAI (GPT-4o) por padrão.
- Sem enrichment_llm_config, o parser multimodal também tenta OpenAI.
- paper_directory no Settings é ignorado; o caminho certo é agent.index.
- Embeddings usam sentence-transformers (st-*), sem API paga.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from paperqa import Docs, Settings
from paperqa.settings import (
    AgentSettings,
    AnswerSettings,
    IndexSettings,
    ParsingSettings,
)

from academic_search import (
    download_pdf,
    resolve_pdf_url,
    search_academic,
    _safe_filename,
)

# ---------------------------------------------------------------------------
# Ambiente
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Evita fallback acidental para a API paga se a chave existir no shell.
os.environ.pop("OPENAI_API_KEY", None)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "st-multi-qa-MiniLM-L6-cos-v1")


def _path_from_env(key: str, default: str) -> Path:
    raw = Path(os.getenv(key, default))
    return raw if raw.is_absolute() else (ROOT / raw)


PDF_DIR = _path_from_env("PDF_DIR", "./documentos")
PQA_HOME = _path_from_env("PQA_HOME", "./.pqa")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "").strip()
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()

# LiteLLM usa o prefixo "ollama/" + nome do modelo no Ollama
LLM_NAME = f"ollama/{OLLAMA_MODEL}"

PDF_DIR.mkdir(parents=True, exist_ok=True)
PQA_HOME.mkdir(parents=True, exist_ok=True)
os.environ["PQA_HOME"] = str(PQA_HOME.resolve())


def build_ollama_llm_config(model_name: str, base_url: str) -> dict:
    """Config LiteLLM Router para o Ollama local (obrigatório para evitar OpenAI)."""
    return {
        "model_list": [
            {
                "model_name": model_name,
                "litellm_params": {
                    "model": model_name,
                    "api_base": base_url,
                    "api_type": "ollama",
                    "timeout": 600,
                    "temperature": 0.0,
                },
            }
        ]
    }


def get_settings() -> Settings:
    """Settings PaperQA2 100% locais: Ollama (LLM) + sentence-transformers (embeddings)."""
    llm_config = build_ollama_llm_config(LLM_NAME, OLLAMA_BASE_URL)
    pdf_dir = str(PDF_DIR.resolve())
    index_dir = str((PQA_HOME / "indexes").resolve())

    return Settings(
        llm=LLM_NAME,
        llm_config=llm_config,
        summary_llm=LLM_NAME,
        summary_llm_config=llm_config,
        embedding=EMBEDDING_MODEL,
        agent=AgentSettings(
            agent_llm=LLM_NAME,
            agent_llm_config=llm_config,
            timeout=1800.0,
            index=IndexSettings(
                paper_directory=pdf_dir,
                index_directory=index_dir,
                concurrency=1,
            ),
        ),
        parsing=ParsingSettings(
            # Sem isto, o PaperQA2 enriquece figuras/tabelas com GPT-4o.
            enrichment_llm=LLM_NAME,
            enrichment_llm_config=llm_config,
            multimodal=False,
        ),
        answer=AnswerSettings(
            max_concurrent_requests=1,
        ),
    )


def ollama_status() -> tuple[bool, str]:
    """Checa se o servidor Ollama responde e se o modelo está instalado."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=3) as resp:
            payload = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.URLError as exc:
        return False, f"Ollama inacessível em {OLLAMA_BASE_URL} ({exc.reason})"
    except Exception as exc:  # noqa: BLE001
        return False, f"Falha ao consultar Ollama: {exc}"

    names = []
    for item in payload.get("models", []):
        name = item.get("name") or item.get("model") or ""
        names.append(name)
        if name == OLLAMA_MODEL or name.startswith(f"{OLLAMA_MODEL}:"):
            return True, f"Ollama ok · modelo `{OLLAMA_MODEL}` encontrado"

    if names:
        preview = ", ".join(names[:8])
        return False, (
            f"Ollama ok, mas `{OLLAMA_MODEL}` não está em `ollama list`. "
            f"Instale com: `ollama pull {OLLAMA_MODEL}`. Disponíveis: {preview}"
        )
    return False, "Ollama respondeu, mas nenhum modelo está instalado."


def init_session_state() -> None:
    if "docs" not in st.session_state:
        st.session_state.docs = Docs()
    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = set()
    if "search_hits" not in st.session_state:
        st.session_state.search_hits = []
    if "search_note" not in st.session_state:
        st.session_state.search_note = ""
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = None


async def index_pdf(path: Path, settings: Settings) -> None:
    await st.session_state.docs.aadd(str(path), settings=settings)


async def ask_question(question: str, settings: Settings):
    return await st.session_state.docs.aquery(question, settings=settings)


def run_async(coro):
    """Executa corrotinas no Streamlit sem brigar com o event loop da UI."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # Streamlit já tem loop: asyncio.run() na mesma thread quebra.
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Furyu",
    page_icon="📘",
    layout="wide",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Furyu — pesquisa e leitura de artigos científicos no PC (IA local, Ollama).",
    },
)

init_session_state()
settings = get_settings()
ollama_ok, ollama_msg = ollama_status()

# ---------------------------------------------------------------------------
# Customização visual (mesma identidade no Windows e no Ubuntu)
# ---------------------------------------------------------------------------
MARK_SVG = """
<svg width="88" height="88" viewBox="0 0 88 88" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="furyuInk" x1="12" y1="8" x2="76" y2="80" gradientUnits="userSpaceOnUse">
      <stop stop-color="#0B4F6C"/>
      <stop offset="1" stop-color="#1B7A9E"/>
    </linearGradient>
  </defs>
  <rect x="6" y="10" width="52" height="68" rx="6" stroke="url(#furyuInk)" stroke-width="3.2"/>
  <path d="M58 18h16c4 0 8 4 8 8v44c0 4-4 8-8 8H58" stroke="url(#furyuInk)" stroke-width="3.2" stroke-linejoin="round"/>
  <path d="M20 28h28M20 40h28M20 52h18" stroke="#0B4F6C" stroke-width="2.6" stroke-linecap="round" opacity="0.85"/>
  <circle cx="68" cy="48" r="10" fill="#E8F4F8" stroke="#0B4F6C" stroke-width="2.4"/>
  <path d="M64 48h8M68 44v8" stroke="#0B4F6C" stroke-width="2.2" stroke-linecap="round"/>
</svg>
"""

_UBUNTU_CSS = (ROOT / "assets" / "fonts.css").read_text(encoding="utf-8")
st.html(
    f"""
    <style>
    {_UBUNTU_CSS}
    :root {{
        --furyu-ink: #0B4F6C;
        --furyu-ink-soft: #1B7A9E;
        --furyu-mist: #E8F4F8;
        --furyu-sand: #F3F7F9;
        --furyu-line: #C9D9E1;
        --furyu-text: #1A2B33;
    }}
    /* Fonte Ubuntu só no texto — NÃO em [class*="css"] (quebra ícones do Streamlit). */
    html, body, .stApp, .stMarkdown, [data-testid="stWidgetLabel"],
    [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] {{
        font-family: 'Ubuntu', sans-serif;
        color: var(--furyu-text);
    }}
    [data-testid="stIconMaterial"] {{
        font-family: 'Material Symbols Rounded' !important;
    }}
    /* Remove chrome do Streamlit que vira letra/ícone fantasma (ex.: "r") */
    [data-testid="stTextInputClearButton"],
    [data-testid="stHeaderActionElements"],
    [data-testid="stElementToolbar"],
    [data-testid="stElementToolbarButton"],
    [data-testid="stElementToolbarButtonContainer"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stBaseButton-header"],
    [data-testid="stBaseButton-headerNoPadding"],
    .stDeployButton,
    [class*="stDeployButton"],
    header[data-testid="stHeader"] {{
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}
    textarea {{
        resize: none !important;
    }}
    .app-section-title {{
        font-family: 'Ubuntu', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.45rem;
        color: var(--furyu-ink);
        margin: 1rem 0 0.35rem 0;
        letter-spacing: -0.02em;
    }}
    /* Botão Perguntar bem visível (não parece caixinha) */
    div[data-testid="stForm"] [data-testid="stBaseButton-primary"],
    div[data-testid="stButton"] > button[kind="primary"] {{
        min-width: 160px !important;
        min-height: 42px !important;
        font-size: 1.05rem !important;
    }}
    .stApp {{
        margin-top: 0 !important;
        padding-top: 0 !important;
        background:
            radial-gradient(1200px 420px at 8% -10%, #d9eef5 0%, transparent 55%),
            radial-gradient(900px 380px at 100% 0%, #e7f2e8 0%, transparent 50%),
            linear-gradient(180deg, #f7fbfc 0%, #eef4f7 100%);
    }}
    .block-container {{
        padding-top: 0.6rem !important;
        padding-bottom: 1.4rem !important;
        max-width: 1180px;
    }}
    .main .block-container {{
        padding-top: 0.6rem !important;
    }}
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0B4F6C 0%, #0a3f56 100%);
        border-right: none;
    }}
    section[data-testid="stSidebar"] * {{
        color: #F4FAFC !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {{
        color: #D7E8EF !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stAlert"] {{
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.18);
    }}
    .brand-wrap {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 0.2rem 0 0.35rem 0;
    }}
    .brand-wrap svg {{
        flex-shrink: 0;
        width: 78px;
        height: 78px;
        filter: drop-shadow(0 8px 18px rgba(11, 79, 108, 0.18));
    }}
    .brand-text {{
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
    }}
    .app-title {{
        font-family: 'Ubuntu', sans-serif !important;
        font-weight: 700 !important;
        font-size: clamp(2.8rem, 5vw, 4.1rem);
        letter-spacing: -0.03em;
        color: var(--furyu-ink);
        margin: 0;
        line-height: 0.95;
    }}
    .app-tagline {{
        font-family: 'Ubuntu', sans-serif !important;
        font-size: 1.05rem;
        color: #456574;
        margin: 0;
    }}
    .meta-strip {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin: 0.55rem 0 0.85rem 0;
    }}
    .meta-chip {{
        font-size: 0.84rem;
        color: var(--furyu-ink);
        background: rgba(232, 244, 248, 0.92);
        border: 1px solid var(--furyu-line);
        padding: 0.28rem 0.7rem;
        border-radius: 999px;
    }}
    .section-rule {{
        height: 1px;
        background: linear-gradient(90deg, var(--furyu-line), transparent);
        margin: 0.35rem 0 0.85rem 0;
        border: 0;
    }}
    h2, h3 {{
        color: var(--furyu-ink) !important;
        letter-spacing: -0.02em;
    }}
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: linear-gradient(135deg, #0B4F6C, #1B7A9E) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 8px 18px rgba(11, 79, 108, 0.22);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    div[data-testid="stButton"] > button[kind="primary"]:hover {{
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(11, 79, 108, 0.28);
    }}
    div[data-testid="stButton"] > button[kind="secondary"] {{
        border: 1px solid var(--furyu-line) !important;
        color: var(--furyu-ink) !important;
        background: rgba(255,255,255,0.72) !important;
    }}
    [data-testid="stFileUploader"] {{
        background: rgba(255,255,255,0.72);
        border: 1px dashed var(--furyu-line);
        border-radius: 14px;
        padding: 0.4rem 0.6rem;
    }}
    </style>
    <div class="brand-wrap">
      {MARK_SVG}
      <div class="brand-text">
        <div class="app-title">Furyu</div>
        <p class="app-tagline">Pesquisa e leitura de artigos científicos no seu computador.</p>
      </div>
    </div>
    <div class="meta-strip">
      <span class="meta-chip">Modelo: {OLLAMA_MODEL}</span>
      <span class="meta-chip">Embeddings: {EMBEDDING_MODEL}</span>
      <span class="meta-chip">Ollama: {OLLAMA_BASE_URL}</span>
    </div>
    <hr class="section-rule" />
    """
)

if ollama_ok:
    st.success(ollama_msg)
else:
    st.error(ollama_msg)

with st.sidebar:
    st.markdown("### Configuração")
    st.markdown(
        f"""
        - **LLM / resumo / agente / enriquecimento**: `{LLM_NAME}`
        - **Embeddings**: locais (`st-*`)
        - **PDFs**: `{PDF_DIR}`
        - **PQA_HOME**: `{PQA_HOME}`

        Troque o modelo no arquivo `.env` (`OLLAMA_MODEL`) para
        `qwen3.5:4b` ou `qwen3.5:2b` se estiver lento demais.
        """
    )
    st.warning(
        "A primeira resposta pode levar alguns minutos (carga do modelo). "
        "Não feche a aba. Isso é normal em PC local."
    )
    if st.button("Limpar sessão", type="secondary", use_container_width=True):
        st.session_state.docs = Docs()
        st.session_state.indexed_files = set()
        st.session_state.search_hits = []
        st.session_state.search_note = ""
        st.session_state.last_answer = None
        st.success("Sessão limpa.")
        st.rerun()

# --- Enviar PDFs ---
st.html('<div class="app-section-title">1. Enviar PDFs</div>')
uploaded = st.file_uploader(
    "Selecione um ou mais PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    help="Apenas arquivos PDF. Cada um é lido e indexado nesta sessão.",
)

if uploaded:
    for f in uploaded:
        dest = PDF_DIR / Path(f.name).name
        if f.name in st.session_state.indexed_files:
            st.info(f"Já indexado: {f.name}")
            continue
        dest.write_bytes(f.getbuffer())
        with st.status(
            f"Indexando `{f.name}` com Ollama + embeddings locais… "
            "(pode demorar)",
            expanded=True,
        ) as status:
            st.write("Salvando arquivo…")
            st.write("Extraindo texto e gerando embeddings locais…")
            st.write("Inferindo metadados via modelo Ollama (lento)…")
            try:
                run_async(index_pdf(dest, settings))
                st.session_state.indexed_files.add(f.name)
                status.update(label=f"Indexado: {f.name}", state="complete")
            except Exception as exc:  # noqa: BLE001
                status.update(label=f"Erro ao indexar {f.name}", state="error")
                st.error(f"Falha: {exc}")

if st.session_state.indexed_files:
    st.success(
        "Documentos na sessão: "
        + ", ".join(sorted(st.session_state.indexed_files))
    )
else:
    st.info("Nenhum PDF indexado ainda.")

# --- Busca acadêmica (acesso aberto) ---
st.html('<div class="app-section-title">2. Buscar artigos (acesso aberto)</div>')
st.caption(
    "Não há login. A busca começa no **Oasisbr (IBICT)**, que reúne SciELO, "
    "repositórios e periódicos brasileiros. Se o Oasisbr falhar, usa Semantic Scholar/Crossref. "
    "Unpaywall só entra para achar PDF **aberto**. Paywall não é baixado."
)
search_q = st.text_input(
    "Tema ou título",
    placeholder="Ex.: educação inclusiva Brasil  OU  photosynthesis chlorophyll",
    key="search_query",
)
col_a, col_b = st.columns([1, 3])
with col_a:
    search_clicked = st.button("Buscar", type="secondary", use_container_width=True)
with col_b:
    if not CONTACT_EMAIL:
        st.caption("Dica: defina CONTACT_EMAIL no `.env` para o Unpaywall achar mais PDFs.")

if search_clicked:
    if not search_q.strip():
        st.warning("Digite um tema para buscar.")
        st.session_state.search_hits = []
        st.session_state.search_note = ""
    else:
        with st.spinner("Consultando Oasisbr / Unpaywall…"):
            try:
                hits, note = search_academic(
                    search_q.strip(),
                    s2_key=S2_API_KEY,
                    email=CONTACT_EMAIL,
                )
                st.session_state.search_hits = hits
                st.session_state.search_note = note
            except Exception as exc:  # noqa: BLE001
                st.session_state.search_hits = []
                st.session_state.search_note = ""
                st.error(f"Falha na busca: {exc}")

hits: list = st.session_state.search_hits
if hits:
    note = st.session_state.get("search_note") or "catálogo público"
    n_oa = sum(1 for h in hits if h.has_open_pdf)
    st.write(f"{len(hits)} resultado(s) via {note} · {n_oa} com PDF aberto:")
    for i, hit in enumerate(hits):
        with st.container(border=True):
            ano = hit.year or "?"
            st.markdown(f"**{hit.title}** ({ano})")
            if hit.authors:
                st.caption(hit.authors)
            extra = " · ".join(x for x in (hit.venue, hit.source) if x)
            if extra:
                st.caption(extra)
            if hit.doi:
                st.caption(f"DOI: {hit.doi}")
            if hit.abstract:
                st.write(hit.abstract)
            can_index = ollama_ok and hit.has_open_pdf
            if not hit.has_open_pdf:
                st.caption("Sem PDF aberto. Baixe no SciELO/revista e use Enviar PDFs.")
            btn_key = f"idx-{i}_{re.sub(r'[^a-zA-Z0-9_-]', '_', (hit.paper_id or hit.doi or hit.title))[:50]}"
            if st.button(
                "Baixar PDF aberto e indexar",
                key=btn_key,
                disabled=not can_index,
            ):
                fname = _safe_filename(hit.title, hit.year)
                if fname in st.session_state.indexed_files:
                    st.info(f"Já indexado: {fname}")
                else:
                    with st.status(f"Obtendo `{fname}`…", expanded=True) as status:
                        try:
                            st.write("Resolvendo link de PDF aberto…")
                            pdf_url = resolve_pdf_url(hit, CONTACT_EMAIL)
                            if not pdf_url:
                                raise RuntimeError(
                                    "Sem PDF em acesso aberto. "
                                    "Baixe no SciELO/site da revista e use Enviar PDFs."
                                )
                            st.write("Baixando…")
                            dest = download_pdf(pdf_url, PDF_DIR, fname)
                            st.write("Indexando com Ollama (pode demorar)…")
                            run_async(index_pdf(dest, settings))
                            st.session_state.indexed_files.add(dest.name)
                            status.update(
                                label=f"Indexado: {dest.name}", state="complete"
                            )
                            st.rerun()
                        except Exception as exc:  # noqa: BLE001
                            status.update(label="Não foi possível indexar", state="error")
                            st.error(str(exc))
elif search_clicked and search_q.strip():
    st.info("Nenhum artigo encontrado. Tente outras palavras.")

# --- Pergunta ---
# Título via HTML próprio (sem link/ícone do Streamlit, que às vezes vira "r" fantasma)
st.html('<div class="app-section-title">3. Pergunta</div>')
st.caption("Exemplo: Quais são as principais conclusões do artigo?")
question = st.text_input(
    "Digite sua pergunta sobre os documentos",
    placeholder="Escreva sua pergunta aqui…",
    key="pergunta_texto",
)
ask_clicked = st.button(
    "Perguntar",
    type="primary",
    use_container_width=False,
    disabled=not st.session_state.indexed_files or not question.strip() or not ollama_ok,
)

if ask_clicked:
    with st.status(
        f"Processando com `{OLLAMA_MODEL}` local… "
        "Não feche a aba. Pode levar 1–3 minutos.",
        expanded=True,
    ) as status:
        st.write("Buscando evidências nos trechos indexados…")
        st.write("Gerando resumos contextuais (summary_llm via Ollama)…")
        st.write("Compondo a resposta final com citações…")
        try:
            session = run_async(ask_question(question.strip(), settings))
            st.session_state.last_answer = session
            status.update(label="Resposta pronta", state="complete")
        except Exception as exc:  # noqa: BLE001
            status.update(label="Erro na consulta", state="error")
            st.error(f"Falha: {exc}")
            st.session_state.last_answer = None

# --- Resposta ---
session = st.session_state.last_answer
if session is not None:
    st.subheader("4. Resposta")
    answer_text = getattr(session, "formatted_answer", None) or getattr(
        session, "answer", str(session)
    )
    st.markdown(answer_text)
    with st.expander("Mostrar fontes", expanded=False):
        contexts = getattr(session, "contexts", None) or []
        if not contexts:
            refs = getattr(session, "references", None)
            if refs:
                st.markdown(refs)
            else:
                st.write("Nenhuma fonte estruturada retornada.")
        else:
            for i, ctx in enumerate(contexts, start=1):
                text = getattr(ctx, "text", None) or getattr(ctx, "context", ctx)
                score = getattr(ctx, "score", None)
                citation = ""
                if hasattr(text, "doc") and getattr(text, "doc", None):
                    citation = getattr(text.doc, "citation", "") or getattr(
                        text.doc, "docname", ""
                    )
                elif hasattr(ctx, "text") and hasattr(ctx.text, "name"):
                    citation = ctx.text.name
                st.markdown(
                    f"**Fonte {i}**"
                    + (f" (relevância: {score})" if score is not None else "")
                )
                if citation:
                    st.caption(citation)
                body = getattr(text, "text", None) if text is not None else None
                st.write(body if body is not None else text)
                st.divider()
