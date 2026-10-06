from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

import academic_search as ac


class _Resp:
    def __init__(
        self,
        *,
        status_code: int = 200,
        json_data: dict | None = None,
        text: str = "",
        url: str = "https://example.com",
    ) -> None:
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text
        self.url = url

    def json(self) -> dict:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=MagicMock(), response=self)


class _StreamCtx:
    def __init__(self, chunks: list[bytes], status: int = 200, ctype: str = "application/pdf") -> None:
        self._chunks = chunks
        self.status_code = status
        self.headers = {"content-type": ctype}

    def __enter__(self) -> _StreamCtx:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=MagicMock(), response=MagicMock())

    def iter_bytes(self):
        for c in self._chunks:
            yield c


def test_scrape_landing_pdf_url() -> None:
    html = """
    <meta name="citation_pdf_url" content="/article/download/99/abc.pdf"/>
    """
    client = MagicMock()
    client.get.return_value = _Resp(text=html, url="https://rev.org/view/1")
    url = ac.scrape_landing_pdf_url("https://rev.org/view/1", client=client)
    assert "article/download" in url
    assert ac.scrape_landing_pdf_url("not-a-url") == ""
    client.get.return_value = _Resp(status_code=404)
    assert ac.scrape_landing_pdf_url("https://rev.org/x", client=client) == ""
    client.get.side_effect = RuntimeError("net")
    assert ac.scrape_landing_pdf_url("https://rev.org/x", client=client) == ""


def test_search_oasisbr_and_scrape_ojs(monkeypatch: pytest.MonkeyPatch) -> None:
    record = {
        "id": "X1",
        "title": "Artigo OJS",
        "urls": [{"url": "https://rev.org/index.php/r/article/view/10"}],
        "authors": {"primary": {"Autor": {}}},
    }
    payload = {"records": [record]}
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = _Resp(json_data=payload)

    def fake_scrape(url: str, *, client=None) -> str:
        return "https://rev.org/article/download/10/galley"

    monkeypatch.setattr(ac, "scrape_landing_pdf_url", fake_scrape)
    with patch.object(ac.httpx, "Client", return_value=client):
        hits = ac.search_oasisbr("tema", limit=5)
    assert len(hits) == 1
    assert hits[0].pdf_url.endswith("galley")
    assert hits[0].source == "oasisbr+ojs"

    client.get.side_effect = [
        _Resp(json_data={"records": []}),
        _Resp(json_data={"records": [record]}),
    ]
    with patch.object(ac.httpx, "Client", return_value=client):
        hits2 = ac.search_oasisbr("tema")
    assert len(hits2) == 1
    assert ac.search_oasisbr("") == []


def test_search_semantic_scholar_429_and_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ac.time, "sleep", lambda *_: None)
    client = MagicMock()
    client.__enter__.return_value = client
    ok = _Resp(
        json_data={
            "data": [
                {
                    "paperId": "p1",
                    "title": "Paper",
                    "year": 2020,
                    "authors": [{"name": "A"}],
                    "externalIds": {"DOI": "10.1/p"},
                    "openAccessPdf": {"url": "https://oa.com/p.pdf"},
                    "venue": "V",
                    "abstract": "ab",
                }
            ]
        }
    )
    client.get.side_effect = [_Resp(status_code=429), ok]
    with patch.object(ac.httpx, "Client", return_value=client):
        hits = ac.search_semantic_scholar("q", api_key="k")
    assert hits[0].doi == "10.1/p"

    client.get.side_effect = [_Resp(status_code=429), _Resp(status_code=429)]
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="Semantic Scholar"):
            ac.search_semantic_scholar("q")


def test_search_crossref() -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = _Resp(
        json_data={
            "message": {
                "items": [
                    {
                        "DOI": "10.1/cr",
                        "title": ["Crossref title"],
                        "author": [{"given": "A", "family": "B"}],
                        "container-title": ["Rev"],
                        "published-print": {"date-parts": [[2019]]},
                        "abstract": "<p>Resumo</p>",
                        "link": [
                            {"content-type": "application/pdf", "URL": "https://x.com/a.pdf"},
                        ],
                    }
                ]
            }
        }
    )
    with patch.object(ac.httpx, "Client", return_value=client):
        hits = ac.search_crossref("q", email="a@b.com")
    assert hits[0].pdf_url.endswith(".pdf")


def test_unpaywall_and_attach() -> None:
    client = MagicMock()
    client.get.return_value = _Resp(
        json_data={
            "best_oa_location": {"url_for_pdf": "https://ojs/dl/1"},
        }
    )
    urls = ac.unpaywall_pdf_urls("10.1/x", "a@b.com", client=client)
    assert urls
    assert ac.unpaywall_pdf_url("10.1/x", "a@b.com", client=client) == urls[0]
    assert ac.unpaywall_pdf_urls("", "a@b.com") == []
    client.get.return_value = _Resp(status_code=422)
    assert ac.unpaywall_pdf_urls("10.1/x", "a@b.com", client=client) == []
    client.get.side_effect = RuntimeError("x")
    assert ac.unpaywall_pdf_urls("10.1/x", "a@b.com", client=client) == []

    hit = ac.PaperHit(
        "1",
        "T",
        None,
        "",
        "",
        "10.1/y",
        "",
        "https://www.scielo.br/j/x/?format=pdf",
        "crossref",
    )
    with patch.object(ac, "unpaywall_pdf_urls", return_value=["https://ojs/dl/2"]):
        ac.attach_unpaywall_pdfs([hit], "a@b.com")
    assert hit.pdf_url == "https://ojs/dl/2"
    assert "unpaywall" in hit.source


def test_search_academic_fallbacks() -> None:
    with patch.object(ac, "search_oasisbr", side_effect=RuntimeError("down")):
        with patch.object(ac, "search_semantic_scholar", side_effect=RuntimeError("s2")):
            with patch.object(
                ac,
                "search_crossref",
                return_value=[
                    ac.PaperHit("1", "T", None, "", "", "10.1/z", "", "", "crossref")
                ],
            ):
                hits, note = ac.search_academic("q", email="a@b.com")
    assert hits and "Crossref" in note


def test_resolve_pdf_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    hit = ac.PaperHit(
        "1",
        "T",
        None,
        "",
        "",
        "10.1590/S0101-32622015000200173",
        "",
        "",
        "scielo",
        landing_url="https://rev.org/view/1",
    )
    monkeypatch.setattr(ac, "scrape_landing_pdf_url", lambda *_a, **_k: "https://rev.org/dl/1")
    monkeypatch.setattr(ac, "unpaywall_pdf_urls", lambda *_a, **_k: [])
    cands = ac.resolve_pdf_candidates(hit, "a@b.com")
    assert cands[0] == "https://rev.org/dl/1"
    assert ac.resolve_pdf_url(hit, "a@b.com") == cands[0]


def test_download_pdf_paths(
    tmp_path: Path,
    minimal_pdf_with_text: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_bytes = minimal_pdf_with_text.read_bytes()
    client = MagicMock()
    client.__enter__.return_value = client
    client.stream.return_value = _StreamCtx([pdf_bytes])

    with patch.object(ac.httpx, "Client", return_value=client):
        dest = ac.download_pdf("https://rev.org/a.pdf", tmp_path, "t.pdf")
    assert dest.exists()

    # arquivo existente -> _novo
    with patch.object(ac.httpx, "Client", return_value=client):
        dest2 = ac.download_pdf("https://rev.org/a.pdf", tmp_path, "t.pdf")
    assert "_novo" in dest2.name

    client.stream.return_value = _StreamCtx([b"<!DOCTYPE html><html></html>"], ctype="text/html")
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="não devolveu um PDF"):
            ac.download_pdf("https://rev.org/x", tmp_path, "bad.pdf")

    client.stream.return_value = _StreamCtx([b"bunny-shield challenge"])
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="anti-bot"):
            ac.download_pdf("https://rev.org/x", tmp_path, "bot.pdf")

    big = b"%PDF" + b"x" * (41 * 1024 * 1024)
    client.stream.return_value = _StreamCtx([big])
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="40 MB"):
            ac.download_pdf("https://rev.org/x", tmp_path, "big.pdf")


def test_download_scan_removed(tmp_path: Path, empty_text_pdf: Path) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    client.stream.return_value = _StreamCtx([empty_text_pdf.read_bytes()])
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="texto selecionável"):
            ac.download_pdf("https://rev.org/x", tmp_path, "scan.pdf")
    assert not (tmp_path / "scan.pdf").exists()


def test_download_first_working_pdf(tmp_path: Path, minimal_pdf_with_text: Path) -> None:
    with patch.object(
        ac,
        "download_pdf",
        side_effect=[RuntimeError("x"), minimal_pdf_with_text],
    ):
        out = ac.download_first_working_pdf(
            ["https://bad.com/x", "https://good.com/y.pdf"],
            tmp_path,
            "out.pdf",
        )
    assert out == minimal_pdf_with_text

    with pytest.raises(RuntimeError, match="Sem PDF"):
        ac.download_first_working_pdf([], tmp_path, "x.pdf")

    with patch.object(ac, "download_pdf", side_effect=RuntimeError("x")):
        with pytest.raises(RuntimeError, match="Não foi possível baixar"):
            ac.download_first_working_pdf(["https://a.com/x"], tmp_path, "x.pdf")


def test_pdf_validation(
    minimal_pdf_with_text: Path,
    empty_text_pdf: Path,
    tmp_path: Path,
) -> None:
    assert ac.pdf_extractable_char_count(minimal_pdf_with_text) >= 40
    assert ac.pdf_extractable_char_count(empty_text_pdf) == 0
    assert ac.pdf_extractable_char_count(tmp_path / "missing.pdf") == -1
    ac.validate_pdf_has_extractable_text(minimal_pdf_with_text)
    with pytest.raises(RuntimeError, match="texto selecionável"):
        ac.validate_pdf_has_extractable_text(empty_text_pdf)
    with pytest.raises(RuntimeError, match="Não foi possível abrir"):
        ac.validate_pdf_has_extractable_text(tmp_path / "nope.pdf")
