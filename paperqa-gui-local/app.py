"""
Furyu: PaperQA2 + Streamlit + Ollama, só na máquina.

llm, summary_llm e agent_llm precisam apontar para ollama/.
Sem agent_llm_config, o PaperQA2 tenta a API da OpenAI.
Os embeddings usam sentence-transformers (st-*), sem API paga.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from paperqa import Docs, Settings
from paperqa.settings import AgentSettings

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "amadeus-verbo")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
PDF_DIR = Path(os.getenv("PDF_DIR", "./documentos"))
PQA_HOME = Path(os.getenv("PQA_HOME", "./.pqa"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "st-multi-qa-MiniLM-L6-cos-v1")
LLM_NAME = f"ollama/{OLLAMA_MODEL}"

PDF_DIR.mkdir(parents=True, exist_ok=True)
PQA_HOME.mkdir(parents=True, exist_ok=True)
os.environ["PQA_HOME"] = str(PQA_HOME.resolve())


def build_ollama_llm_config(model_name: str, base_url: str) -> dict:
    return {
        "model_list": [
            {
                "model_name": model_name,
                "litellm_params": {
                    "model": model_name,
                    "api_base": base_url,
                    "api_type": "ollama",
                },
            }
        ]
    }


def get_settings() -> Settings:
    llm_config = build_ollama_llm_config(LLM_NAME, OLLAMA_BASE_URL)
    return Settings(
        llm=LLM_NAME,
        llm_config=llm_config,
        summary_llm=LLM_NAME,
        summary_llm_config=llm_config,
        agent=AgentSettings(
            agent_llm=LLM_NAME,
            agent_llm_config=llm_config,
        ),
        embedding=EMBEDDING_MODEL,
        paper_directory=str(PDF_DIR.resolve()),
    )


def init_session_state() -> None:
    if "docs" not in st.session_state:
        st.session_state.docs = Docs()
    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = set()
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = None


async def index_pdf(path: Path, settings: Settings) -> None:
    await st.session_state.docs.aadd(str(path), settings=settings)


async def ask_question(question: str, settings: Settings):
    return await st.session_state.docs.aquery(question, settings=settings)


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


st.set_page_config(page_title="Furyu", page_icon="📄", layout="wide")
init_session_state()
settings = get_settings()

st.title("Furyu")
st.caption(
    f"Modelo: `{OLLAMA_MODEL}` · Embeddings: `{EMBEDDING_MODEL}` · "
    f"Ollama: `{OLLAMA_BASE_URL}`"
)

with st.sidebar:
    st.header("Configuração")
    st.markdown(
        f"""
        - **LLM**: `{LLM_NAME}`
        - **Embeddings**: local (`st-*`)
        - **PDFs**: `{PDF_DIR}`
        - **PQA_HOME**: `{PQA_HOME}`

        O modelo é o Amadeus Verbo de 0,5 bilhão, registrado no Ollama
        como `amadeus-verbo`. Não defina `OPENAI_API_KEY`.
        """
    )
    if st.button("Limpar sessão", type="secondary", use_container_width=True):
        st.session_state.docs = Docs()
        st.session_state.indexed_files = set()
        st.session_state.last_answer = None
        st.success("Sessão limpa.")
        st.rerun()

st.subheader("1. Enviar PDFs")
uploaded = st.file_uploader(
    "Selecione um ou mais PDFs",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded:
    for f in uploaded:
        dest = PDF_DIR / f.name
        if f.name in st.session_state.indexed_files:
            st.info(f"Já indexado: {f.name}")
            continue
        dest.write_bytes(f.getbuffer())
        with st.status(
            f"Indexando `{f.name}` neste computador. Pode demorar.",
            expanded=True,
        ) as status:
            st.write("Salvando o arquivo…")
            st.write("Extraindo o texto e gerando os embeddings locais…")
            st.write("Lendo os metadados com o Amadeus Verbo…")
            try:
                run_async(index_pdf(dest, settings))
                st.session_state.indexed_files.add(f.name)
                status.update(label=f"Indexado: {f.name}", state="complete")
            except Exception as exc:  # noqa: BLE001
                status.update(label=f"Erro ao indexar {f.name}", state="error")
                st.error(f"Falha: {exc}")

if st.session_state.indexed_files:
    st.success(
        "Documentos na sessão: " + ", ".join(sorted(st.session_state.indexed_files))
    )
else:
    st.info("Nenhum PDF indexado ainda.")

st.subheader("2. Pergunta")
question = st.text_area(
    "Digite sua pergunta sobre os documentos",
    placeholder="Ex.: Quais são as principais conclusões do artigo?",
    height=100,
)
ask_clicked = st.button(
    "Perguntar",
    type="primary",
    disabled=not st.session_state.indexed_files or not question.strip(),
)

if ask_clicked:
    with st.status(
        "Processando com o Amadeus Verbo neste computador. Não feche a aba.",
        expanded=True,
    ) as status:
        st.write("Buscando trechos nos documentos…")
        st.write("Resumindo as evidências…")
        st.write("Escrevendo a resposta com as citações…")
        try:
            session = run_async(ask_question(question.strip(), settings))
            st.session_state.last_answer = session
            status.update(label="Resposta pronta", state="complete")
        except Exception as exc:  # noqa: BLE001
            status.update(label="Erro na consulta", state="error")
            st.error(f"Falha: {exc}")
            st.session_state.last_answer = None

session = st.session_state.last_answer
if session is not None:
    st.subheader("3. Resposta")
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
                    + (f" (score: {score})" if score is not None else "")
                )
                if citation:
                    st.caption(citation)
                body = getattr(text, "text", None) if text is not None else None
                st.write(body if body is not None else text)
                st.divider()
