"""
Exportador de Bibliografía para Zotero / Mendeley / EndNote -- Fase 2 Avanzada
Convierte identificadores verificados (PMID, DOI, NCT) en formatos estándares RIS y CSL-JSON.
"""

import os
import json
import re
import time
import requests

# Reintentos y pausa ante 429 de NCBI/Crossref: sin ellos, un lote de PMIDs
# seguidos acababa con registros "METADATOS NO RECUPERADOS" que si existen.
from research_tools import safe_get


def _ris_author(name: str) -> str:
    """PubMed da 'Apellido Iniciales'; RIS espera 'Apellido, Iniciales'."""
    if "," in name:
        return name
    parts = name.rsplit(" ", 1)
    return f"{parts[0]}, {parts[1]}" if len(parts) == 2 and parts[1].isupper() else name


def _doi_org_csl(doi: str) -> dict | None:
    """Metadatos CSL-JSON por negociacion de contenido en doi.org: cubre los DOI
    registrados fuera de Crossref (DataCite, mEDRA, revistas regionales)."""
    r = safe_get(f"https://doi.org/{doi}", timeout=20,
                 headers={"Accept": "application/vnd.citationstyles.csl+json"})
    if not r or r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


def fetch_item_metadata(identifier: str) -> dict:
    """Recupera metadatos básicos de una cita a partir de su identificador normalizado.

    Si la API no responde, el registro se marca complete=False y su título deja
    claro que faltan metadatos — nunca se rellena con un título inventado.
    """
    kind, val = identifier.split(":", 1) if ":" in identifier else ("UNKNOWN", identifier)
    meta = {
        "identifier": identifier,
        "type": "journal",
        "title": f"[METADATOS NO RECUPERADOS — cotejar manualmente] {identifier}",
        "authors": [],
        "year": "",
        "journal": "",
        "doi": val if kind == "DOI" else "",
        "pmid": val if kind == "PMID" else "",
        "nct": val if kind == "NCT" else "",
        "complete": False,
    }

    try:
        if kind == "PMID":
            r = safe_get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "id": val, "retmode": "json"},
                timeout=15,
            )
            if r is not None and r.status_code == 200:
                doc = r.json().get("result", {}).get(val, {})
                if doc.get("title") and "error" not in doc:
                    meta["title"] = doc["title"]
                    meta["complete"] = True
                meta["journal"] = doc.get("source", "")
                pubdate = doc.get("pubdate", "")
                meta["year"] = pubdate.split()[0] if pubdate else ""
                authors = doc.get("authors", [])
                meta["authors"] = [_ris_author(a.get("name", "")) for a in authors if isinstance(a, dict)]
                for articleid in doc.get("articleids", []):
                    if articleid.get("idtype") == "doi":
                        meta["doi"] = articleid.get("value", "")

        elif kind == "DOI":
            r = safe_get(f"https://api.crossref.org/works/{val}", timeout=15)
            item = r.json().get("message", {}) if (r is not None and r.status_code == 200) else _doi_org_csl(val)
            if item:
                # Crossref da listas; el CSL-JSON de doi.org puede dar cadenas.
                title = item.get("title", [])
                title = title[0] if isinstance(title, list) and title else title
                if title:
                    meta["title"] = title
                    meta["complete"] = True
                container = item.get("container-title", [])
                meta["journal"] = (container[0] if container else "") if isinstance(container, list) else container
                issued = item.get("issued", {}).get("date-parts", [[]])
                if issued and issued[0]:
                    meta["year"] = str(issued[0][0])
                authors = item.get("author", [])
                meta["authors"] = [f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in authors]

        elif kind == "NCT":
            r = safe_get(f"https://clinicaltrials.gov/api/v2/studies/{val}", timeout=15)
            if r is not None and r.status_code == 200:
                study = r.json()
                ident = study.get("protocolSection", {}).get("identificationModule", {})
                status = study.get("protocolSection", {}).get("statusModule", {})
                if ident.get("briefTitle"):
                    meta["title"] = ident["briefTitle"]
                    meta["complete"] = True
                meta["type"] = "clinical_trial"
                date_str = status.get("lastUpdatePostDateStruct", {}).get("date", "")
                meta["year"] = date_str.split("-")[0] if date_str else ""
    except Exception:
        pass

    return meta


def generate_ris(items: list[dict]) -> str:
    """Genera archivo formato RIS compatible con Zotero, Mendeley y EndNote."""
    ris_lines = []
    for item in items:
        ris_lines.append("TY  - JOUR")
        ris_lines.append(f"TI  - {item.get('title', '')}")
        for author in item.get("authors", []):
            ris_lines.append(f"AU  - {author}")
        if item.get("journal"):
            ris_lines.append(f"JO  - {item['journal']}")
        if item.get("year"):
            ris_lines.append(f"PY  - {item['year']}")
        if item.get("doi"):
            ris_lines.append(f"DO  - {item['doi']}")
        if item.get("pmid"):
            ris_lines.append(f"AN  - PMID:{item['pmid']}")
        if item.get("nct"):
            ris_lines.append(f"C1  - NCT:{item['nct']}")
        if not item.get("complete", True):
            ris_lines.append("N1  - METADATOS INCOMPLETOS: la API no respondió; cotejar manualmente antes de citar")
        ris_lines.append("ER  - \n")

    return "\n".join(ris_lines)


def generate_csl_json(items: list[dict]) -> str:
    """Genera formato CSL-JSON para herramientas bibliográficas."""
    csl = []
    for i, item in enumerate(items):
        csl_item = {
            "id": f"item-{i+1}",
            "type": "article-journal" if item.get("type") == "journal" else "entry",
            "title": item.get("title", ""),
            "DOI": item.get("doi", ""),
            "PMID": item.get("pmid", ""),
            "container-title": item.get("journal", ""),
        }
        if not item.get("complete", True):
            csl_item["note"] = "METADATOS INCOMPLETOS: la API no respondió; cotejar manualmente antes de citar"
        if item.get("year"):
            csl_item["issued"] = {"date-parts": [[int(item["year"])]]} if item["year"].isdigit() else {"raw": item["year"]}
        csl.append(csl_item)
    return json.dumps(csl, ensure_ascii=False, indent=2)


def sync_to_zotero_api(items: list[dict], collection_name: str) -> bool:
    """Sync opcional con la API Web de Zotero si se proveen las variables de entorno ZOTERO_API_KEY y ZOTERO_USER_ID."""
    api_key = os.environ.get("ZOTERO_API_KEY")
    user_id = os.environ.get("ZOTERO_USER_ID")

    if not api_key or not user_id:
        return False

    try:
        headers = {"Zotero-API-Key": api_key, "Content-Type": "application/json"}
        # 1. Crear colección
        col_url = f"https://api.zotero.org/users/{user_id}/collections"
        col_resp = requests.post(col_url, headers=headers, json=[{"name": collection_name}], timeout=15)
        if col_resp.status_code not in (200, 201):
            return False
        col_key = col_resp.json().get("success", {}).get("0", "")

        # 2. Subir items a la colección
        items_url = f"https://api.zotero.org/users/{user_id}/items"
        zotero_payload = []
        # Los registros incompletos no se suben a Zotero: mejor un hueco visible
        # en el .ris local que un item con título placeholder en la biblioteca.
        for item in items:
            if not item.get("complete", True):
                continue
            zotero_payload.append({
                "itemType": "journalArticle",
                "title": item.get("title", ""),
                "publicationTitle": item.get("journal", ""),
                "DOI": item.get("doi", ""),
                "extra": f"PMID: {item.get('pmid', '')}" if item.get('pmid') else "",
                "collections": [col_key] if col_key else [],
            })
        # La API de Zotero admite como maximo 50 items por peticion.
        for i in range(0, len(zotero_payload), 50):
            resp = requests.post(items_url, headers=headers, json=zotero_payload[i:i + 50], timeout=30)
            if resp.status_code not in (200, 201):
                return False
        return True
    except Exception:
        return False


def export_zotero_bibliografia(expediente_dir: str, valid_identifiers: list[str], expediente_title: str = "Expediente") -> tuple[str, str]:
    """Genera los archivos .ris y .json dentro del expediente."""
    items = []
    for ident in valid_identifiers:
        items.append(fetch_item_metadata(ident))
        time.sleep(0.34)  # NCBI admite ~3 peticiones/s sin clave

    ris_content = generate_ris(items)
    ris_path = f"{expediente_dir}/08-bibliografia-zotero.ris"
    with open(ris_path, "w", encoding="utf-8") as f:
        f.write(ris_content)

    csl_content = generate_csl_json(items)
    csl_path = f"{expediente_dir}/08-bibliografia-zotero.json"
    with open(csl_path, "w", encoding="utf-8") as f:
        f.write(csl_content)

    # Intento de Sync con Zotero Web API si hay credenciales
    sync_to_zotero_api(items, collection_name=f"investigacion-agentica: {expediente_title}")

    return ris_path, csl_path
