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
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import httpx

S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_SEARCH = "https://api.crossref.org/works"
UNPAYWALL = "https://api.unpaywall.org/v2/{doi}"
OASISBR_SEARCH = "https://oasisbr.ibict.br/vufind/api/v1/search"
SCIELO_PDF = "https://www.scielo.br/scielo.php?script=sci_pdf&pid={pid}&lng=pt&tlng=pt"

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+", re.I)
_PID_RE = re.compile(r"(S\d{4}-\d{4}\d{13})", re.I)
USER_AGENT = (
    "Furyu/2.0 (MVP educacional; "
    "+https://github.com/edidiodantas/ProjetoGuit)"
)


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

    @property
    def has_open_pdf(self) -> bool:
        return bool(self.pdf_url)


def _headers(s2_key: str = "") -> dict[str, str]:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if s2_key:
        h["x-api-key"] = s2_key
    return h


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
    ):
        return True
    return False


def _pdf_from_unpaywall(data: dict) -> str:
    locations = []
    best = data.get("best_oa_location")
    if best:
        locations.append(best)
    for loc in data.get("oa_locations") or []:
        if loc and loc not in locations:
            locations.append(loc)
    for loc in locations:
        pdf = (loc.get("url_for_pdf") or "").strip()
        if pdf:
            return pdf
        url = (loc.get("url") or "").strip()
        if _looks_like_pdf_url(url):
            return url
    return ""


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
        for u in urls:
            if _looks_like_pdf_url(u):
                pdf_url = u
                break
        source = "scielo" if pid else "oasisbr"
        venue = "SciELO" if pid else "Oasisbr"
        hits.append(
            PaperHit(
                paper_id=str(item.get("id") or doi or item.get("title") or ""),
                title=(item.get("title") or "Sem título").strip(),
                year=_year_from_pid(pid),
                authors=_vufind_authors(item.get("authors")),
                venue=venue,
                doi=doi,
                abstract="",
                pdf_url=pdf_url,
                source=source,
            )
        )
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
    doi = doi.strip()
    email = email.strip()
    if not doi or "@" not in email:
        return ""
    url = UNPAYWALL.format(doi=quote(doi, safe="/"))
    own = client is None
    if own:
        client = httpx.Client(timeout=30.0, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    try:
        r = client.get(url, params={"email": email})
        if r.status_code == 404:
            return ""
        if r.status_code == 422:
            raise RuntimeError(
                "Unpaywall recusou o e-mail. Use um e-mail real em CONTACT_EMAIL no .env."
            )
        r.raise_for_status()
        data = r.json()
    finally:
        if own and client is not None:
            client.close()
    return _pdf_from_unpaywall(data)


def attach_unpaywall_pdfs(hits: list[PaperHit], email: str) -> None:
    """Preenche pdf_url via Unpaywall quando o catálogo não trouxe PDF."""
    if "@" not in (email or ""):
        return
    missing = [h for h in hits if not h.pdf_url and h.doi]
    if not missing:
        return
    with httpx.Client(timeout=30.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        for hit in missing:
            try:
                url = unpaywall_pdf_url(hit.doi, email, client=client)
            except RuntimeError:
                raise
            except Exception:
                continue
            if url:
                hit.pdf_url = url
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
    if hit.pdf_url and _looks_like_pdf_url(hit.pdf_url):
        return hit.pdf_url
    if hit.doi:
        url = unpaywall_pdf_url(hit.doi, contact_email)
        if url:
            return url
    pid = _scielo_pid(hit.doi or "", hit.paper_id)
    if pid:
        return scielo_pdf_url(pid)
    return hit.pdf_url or ""


def _safe_filename(title: str, year: int | None) -> str:
    slug = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
    slug = re.sub(r"\s+", "_", slug).strip("_")[:60] or "artigo"
    y = f"_{year}" if year else ""
    return f"{slug}{y}.pdf"


def download_pdf(url: str, dest_dir: Path, filename: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    if dest.exists():
        dest = dest_dir / f"{dest.stem}_novo{dest.suffix}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"}
    with httpx.Client(timeout=90.0, follow_redirects=True, headers=headers) as client:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            chunks = []
            size = 0
            for chunk in r.iter_bytes():
                size += len(chunk)
                if size > 40 * 1024 * 1024:
                    raise RuntimeError("PDF maior que 40 MB; baixe manualmente e envie em Enviar PDFs.")
                chunks.append(chunk)
    data = b"".join(chunks)
    if not data.startswith(b"%PDF"):
        raise RuntimeError(
            "O link não devolveu um PDF (página HTML ou acesso restrito). "
            "Baixe o arquivo no site e use Enviar PDFs."
        )
    dest.write_bytes(data)
    return dest
