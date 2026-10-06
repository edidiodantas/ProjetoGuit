"""Fixtures compartilhadas da suíte de avaliação RAG."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

TESTES = Path(__file__).resolve().parent
ROOT = TESTES.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CORPUS = TESTES / "corpus"
GOLDEN = json.loads((CORPUS / "golden.json").read_text(encoding="utf-8"))
RESULTADOS = TESTES / "resultados"
RESULTADOS.mkdir(parents=True, exist_ok=True)

ALL_PDFS = sorted(CORPUS.glob("*.pdf"))


@pytest.fixture(scope="session")
def corpus_dir() -> Path:
    return CORPUS


@pytest.fixture(scope="session")
def golden() -> dict:
    return GOLDEN


@pytest.fixture(scope="session")
def all_pdfs() -> list[Path]:
    return ALL_PDFS


def ollama_available() -> bool:
    import urllib.request

    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


skip_without_ollama = pytest.mark.skipif(
    not ollama_available(),
    reason="Ollama indisponível — pulando integração PaperQA/DeepEval",
)

skip_llm_judge = pytest.mark.skipif(
    os.getenv("FURYU_SKIP_LLM_JUDGE", "").strip() in {"1", "true", "yes"}
    or not ollama_available(),
    reason="Juiz LLM DeepEval desativado ou Ollama ausente",
)


@pytest.fixture(scope="session")
def indexed_docs():
    """Indexa o corpus uma vez por sessão de pytest (caro)."""
    if not ollama_available():
        pytest.skip("Ollama indisponível")
    from testes.lib.pipeline import build_settings, index_paths, run_async

    settings = build_settings()
    docs = run_async(index_paths(ALL_PDFS, settings))
    return docs, settings
