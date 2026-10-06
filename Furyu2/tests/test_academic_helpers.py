from __future__ import annotations

import academic_search as ac


def test_paper_hit_open_pdf_and_candidates() -> None:
    hit = ac.PaperHit(
        paper_id="1",
        title="T",
        year=2020,
        authors="A",
        venue="V",
        doi="10.1/x",
        abstract="",
        pdf_url="https://ex.com/a.pdf",
        source="oasisbr",
        pdf_candidates=["https://ex.com/b.pdf", "https://ex.com/a.pdf"],
    )
    assert hit.has_open_pdf is True
    assert hit.all_pdf_candidates() == [
        "https://ex.com/a.pdf",
        "https://ex.com/b.pdf",
    ]


def test_headers_and_looks_like_pdf() -> None:
    h = ac._headers("key123")
    assert h["x-api-key"] == "key123"
    assert ac._looks_like_pdf_url("https://rev.org/article/download/1/2")
    assert ac._looks_like_pdf_url("https://www.scielo.br/j/x/?format=pdf")
    assert not ac._looks_like_pdf_url("https://doi.org/10.1/x")
    assert not ac._looks_like_pdf_url("ftp://x.com/a.pdf")


def test_prefer_direct_pdf_and_scielo_host() -> None:
    ojs = "https://rev.org/article/download/1/2"
    sci = "https://www.scielo.br/j/x/?format=pdf"
    ordered = ac._prefer_direct_pdf([sci, ojs])
    assert ordered[0] == ojs
    assert ac._is_scielo_host(sci)


def test_authors_and_doi_pid() -> None:
    assert ac._authors([{"name": "Ana"}, {"name": ""}, None]) == "Ana"
    assert ac._crossref_authors([{"given": "Jo", "family": "Silva"}]) == "Jo Silva"
    assert ac._first_doi("ver 10.1234/abc.)") == "10.1234/abc"
    pid = "S0101-32622015000200173"
    assert ac._scielo_pid(f"pid={pid}") == pid
    assert ac._year_from_pid(pid) == 2015
    assert ac._year_from_pid("S0101-32621899000200173") is None  # ano 1899 fora do intervalo
    assert ac._year_from_pid("short") is None
    assert ac.scielo_pdf_url("") == ""
    assert ac.scielo_pdf_url(pid).startswith("https://www.scielo.br/")


def test_crossref_title_and_year() -> None:
    item = {
        "title": ["http://bad"],
        "short-title": ["Título curto"],
        "published-print": {"date-parts": [[2021, 3]]},
    }
    assert ac._crossref_title(item) == "Título curto"
    assert ac._crossref_year(item) == 2021
    assert ac._crossref_year({"published": {"date-parts": [["x"]]}}) is None


def test_vufind_authors() -> None:
    raw = {
        "primary": {"Maria [BR]": {}, "": {}},
        "secondary": {"João": {}},
        "corporate": {"UF": {}},
    }
    out = ac._vufind_authors(raw)
    assert "Maria" in out and "João" in out


def test_pdfs_from_unpaywall() -> None:
    data = {
        "best_oa_location": {"url_for_pdf": "https://ojs/article/download/1/2"},
        "oa_locations": [
            {"url": "https://www.scielo.br/j/x/?format=pdf"},
            {"url": "https://doi.org/10.1/x"},
        ],
    }
    urls = ac._pdfs_from_unpaywall(data)
    assert urls[0].startswith("https://ojs")
    assert ac._pdf_from_unpaywall(data) == urls[0]


def test_dedupe_and_safe_filename() -> None:
    h1 = ac.PaperHit("a", "T1", None, "", "", "10.1/same", "", "", "x")
    h2 = ac.PaperHit("b", "T2", None, "", "", "10.1/same", "", "", "x")
    h3 = ac.PaperHit("", "T3", None, "", "", "", "", "", "x")
    assert len(ac._dedupe([h1, h2, h3])) == 1
    name = ac._safe_filename("Artigo: teste!", 2024)
    assert name.endswith("_2024.pdf")


def test_best_open_url() -> None:
    with_pdf = ac.PaperHit(
        "1",
        "T",
        None,
        "",
        "",
        "",
        "",
        "https://pdf.com/x.pdf",
        "oasisbr",
    )
    assert ac.best_open_url(with_pdf) == "https://pdf.com/x.pdf"
    with_landing = ac.PaperHit(
        "1",
        "T",
        None,
        "",
        "",
        "10.1/x",
        "",
        "",
        "oasisbr",
        landing_url="https://rev.org/view/1",
    )
    assert ac.best_open_url(with_landing) == "https://rev.org/view/1"
    assert ac.best_open_url(
        ac.PaperHit("1", "T", None, "", "", "10.1/x", "", "", "oasisbr")
    ) == "https://doi.org/10.1/x"
