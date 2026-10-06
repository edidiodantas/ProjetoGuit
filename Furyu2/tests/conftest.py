from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def tmp_pdf_dir(tmp_path: Path) -> Path:
    return tmp_path / "pdfs"


@pytest.fixture
def minimal_pdf_with_text(tmp_path: Path) -> Path:
    """PDF mínimo com texto extraível (PyMuPDF)."""
    import pymupdf

    path = tmp_path / "sample.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Texto de teste para indexacao academica Furyu.")
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def empty_text_pdf(tmp_path: Path) -> Path:
    """PDF sem camada de texto (só página em branco)."""
    import pymupdf

    path = tmp_path / "blank.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(path)
    doc.close()
    return path


class _SessionState(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


@pytest.fixture
def mock_streamlit(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    st = MagicMock()
    st.session_state = _SessionState()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st
