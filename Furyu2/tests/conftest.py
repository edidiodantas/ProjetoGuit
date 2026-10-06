from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

import academic_search as ac

# Função original (antes do autouse relaxar DNS nos testes de rede)
_REAL_IS_SAFE_PUBLIC_URL = ac.is_safe_public_url


@pytest.fixture(autouse=True)
def _relax_ssrf_dns_for_unit_tests(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
):
    """Evita getaddrinfo em hosts fictícios (rev.org, etc.) nos testes de rede.

    Testes marcados com @pytest.mark.ssrf_dns usam a validação completa.
    """
    if request.node.get_closest_marker("ssrf_dns"):
        return

    def _safe(url: str, *, resolve_dns: bool = True) -> bool:
        return _REAL_IS_SAFE_PUBLIC_URL(url, resolve_dns=False)

    monkeypatch.setattr(ac, "is_safe_public_url", _safe)


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
