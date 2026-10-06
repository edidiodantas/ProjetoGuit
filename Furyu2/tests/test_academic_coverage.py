"""Testes adicionais para cobertura de ramos em academic_search."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

import academic_search as ac
from tests.test_academic_network import _Resp, _StreamCtx


def test_prefer_direct_pdf_skips_empty_and_doi_scoring() -> None:
    assert ac._prefer_direct_pdf(["", "https://doi.org/10.1/x", "https://x.com/a.pdf"])[0].endswith(".pdf")


def test_scrape_landing_own_client_href_and_reverse_meta() -> None:
    html = """
    <a href="/article/download/1/2.pdf">PDF</a>
    https://rev.org/static/extra/file.pdf
    <meta content="/galley.pdf" name="citation_pdf_url"/>
    """
    client = MagicMock()
    client.get.return_value = _Resp(text=html, url="https://rev.org/view/1")
    url = ac.scrape_landing_pdf_url("https://rev.org/view/1", client=client)
    assert "download" in url or "galley" in url

    with patch.object(ac.httpx, "Client") as mock_cls:
        inst = MagicMock()
        mock_cls.return_value = inst
        inst.get.return_value = _Resp(text=html, url="https://rev.org/view/1")
        ac.scrape_landing_pdf_url("https://rev.org/view/2")
        inst.close.assert_called_once()


def test_year_from_pid_value_error() -> None:
    bad = "S0101-3262XXXX2015002000173"
    assert len(bad) >= 14 and bad[0] == "S"
    assert ac._year_from_pid(bad) is None


def test_search_oasisbr_scielo_paths() -> None:
    pid = "S0101-32622015000200173"
    record = {
        "id": "sc1",
        "title": "SciELO art",
        "oai_identifier_st": pid,
        "urls": [
            {"url": f"https://www.scielo.br/scielo.php?script=sci_arttext&pid={pid}"},
            {"url": "https://rev.org/outro"},
        ],
        "authors": {},
    }
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = _Resp(json_data={"records": [record]})
    with patch.object(ac.httpx, "Client", return_value=client):
        hits = ac.search_oasisbr("tema", limit=3)
    assert hits[0].source == "scielo"
    assert hits[0].pdf_url.startswith("https://www.scielo.br/")


def test_search_oasisbr_direct_pdf_in_urls() -> None:
    record = {
        "id": "p1",
        "title": "Com PDF",
        "urls": [
            {"url": "https://repo.org/paper.pdf"},
            {"url": "https://rev.org/index.php/r/article/view/99"},
        ],
        "authors": {},
    }
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = _Resp(json_data={"records": [record]})
    with patch.object(ac.httpx, "Client", return_value=client):
        with patch.object(ac, "scrape_landing_pdf_url", return_value=""):
            hits = ac.search_oasisbr("q")
    assert hits[0].pdf_url.endswith("paper.pdf")


def test_crossref_title_fallback_and_empty_query() -> None:
    assert ac._crossref_title({"title": ["http://skip"], "subtitle": ["Sub"]}) == "Sub"
    assert ac._crossref_title({"title": ["http://only"]}) == "Sem título"
    assert ac.search_crossref("  ") == []


def test_search_oasisbr_skips_blank_urls_and_pid_sci_candidate() -> None:
    pid = "S0101-32622015000200173"
    record = {
        "id": "pid-only",
        "title": "Só PID",
        "oai_identifier_st": pid,
        "urls": [{"url": ""}, {"url": "https://example.org/landing"}],
        "authors": {},
    }
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = _Resp(json_data={"records": [record]})
    with patch.object(ac.httpx, "Client", return_value=client):
        with patch.object(ac, "scrape_landing_pdf_url", return_value=""):
            hits = ac.search_oasisbr("q")
    assert hits[0].pdf_url.startswith("https://www.scielo.br/")


def test_semantic_scholar_empty_and_open_pdf_only() -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = _Resp(json_data={"data": []})
    with patch.object(ac.httpx, "Client", return_value=client):
        assert ac.search_semantic_scholar("") == []
        ac.search_semantic_scholar("q", open_pdf_only=True)
    params = client.get.call_args.kwargs.get("params") or client.get.call_args[1].get("params")
    assert any(p[0] == "openAccessPdf" for p in params)


def test_semantic_scholar_payload_loop_else() -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = _Resp(json_data={"data": [{"paperId": "x", "title": "T"}]})
    with patch.object(ac.httpx, "Client", return_value=client):
        hits = ac.search_semantic_scholar("q")
    assert hits[0].paper_id == "x"


def test_unpaywall_own_client_and_attach_early_returns() -> None:
    with patch.object(ac.httpx, "Client") as mock_cls:
        inst = MagicMock()
        mock_cls.return_value = inst
        inst.get.return_value = _Resp(json_data={"best_oa_location": {"url_for_pdf": "https://ojs/x.pdf"}})
        urls = ac.unpaywall_pdf_urls("10.1/a", "a@b.com")
        assert urls
        inst.close.assert_called_once()

    hit = ac.PaperHit("1", "T", None, "", "", "10.1/x", "https://scielo.br/x", "https://scielo.br/x", "scielo")
    ac.attach_unpaywall_pdfs([hit], "")
    ac.attach_unpaywall_pdfs(
        [ac.PaperHit("1", "T", None, "", "", "", "https://x.com/a.pdf", "", "x")],
        "a@b.com",
    )


def test_search_academic_oasisbr_ok_and_s2_ok() -> None:
    h = ac.PaperHit("1", "T", None, "", "", "10.1/a", "", "", "oasisbr")
    with patch.object(ac, "search_oasisbr", return_value=[h]):
        hits, note = ac.search_academic("q", email="a@b.com")
    assert note == "Oasisbr (IBICT)" and hits

    with patch.object(ac, "search_oasisbr", return_value=[]):
        with patch.object(ac, "search_semantic_scholar", return_value=[h]):
            hits2, note2 = ac.search_academic("q")
    assert note2 == "Semantic Scholar"


def test_best_open_url_empty() -> None:
    assert ac.best_open_url(ac.PaperHit("", "T", None, "", "", "", "", "", "x")) == ""


def test_resolve_pdf_candidates_unpaywall_merge() -> None:
    hit = ac.PaperHit("1", "T", None, "", "", "10.1/x", "", "", "x")
    with patch.object(ac, "unpaywall_pdf_urls", return_value=["https://ojs/dl.pdf"]):
        c = ac.resolve_pdf_candidates(hit, "a@b.com")
    assert any("ojs" in u for u in c)


def test_download_non_pdf_final_raise(tmp_path: Path) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    client.stream.return_value = _StreamCtx([b"NOTPDF" * 10], ctype="application/octet-stream")
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="não devolveu um PDF"):
            ac.download_pdf("https://rev.org/x", tmp_path, "n.pdf")


def test_download_first_skips_empty_url(tmp_path: Path, minimal_pdf_with_text: Path) -> None:
    with patch.object(ac, "download_pdf", return_value=minimal_pdf_with_text) as dl:
        ac.download_first_working_pdf(["", "https://good.com/y.pdf"], tmp_path, "o.pdf")
    dl.assert_called_once()


def test_download_first_all_fail_with_detail(tmp_path: Path) -> None:
    with patch.object(ac, "download_pdf", side_effect=RuntimeError("falhou")):
        with pytest.raises(RuntimeError, match="Não foi possível baixar"):
            ac.download_first_working_pdf(["https://a.com/x.pdf"], tmp_path, "z.pdf")
