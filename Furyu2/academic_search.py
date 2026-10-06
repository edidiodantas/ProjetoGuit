"""Busca acadêmica pública (sem login).

Oasisbr (IBICT): busca brasileira (artigos, teses, repositórios) — API VuFind grátis.
Semantic Scholar / Crossref: fallback internacional.
Unpaywall: tenta o PDF legal em acesso aberto (precisa de e-mail de contato).
SciELO: PDF pelo PID quando o Oasisbr aponta para a coleção.
Não baixa artigo fechado (paywall).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

import httpx

S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_SEARCH = "https://api.crossref.org/works"
UNPAYWALL = "https://api.unpaywall.org/v2/{doi}"
OASISBR_SEARCH = "https://oasisbr.ibict.br/vufind/api/v1/search"
SCIELO_PDF = "https://www.scielo.br/scielo.php?script=sci_pdf&pid={pid}&lng=pt&tlng=pt"

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+", re.I)
_PID_RE = re.compile(r"(S\d{4}-\d{4}\d{13})", re.I)
_OJS_VIEW_RE = re.compile(r"/article/view/\d+", re.I)
_PDF_HREF_RE = re.compile(
    r"""(?:href|content)=["']([^"']+(?:article/download/[^"']+|\.pdf)[^"']*)["']""",
    re.I,
)
_PDF_ABS_RE = re.compile(
    r"""https?://[^\s"'<>]+(?:article/download/[^\s"'<>]+|[^\s"'<>]+\.pdf)""",
    re.I,
)
USER_AGENT = (
    "Furyu/2.0 (MVP educacional; "
    "+https://github.com/edidiodantas/ProjetoGuit)"
)
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "application/pdf,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass
class PaperHit:
    paper_id: str
    title: str
    year: int | None
    authors: str
    venue: str
    doi: str
    abstract: str
    pdf_url: str
    source: str  # oasisbr | scielo | semantic-scholar | crossref | unpaywall
    landing_url: str = ""
    pdf_candidates: list[str] = field(default_factory=list)

    @property
    def has_open_pdf(self) -> bool:
        return bool(self.pdf_url or self.pdf_candidates)

    def all_pdf_candidates(self) -> list[str]:
        ordered: list[str] = []
        for url in [self.pdf_url, *self.pdf_candidates]:
            u = (url or "").strip()
            if u and u not in ordered:
                ordered.append(u)
        return ordered


def _headers(s2_key: str = "") -> dict[str, str]:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if s2_key:
        h["x-api-key"] = s2_key
    return h


def _is_scielo_host(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return "scielo" in host


def _prefer_direct_pdf(urls: list[str]) -> list[str]:
    """Ordena candidatos: PDF direto / OJS download antes de SciELO (anti-bot)."""
    scored: list[tuple[int, str]] = []
    for url in urls:
        u = (url or "").strip()
        if not u:
            continue
        low = u.lower()
        score = 50
        if "/article/download/" in low or low.endswith(".pdf"):
            score -= 20
        if "format=pdf" in low or "script=sci_pdf" in low:
            score -= 5
        if _is_scielo_host(u):
            score += 30
        if "doi.org" in low:
            score += 40
        scored.append((score, u))
    scored.sort(key=lambda x: x[0])
    out: list[str] = []
    for _, u in scored:
        if u not in out:
            out.append(u)
    return out


def _authors(raw: list | None) -> str:
    names = []
    for item in raw or []:
        name = (item or {}).get("name") or ""
        if name:
            names.append(name)
    return ", ".join(names[:8])


def _crossref_authors(raw: list | None) -> str:
    names = []
    for item in raw or []:
        given = (item or {}).get("given") or ""
        family = (item or {}).get("family") or ""
        name = f"{given} {family}".strip() or (item or {}).get("name") or ""
        if name:
            names.append(name)
    return ", ".join(names[:8])


def _crossref_year(item: dict) -> int | None:
    for key in ("published-print", "published-online", "published"):
        parts = ((item.get(key) or {}).get("date-parts") or [[]])
        if parts and parts[0] and parts[0][0]:
            try:
                return int(parts[0][0])
            except (TypeError, ValueError):
                continue
    return None


def _looks_like_pdf_url(url: str) -> bool:
    u = url.lower()
    if not u.startswith("http"):
        return False
    if u.startswith("https://doi.org/") or u.startswith("http://doi.org/"):
        return False
    if (
        u.endswith(".pdf")
        or "/pdf" in u
        or "pdf=" in u
        or "format=pdf" in u
        or "type=printable" in u
        or "script=sci_pdf" in u
        or "/article/download/" in u
    ):
        return True
    return False


def _pdf_from_unpaywall(data: dict) -> str:
    cands = _pdfs_from_unpaywall(data)
    return cands[0] if cands else ""


def _pdfs_from_unpaywall(data: dict) -> list[str]:
    locations = []
    best = data.get("best_oa_location")
    if best:
        locations.append(best)
    for loc in data.get("oa_locations") or []:
        if loc and loc not in locations:
            locations.append(loc)
    found: list[str] = []
    for loc in locations:
        pdf = (loc.get("url_for_pdf") or "").strip()
        if pdf and pdf not in found:
            found.append(pdf)
        url = (loc.get("url") or "").strip()
        if url and _looks_like_pdf_url(url) and url not in found:
            found.append(url)
    return _prefer_direct_pdf(found)


def scrape_landing_pdf_url(landing_url: str, *, client: httpx.Client | None = None) -> str:
    """Extrai PDF de páginas OJS (/article/view/) via citation_pdf_url / download."""
    landing_url = (landing_url or "").strip()
    if not landing_url.startswith("http"):
        return ""
    own = client is None
    if own:
        client = httpx.Client(timeout=25.0, follow_redirects=True, headers=BROWSER_HEADERS)
    try:
        r = client.get(landing_url)
        if r.status_code >= 400:
            return ""
        html = r.text or ""
        base = str(r.url)
        cands: list[str] = []
        for m in _PDF_HREF_RE.finditer(html):
            cands.append(urljoin(base, m.group(1).strip()))
        for m in _PDF_ABS_RE.finditer(html):
            cands.append(m.group(0).rstrip(").,;"))
        # citation_pdf_url meta (OJS clássico)
        for m in re.finditer(
            r'name=["\']citation_pdf_url["\'][^>]*content=["\']([^"\']+)["\']',
            html,
            re.I,
        ):
            cands.append(urljoin(base, m.group(1).strip()))
        for m in re.finditer(
            r'content=["\']([^"\']+)["\'][^>]*name=["\']citation_pdf_url["\']',
            html,
            re.I,
        ):
            cands.append(urljoin(base, m.group(1).strip()))
        ranked = _prefer_direct_pdf(
            [c for c in cands if _looks_like_pdf_url(c) or "/article/download/" in c.lower()]
        )
        return ranked[0] if ranked else ""
    except Exception:
        return ""
    finally:
        if own and client is not None:
            client.close()


def _vufind_authors(authors: dict | None) -> str:
    names = []
    block = authors or {}
    for role in ("primary", "secondary", "corporate"):
        group = block.get(role) or {}
        if isinstance(group, dict):
            names.extend(group.keys())
    cleaned = []
    for name in names:
        n = re.sub(r"\s*\[[^\]]*\]", "", str(name)).strip()
        if n:
            cleaned.append(n)
    return ", ".join(cleaned[:8])


def _first_doi(*texts: str) -> str:
    for text in texts:
        m = _DOI_RE.search(text or "")
        if m:
            return m.group(0).rstrip(").,;")
    return ""


def _scielo_pid(*texts: str) -> str:
    for text in texts:
        m = _PID_RE.search(text or "")
        if m:
            return m.group(1).upper()
    return ""


def _year_from_pid(pid: str) -> int | None:
    if len(pid) >= 14 and pid[0] == "S":
        try:
            y = int(pid[10:14])
        except ValueError:
            return None
        if 1900 <= y <= 2100:
            return y
    return None


def scielo_pdf_url(pid: str) -> str:
    pid = (pid or "").strip()
    if not pid:
        return ""
    return SCIELO_PDF.format(pid=pid)


def search_oasisbr(query: str, *, limit: int = 8) -> list[PaperHit]:
    """Busca no Oasisbr (IBICT) — API VuFind pública, sem chave."""
    q = query.strip()
    if not q:
        return []
    params: list[tuple[str, str | int]] = [
        ("lookfor", q),
        ("type", "AllFields"),
        ("limit", max(1, min(limit, 20))),
        ("filter[]", "format:article"),
    ]
    with httpx.Client(timeout=35.0, follow_redirects=True, headers=_headers()) as client:
        r = client.get(OASISBR_SEARCH, params=params)
        r.raise_for_status()
        payload = r.json()
        records = list(payload.get("records") or [])
        if not records:
            params = [("lookfor", q), ("type", "AllFields"), ("limit", max(1, min(limit, 20)))]
            r = client.get(OASISBR_SEARCH, params=params)
            r.raise_for_status()
            payload = r.json()
            records = list(payload.get("records") or [])

    hits: list[PaperHit] = []
    landings_to_scrape: list[tuple[PaperHit, str]] = []
    for item in records:
        urls = [(u or {}).get("url") or "" for u in (item.get("urls") or [])]
        blob = " ".join(
            [
                str(item.get("id") or ""),
                str(item.get("oai_identifier_st") or ""),
                *urls,
            ]
        )
        doi = _first_doi(*urls, blob)
        pid = _scielo_pid(blob, doi)
        if pid and not doi:
            doi = f"10.1590/{pid}"
        pdf_url = ""
        landing_url = ""
        candidates: list[str] = []
        for u in urls:
            if not u:
                continue
            if _looks_like_pdf_url(u):
                if not pdf_url:
                    pdf_url = u
                if u not in candidates:
                    candidates.append(u)
            elif _OJS_VIEW_RE.search(u) or "/article/view/" in u.lower():
                if not landing_url:
                    landing_url = u
            elif "scielo" in u.lower() and "sci_arttext" in u.lower() and pid:
                # página HTML SciELO — PDF clássico como candidato
                sci = scielo_pdf_url(pid)
                if sci and sci not in candidates:
                    candidates.append(sci)
            elif not landing_url and u.startswith("http") and "doi.org" not in u.lower():
                landing_url = landing_url or u
        if pid and not pdf_url:
            sci = scielo_pdf_url(pid)
            if sci and sci not in candidates:
                candidates.append(sci)
            if not pdf_url and sci:
                pdf_url = sci
        source = "scielo" if pid else "oasisbr"
        venue = "SciELO" if pid else "Oasisbr"
        hit = PaperHit(
            paper_id=str(item.get("id") or doi or item.get("title") or ""),
            title=(item.get("title") or "Sem título").strip(),
            year=_year_from_pid(pid),
            authors=_vufind_authors(item.get("authors")),
            venue=venue,
            doi=doi,
            abstract="",
            pdf_url=pdf_url,
            source=source,
            landing_url=landing_url,
            pdf_candidates=candidates,
        )
        hits.append(hit)
        if landing_url and not (pdf_url and "/article/download/" in pdf_url.lower()):
            landings_to_scrape.append((hit, landing_url))

    if landings_to_scrape:
        with httpx.Client(timeout=25.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
            for hit, landing in landings_to_scrape[:12]:
                scraped = scrape_landing_pdf_url(landing, client=client)
                if scraped:
                    if scraped not in hit.pdf_candidates:
                        hit.pdf_candidates.insert(0, scraped)
                    # Prefere download OJS ao PDF SciELO bloqueado
                    if (
                        not hit.pdf_url
                        or _is_scielo_host(hit.pdf_url)
                        or "/article/download/" in scraped.lower()
                    ):
                        hit.pdf_url = scraped
                        if "unpaywall" not in hit.source and hit.source == "oasisbr":
                            hit.source = "oasisbr+ojs"
    return hits


def _crossref_title(item: dict) -> str:
    for key in ("title", "short-title", "subtitle"):
        for raw in item.get(key) or []:
            t = (raw or "").strip()
            if t and not t.lower().startswith("http"):
                return t
    return "Sem título"


def search_semantic_scholar(
    query: str,
    *,
    api_key: str = "",
    limit: int = 8,
    open_pdf_only: bool = False,
) -> list[PaperHit]:
    q = query.strip()
    if not q:
        return []
    params: list[tuple[str, str | int]] = [
        ("query", q),
        ("limit", max(1, min(limit, 20))),
        (
            "fields",
            "title,year,authors,abstract,externalIds,openAccessPdf,venue,isOpenAccess",
        ),
    ]
    if open_pdf_only:
        params.append(("openAccessPdf", ""))

    last_error: Exception | None = None
    payload: dict = {}
    with httpx.Client(timeout=30.0, follow_redirects=True, headers=_headers(api_key)) as client:
        for attempt in range(2):
            r = client.get(S2_SEARCH, params=params)
            if r.status_code == 429:
                last_error = RuntimeError(
                    "Semantic Scholar pediu para esperar (limite de buscas). "
                    "Aguarde 1 minuto ou coloque SEMANTIC_SCHOLAR_API_KEY no .env (chave grátis)."
                )
                if attempt == 0:
                    time.sleep(1.5)
                    continue
                raise last_error
            r.raise_for_status()
            payload = r.json()
            break
        else:
            if last_error:
                raise last_error

    hits: list[PaperHit] = []
    for item in payload.get("data") or []:
        ext = item.get("externalIds") or {}
        doi = (ext.get("DOI") or "").strip()
        oa = item.get("openAccessPdf") or {}
        pdf_url = (oa.get("url") or "").strip()
        hits.append(
            PaperHit(
                paper_id=str(item.get("paperId") or doi or item.get("title") or ""),
                title=(item.get("title") or "Sem título").strip(),
                year=item.get("year"),
                authors=_authors(item.get("authors")),
                venue=(item.get("venue") or "").strip(),
                doi=doi,
                abstract=((item.get("abstract") or "")[:500]).strip(),
                pdf_url=pdf_url,
                source="semantic-scholar",
            )
        )
    return hits


def search_crossref(query: str, *, email: str = "", limit: int = 8) -> list[PaperHit]:
    q = query.strip()
    if not q:
        return []
    params: dict[str, str | int] = {
        "query": q,
        "rows": max(1, min(limit, 20)),
        "filter": "type:journal-article",
        "select": "DOI,title,author,published-print,published-online,published,container-title,abstract,link",
    }
    if email and "@" in email:
        params["mailto"] = email

    with httpx.Client(timeout=30.0, follow_redirects=True, headers=_headers()) as client:
        r = client.get(CROSSREF_SEARCH, params=params)
        r.raise_for_status()
        payload = r.json()

    hits: list[PaperHit] = []
    for item in (payload.get("message") or {}).get("items") or []:
        doi = (item.get("DOI") or "").strip()
        title = _crossref_title(item)
        venues = item.get("container-title") or []
        venue = (venues[0] if venues else "").strip()
        abstract = re.sub(r"<[^>]+>", "", item.get("abstract") or "")
        pdf_url = ""
        for link in item.get("link") or []:
            if (link.get("content-type") or "") == "application/pdf":
                candidate = (link.get("URL") or "").strip()
                if _looks_like_pdf_url(candidate):
                    pdf_url = candidate
                    break
        hits.append(
            PaperHit(
                paper_id=doi or title,
                title=title,
                year=_crossref_year(item),
                authors=_crossref_authors(item.get("author")),
                venue=venue,
                doi=doi,
                abstract=abstract[:500].strip(),
                pdf_url=pdf_url,
                source="crossref",
            )
        )
    return hits


def unpaywall_pdf_url(doi: str, email: str, *, client: httpx.Client | None = None) -> str:
    cands = unpaywall_pdf_urls(doi, email, client=client)
    return cands[0] if cands else ""


def unpaywall_pdf_urls(doi: str, email: str, *, client: httpx.Client | None = None) -> list[str]:
    doi = doi.strip()
    email = email.strip()
    if not doi or "@" not in email:
        return []
    url = UNPAYWALL.format(doi=quote(doi, safe="/"))
    own = client is None
    if own:
        client = httpx.Client(timeout=30.0, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    try:
        r = client.get(url, params={"email": email})
        if r.status_code in (404, 422):
            # 422 = e-mail rejeitado; não aborta a busca inteira
            return []
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []
    finally:
        if own and client is not None:
            client.close()
    return _pdfs_from_unpaywall(data)


def attach_unpaywall_pdfs(hits: list[PaperHit], email: str) -> None:
    """Preenche pdf_url via Unpaywall quando o catálogo não trouxe PDF."""
    if "@" not in (email or ""):
        return
    missing = [h for h in hits if (not h.pdf_url or _is_scielo_host(h.pdf_url)) and h.doi]
    if not missing:
        return
    with httpx.Client(timeout=30.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        for hit in missing:
            urls = unpaywall_pdf_urls(hit.doi, email, client=client)
            if not urls:
                continue
            for u in urls:
                if u not in hit.pdf_candidates:
                    hit.pdf_candidates.append(u)
            hit.pdf_candidates = _prefer_direct_pdf(hit.pdf_candidates)
            best = hit.pdf_candidates[0] if hit.pdf_candidates else urls[0]
            # Troca SciELO por espelho OJS/repositório quando existir
            if not hit.pdf_url or _is_scielo_host(hit.pdf_url) or not _is_scielo_host(best):
                hit.pdf_url = best
            if "unpaywall" not in hit.source:
                hit.source = f"{hit.source}+unpaywall"


def search_academic(
    query: str,
    *,
    s2_key: str = "",
    email: str = "",
    limit: int = 8,
) -> tuple[list[PaperHit], str]:
    """Oasisbr primeiro; S2/Crossref se o IBICT falhar. Unpaywall nos DOIs.

    Retorna (hits, nota_para_a_tela).
    """
    note = ""
    hits: list[PaperHit] = []
    try:
        hits = search_oasisbr(query, limit=limit)
        note = "Oasisbr (IBICT)"
    except Exception as exc:
        note = f"Oasisbr indisponível ({exc}). Tentando catálogos internacionais…"
        hits = []

    if not hits:
        try:
            hits = search_semantic_scholar(query, api_key=s2_key, limit=limit)
            note = "Semantic Scholar"
        except Exception as exc:
            note = f"{note} Semantic Scholar indisponível ({exc}). Tentando Crossref…"
            hits = []
        if not hits:
            hits = search_crossref(query, email=email, limit=limit)
            if hits:
                note = "Crossref"

    attach_unpaywall_pdfs(hits, email)
    return _dedupe(hits), note


def _dedupe(hits: list[PaperHit]) -> list[PaperHit]:
    seen: set[str] = set()
    out: list[PaperHit] = []
    for hit in hits:
        key = (hit.doi or hit.paper_id).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(hit)
    return out


def resolve_pdf_url(hit: PaperHit, contact_email: str) -> str:
    cands = resolve_pdf_candidates(hit, contact_email)
    return cands[0] if cands else ""


def resolve_pdf_candidates(hit: PaperHit, contact_email: str) -> list[str]:
    """Lista ordenada de URLs candidatas a PDF aberto."""
    found: list[str] = list(hit.all_pdf_candidates())
    if hit.landing_url:
        scraped = scrape_landing_pdf_url(hit.landing_url)
        if scraped and scraped not in found:
            found.insert(0, scraped)
    if hit.doi:
        for u in unpaywall_pdf_urls(hit.doi, contact_email):
            if u not in found:
                found.append(u)
    pid = _scielo_pid(hit.doi or "", hit.paper_id, hit.landing_url or "")
    if pid:
        sci = scielo_pdf_url(pid)
        if sci and sci not in found:
            found.append(sci)
    return _prefer_direct_pdf(found)


def _safe_filename(title: str, year: int | None) -> str:
    slug = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
    slug = re.sub(r"\s+", "_", slug).strip("_")[:60] or "artigo"
    y = f"_{year}" if year else ""
    return f"{slug}{y}.pdf"


def pdf_extractable_char_count(path: Path) -> int:
    """Quantidade de texto selecionável no PDF (0 = scan só imagem)."""
    try:
        import pymupdf

        doc = pymupdf.open(path)
        try:
            return sum(len(page.get_text()) for page in doc)
        finally:
            doc.close()
    except Exception:
        return -1


def validate_pdf_has_extractable_text(path: Path, *, min_chars: int = 40) -> None:
    """PaperQA precisa de texto; PDFs só imagem falham com 'Is it empty?'."""
    count = pdf_extractable_char_count(path)
    if count < 0:
        raise RuntimeError(f"Não foi possível abrir o PDF: {path.name}")
    if count < min_chars:
        raise RuntimeError(
            f"O PDF «{path.name}» não tem texto selecionável (provavelmente é scan/só imagem). "
            "Baixe uma versão com texto ou use OCR e envie em Enviar PDFs."
        )


def download_pdf(url: str, dest_dir: Path, filename: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    if dest.exists():
        dest = dest_dir / f"{dest.stem}_novo{dest.suffix}"
    parsed = urlparse(url)
    referer = f"{parsed.scheme}://{parsed.netloc}/" if parsed.scheme and parsed.netloc else ""
    headers = {
        **BROWSER_HEADERS,
        "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    with httpx.Client(timeout=90.0, follow_redirects=True, headers=headers) as client:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            ctype = (r.headers.get("content-type") or "").lower()
            chunks = []
            size = 0
            for chunk in r.iter_bytes():
                size += len(chunk)
                if size > 40 * 1024 * 1024:
                    raise RuntimeError("PDF maior que 40 MB; baixe manualmente e envie em Enviar PDFs.")
                chunks.append(chunk)
    data = b"".join(chunks)
    if data.startswith(b"%PDF"):
        dest.write_bytes(data)
        try:
            validate_pdf_has_extractable_text(dest)
        except RuntimeError:
            dest.unlink(missing_ok=True)
            raise
        return dest
    # Às vezes o "PDF" é HTML de desafio anti-bot (SciELO/Bunny Shield)
    if b"bunny-shield" in data[:4000].lower() or b"challenge" in data[:2000].lower():
        raise RuntimeError(
            "O site do PDF bloqueou o download automático (proteção anti-bot). "
            "Abra o link no navegador, salve o PDF e use Enviar PDFs."
        )
    if "html" in ctype or data[:32].lstrip().lower().startswith((b"<!doctype", b"<html")):
        raise RuntimeError(
            "O link não devolveu um PDF (página HTML ou acesso restrito). "
            "Baixe o arquivo no site e use Enviar PDFs."
        )
    raise RuntimeError(
        "O link não devolveu um PDF (página HTML ou acesso restrito). "
        "Baixe o arquivo no site e use Enviar PDFs."
    )


def download_first_working_pdf(
    urls: list[str],
    dest_dir: Path,
    filename: str,
) -> Path:
    """Tenta cada URL candidata até obter um PDF válido."""
    errors: list[str] = []
    for url in urls:
        if not url:
            continue
        try:
            return download_pdf(url, dest_dir, filename)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{urlparse(url).hostname or url}: {exc}")
            continue
    if not urls:
        raise RuntimeError(
            "Sem PDF em acesso aberto. Baixe no SciELO/site da revista e use Enviar PDFs."
        )
    detail = errors[-1] if errors else "falha desconhecida"
    raise RuntimeError(
        f"Não foi possível baixar o PDF automaticamente ({detail}). "
        "Baixe no site da revista e use Enviar PDFs."
    )
