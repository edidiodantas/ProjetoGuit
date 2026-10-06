#!/usr/bin/env python3
"""Executa a suíte de avaliação RAG e grava relatório consolidado."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TESTES = Path(__file__).resolve().parent
ROOT = TESTES.parent
RESULTADOS = TESTES / "resultados"
RESULTADOS.mkdir(parents=True, exist_ok=True)


def main() -> int:
    os.chdir(ROOT)
    # Garante corpus
    if not (TESTES / "corpus" / "golden.json").exists():
        print("Corpus ausente", file=sys.stderr)
        return 2

    env = os.environ.copy()
    # DeepEval juiz LLM é opcional (lento). Ative com FURYU_RUN_LLM_JUDGE=1
    if env.get("FURYU_RUN_LLM_JUDGE", "").strip() not in {"1", "true", "yes"}:
        env["FURYU_SKIP_LLM_JUDGE"] = "1"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(TESTES),
        "-c",
        str(TESTES / "pytest.ini"),
        "-v",
        "--tb=short",
    ]
    print(">>", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env)
    code = int(proc.returncode or 0)

    reports = {}
    for name in (
        "retrieval_report.json",
        "generation_report.json",
        "edge_cases_report.json",
        "deepeval_generation.json",
    ):
        path = RESULTADOS / name
        if path.exists():
            reports[name] = json.loads(path.read_text(encoding="utf-8"))

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pytest_exit_code": proc.returncode,
        "pass": proc.returncode == 0,
        "reports": reports,
        "pillars": {
            "1_retrieval": "context_relevance + context_recall (heurística + PaperQA)",
            "2_generation": "faithfulness + answer_relevance (heurística + DeepEval opcional)",
            "3_edge_cases": "5 cenários críticos em edge_cases_report.json",
        },
    }
    (RESULTADOS / "relatorio_rag.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Relatório RAG Furyu",
        "",
        f"- Gerado em: `{summary['generated_at']}`",
        f"- pytest exit: **{proc.returncode}** ({'PASS' if proc.returncode == 0 else 'FAIL'})",
        "",
        "## Pilares",
        "",
        "1. Retrieval — Context Relevance / Recall",
        "2. Geração — Faithfulness / Answer Relevance",
        "3. Edge cases — fora de escopo, conflito, injeção pergunta/doc, corpus vazio",
        "",
        "## Arquivos",
        "",
    ]
    for name in reports:
        lines.append(f"- `{name}`")
    (RESULTADOS / "relatorio_rag.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((RESULTADOS / "relatorio_rag.md").read_text(encoding="utf-8"))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
