"""Testes de segurança: SSRF, sanitização de URL, limites de PDF."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import academic_search as ac
from tests.conftest import _REAL_IS_SAFE_PUBLIC_URL
from tests.test_academic_network import _Resp, _StreamCtx


def test_ssrf_blocks_private_and_local() -> None:
    blocked = [
        "http://127.0.0.1/secret.pdf",
        "https://localhost/a.pdf",
        "http://[::1]/pdf",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/internal.pdf",
        "http://192.168.1.1/x.pdf",
        "http://172.16.0.1/x.pdf",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "ftp://files.example.com/a.pdf",
        "https://user:pass@example.com/a.pdf",
        "http://metadata.google.internal/",
        "http://evil.local/a.pdf",
        "http://x.lan/a.pdf",
        "http://x.corp/a.pdf",
        "https://" + ("a" * 2100) + ".com/x.pdf",
        "",
    ]
    for url in blocked:
        assert _REAL_IS_SAFE_PUBLIC_URL(url, resolve_dns=False) is False
        with pytest.raises(RuntimeError, match="bloqueada"):
            ac.assert_safe_fetch_url(url, resolve_dns=False)


@pytest.mark.ssrf_dns
def test_ssrf_allows_public_example() -> None:
    assert _REAL_IS_SAFE_PUBLIC_URL("https://example.com/paper.pdf", resolve_dns=True)
    ac.assert_safe_fetch_url("https://example.com/paper.pdf")


@pytest.mark.ssrf_dns
def test_ssrf_dns_getaddrinfo_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ac.socket, "getaddrinfo", lambda *_a, **_k: (_ for _ in ()).throw(OSError("nx")))
    assert _REAL_IS_SAFE_PUBLIC_URL("https://no-such-host.invalid/x.pdf", resolve_dns=True) is False

    monkeypatch.setattr(ac.socket, "getaddrinfo", lambda *_a, **_k: [])
    assert _REAL_IS_SAFE_PUBLIC_URL("https://empty-dns.example/x.pdf", resolve_dns=True) is False

    monkeypatch.setattr(
        ac.socket,
        "getaddrinfo",
        lambda *_a, **_k: [(None, None, None, None, ("127.0.0.1", 0))],
    )
    assert _REAL_IS_SAFE_PUBLIC_URL("https://evil-rebinding.example/x.pdf", resolve_dns=True) is False

    monkeypatch.setattr(
        ac.socket,
        "getaddrinfo",
        lambda *_a, **_k: [(None, None, None, None, ("not-an-ip", 0))],
    )
    assert _REAL_IS_SAFE_PUBLIC_URL("https://weird.example/x.pdf", resolve_dns=True) is False


def test_sanitize_open_url() -> None:
    assert ac.sanitize_open_url("https://rev.org/view/1") == "https://rev.org/view/1"
    assert ac.sanitize_open_url("http://127.0.0.1/x") == ""
    assert ac.sanitize_open_url("javascript:alert(1)") == ""
    assert ac.sanitize_open_url("") == ""


def test_best_open_url_skips_unsafe() -> None:
    hit = ac.PaperHit(
        "1",
        "T",
        None,
        "",
        "",
        "10.1/x",
        "",
        "http://127.0.0.1/evil.pdf",
        "x",
        landing_url="http://localhost/land",
    )
    assert ac.best_open_url(hit) == "https://doi.org/10.1/x"


def test_download_blocks_ssrf(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="bloqueada"):
        ac.download_pdf("http://127.0.0.1/a.pdf", tmp_path, "x.pdf")


def test_download_blocks_redirect_to_localhost(tmp_path: Path) -> None:
    client = MagicMock()
    client.__enter__.return_value = client

    redirect = _StreamCtx([b""], status=302)
    redirect.headers = {"location": "http://127.0.0.1/secret.pdf"}
    redirect.url = "https://rev.org/a.pdf"

    client.stream.return_value = redirect
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="bloqueada"):
            ac.download_pdf("https://rev.org/a.pdf", tmp_path, "x.pdf")


def test_download_redirect_without_location(tmp_path: Path) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    redirect = _StreamCtx([b""], status=302)
    redirect.headers = {}
    redirect.url = "https://rev.org/a.pdf"
    client.stream.return_value = redirect
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="Redirect"):
            ac.download_pdf("https://rev.org/a.pdf", tmp_path, "x.pdf")


def test_scrape_follows_redirect_then_pdf() -> None:
    html = '<meta name="citation_pdf_url" content="/article/download/1/2.pdf"/>'
    client = MagicMock()
    r1 = _Resp(status_code=302, url="https://rev.org/view/1")
    r1.headers = {"location": "/view/1b"}
    r2 = _Resp(text=html, url="https://rev.org/view/1b")
    r2.headers = {}
    client.get.side_effect = [r1, r2]
    url = ac.scrape_landing_pdf_url("https://rev.org/view/1", client=client)
    assert "download" in url


def test_scrape_redirect_empty_location() -> None:
    client = MagicMock()
    r1 = _Resp(status_code=302, url="https://rev.org/view/1")
    r1.headers = {"location": ""}
    client.get.return_value = r1
    assert ac.scrape_landing_pdf_url("https://rev.org/view/1", client=client) == ""


def test_scrape_too_many_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ac, "MAX_HTTP_REDIRECTS", 2)
    client = MagicMock()
    r = _Resp(status_code=302, url="https://rev.org/view/1")
    r.headers = {"location": "/view/2"}
    client.get.return_value = r
    assert ac.scrape_landing_pdf_url("https://rev.org/view/1", client=client) == ""


def test_scrape_blocks_ssrf_landing() -> None:
    assert ac.scrape_landing_pdf_url("http://127.0.0.1/view/1") == ""
    assert ac.scrape_landing_pdf_url("http://169.254.169.254/latest") == ""


def test_download_too_many_redirects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ac, "MAX_HTTP_REDIRECTS", 2)
    client = MagicMock()
    client.__enter__.return_value = client
    redirect = _StreamCtx([b""], status=302)
    redirect.headers = {"location": "https://rev.org/b.pdf"}
    redirect.url = "https://rev.org/a.pdf"
    client.stream.return_value = redirect
    with patch.object(ac.httpx, "Client", return_value=client):
        with pytest.raises(RuntimeError, match="Muitos redirects"):
            ac.download_pdf("https://rev.org/a.pdf", tmp_path, "x.pdf")


def test_pdf_outer_exception(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    p = tmp_path / "a.pdf"
    p.write_bytes(b"%PDF-1.4 x")
    monkeypatch.setattr(ac, "ThreadPoolExecutor", lambda **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert ac.pdf_extractable_char_count(p) == -1


def test_validate_when_char_count_fails(minimal_pdf_with_text: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ac, "pdf_extractable_char_count", lambda *_a, **_k: -1)
    with pytest.raises(RuntimeError, match="timeout ou protegido"):
        ac.validate_pdf_has_extractable_text(minimal_pdf_with_text)


def test_host_blocked_empty() -> None:
    assert ac._host_is_blocked_name("") is True
    assert ac._host_is_blocked_name("example.com") is False


def test_validate_rejects_oversized(tmp_path: Path) -> None:
    big = tmp_path / "huge.pdf"
    big.write_bytes(b"%PDF-1.4 fake")
    with patch.object(Path, "stat") as st_mock:
        st_mock.return_value = MagicMock(st_size=ac.MAX_PDF_BYTES + 1)
        with patch.object(Path, "is_file", return_value=True):
            with pytest.raises(RuntimeError, match="excede"):
                ac.validate_pdf_has_extractable_text(big)


def test_pdf_timeout_returns_minus_one(
    minimal_pdf_with_text: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Fut:
        def result(self, timeout=None):
            raise ac.FuturesTimeout()

    class _Pool:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def submit(self, *a, **k):
            return _Fut()

    monkeypatch.setattr(ac, "ThreadPoolExecutor", lambda **k: _Pool())
    assert ac.pdf_extractable_char_count(minimal_pdf_with_text) == -1


def test_pdf_char_count_page_cap(minimal_pdf_with_text: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ac, "MAX_PDF_PAGES_SCAN", 0)
    # 0 páginas lidas → 0 chars (ainda é arquivo válido)
    assert ac.pdf_extractable_char_count(minimal_pdf_with_text) == 0


def test_pdf_zero_byte_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.pdf"
    p.write_bytes(b"")
    assert ac.pdf_extractable_char_count(p) == -1


def test_validate_stat_oserror(tmp_path: Path) -> None:
    p = tmp_path / "x.pdf"
    p.write_bytes(b"%PDF")
    with patch.object(Path, "is_file", return_value=True):
        with patch.object(Path, "stat", side_effect=OSError("x")):
            with pytest.raises(RuntimeError, match="Não foi possível abrir"):
                ac.validate_pdf_has_extractable_text(p)


def test_urlparse_exception_returns_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ac, "urlparse", lambda *_a, **_k: (_ for _ in ()).throw(ValueError("bad")))
    assert _REAL_IS_SAFE_PUBLIC_URL("https://ok.example/x", resolve_dns=False) is False
