"""
research_tools.py -- Ancla determinista de investigacion-agentica.

Este modulo NO usa ningun LLM. Es la fuente de verdad del sistema: hace las
busquedas reproducibles y comprueba, contra APIs oficiales, que cada
identificador citado (PMID / NCT / DOI) existe de verdad y si esta retractado.

Uso como CLI (lo invoca la skill /investigar):

  # Buscar candidatos para una faceta (imprime JSON a stdout)
  python tools/research_tools.py search --query "PSMA PET biochemical recurrence prostate cancer" \
      --condition "Prostate Cancer" --days 3650

  # Verificar existencia + retractacion de una lista de identificadores
  python tools/research_tools.py verify PMID:29565221 DOI:10.1056/nejmoa1910038 NCT:NCT02043678

La salida siempre es JSON en stdout, para que la skill la lea sin ambiguedad.
"""

from __future__ import annotations

import re
import sys
import json
import time
import argparse
from datetime import datetime, timedelta, timezone

import requests

HTTP_HEADERS = {
    "User-Agent": "investigacion-agentica/2.0 (research assistant; mailto:investigacion@agente.local)"
}


# ---------------------------------------------------------------------
# Red resiliente
# ---------------------------------------------------------------------

def safe_get(url: str, params: dict | None = None, timeout: int = 30, retries: int = 2) -> requests.Response | None:
    """GET con User-Agent polite, reintentos y tolerancia a rate-limiting."""
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=timeout)
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
        return []
    try:
        ids = resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []
    if not ids:
        return []
    time.sleep(0.4)
    resp_sum = safe_get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
    )
    if not resp_sum or resp_sum.status_code != 200:
        return []
    try:
        result = resp_sum.json().get("result", {})
    except Exception:
        return []
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
    return out


def fetch_clinicaltrials(condition: str, page_size: int = 15) -> list[dict]:
    resp = safe_get(
        "https://clinicaltrials.gov/api/v2/studies",
        params={"query.cond": condition, "pageSize": page_size, "sort": "LastUpdatePostDate:desc"},
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        studies = resp.json().get("studies", [])
    except Exception:
        return []
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
    return out


def fetch_europepmc(query: str, page_size: int = 20) -> list[dict]:
    resp = safe_get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={"query": query, "format": "json", "pageSize": page_size, "resultType": "core"},
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        results = resp.json().get("resultList", {}).get("result", [])
    except Exception:
        return []
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
                "abstract": (item.get("abstractText") or "")[:1800],
                "source": "Europe PMC",
            })
    return out


def fetch_semantic_scholar(query: str, limit: int = 20) -> list[dict]:
    resp = safe_get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": query, "limit": limit, "fields": "title,externalIds,year,venue,abstract"},
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        data = resp.json().get("data", [])
    except Exception:
        return []
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
                "abstract": (item.get("abstract") or "")[:1800],
                "source": "Semantic Scholar",
            })
    return out


def fetch_openalex(query: str, per_page: int = 20) -> list[dict]:
    resp = safe_get(
        "https://api.openalex.org/works",
        params={"search": query, "per_page": per_page},
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        results = resp.json().get("results", [])
    except Exception:
        return []
    out = []
    for item in results:
        doi_url = item.get("doi")
        if doi_url:
            out.append({
                "identifier": normalize_identifier(doi_url),
                "title": item.get("title", ""),
                "date": item.get("publication_date", ""),
                "abstract": _openalex_abstract(item.get("abstract_inverted_index"))[:1800],
                "source": "OpenAlex",
            })
    return out


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
            text = " ".join(re.sub(r"<[^>]+>", "", p) for p in parts).strip()
            text = re.sub(r"\s+", " ", text)
            if text:
                out[pmid] = text[:1800]
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
# ---------------------------------------------------------------------

def _pubmed_retracted_set(pmids: list[str]) -> set[str]:
    """Devuelve el subconjunto de PMIDs marcados como 'Retracted Publication' en PubMed."""
    if not pmids:
        return set()
    resp = safe_get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={"db": "pubmed", "id": ",".join(pmids), "rettype": "xml", "retmode": "xml"},
    )
    if not resp or resp.status_code != 200:
        return set()
    xml = resp.text
    retracted: set[str] = set()
    # Cada <PubmedArticle> contiene su PMID y su PublicationTypeList.
    for block in re.split(r"<PubmedArticle>", xml)[1:]:
        m = re.search(r"<PMID[^>]*>(\d+)</PMID>", block)
        if not m:
            continue
        pmid = m.group(1)
        if re.search(r"Retracted Publication", block, re.IGNORECASE):
            retracted.add(pmid)
    return retracted


def verify_identifiers(identifiers: list[str]) -> dict[str, dict]:
    """Comprueba existencia (y retractacion en PMIDs) de cada identificador.

    Devuelve {identificador_normalizado: {"exists": bool, "retracted": bool|None,
    "checked_against": str}}. retracted=None => no se pudo evaluar (p.ej. DOI/NCT
    sin PMID; usar Scite MCP para esos casos).
    """
    norm = [normalize_identifier(i) for i in identifiers if i]
    norm = list(dict.fromkeys([n for n in norm if n and ":" in n]))  # dedup preservando orden

    pmids = [n.split(":", 1)[1] for n in norm if n.startswith("PMID:")]
    retracted_pmids = _pubmed_retracted_set(pmids)

    out: dict[str, dict] = {}
    for ident in norm:
        kind, value = ident.split(":", 1)
        exists = False
        retracted: bool | None = None
        checked = ""
        try:
            if kind == "PMID":
                checked = "PubMed E-utilities"
                r = safe_get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                    params={"db": "pubmed", "id": value, "retmode": "json"}, timeout=15,
                )
                # PubMed devuelve una entrada con campo "error" para PMIDs inexistentes:
                # la presencia de la clave NO basta, hay que exigir que no tenga error.
                doc = r.json().get("result", {}).get(value, {}) if (r and r.status_code == 200) else {}
                exists = bool(doc) and "error" not in doc
                retracted = value in retracted_pmids if exists else None
            elif kind == "NCT":
                checked = "ClinicalTrials.gov API v2"
                r = safe_get(f"https://clinicaltrials.gov/api/v2/studies/{value}", timeout=15)
                exists = bool(r and r.status_code == 200)
            elif kind == "DOI":
                checked = "Crossref"
                r = safe_get(f"https://api.crossref.org/works/{value}", timeout=15)
                exists = bool(r and r.status_code == 200)
        except Exception:
            exists = False
        out[ident] = {"exists": exists, "retracted": retracted, "checked_against": checked}
        time.sleep(0.1)
    return out


# ---------------------------------------------------------------------
# Auditoria de cifras: toda cifra cuantitativa debe estar respaldada por
# el abstract de alguna de las citas de su misma frase.
# ---------------------------------------------------------------------

# Cifras que importan clínicamente: porcentajes, decimales tipo 0.xx, e enteros
# de >=3 dígitos (tamaños muestrales, estadísticos). Los enteros de 1-2 dígitos
# suelen ser estructura (nº de diapositiva, ratios 16:9) y se ignoran.
_NUM_RE = re.compile(r"(?<![\w.])\d{1,3}(?:[.,]\d+)?\s?%|(?<![\w.])0[.,]\d+|(?<![\w])\d{3,}(?![\w.])")


def _norm_num(tok: str) -> str:
    return tok.replace(" ", "").replace(",", ".").rstrip("%")


def audit_figures(doc: str, corpus: dict[str, str]) -> dict:
    """Recorre el documento frase a frase y marca las cifras cuantitativas que NO
    aparecen en el abstract de ninguna de las citas de esa misma frase.

    corpus: {identificador_normalizado: abstract}. Devuelve las cifras a cotejar a
    mano. Es un guardarrail determinista contra atribuir números no leídos.
    """
    corpus_norm = {normalize_identifier(k): (v or "") for k, v in corpus.items()}
    # Ignora el contenido en `backticks` (prompts visuales, code spans): no son afirmaciones.
    doc = re.sub(r"`[^`]*`", " ", doc)
    # Asocia cada cifra con las citas de su MISMA LÍNEA. En markdown, cada párrafo o
    # viñeta es una línea, y la cita suele acompañar a la cifra ahí mismo; esto evita
    # que las abreviaturas con punto ("sens.", "espec.") separen la cifra de su cita.
    frases = [ln for ln in doc.split("\n") if ln.strip()]
    flagged: list[dict] = []
    for frase in frases:
        ids = [normalize_identifier(m) for m in re.findall(r"\[(PMID:\d+|DOI:[^\]]+|NCT:[^\]]+)\]", frase)]
        # Elimina los bloques de cita [PMID:..]/[DOI:..]/[NCT:..] antes de buscar cifras,
        # para no confundir los dígitos del propio identificador con un dato.
        frase_limpia = re.sub(r"\[(?:PMID:\d+|DOI:[^\]]+|NCT:[^\]]+)\]", " ", frase)
        nums = [m.group(0) for m in _NUM_RE.finditer(frase_limpia)]
        if not nums:
            continue
        # abstracts disponibles para las citas de esta frase
        respaldo = " ".join(corpus_norm.get(i, "") for i in ids)
        for tok in nums:
            n = _norm_num(tok)
            # ignora años sueltos y números triviales de estructura
            if re.fullmatch(r"(19|20)\d{2}", n):
                continue
            encontrado = n in respaldo.replace(",", ".") or tok in respaldo
            if not encontrado:
                flagged.append({
                    "cifra": tok,
                    "citas_en_frase": ids or ["(sin cita en la frase)"],
                    "respaldo_en_abstract": encontrado,
                    "frase": frase.strip()[:200],
                })
    return {
        "n_cifras_sin_respaldo": len(flagged),
        "veredicto": "OK" if not flagged else "REVISAR: cifras sin respaldo en los abstracts citados",
        "cifras_a_cotejar": flagged,
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

    p_build = sub.add_parser("build-query", help="Construye query PubMed booleana desde PICO (MeSH validado)")
    p_build.add_argument("--pico", required=True, help="Ruta a JSON {concepts:[{label,mesh,tiab}]}")
    p_build.add_argument("--no-validate", action="store_true", help="No validar los MeSH contra NCBI")

    p_verify = sub.add_parser("verify", help="Verificar existencia + retractacion")
    p_verify.add_argument("identifiers", nargs="+")

    p_audit = sub.add_parser("audit-figures", help="Marca cifras del documento no respaldadas por los abstracts")
    p_audit.add_argument("--doc", required=True, help="Ruta del markdown a auditar")
    p_audit.add_argument("--corpus", required=True, help="JSON {identificador: abstract} de respaldo")

    args = parser.parse_args()

    if args.cmd == "search":
        days = None if args.days == 0 else args.days
        result = search_all(args.query, condition=args.condition, days=days,
                            with_abstracts=args.with_abstracts, pubmed_query=args.pubmed_query)
        json.dump({"query": args.query, "pubmed_query": args.pubmed_query,
                   "n": len(result), "candidatos": result},
                  sys.stdout, ensure_ascii=False, indent=2)
    elif args.cmd == "build-query":
        pico = json.load(open(args.pico, encoding="utf-8"))
        concepts = pico.get("concepts", pico) if isinstance(pico, dict) else pico
        result = build_pubmed_query(concepts, validate=not args.no_validate)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    elif args.cmd == "verify":
        result = verify_identifiers(args.identifiers)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    elif args.cmd == "audit-figures":
        doc = open(args.doc, encoding="utf-8").read()
        corpus = json.load(open(args.corpus, encoding="utf-8"))
        json.dump(audit_figures(doc, corpus), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
