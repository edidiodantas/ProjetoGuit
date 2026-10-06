"""Pilar 1 — Avaliação do Retrieval (Context Relevance + Context Recall)."""

from __future__ import annotations

import json

from testes.conftest import RESULTADOS, skip_without_ollama
from testes.lib.metrics_heuristics import (
    context_recall_markers,
    context_relevance,
    doc_name_recall,
)
from testes.lib.pipeline import query_docs_fast


@skip_without_ollama
def test_retrieval_context_relevance_and_recall(golden, indexed_docs):
    """Para cada caso ret_*: contextos relevantes e cobrindo marcadores-ouro."""
    docs, settings = indexed_docs
    report = []
    cases = [c for c in golden["cases"] if c["id"].startswith("ret_")]
    assert cases, "golden.json sem casos ret_*"

    failures = []
    for case in cases:
        turn = query_docs_fast(docs, case["question"])
        assert not turn.error, f"{case['id']}: pipeline error {turn.error}"
        assert turn.contexts, f"{case['id']}: nenhum contexto recuperado"

        rel = context_relevance(case["question"], turn.contexts)
        rec = context_recall_markers(turn.contexts, case["must_include_markers"])
        doc_rec = doc_name_recall(
            turn.context_names, turn.contexts, case["ground_truth_doc"]
        )

        row = {
            "id": case["id"],
            "question": case["question"],
            "n_contexts": len(turn.contexts),
            "context_relevance": rel.score,
            "context_recall": rec.score,
            "doc_recall": doc_rec.score,
            "detail": {
                "relevance": rel.detail,
                "recall": rec.detail,
                "doc": doc_rec.detail,
                "context_names": turn.context_names[:8],
            },
        }
        report.append(row)

        if rel.score < 0.20:
            failures.append(f"{case['id']} context_relevance={rel.score:.3f}")
        if rec.score < 0.34:
            failures.append(f"{case['id']} context_recall={rec.score:.3f} ({rec.detail})")

    out = RESULTADOS / "retrieval_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    assert not failures, "Retrieval abaixo do limiar:\n" + "\n".join(failures)


def test_retrieval_metrics_unit_offline():
    """Sanidade das métricas sem PaperQA (sempre roda no CI)."""
    q = "educacao ambiental nas escolas"
    good = [
        "A educacao ambiental melhora a consciencia coletiva nas escolas ALPHA-EA-2024"
    ]
    bad = ["Receita de bolo de chocolate com cobertura"]
    assert context_relevance(q, good).score > context_relevance(q, bad).score
    assert context_recall_markers(good, ["ALPHA-EA-2024", "consciencia"]).score == 1.0
    assert context_recall_markers(bad, ["ALPHA-EA-2024"]).score == 0.0
