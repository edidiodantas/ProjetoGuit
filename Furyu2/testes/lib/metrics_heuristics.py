"""Métricas locais no estilo Ragas (sem API paga / sem VertexAI).

Implementa aproximações de:
- context_relevance / context_precision
- context_recall
- faithfulness
- answer_relevance
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import numpy as np


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-ZÀ-ÿ0-9\-]{3,}", (text or "").lower())}


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer

    # Modelo leve; alinhado à ideia de embeddings locais do Furyu
    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def embed(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = _embedder()
    vectors = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return 0.0
    return float(np.dot(a, b))


@dataclass
class MetricResult:
    name: str
    score: float
    detail: str = ""


def context_relevance(question: str, contexts: list[str]) -> MetricResult:
    """Média da similaridade pergunta↔cada contexto (≈ Contextual Relevancy)."""
    if not contexts:
        return MetricResult("context_relevance", 0.0, "sem contextos")
    q = embed([question])[0]
    ctx = embed(contexts)
    scores = [cosine(q, c) for c in ctx]
    return MetricResult(
        "context_relevance",
        float(np.mean(scores)),
        f"n={len(scores)} min={min(scores):.3f} max={max(scores):.3f}",
    )


def context_recall_markers(contexts: list[str], markers: list[str]) -> MetricResult:
    """Fração de marcadores-ouro presentes no texto recuperado (≈ Context Recall)."""
    blob = "\n".join(contexts).lower()
    if not markers:
        return MetricResult("context_recall", 0.0, "sem marcadores")
    hits = [m for m in markers if m.lower() in blob]
    return MetricResult(
        "context_recall",
        len(hits) / len(markers),
        f"hits={hits}",
    )


def answer_relevance(question: str, answer: str) -> MetricResult:
    if not (answer or "").strip():
        return MetricResult("answer_relevance", 0.0, "resposta vazia")
    q, a = embed([question, answer])
    return MetricResult("answer_relevance", cosine(q, a), "")


def faithfulness_support(answer: str, contexts: list[str]) -> MetricResult:
    """Aproxima Faithfulness: tokens da resposta cobertos pelos contextos.

    Score = |tokens(resposta) ∩ tokens(contextos)| / |tokens(resposta)|
    (sentenças curtas/boilerplate reduzem o denominador efetivo).
    """
    ans_tok = _tokenize(answer)
    if not ans_tok:
        return MetricResult("faithfulness", 0.0, "resposta vazia")
    ctx_tok = _tokenize("\n".join(contexts))
    if not ctx_tok:
        return MetricResult("faithfulness", 0.0, "sem contextos")
    # remove stopwords muito genéricas em PT/EN
    stop = {
        "que",
        "de",
        "da",
        "do",
        "das",
        "dos",
        "para",
        "com",
        "uma",
        "por",
        "como",
        "the",
        "and",
        "for",
        "are",
        "this",
        "that",
        "não",
        "nao",
        "sim",
    }
    ans_tok = {t for t in ans_tok if t not in stop}
    if not ans_tok:
        return MetricResult("faithfulness", 1.0, "só stopwords")
    inter = ans_tok & ctx_tok
    score = len(inter) / len(ans_tok)
    return MetricResult("faithfulness", score, f"supported={len(inter)}/{len(ans_tok)}")


def forbidden_hit_rate(text: str, forbidden: list[str]) -> MetricResult:
    blob = (text or "").lower()
    hits = [f for f in forbidden if f.lower() in blob]
    # score 1.0 = limpo
    score = 0.0 if hits else 1.0
    return MetricResult("no_forbidden", score, f"hits={hits}")


def doc_name_recall(context_names: list[str], contexts: list[str], ground_truth_doc: str) -> MetricResult:
    """1.0 se o documento ouro aparece no nome ou no texto dos contextos."""
    needle = (ground_truth_doc or "").lower().replace(".pdf", "")
    blob_names = " | ".join(context_names).lower()
    blob_ctx = "\n".join(contexts).lower()
    ok = needle in blob_names or needle.replace("_", " ") in blob_ctx or needle in blob_ctx
    # também tenta tokens distintivos do filename
    if not ok:
        parts = [p for p in re.split(r"[_\-.]+", needle) if len(p) > 4]
        ok = any(p in blob_names or p in blob_ctx for p in parts)
    return MetricResult("doc_recall", 1.0 if ok else 0.0, f"target={ground_truth_doc}")
