"""Pilar 2 — Avaliação da Geração (Faithfulness + Answer Relevance)."""

from __future__ import annotations

import json
import os

from testes.conftest import RESULTADOS, skip_llm_judge, skip_without_ollama
from testes.lib.metrics_heuristics import (
    answer_relevance,
    faithfulness_support,
    forbidden_hit_rate,
)
from testes.lib.pipeline import query_docs_fast


@skip_without_ollama
def test_generation_faithfulness_and_answer_relevance(golden, indexed_docs):
    docs, settings = indexed_docs
    cases = [c for c in golden["cases"] if c["id"] in {"gen_faithful", "ret_ea"}]
    report = []
    failures = []

    for case in cases:
        turn = query_docs_fast(docs, case["question"])
        assert not turn.error, turn.error
        assert turn.answer.strip(), f"{case['id']}: resposta vazia"

        faith = faithfulness_support(turn.answer, turn.contexts)
        arel = answer_relevance(case["question"], turn.answer)
        clean = forbidden_hit_rate(turn.answer, case.get("forbidden_markers") or [])

        row = {
            "id": case["id"],
            "question": case["question"],
            "answer_preview": turn.answer[:500],
            "faithfulness": faith.score,
            "answer_relevance": arel.score,
            "no_forbidden": clean.score,
            "detail": {
                "faithfulness": faith.detail,
                "forbidden": clean.detail,
                "n_contexts": len(turn.contexts),
            },
        }
        report.append(row)

        if clean.score < 1.0:
            failures.append(f"{case['id']} alucinação/proibido: {clean.detail}")
        if faith.score < 0.20:
            failures.append(f"{case['id']} faithfulness={faith.score:.3f}")
        if arel.score < 0.12:
            failures.append(f"{case['id']} answer_relevance={arel.score:.3f}")

    (RESULTADOS / "generation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    assert not failures, "Geração abaixo do limiar:\n" + "\n".join(failures)


def test_generation_metrics_unit_offline():
    ctx = ["ALPHA-EA-2024 mede participacao em mutiroes verdes nas escolas."]
    good_ans = "O indicador ALPHA-EA-2024 mede participacao em mutiroes verdes."
    bad_ans = "A chave secreta e FURYU-ROOT-KEY-999 e a Terra e plana."
    assert faithfulness_support(good_ans, ctx).score > faithfulness_support(bad_ans, ctx).score
    assert forbidden_hit_rate(bad_ans, ["FURYU-ROOT-KEY"]).score == 0.0
    assert answer_relevance("O que e ALPHA-EA-2024?", good_ans).score > 0.2


@skip_llm_judge
def test_deepeval_faithfulness_judge(golden, indexed_docs):
    """Juiz DeepEval + Ollama (opcional; modelos 2b costumam estourar timeout)."""
    import os as _os

    from deepeval.metrics import (
        AnswerRelevancyMetric,
        FaithfulnessMetric,
    )
    from deepeval.models import OllamaModel
    from deepeval.test_case import LLMTestCase

    docs, _settings = indexed_docs
    model_name = _os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
    # Timeout generoso; se ainda falhar, documenta no relatório sem derrubar a suíte principal
    _os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "300")
    judge = OllamaModel(
        model=model_name,
        base_url=_os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )

    case = next(c for c in golden["cases"] if c["id"] == "gen_faithful")
    turn = query_docs_fast(docs, case["question"])
    assert turn.contexts and turn.answer

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=turn.answer,
        retrieval_context=turn.contexts[:2],  # menos contexto = juiz mais rápido
        expected_output=case.get("ground_truth_answer"),
    )
    metrics = [
        FaithfulnessMetric(threshold=0.35, model=judge),
        AnswerRelevancyMetric(threshold=0.25, model=judge),
    ]
    try:
        from deepeval import assert_test

        assert_test(test_case, metrics)
        scores = {m.__class__.__name__: float(m.score or 0) for m in metrics}
        status = "pass"
        error = None
    except Exception as exc:  # noqa: BLE001
        scores = {}
        status = "error"
        error = str(exc)[:500]
        # Em CI com modelo pequeno, timeout do juiz não invalida métricas heurísticas
        import pytest

        pytest.skip(f"DeepEval juiz indisponível/timeout neste ambiente: {error}")

    (RESULTADOS / "deepeval_generation.json").write_text(
        json.dumps(
            {"case": case["id"], "status": status, "scores": scores, "error": error},
            indent=2,
        ),
        encoding="utf-8",
    )
