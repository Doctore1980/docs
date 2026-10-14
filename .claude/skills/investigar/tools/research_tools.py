"""
research_tools.py -- Ancla determinista de investigacion-agentica.

Este modulo NO usa ningun LLM. Es la fuente de verdad del sistema: hace las
busquedas reproducibles y comprueba, contra APIs oficiales, que cada
identificador citado (PMID / NCT / DOI) existe de verdad y si esta retractado.

Uso como CLI (lo invoca la skill /investigar):

  # Buscar candidatos para una faceta (imprime JSON a stdout)
  python tools/research_tools.py search --query "PSMA PET biochemical recurrence prostate cancer" \
      --condition "Prostate Cancer" --days 3650

  # Puerta de verificacion de un expediente (lee los identificadores de sus JSON)
  python tools/research_tools.py gate --caso casos/2026-10-03-ejemplo

  # Citas del documento contra la lista de VALIDOS, y auditoria de cifras
  python tools/research_tools.py check-citations --doc DOC.md --validos _validos.json
  python tools/research_tools.py audit-figures --doc DOC.md --caso casos/2026-10-03-ejemplo

  # Comprobacion suelta de identificadores
  python tools/research_tools.py verify PMID:29565221 NCT:NCT02043678

La salida siempre es JSON en stdout, para que la skill la lea sin ambiguedad.
"""

from __future__ import annotations

import re
import sys
import html
import json
import time
import argparse
import glob
import os
from urllib.parse import quote
from datetime import datetime, timedelta, timezone

import requests

HTTP_HEADERS = {
    "User-Agent": "investigacion-agentica/2.0 (research assistant; mailto:investigacion@agente.local)"
}


# ---------------------------------------------------------------------
# Red resiliente
# ---------------------------------------------------------------------

def safe_get(url: str, params: dict | None = None, timeout: int = 30, retries: int = 2,
             headers: dict | None = None) -> requests.Response | None:
    """GET con User-Agent polite, reintentos y tolerancia a rate-limiting."""
    cabeceras = {**HTTP_HEADERS, **(headers or {})}
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, headers=cabeceras, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return resp
        except requests.RequestException:
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return None
    return None


# Estado de cada fuente en la ultima busqueda: una fuente que falla (429, cuota
# agotada, sin red) devuelve 0 candidatos, y sin este registro no se distingue
# de "no hay estudios". `search` lo publica en el campo `fuentes`.
FUENTES_ESTADO: dict[str, str] = {}


def _fallo(fuente: str, resp) -> list:
    FUENTES_ESTADO[fuente] = f"error: {_http(resp)}"
    return []


def _ok(fuente: str, out: list) -> list:
    FUENTES_ESTADO[fuente] = f"ok ({len(out)})"
    return out


def _texto_plano(s: str | None) -> str:
    """Quita etiquetas y decodifica entidades (p&lt;0.001 -> p<0.001), en ese orden."""
    sin_etiquetas = re.sub(r"</?[A-Za-z][^<>]*>", "", s or "")  # respeta "p<0.05" literal
    return re.sub(r"\s+", " ", html.unescape(sin_etiquetas)).strip()


# ---------------------------------------------------------------------
# Normalizacion de identificadores
# ---------------------------------------------------------------------

def normalize_identifier(identifier: str) -> str:
    """Normaliza PMID / NCT / DOI para deduplicar y evitar errores de formato."""
    if not identifier:
        return ""
    identifier = identifier.strip()
    identifier = re.sub(r"^https?://(?:dx\.)?doi\.org/", "DOI:", identifier, flags=re.IGNORECASE)
    if ":" not in identifier:
        return identifier
    kind, val = identifier.split(":", 1)
    kind, val = kind.strip().upper(), val.strip()
    if kind == "DOI":
        return f"DOI:{val.lower()}"
    if kind == "PMID":
        digits = re.sub(r"\D", "", val)
        return f"PMID:{digits if digits else val}"
    if kind == "NCT":
        return f"NCT:{val.upper()}"
    return f"{kind}:{val}"


# ---------------------------------------------------------------------
# Busqueda determinista multi-fuente
# ---------------------------------------------------------------------

def fetch_pubmed(query: str, days: int | None = 3650, retmax: int = 25) -> list[dict]:
    term = query
    if days:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        term = f"{query} AND {start:%Y/%m/%d}:{end:%Y/%m/%d}[edat]"
    resp = safe_get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": term, "retmode": "json", "retmax": retmax, "sort": "relevance"},
    )
    if not resp or resp.status_code != 200:
        return _fallo("PubMed", resp)
    try:
        ids = resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception:
        return _fallo("PubMed", resp)
    if not ids:
        return _ok("PubMed", [])
    time.sleep(0.4)
    resp_sum = safe_get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
    )
    if not resp_sum or resp_sum.status_code != 200:
        return _fallo("PubMed", resp_sum)
    try:
        result = resp_sum.json().get("result", {})
    except Exception:
        return _fallo("PubMed", resp_sum)
    out = []
    for pmid in ids:
        doc = result.get(pmid, {})
        if not doc:
            continue
        pubtypes = doc.get("pubtype", []) or []
        out.append({
            "identifier": normalize_identifier(f"PMID:{pmid}"),
            "title": doc.get("title", ""),
            "date": doc.get("pubdate", ""),
            "journal": doc.get("fulljournalname", "") or doc.get("source", ""),
            "pubtypes": pubtypes,
            "source": "PubMed",
        })
    return _ok("PubMed", out)


def fetch_clinicaltrials(condition: str, page_size: int = 15) -> list[dict]:
    resp = safe_get(
        "https://clinicaltrials.gov/api/v2/studies",
        params={"query.cond": condition, "pageSize": page_size, "sort": "LastUpdatePostDate:desc"},
    )
    if not resp or resp.status_code != 200:
        return _fallo("ClinicalTrials.gov", resp)
    try:
        studies = resp.json().get("studies", [])
    except Exception:
        return _fallo("ClinicalTrials.gov", resp)
    out = []
    for study in studies:
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status = proto.get("statusModule", {})
        nct = ident.get("nctId", "")
        if nct:
            out.append({
                "identifier": normalize_identifier(f"NCT:{nct}"),
                "title": ident.get("briefTitle", ""),
                "date": status.get("lastUpdatePostDateStruct", {}).get("date", ""),
                "status": status.get("overallStatus", ""),
                "source": "ClinicalTrials.gov",
            })
    return _ok("ClinicalTrials.gov", out)


def fetch_europepmc(query: str, page_size: int = 20) -> list[dict]:
    resp = safe_get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={"query": query, "format": "json", "pageSize": page_size, "resultType": "core"},
    )
    if not resp or resp.status_code != 200:
        return _fallo("Europe PMC", resp)
    try:
        results = resp.json().get("resultList", {}).get("result", [])
    except Exception:
        return _fallo("Europe PMC", resp)
    out = []
    for item in results:
        doi, pmid = item.get("doi"), item.get("pmid")
        ident = f"DOI:{doi}" if doi else (f"PMID:{pmid}" if pmid else None)
        if ident:
            out.append({
                "identifier": normalize_identifier(ident),
                "title": item.get("title", ""),
                "date": item.get("firstPublicationDate", ""),
                "journal": item.get("journalTitle", ""),
                "abstract": _texto_plano(item.get("abstractText"))[:6000],
                "source": "Europe PMC",
            })
    return _ok("Europe PMC", out)


def fetch_semantic_scholar(query: str, limit: int = 20) -> list[dict]:
    resp = safe_get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": query, "limit": limit, "fields": "title,externalIds,year,venue,abstract"},
        headers={"x-api-key": key} if (key := os.environ.get("SEMANTIC_SCHOLAR_API_KEY")) else None,
    )
    if not resp or resp.status_code != 200:
        return _fallo("Semantic Scholar", resp)
    try:
        data = resp.json().get("data", [])
    except Exception:
        return _fallo("Semantic Scholar", resp)
    out = []
    for item in data:
        ext = item.get("externalIds") or {}
        doi, pmid = ext.get("DOI"), ext.get("PubMed")
        ident = f"DOI:{doi}" if doi else (f"PMID:{pmid}" if pmid else None)
        if ident:
            out.append({
                "identifier": normalize_identifier(ident),
                "title": item.get("title", ""),
                "date": str(item.get("year", "")),
                "journal": item.get("venue", ""),
                "abstract": (item.get("abstract") or "")[:6000],
                "source": "Semantic Scholar",
            })
    return _ok("Semantic Scholar", out)


def fetch_openalex(query: str, per_page: int = 20) -> list[dict]:
    resp = safe_get(
        "https://api.openalex.org/works",
        params={"search": query, "per_page": per_page,
                **({"api_key": key} if (key := os.environ.get("OPENALEX_API_KEY")) else {})},
    )
    if not resp or resp.status_code != 200:
        return _fallo("OpenAlex", resp)
    try:
        results = resp.json().get("results", [])
    except Exception:
        return _fallo("OpenAlex", resp)
    out = []
    for item in results:
        doi_url = item.get("doi")
        if doi_url:
            out.append({
                "identifier": normalize_identifier(doi_url),
                "title": item.get("title", ""),
                "date": item.get("publication_date", ""),
                "abstract": _openalex_abstract(item.get("abstract_inverted_index"))[:6000],
                "source": "OpenAlex",
            })
    return _ok("OpenAlex", out)


def _openalex_abstract(inv_index: dict | None) -> str:
    """Reconstruye el abstract a partir del abstract_inverted_index de OpenAlex."""
    if not inv_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def fetch_pubmed_abstracts(pmids: list[str]) -> dict[str, str]:
    """Recupera el abstract de cada PMID vía efetch (determinista, sin LLM)."""
    if not pmids:
        return {}
    out: dict[str, str] = {}
    # efetch admite lotes; troceamos en grupos de 100 para no exceder URL/carga.
    for i in range(0, len(pmids), 100):
        batch = pmids[i:i + 100]
        resp = safe_get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(batch), "rettype": "abstract", "retmode": "xml"},
        )
        if not resp or resp.status_code != 200:
            continue
        for block in re.split(r"<PubmedArticle>", resp.text)[1:]:
            m = re.search(r"<PMID[^>]*>(\d+)</PMID>", block)
            if not m:
                continue
            pmid = m.group(1)
            parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", block, re.DOTALL)
            text = _texto_plano(" ".join(parts))
            if text:
                out[pmid] = text[:6000]
        time.sleep(0.34)
    return out


def enrich_abstracts(candidates: list[dict]) -> list[dict]:
    """Rellena el campo 'abstract' de cada candidato que no lo tenga (PMID vía efetch)."""
    faltan_pmid = [c["identifier"].split(":", 1)[1]
                   for c in candidates
                   if c["identifier"].startswith("PMID:") and not (c.get("abstract") or "").strip()]
    abstracts = fetch_pubmed_abstracts(list(dict.fromkeys(faltan_pmid)))
    for c in candidates:
        if (c.get("abstract") or "").strip():
            continue
        if c["identifier"].startswith("PMID:"):
            pmid = c["identifier"].split(":", 1)[1]
            c["abstract"] = abstracts.get(pmid, "")
        else:
            c.setdefault("abstract", "")
    return candidates


def search_all(query: str, condition: str | None = None, days: int | None = 3650,
               with_abstracts: bool = False, pubmed_query: str | None = None) -> list[dict]:
    """Ejecuta todas las fuentes deterministas y deduplica por identificador.

    `pubmed_query`: si se pasa (query booleana MeSH), se usa SOLO para PubMed;
    los motores semanticos (Europe PMC, Semantic Scholar, OpenAlex) siguen con
    `query` en texto libre, que es donde mejor rinden. Carril doble.
    """
    FUENTES_ESTADO.clear()
    candidatos: list[dict] = []
    candidatos += fetch_pubmed(pubmed_query or query, days=days)
    candidatos += fetch_europepmc(query)
    candidatos += fetch_semantic_scholar(query)
    candidatos += fetch_openalex(query)
    if condition:
        candidatos += fetch_clinicaltrials(condition)

    vistos: set[str] = set()
    unicos: list[dict] = []
    for c in candidatos:
        nid = normalize_identifier(c.get("identifier", ""))
        if nid and nid not in vistos:
            vistos.add(nid)
            c["identifier"] = nid
            unicos.append(c)
    if with_abstracts:
        unicos = enrich_abstracts(unicos)
    return unicos


# ---------------------------------------------------------------------
# Construccion de consulta: PICO + MeSH validado contra NCBI + booleanos.
# El modelo (Orquestador) propone conceptos con descriptores MeSH candidatos
# y sinonimos de texto libre; aqui se VALIDA cada MeSH contra PubMed (igual
# que se validan los PMIDs) y se arma una query booleana reproducible.
# ---------------------------------------------------------------------

def mesh_validate(term: str) -> dict:
    """Comprueba si `term` funciona como encabezado MeSH real en PubMed.

    Usa la propia traduccion de PubMed (`querytranslation`): si el termino se
    mapea a "...[MeSH Terms]" y hay resultados, es un descriptor valido.
    """
    term = (term or "").strip().strip('"')
    if not term:
        return {"term": term, "valid": False, "count": 0, "translation": ""}
    r = safe_get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": f'"{term}"[Mesh]', "retmode": "json", "retmax": 0},
        timeout=15,
    )
    time.sleep(0.15)
    if not r or r.status_code != 200:
        return {"term": term, "valid": False, "count": 0, "translation": "(sin respuesta)"}
    er = r.json().get("esearchresult", {})
    qt = er.get("querytranslation", "")
    count = int(er.get("count", "0") or 0)
    valid = ("[MeSH Terms]" in qt) and count > 0
    return {"term": term, "valid": valid, "count": count, "translation": qt}


def _tiab(term: str) -> str:
    t = (term or "").strip().strip('"')
    return f'"{t}"[tiab]' if " " in t else f'{t}[tiab]'


def build_pubmed_query(concepts: list[dict], validate: bool = True) -> dict:
    """Construye una query PubMed booleana a partir de conceptos PICO.

    concepts: [{"label": "P|I|C|O|...", "mesh": ["Descriptor", ...], "tiab": ["sinonimo", ...]}]
    Cada concepto -> bloque OR de sus MeSH validados + sinonimos [tiab]; los
    bloques se unen con AND. Los MeSH que no validan se degradan a [tiab] y se
    reportan. Devuelve la query, los bloques, el veredicto MeSH y (si se puede)
    el recuento y la traduccion real de PubMed para el expediente.
    """
    blocks: list[str] = []
    detalle: list[dict] = []
    mesh_ok: list[str] = []
    mesh_bad: list[str] = []
    for c in concepts:
        parts: list[str] = []
        for m in c.get("mesh", []):
            if validate:
                v = mesh_validate(m)
                if v["valid"]:
                    parts.append(f'"{m}"[Mesh]'); mesh_ok.append(m)
                else:
                    parts.append(_tiab(m)); mesh_bad.append(m)
            else:
                parts.append(f'"{m}"[Mesh]')
        for t in c.get("tiab", []):
            parts.append(_tiab(t))
        seen: set[str] = set()
        uniq = [p for p in parts if not (p in seen or seen.add(p))]
        if uniq:
            block = "(" + " OR ".join(uniq) + ")"
            blocks.append(block)
            detalle.append({"label": c.get("label", ""), "block": block})
    query = " AND ".join(blocks)
    out = {
        "query": query,
        "bloques": detalle,
        "mesh_validados": mesh_ok,
        "mesh_degradados_a_tiab": mesh_bad,
    }
    if query:
        r = safe_get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmode": "json", "retmax": 0},
            timeout=20,
        )
        if r and r.status_code == 200:
            er = r.json().get("esearchresult", {})
            out["pubmed_count"] = int(er.get("count", "0") or 0)
            out["pubmed_translation"] = er.get("querytranslation", "")
    return out


# ---------------------------------------------------------------------
# Verificacion determinista: existencia + retractacion
#
# Estados (unica definicion del sistema; SKILL.md y prompts la citan, no la
# redefinen). Solo VALIDO es citable.
#   VALIDO         existe y no consta retractacion en las fuentes consultadas
#   RETRACTADO     existe y consta retractado
#   NO_ENCONTRADO  la fuente oficial respondio que no existe
#   INCONCLUSO     no se pudo comprobar (red, limite de API, fuente caida o
#                  retractacion no evaluable). NO equivale a cita inventada.
#   MAL_FORMADO    el identificador no tiene forma valida; no se consulto nada
# ---------------------------------------------------------------------

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

_ID_FORMATS = {
    "PMID": re.compile(r"^\d{1,9}$"),
    "NCT": re.compile(r"^NCT\d{8}$"),
    "DOI": re.compile(r"^10\.\d{4,9}/\S+$"),
}

# Tipos de "update" de Crossref que invalidan un trabajo como apoyo de una
# afirmación. Las expressions of concern no invalidan.
_CROSSREF_RETRACTION_TYPES = {"retraction", "removal", "withdrawal", "partial_retraction"}


def coerce_identifier(raw: str) -> str:
    """Normaliza y, si falta el prefijo, lo infiere de la forma del identificador."""
    s = (raw or "").strip()
    if re.match(r"^https?://(?:dx\.)?doi\.org/", s, re.IGNORECASE) or re.match(r"^(PMID|NCT|DOI)\s*:", s, re.IGNORECASE):
        return normalize_identifier(s)
    if re.fullmatch(r"NCT\d{8}", s, re.IGNORECASE):
        return f"NCT:{s.upper()}"
    if s.startswith("10."):
        return f"DOI:{s.lower()}"
    if re.fullmatch(r"\d{1,9}", s):
        return f"PMID:{s}"
    return s


def _well_formed(ident: str) -> bool:
    if ":" not in ident:
        return False
    kind, value = ident.split(":", 1)
    pat = _ID_FORMATS.get(kind)
    return bool(pat and pat.match(value))


def _http(resp) -> str:
    return "sin conexion" if resp is None else f"HTTP {resp.status_code}"


def _pubmed_check(pmids: list[str]) -> dict[str, tuple]:
    """Devuelve {pmid: (exists, retractacion, detalle)} consultando PubMed por lotes.

    exists: True / False (PubMed dice que no existe) / None (no se pudo saber).
    retractacion: 'retractado' / 'no_encontrada' / 'inconclusa'. Un PMID que no
    aparece en la respuesta de efetch queda 'inconclusa', nunca 'no_encontrada'.
    """
    out: dict[str, tuple] = {}
    for i in range(0, len(pmids), 100):
        batch = pmids[i:i + 100]
        exists: dict[str, bool | None] = {p: None for p in batch}
        detalle = {p: "" for p in batch}
        r = safe_get(f"{EUTILS}/esummary.fcgi",
                     params={"db": "pubmed", "id": ",".join(batch), "retmode": "json"}, timeout=20)
        result = None
        if r is not None and r.status_code == 200:
            try:
                result = r.json().get("result")
            except Exception:
                result = None
        for p in batch:
            doc = result.get(p) if isinstance(result, dict) else None
            if doc is None:
                detalle[p] = f"esummary de PubMed sin respuesta util ({_http(r)})"
            elif "error" in doc:
                # PubMed devuelve una entrada con campo "error" para PMIDs inexistentes.
                exists[p] = False
                detalle[p] = "PubMed: " + str(doc.get("error"))
            else:
                exists[p] = True
        time.sleep(0.34)
        retr = {p: "inconclusa" for p in batch}
        vivos = [p for p in batch if exists[p]]
        if vivos:
            r2 = safe_get(f"{EUTILS}/efetch.fcgi",
                          params={"db": "pubmed", "id": ",".join(vivos), "retmode": "xml"}, timeout=30)
            if r2 is not None and r2.status_code == 200:
                for block in re.split(r"<PubmedArticle>|<PubmedBookArticle>", r2.text)[1:]:
                    m = re.search(r"<PMID[^>]*>(\d+)</PMID>", block)
                    if not m:
                        continue
                    retractado = bool(
                        re.search(r"<PublicationType[^>]*>Retracted Publication</PublicationType>", block)
                        or re.search(r'RefType="RetractionIn"', block)
                    )
                    retr[m.group(1)] = "retractado" if retractado else "no_encontrada"
            for p in vivos:
                if retr[p] == "inconclusa":
                    detalle[p] = f"efetch de PubMed no devolvio el registro ({_http(r2)}): retractacion sin comprobar"
            time.sleep(0.34)
        for p in batch:
            out[p] = (exists[p], retr[p], detalle[p])
    return out


def _crossref_retraction(doi: str) -> str:
    """'retractado' / 'no_encontrada' / 'inconclusa' segun las notas que actualizan el DOI.

    Crossref registra las retractaciones como trabajos con campo `update-to`
    apuntando al DOI original; `filter=updates:{doi}` los recupera.
    """
    resp = safe_get("https://api.crossref.org/works",
                    params={"filter": f"updates:{doi}", "rows": 20}, timeout=15)
    if resp is None or resp.status_code != 200:
        return "inconclusa"
    try:
        items = resp.json().get("message", {}).get("items", [])
    except Exception:
        return "inconclusa"
    for item in items:
        for upd in item.get("update-to", []) or []:
            if (upd.get("DOI") or "").lower() == doi.lower() and \
                    (upd.get("type") or "").lower() in _CROSSREF_RETRACTION_TYPES:
                return "retractado"
    return "no_encontrada"


def _doi_check(doi: str) -> tuple:
    """Devuelve (exists, retractacion, checked_against, detalle, reintentable)."""
    path = quote(doi, safe="/")
    r = safe_get(f"https://api.crossref.org/works/{path}", timeout=15)
    if r is not None and r.status_code == 200:
        try:
            msg = r.json().get("message", {})
        except Exception:
            return None, "inconclusa", "Crossref", "respuesta ilegible de Crossref", True
        for upd in msg.get("updated-by", []) or []:
            if (upd.get("type") or "").lower() in _CROSSREF_RETRACTION_TYPES:
                return True, "retractado", "Crossref (updated-by)", "", False
        retr = _crossref_retraction(doi)
        detalle = "" if retr != "inconclusa" else "Crossref no respondio a la consulta de retractacion"
        return True, retr, "Crossref (existencia + notas de retractacion)", detalle, retr == "inconclusa"
    if r is not None and r.status_code == 404:
        # Crossref no es el unico registro de DOI (DataCite: preprints, datasets).
        h = safe_get(f"https://doi.org/api/handles/{path}", timeout=15)
        if h is not None and h.status_code == 200:
            return (True, "inconclusa", "doi.org (DOI ajeno a Crossref)",
                    "existe pero no esta en Crossref: retractacion no evaluable por script", False)
        if h is not None and h.status_code == 404:
            return False, "inconclusa", "Crossref + doi.org", "no resuelve en Crossref ni en doi.org", False
        return None, "inconclusa", "Crossref + doi.org", f"Crossref 404 y doi.org sin respuesta util ({_http(h)})", True
    return None, "inconclusa", "Crossref", f"sin respuesta util ({_http(r)})", True


def _entry(exists, retr: str, checked: str, detalle: str, reintentable: bool) -> dict:
    if exists is False:
        estado = "NO_ENCONTRADO"
    elif exists is None:
        estado = "INCONCLUSO"
    elif retr == "retractado":
        estado = "RETRACTADO"
    elif retr == "inconclusa":
        estado = "INCONCLUSO"
    else:
        estado = "VALIDO"
    retracted = None
    if exists:
        retracted = {"retractado": True, "no_encontrada": False, "no_aplica": False}.get(retr)
    return {
        "estado": estado,
        "exists": exists,
        "retracted": retracted,
        "retractacion": retr if exists else "sin_comprobar",
        "checked_against": checked,
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "detalle": detalle,
        "reintentable": bool(reintentable) and estado == "INCONCLUSO",
    }


def _verify_once(norm: list[str]) -> dict[str, dict]:
    pmids = [n.split(":", 1)[1] for n in norm if n.startswith("PMID:") and _well_formed(n)]
    pm = _pubmed_check(pmids) if pmids else {}
    out: dict[str, dict] = {}
    for ident in norm:
        if not _well_formed(ident):
            out[ident] = {
                "estado": "MAL_FORMADO", "exists": None, "retracted": None,
                "retractacion": "sin_comprobar", "checked_against": "",
                "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "detalle": "no tiene forma de PMID, NCT ni DOI; no se consulto ninguna fuente",
                "reintentable": False,
            }
            continue
        kind, value = ident.split(":", 1)
        if kind == "PMID":
            exists, retr, detalle = pm[value]
            out[ident] = _entry(exists, retr, "PubMed E-utilities (esummary + efetch)", detalle, True)
        elif kind == "NCT":
            r = safe_get(f"https://clinicaltrials.gov/api/v2/studies/{value}", timeout=15)
            if r is not None and r.status_code == 200:
                out[ident] = _entry(True, "no_aplica", "ClinicalTrials.gov API v2", "", False)
            elif r is not None and r.status_code == 404:
                out[ident] = _entry(False, "inconclusa", "ClinicalTrials.gov API v2", "ClinicalTrials.gov: 404", False)
            else:
                out[ident] = _entry(None, "inconclusa", "ClinicalTrials.gov API v2",
                                    f"sin respuesta util ({_http(r)})", True)
            time.sleep(0.1)
        else:
            out[ident] = _entry(*_doi_check(value))
            time.sleep(0.1)
    return out


def verify_identifiers(identifiers: list[str], reintentos: int = 1) -> dict[str, dict]:
    """Comprueba existencia y retractacion de cada identificador.

    Devuelve {identificador_normalizado: {estado, exists, retracted, retractacion,
    checked_against, checked_at, detalle, reintentable}}. Los INCONCLUSO por
    fallo tecnico se reintentan `reintentos` veces antes de darlos por tales.
    """
    norm = list(dict.fromkeys(coerce_identifier(i) for i in identifiers if i and i.strip()))
    out = _verify_once(norm)
    for _ in range(reintentos):
        pend = [k for k, v in out.items() if v["reintentable"]]
        if not pend:
            break
        time.sleep(3)
        out.update(_verify_once(pend))
    return out


# ---------------------------------------------------------------------
# Puerta de verificacion sobre un expediente: lee los identificadores de los
# JSON (nunca de la linea de comandos), verifica y deja la lista citable.
# ---------------------------------------------------------------------

def _load_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _walk_identifiers(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "identifier" and isinstance(v, str) and v.strip():
                yield v
            else:
                yield from _walk_identifiers(v)
    elif isinstance(obj, list):
        for x in obj:
            yield from _walk_identifiers(x)


def run_gate(caso: str) -> tuple[dict, int]:
    """Verifica todo identificador citado en el expediente (investigadores + deep research).

    Escribe 03-verificacion.json y _validos.json. Devuelve (resumen, codigo):
    0 continuar, 2 detener (no encontrados, mal formados o nada que verificar),
    3 fallo tecnico (quedan INCONCLUSO tras reintentar).
    """
    fuentes = sorted(glob.glob(os.path.join(caso, "02-investigador", "*.json")))
    deep = os.path.join(caso, "02b-deepresearch.json")
    if os.path.exists(deep):
        fuentes.append(deep)
    citados: list[str] = []
    ilegibles: list[str] = []
    for f in fuentes:
        data = _load_json(f)
        if data is None:
            ilegibles.append(f)
            continue
        citados += list(_walk_identifiers(data))
    candidatos: set[str] = set()
    for f in glob.glob(os.path.join(caso, "_candidatos*", "*.json")):
        candidatos |= {coerce_identifier(i) for i in _walk_identifiers(_load_json(f) or {})}

    res = verify_identifiers(citados)
    por_estado: dict[str, list[str]] = {}
    for ident, v in res.items():
        v["origen"] = "candidatos" if ident in candidatos else "fuera_de_candidatos"
        por_estado.setdefault(v["estado"], []).append(ident)
    validos = por_estado.get("VALIDO", [])

    with open(os.path.join(caso, "03-verificacion.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(caso, "_validos.json"), "w", encoding="utf-8") as fh:
        json.dump(validos, fh, ensure_ascii=False, indent=2)

    if ilegibles or not res or por_estado.get("NO_ENCONTRADO") or por_estado.get("MAL_FORMADO"):
        codigo, puerta = 2, "DETENER: hay identificadores no encontrados o mal formados, ficheros ilegibles o nada que verificar"
    elif por_estado.get("INCONCLUSO"):
        codigo, puerta = 3, "FALLO TECNICO: quedan identificadores sin poder comprobar tras reintentar"
    else:
        codigo, puerta = 0, "CONTINUAR"
    resumen = {
        "puerta": puerta,
        "n_citados": len(res),
        "por_estado": por_estado,
        "fuera_de_candidatos": [k for k, v in res.items() if v["origen"] == "fuera_de_candidatos"],
        "ficheros_ilegibles": ilegibles,
        "detalle_no_validos": {k: v["detalle"] for k, v in res.items() if v["estado"] != "VALIDO"},
    }
    return resumen, codigo


# ---------------------------------------------------------------------
# Citas del documento: toda cita debe estar en la lista de VALIDOS.
# ---------------------------------------------------------------------

_BRACKET_CITE_RE = re.compile(r"\[((?:PMID|DOI|NCT)\s*:[^\]]+)\]", re.IGNORECASE)


def _trim_doi(s: str) -> str:
    while s and (s[-1] in ".,;:" or (s[-1] == ")" and s.count("(") < s.count(")"))):
        s = s[:-1]
    return s


def extract_citations(text: str) -> list[str]:
    """Identificadores citados en un texto: entre corchetes o sueltos."""
    found: list[str] = []
    for m in _BRACKET_CITE_RE.finditer(text):
        for part in re.split(r"\s*[;,]\s*(?=(?:PMID|DOI|NCT)\s*:)", m.group(1), flags=re.IGNORECASE):
            found.append(coerce_identifier(part))
    resto = _BRACKET_CITE_RE.sub(" ", text)
    for m in re.finditer(r"PMID\s*:?\s*(\d{1,9})", resto, re.IGNORECASE):
        found.append(f"PMID:{m.group(1)}")
    for m in re.finditer(r"\bNCT\d{8}\b", resto, re.IGNORECASE):
        found.append(f"NCT:{m.group(0).upper()}")
    for m in re.finditer(r"10\.\d{4,9}/[^\s\]>\"',;]+", resto):
        found.append(f"DOI:{_trim_doi(m.group(0)).lower()}")
    return list(dict.fromkeys(found))


def check_citations(doc: str, validos: list[str]) -> dict:
    """Marca toda cita del documento que no este en la lista de VALIDOS."""
    permitidos = {coerce_identifier(v) for v in validos}
    citas = extract_citations(doc)
    fuera = [c for c in citas if c not in permitidos]
    return {
        "n_citas": len(citas),
        "fuera_de_validos": fuera,
        "veredicto": "OK" if not fuera else "DETENER: el documento cita identificadores que no estan en VALIDOS",
    }


# ---------------------------------------------------------------------
# Auditoria de cifras: localiza cada cifra del documento en las fuentes de
# las citas de su misma linea. Encontrar el numero NO demuestra que la fuente
# respalde la afirmacion: por eso se devuelve el fragmento, para cotejarlo.
# ---------------------------------------------------------------------

# Cifras que importan clínicamente: porcentajes, decimales tipo 0.xx, e enteros
# de >=3 dígitos (tamaños muestrales, estadísticos). Los enteros de 1-2 dígitos
# suelen ser estructura (nº de diapositiva, ratios 16:9) y se ignoran. Los enteros
# con separador de millares ("2.586", "1,204") cuentan como un solo número.
_NUM_RE = re.compile(
    r"(?<![\w.])\d{1,3}(?:[.,]\d+)?\s?%"
    r"|(?<![\w.])0[.,]\d+"
    r"|(?<![\w.,])[1-9]\d{0,2}(?:[.,]\d{3})+(?![\w]|[.,]\d)"
    r"|(?<![\w.,])\d{3,}(?![\w.])"
)
_MILLARES_RE = re.compile(r"(?<!(?<!\d)0)(?<=\d)[.,](?=\d{3}(?!\d))")


def _norm_num(tok: str) -> str:
    tok = tok.replace(" ", "")
    if re.fullmatch(r"[1-9]\d{0,2}(?:[.,]\d{3})+", tok):
        return re.sub(r"[.,]", "", tok)
    return tok.replace(",", ".").rstrip("%")


def _find_number(n: str, texto: str) -> str | None:
    """Fragmento de `texto` donde aparece la cifra `n` como numero completo, o None."""
    patron = r"(?<![\d.])" + re.escape(n) + r"(?!\d|\.\d)"
    m = re.search(patron, texto.replace(",", "."))  # misma longitud: los indices valen para `texto`
    if m:
        return texto[max(0, m.start() - 70): m.end() + 70].strip()
    if n.isdigit() and len(n) >= 4:
        sin_millares = _MILLARES_RE.sub("", texto)
        m = re.search(patron, sin_millares)
        if m:
            return sin_millares[max(0, m.start() - 70): m.end() + 70].strip()
    return None


def build_corpus(caso: str) -> dict[str, list[dict]]:
    """Fuentes de respaldo del expediente: {cita: [{lugar, texto}]}.

    Abstracts de los candidatos, fragmentos transcritos por los investigadores
    (`evidencia_numerica`: abstract, Elicit o texto completo) y extractos de
    guias / deep research (clave = identificador o URL).
    """
    corpus: dict[str, list[dict]] = {}

    def add(clave: str, lugar: str, texto) -> None:
        if clave and texto:
            corpus.setdefault(clave, []).append({"lugar": lugar, "texto": str(texto)})

    for f in glob.glob(os.path.join(caso, "_candidatos*", "*.json")):
        for c in (_load_json(f) or {}).get("candidatos", []):
            add(coerce_identifier(c.get("identifier", "")), f"abstract ({c.get('source', '')})", c.get("abstract"))
    for f in glob.glob(os.path.join(caso, "02-investigador", "*.json")):
        for it in (_load_json(f) or {}).get("items", []):
            add(coerce_identifier(it.get("identifier", "")),
                "transcrito por el investigador, sin comprobar por script ("
                + (it.get("fuente_cifra") or "abstract/Elicit") + ")",
                it.get("evidencia_numerica"))
    for it in (_load_json(os.path.join(caso, "02b-deepresearch.json")) or {}).get("items", []):
        clave = coerce_identifier(it.get("identifier", "")) if it.get("identifier") else (it.get("url") or "")
        add(clave, f"guia / deep research: {it.get('url', '')}", it.get("extracto"))
    return corpus


def audit_figures(doc: str, corpus: dict) -> dict:
    """Recorre el documento linea a linea y busca cada cifra en las fuentes de
    las citas de esa misma linea.

    corpus: {cita: abstract} o {cita: [{lugar, texto}]} (cita = identificador o URL).
    """
    fuentes: dict[str, list[dict]] = {}
    for k, v in corpus.items():
        clave = k if k.lower().startswith("http") else coerce_identifier(k)
        fuentes[clave] = [{"lugar": "abstract", "texto": v or ""}] if isinstance(v, str) else list(v or [])
    urls = [k for k in fuentes if k.lower().startswith("http")]
    # Ignora el contenido en `backticks` (prompts visuales, code spans): no son afirmaciones.
    doc = re.sub(r"`[^`]*`", " ", doc)
    flagged: list[dict] = []
    marcadas: list[dict] = []
    coincidencias: list[dict] = []
    # Asocia cada cifra con las citas de su MISMA LÍNEA (párrafo o viñeta en markdown).
    for linea in (ln for ln in doc.split("\n") if ln.strip()):
        ids = extract_citations(linea) + [u for u in urls if u in linea]
        # Quita citas y URLs antes de buscar cifras, para no tomar sus dígitos por datos.
        limpia = _BRACKET_CITE_RE.sub(" ", linea)
        limpia = re.sub(r"https?://\S+|10\.\d{4,9}/\S+|PMID\s*:?\s*\d+|NCT\d{8}", " ", limpia, flags=re.IGNORECASE)
        for tok in (m.group(0) for m in _NUM_RE.finditer(limpia)):
            n = _norm_num(tok)
            if re.fullmatch(r"(19|20)\d{2}", n):  # años sueltos
                continue
            loc = []
            for i in ids:
                for src in fuentes.get(i, []):
                    frag = _find_number(n, src.get("texto", ""))
                    if frag:
                        loc.append({"cita": i, "lugar": src.get("lugar", ""), "fragmento": frag})
            if loc:
                coincidencias.append({"cifra": tok, "frase": linea.strip()[:200], "localizacion": loc})
            elif re.search(r"pendiente de cotejo", linea, re.IGNORECASE):
                marcadas.append({"cifra": tok, "frase": linea.strip()[:200]})
            else:
                flagged.append({
                    "cifra": tok,
                    "motivo": "sin cita en la linea" if not ids else "la cifra no aparece en las fuentes de sus citas",
                    "citas_en_frase": ids,
                    "frase": linea.strip()[:200],
                })
    return {
        "n_cifras_sin_respaldo": len(flagged),
        "veredicto": "OK" if not flagged else "REVISAR: cifras sin respaldo en las fuentes citadas",
        "aviso": "Una coincidencia numerica no prueba que la fuente respalde la afirmacion: "
                 "coteja cada fragmento de `coincidencias` con su frase.",
        "cifras_a_cotejar": flagged,
        "marcadas_pendiente_cotejo": marcadas,
        "coincidencias": coincidencias,
    }


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Ancla determinista de investigacion-agentica")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="Buscar candidatos deterministas")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--condition", default=None)
    p_search.add_argument("--days", type=int, default=3650, help="Ventana temporal PubMed (0 = sin limite)")
    p_search.add_argument("--with-abstracts", action="store_true",
                          help="Adjunta el abstract de cada candidato (grounding real)")
    p_search.add_argument("--pubmed-query", default=None,
                          help="Query booleana MeSH solo para PubMed (los motores semanticos usan --query)")
    p_search.add_argument("--from-build", default=None,
                          help="JSON de build-query: toma de ahi la query booleana (evita pasarla por la shell)")

    p_build = sub.add_parser("build-query", help="Construye query PubMed booleana desde PICO (MeSH validado)")
    p_build.add_argument("--pico", required=True, help="Ruta a JSON {concepts:[{label,mesh,tiab}]}")
    p_build.add_argument("--no-validate", action="store_true", help="No validar los MeSH contra NCBI")

    p_verify = sub.add_parser("verify", help="Verificar existencia + retractacion (comprobaciones sueltas)")
    p_verify.add_argument("identifiers", nargs="+")

    p_gate = sub.add_parser("gate", help="Puerta: verifica todos los identificadores citados en un expediente")
    p_gate.add_argument("--caso", required=True, help="Directorio del expediente")

    p_cites = sub.add_parser("check-citations", help="Comprueba que toda cita del documento esta en VALIDOS")
    p_cites.add_argument("--doc", required=True)
    p_cites.add_argument("--validos", required=True, help="Ruta a _validos.json")

    p_audit = sub.add_parser("audit-figures", help="Localiza cada cifra del documento en las fuentes de sus citas")
    p_audit.add_argument("--doc", required=True, help="Ruta del markdown a auditar")
    grp = p_audit.add_mutually_exclusive_group(required=True)
    grp.add_argument("--caso", help="Expediente: el corpus se construye de sus ficheros")
    grp.add_argument("--corpus", help="JSON {identificador: abstract} de respaldo")

    args = parser.parse_args()
    codigo = 0

    if args.cmd == "search":
        days = None if args.days == 0 else args.days
        pubmed_query = args.pubmed_query
        if args.from_build:
            pubmed_query = (_load_json(args.from_build) or {}).get("query") or pubmed_query
        result = search_all(args.query, condition=args.condition, days=days,
                            with_abstracts=args.with_abstracts, pubmed_query=pubmed_query)
        json.dump({"query": args.query, "pubmed_query": pubmed_query,
                   "fuentes": FUENTES_ESTADO, "n": len(result), "candidatos": result},
                  sys.stdout, ensure_ascii=False, indent=2)
    elif args.cmd == "build-query":
        pico = json.load(open(args.pico, encoding="utf-8"))
        concepts = pico.get("concepts", pico) if isinstance(pico, dict) else pico
        result = build_pubmed_query(concepts, validate=not args.no_validate)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    elif args.cmd == "verify":
        result = verify_identifiers(args.identifiers)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    elif args.cmd == "gate":
        resumen, codigo = run_gate(args.caso)
        json.dump(resumen, sys.stdout, ensure_ascii=False, indent=2)
    elif args.cmd == "check-citations":
        doc = open(args.doc, encoding="utf-8").read()
        result = check_citations(doc, json.load(open(args.validos, encoding="utf-8")))
        codigo = 0 if not result["fuera_de_validos"] else 2
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    elif args.cmd == "audit-figures":
        doc = open(args.doc, encoding="utf-8").read()
        corpus = build_corpus(args.caso) if args.caso else json.load(open(args.corpus, encoding="utf-8"))
        json.dump(audit_figures(doc, corpus), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    sys.exit(codigo)


if __name__ == "__main__":
    main()
