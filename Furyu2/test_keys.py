"""Teste unitário: keys dos botões de indexar são únicas mesmo com paper_id vazio."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class FakeHit:
    paper_id: str
    title: str
    doi: str = ""


def make_key(i: int, hit: FakeHit) -> str:
    """Replica a lógica de app.py."""
    return f"idx-{i}_{re.sub(r'[^a-zA-Z0-9_-]', '_', (hit.paper_id or hit.doi or hit.title))[:50]}"


def main() -> None:
    hits = [
        FakeHit("", "Artigo sem ID 1"),
        FakeHit("", "Artigo sem ID 2"),
        FakeHit("", "Artigo sem ID 1"),  # mesmo título do primeiro
        FakeHit("ABC-123", "Artigo com ID"),
        FakeHit("", "Título/com caracteres: especiais!"),
    ]

    keys = [make_key(i, h) for i, h in enumerate(hits)]
    print("Keys geradas:")
    for k in keys:
        print(f"  {k}")

    assert len(keys) == len(set(keys)), "ERRO: keys duplicadas!"
    print("OK: todas as keys são únicas.")


if __name__ == "__main__":
    main()
