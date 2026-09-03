"""
Orquestador de investigacion-agentica -- Fase 1 & Fase 2 Completa
(Orquestador -> Investigador(es) -> Verificador 1 -> Analista -> Redactor -> Verificador 2 -> Zotero & Slides & Prompts)

Ejecutable tanto por GitHub Actions (modo Issue) como localmente mediante CLI:
  python orchestrator.py --pregunta "¿Es eficaz el PSMA-PET en recaída bioquímica?" --tipo "Duda clínica rápida"

Autenticacion por suscripcion (CLAUDE_CODE_OAUTH_TOKEN), sin coste por token.
Todo el proceso queda guardado en casos/<expediente>/ para poder reconstruir exactamente
que se busco y que se decidio en cada paso.
"""

import os
import re
import json
import time
import argparse
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

import requests

from zotero_exporter import export_zotero_bibliografia
from slide_generator import generate_advanced_presentation_artifacts

MODEL_ALIAS = "sonnet"
MAX_FACETAS_PARALELO = 4

HTTP_HEADERS = {
    "User-Agent": "investigacion-agentica/1.0 (https://github.com/investigacion-agentica; mailto:investigacion@agente.local)"
}


# ---------------------------------------------------------------------
# Utilidades de Resiliencia, Normalizacion y Parseo
# ---------------------------------------------------------------------

def safe_get(url: str, params: dict | None = None, timeout: int = 30, retries: int = 2) -> requests.Response | None:
    """Realiza peticiones GET con User-Agent polite, reintentos y tolerancia a fallos de red/rate-limiting."""
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp
            elif resp.status_code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            else:
                return resp
        except requests.RequestException:
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return None
    return None


def normalize_identifier(identifier: str) -> str:
    """Normaliza identificadores (PMID, NCT, DOI) para evitar duplicados y errores de formato."""
    if not identifier:
        return ""
    identifier = identifier.strip()
    identifier = re.sub(r"^https?://(?:dx\.)?doi\.org/", "DOI:", identifier, flags=re.IGNORECASE)

    if ":" not in identifier:
        return identifier

    kind, val = identifier.split(":", 1)
    kind = kind.strip().upper()
    val = val.strip()

    if kind == "DOI":
        return f"DOI:{val.lower()}"
    elif kind == "PMID":
        digits = re.sub(r"\D", "", val)
        return f"PMID:{digits if digits else val}"
    elif kind == "NCT":
        return f"NCT:{val.upper()}"

    return f"{kind}:{val}"


def extract_json(raw: str) -> dict | list:
    """Extrae y parsea JSON de forma robusta incluso si el LLM incluye texto alrededor o bloques de markdown."""
    if not raw:
        raise ValueError("Respuesta vacia al intentar extraer JSON.")
    raw_str = raw.strip()

    try:
        return json.loads(raw_str)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_str, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    match = re.search(r"(\{.*\}|\[.*\])", raw_str, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No se pudo extraer JSON valido de la respuesta: {raw_str[:200]}...")


def update_indice_md(issue_ref: str, fecha: str, pregunta: str, nivel: str, veredicto: str) -> None:
    """Actualiza automáticamente la tabla de INDICE.md con el nuevo expediente."""
    indice_path = "INDICE.md"
    if not os.path.exists(indice_path):
        return

    with open(indice_path, "r", encoding="utf-8") as f:
        content = f.read()

    pregunta_corta = (pregunta[:75] + "...") if len(pregunta) > 75 else pregunta
    pregunta_corta = pregunta_corta.replace("|", "-").replace("\n", " ")
    nueva_fila = f"| #{issue_ref} | {fecha} | {pregunta_corta} | {nivel} | {veredicto} |"

    if f"| #{issue_ref} |" in content:
        pattern = rf"\| #{re.escape(issue_ref)} \|.*$"
        content = re.sub(pattern, nueva_fila, content, flags=re.MULTILINE)
    else:
        content = content.strip() + "\n" + nueva_fila + "\n"

    with open(indice_path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------
# Parseo del Issue o CLI
# ---------------------------------------------------------------------

def parse_issue_body(body: str) -> dict:
    """Extrae los campos del formulario a partir del cuerpo markdown del Issue."""
    def extract(label: str) -> str:
        pattern = rf"### {re.escape(label)}\s*\n+(.*?)(?=\n### |\Z)"
        match = re.search(pattern, body, re.DOTALL)
        if not match:
            return ""
        text = match.group(1).strip()
        return "" if text.startswith("_No response_") else text

    return {
        "tipo": extract("Tipo de encargo"),
        "pregunta": extract("Pregunta, duda o título"),
        "contexto": extract("Contexto adicional (opcional)"),
        "plazo": extract("Plazo (opcional)"),
    }


# ---------------------------------------------------------------------
# Llamadas aisladas al CLI de Claude Code
# ---------------------------------------------------------------------

def call_claude_cli(
    system_prompt: str,
    user_content: str,
    max_turns: int = 3,
    allowed_mcp_tools: list[str] | None = None,
) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as sysfile:
        sysfile.write(system_prompt)
        sysfile_path = sysfile.name

    disallowed = "Bash,Read,Write,Edit,WebSearch,WebFetch"
    cmd = [
        "claude",
        "-p", user_content,
        "--system-prompt-file", sysfile_path,
        "--model", MODEL_ALIAS,
        "--output-format", "json",
        "--max-turns", str(max_turns),
    ]
    if allowed_mcp_tools:
        cmd += ["--allowedTools", ",".join(allowed_mcp_tools)]
        if os.path.exists("tooluniverse-mcp.json"):
            cmd += ["--mcp-config", "tooluniverse-mcp.json"]
    else:
        cmd += ["--disallowedTools", disallowed]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=420, check=True)
    finally:
        os.unlink(sysfile_path)
    try:
        return json.loads(result.stdout).get("result", result.stdout)
    except json.JSONDecodeError:
        return result.stdout


def read_prompt(name: str) -> str:
    with open(f"prompts/{name}", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------
# Busqueda deterministica
# ---------------------------------------------------------------------

def fetch_pubmed(query: str, days: int = 1825) -> list[dict]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    date_range = f"{start:%Y/%m/%d}:{end:%Y/%m/%d}[edat]"
    resp = safe_get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": f"{query} AND {date_range}",
                "retmode": "json", "retmax": 25, "sort": "relevance"},
        timeout=30,
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        esearch = resp.json()
    except Exception:
        return []
    ids = esearch.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    time.sleep(0.4)
    resp_sum = safe_get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
        timeout=30,
    )
    if not resp_sum or resp_sum.status_code != 200:
        return []
    try:
        esummary = resp_sum.json()
    except Exception:
        return []
    results = []
    for pmid in ids:
        doc = esummary.get("result", {}).get(pmid, {})
        if doc:
            results.append({
                "identifier": normalize_identifier(f"PMID:{pmid}"),
                "title": doc.get("title", ""),
                "date": doc.get("pubdate", ""),
                "source": "PubMed"
            })
    return results


def fetch_clinicaltrials(condition: str) -> list[dict]:
    resp = safe_get(
        "https://clinicaltrials.gov/api/v2/studies",
        params={"query.cond": condition, "pageSize": 15,
                "sort": "LastUpdatePostDate:desc"},
        timeout=30,
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    results = []
    for study in data.get("studies", []):
        ident = study.get("protocolSection", {}).get("identificationModule", {})
        status = study.get("protocolSection", {}).get("statusModule", {})
        nct_id = ident.get("nctId", "")
        if nct_id:
            results.append({
                "identifier": normalize_identifier(f"NCT:{nct_id}"),
                "title": ident.get("briefTitle", ""),
                "date": status.get("lastUpdatePostDateStruct", {}).get("date", ""),
                "source": "ClinicalTrials.gov",
            })
    return results


def fetch_europepmc(query: str) -> list[dict]:
    resp = safe_get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={"query": query, "format": "json", "pageSize": 20, "resultType": "core"},
        timeout=30,
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    out = []
    for item in data.get("resultList", {}).get("result", []):
        doi, pmid = item.get("doi"), item.get("pmid")
        ident = f"DOI:{doi}" if doi else (f"PMID:{pmid}" if pmid else None)
        if ident:
            out.append({
                "identifier": normalize_identifier(ident),
                "title": item.get("title", ""),
                "date": item.get("firstPublicationDate", ""),
                "source": "Europe PMC"
            })
    return out


def fetch_semantic_scholar(query: str) -> list[dict]:
    resp = safe_get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={"query": query, "limit": 20, "fields": "title,externalIds,year"},
        timeout=30,
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    out = []
    for item in data.get("data", []):
        ext = item.get("externalIds") or {}
        doi, pmid = ext.get("DOI"), ext.get("PubMed")
        ident = f"DOI:{doi}" if doi else (f"PMID:{pmid}" if pmid else None)
        if ident:
            out.append({
                "identifier": normalize_identifier(ident),
                "title": item.get("title", ""),
                "date": str(item.get("year", "")),
                "source": "Semantic Scholar"
            })
    return out


def fetch_openalex(query: str) -> list[dict]:
    resp = safe_get(
        "https://api.openalex.org/works",
        params={"search": query, "per_page": 20},
        timeout=30,
    )
    if not resp or resp.status_code != 200:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    out = []
    for item in data.get("results", []):
        doi_url = item.get("doi")
        if doi_url:
            out.append({
                "identifier": normalize_identifier(doi_url),
                "title": item.get("title", ""),
                "date": item.get("publication_date", ""),
                "source": "OpenAlex"
            })
    return out


def verify_identifier(identifier: str) -> bool:
    """Comprobacion determinista de existencia real contra APIs oficiales."""
    normalized = normalize_identifier(identifier)
    if not normalized or ":" not in normalized:
        return False
    kind, value = normalized.split(":", 1)
    try:
        if kind == "PMID":
            r = safe_get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "id": value, "retmode": "json"}, timeout=15,
            )
            if not r or r.status_code != 200:
                return False
            return value in r.json().get("result", {})
        if kind == "NCT":
            r = safe_get(f"https://clinicaltrials.gov/api/v2/studies/{value}", timeout=15)
            return r is not None and r.status_code == 200
        if kind == "DOI":
            r = safe_get(f"https://api.crossref.org/works/{value}", timeout=15)
            return r is not None and r.status_code == 200
    except Exception:
        return False
    return False


# ---------------------------------------------------------------------
# Generador de Paquete NotebookLM
# ---------------------------------------------------------------------

def generate_notebooklm_package(
    expediente_dir: str,
    encargo: dict,
    plan: dict,
    sintesis_facetas: list[dict],
    verificacion_ids: dict,
    informe_verificador: str,
) -> str:
    """Genera un archivo markdown consolidado listo para ser usado como fuente en NotebookLM o Claude Desktop."""
    doc = []
    doc.append(f"# Paquete de Investigación: {encargo.get('pregunta', '')}\n")
    doc.append(f"**Fecha**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    doc.append(f"**Nivel de Clasificación**: {plan.get('nivel', '')}")
    doc.append(f"**Tipo de Encargo**: {encargo.get('tipo', '')}\n")

    if encargo.get("contexto"):
        doc.append(f"## Contexto Inicial\n{encargo['contexto']}\n")

    doc.append("## Facetas Investigadas\n")
    for f in plan.get("facetas", []):
        doc.append(f"- **{f['id']}**: {f['descripcion']} (Consulta: `{f['query_pubmed']}`)")
    doc.append("")

    doc.append("## Síntesis de Evidencia por Faceta\n")
    for s in sintesis_facetas:
        doc.append(f"### Faceta: {s.get('faceta_id', '')}")
        doc.append(f"**Síntesis**: {s.get('sintesis', '')}\n")
        if s.get("vacios_o_contradicciones"):
            doc.append(f"**Vacíos / Contradicciones**: {s['vacios_o_contradicciones']}\n")
        doc.append("#### Estudios Seleccionados:")
        for item in s.get("items", []):
            ident = normalize_identifier(item.get("identifier", ""))
            ok = verificacion_ids.get(ident, False)
            estado = "✅ Verificado" if ok else "⚠️ No verificado"
            doc.append(f"- [{ident}] **{item.get('title', '')}** ({item.get('evidence_level', '')}) - {estado}")
            doc.append(f"  *Relevancia*: {item.get('relevancia', '')}")
        doc.append("")

    doc.append("## Informe de Verificación de Hechos (Verificador 1)\n")
    doc.append(informe_verificador)

    full_md = "\n".join(doc)
    filepath = f"{expediente_dir}/04-fuente-notebooklm.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_md)
    return filepath


# ---------------------------------------------------------------------
# Etapas (Fase 1 y Fase 2)
# ---------------------------------------------------------------------

HERRAMIENTAS_INVESTIGADOR = ["mcp__consensus", "mcp__scholar-gateway", "mcp__elicit"]
if os.path.exists("tooluniverse-mcp.json"):
    HERRAMIENTAS_INVESTIGADOR.append("mcp__tooluniverse")
HERRAMIENTAS_VERIFICADOR = ["mcp__scite"]


def orquestador_stage(encargo: dict) -> dict:
    raw = call_claude_cli(read_prompt("orquestador_system_prompt.md"),
                           json.dumps(encargo, ensure_ascii=False, indent=2))
    return extract_json(raw)


def investigador_stage(faceta: dict) -> dict:
    query = faceta["query_pubmed"]
    candidatos = fetch_pubmed(query)
    candidatos += fetch_europepmc(query)
    candidatos += fetch_semantic_scholar(query)
    candidatos += fetch_openalex(query)
    if faceta.get("condicion_ctgov"):
        candidatos += fetch_clinicaltrials(faceta["condicion_ctgov"])

    vistos = set()
    candidatos_unicos = []
    for c in candidatos:
        norm_id = normalize_identifier(c.get("identifier", ""))
        if norm_id and norm_id not in vistos:
            vistos.add(norm_id)
            c["identifier"] = norm_id
            candidatos_unicos.append(c)

    payload = {
        "faceta_id": faceta["id"],
        "descripcion": faceta["descripcion"],
        "brief": faceta["brief_investigador"],
        "candidatos": candidatos_unicos,
    }
    raw = call_claude_cli(
        read_prompt("investigador_system_prompt.md"),
        json.dumps(payload, ensure_ascii=False, indent=2),
        max_turns=8,
        allowed_mcp_tools=HERRAMIENTAS_INVESTIGADOR,
    )
    resultado = extract_json(raw)
    resultado["_candidatos_brutos"] = candidatos_unicos
    return resultado


def verificador1_stage(brief: str, sintesis_facetas: list[dict]) -> tuple[str, dict]:
    todos_ids = set()
    for s in sintesis_facetas:
        for item in s.get("items", []):
            if "identifier" in item:
                norm = normalize_identifier(item["identifier"])
                if norm:
                    todos_ids.add(norm)

    verificacion_ids = {ident: verify_identifier(ident) for ident in todos_ids}
    validos = [i for i, ok in verificacion_ids.items() if ok]

    payload = {
        "brief_verificador": brief,
        "sintesis_por_faceta": sintesis_facetas,
        "identificadores_verificados_como_reales": validos,
        "identificadores_que_no_resolvieron": [i for i, ok in verificacion_ids.items() if not ok],
    }
    informe = call_claude_cli(
        read_prompt("verificador1_system_prompt.md"),
        json.dumps(payload, ensure_ascii=False, indent=2),
        max_turns=6,
        allowed_mcp_tools=HERRAMIENTAS_VERIFICADOR,
    )
    return informe, verificacion_ids


def analista_stage(encargo: dict, informe_verificador1: str, sintesis_facetas: list[dict], validos: list[str]) -> dict:
    """Etapa 4 (Fase 2): Integra los hallazgos entre facetas y resuelve discrepancias."""
    payload = {
        "encargo": encargo,
        "informe_verificador1": informe_verificador1,
        "sintesis_facetas": sintesis_facetas,
        "estudios_verificados_reales": validos,
    }
    raw = call_claude_cli(
        read_prompt("analista_system_prompt.md"),
        json.dumps(payload, ensure_ascii=False, indent=2),
        max_turns=5,
    )
    return extract_json(raw)


def redactor_stage(encargo: dict, nivel: str, informe_analista: dict, validos: list[str]) -> str:
    """Etapa 5 (Fase 2): Produce el documento redactado adaptado al nivel."""
    payload = {
        "encargo": encargo,
        "nivel": nivel,
        "informe_analista": informe_analista,
        "estudios_verificados_reales": validos,
    }
    borrador = call_claude_cli(
        read_prompt("redactor_system_prompt.md"),
        json.dumps(payload, ensure_ascii=False, indent=2),
        max_turns=5,
    )
    return borrador


def verificador2_stage(borrador_redactor: str, validos: list[str]) -> str:
    """Etapa 6 (Fase 2): Verificador de fluidez, estilo y rigor clínico (Humanizador)."""
    payload = {
        "borrador_redactor": borrador_redactor,
        "estudios_verificados_reales": validos,
    }
    resultado_final = call_claude_cli(
        read_prompt("verificador2_system_prompt.md"),
        json.dumps(payload, ensure_ascii=False, indent=2),
        max_turns=3,
    )
    return resultado_final


# ---------------------------------------------------------------------
# Main CLI & Workflow
# ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Orquestador investigacion-agentica (Fase 1 + Fase 2)")
    parser.add_argument("--pregunta", type=str, help="Pregunta o título de la investigación")
    parser.add_argument("--tipo", type=str, default="No lo sé, que lo decida el sistema", help="Tipo de encargo")
    parser.add_argument("--contexto", type=str, default="", help="Contexto adicional")
    parser.add_argument("--plazo", type=str, default="", help="Plazo límite")
    args = parser.parse_args()

    if args.pregunta:
        encargo = {
            "tipo": args.tipo,
            "pregunta": args.pregunta,
            "contexto": args.contexto,
            "plazo": args.plazo,
        }
        issue_number = f"local-{int(time.time())}"
    else:
        issue_number = os.environ.get("ISSUE_NUMBER", "local-test")
        issue_body = os.environ.get("ISSUE_BODY", "")
        encargo = parse_issue_body(issue_body)

    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expediente = f"casos/{fecha}-issue-{issue_number}"
    os.makedirs(expediente, exist_ok=True)

    with open(f"{expediente}/00-encargo-original.md", "w", encoding="utf-8") as f:
        f.write(f"# Encargo original (Ref #{issue_number})\n\n")
        for k, v in encargo.items():
            f.write(f"**{k}**: {v}\n\n")

    # Etapa 1: Orquestador
    print("Etapa 1/6 -- Orquestador: clasificando y planificando...")
    plan = orquestador_stage(encargo)
    with open(f"{expediente}/01-clasificacion-orquestador.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"  Nivel: {plan['nivel']} -- {len(plan['facetas'])} faceta(s)")

    # Etapa 2: Investigador(es)
    print("Etapa 2/6 -- Investigador(es): buscando en paralelo...")
    os.makedirs(f"{expediente}/02-investigador", exist_ok=True)
    facetas = plan["facetas"][:MAX_FACETAS_PARALELO]
    sintesis_facetas = []
    with ThreadPoolExecutor(max_workers=MAX_FACETAS_PARALELO) as pool:
        futuros = {pool.submit(investigador_stage, f): f["id"] for f in facetas}
        for fut in as_completed(futuros):
            faceta_id = futuros[fut]
            resultado = fut.result()
            sintesis_facetas.append(resultado)
            with open(f"{expediente}/02-investigador/{faceta_id}.json", "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)

    # Etapa 3: Verificador 1
    print("Etapa 3/6 -- Verificador 1: verificacion de hechos...")
    informe_v1, verificacion_ids = verificador1_stage(plan["brief_verificador"], sintesis_facetas)
    with open(f"{expediente}/03-verificacion1.md", "w", encoding="utf-8") as f:
        f.write(informe_v1)
    with open(f"{expediente}/03-identificadores-verificados.json", "w", encoding="utf-8") as f:
        json.dump(verificacion_ids, f, ensure_ascii=False, indent=2)

    # Paquete NotebookLM
    print("Generando paquete consolidado para NotebookLM...")
    generate_notebooklm_package(expediente, encargo, plan, sintesis_facetas, verificacion_ids, informe_v1)

    validos = [i for i, ok in verificacion_ids.items() if ok]
    veredicto = "APTO" if "APTO PARA CONTINUAR" in informe_v1 else "REQUIERE ACLARACIÓN"

    # Etapa 4: Analista (Fase 2)
    print("Etapa 4/6 -- Analista: integración de evidencia cruzada...")
    informe_analista = analista_stage(encargo, informe_v1, sintesis_facetas, validos)
    with open(f"{expediente}/05-analista.json", "w", encoding="utf-8") as f:
        json.dump(informe_analista, f, ensure_ascii=False, indent=2)

    # Etapa 5: Redactor (Fase 2)
    print("Etapa 5/6 -- Redactor: elaboración del informe/borrador...")
    borrador = redactor_stage(encargo, plan["nivel"], informe_analista, validos)
    with open(f"{expediente}/06-redaccion-borrador.md", "w", encoding="utf-8") as f:
        f.write(borrador)

    # Etapa 6: Verificador 2 / Humanizador (Fase 2)
    print("Etapa 6/6 -- Verificador 2: revisión de estilo, rigor y fluidez...")
    resultado_final = verificador2_stage(borrador, validos)
    with open(f"{expediente}/07-resultado-final.md", "w", encoding="utf-8") as f:
        f.write(resultado_final)

    # Generar Artefactos Avanzados de Fase 2 (Zotero + Marp Presentación + Prompts Visuales)
    print("Generando artefactos avanzados de Fase 2 (Zotero, Diapositivas Marp y Prompts Visuales)...")
    try:
        export_zotero_bibliografia(expediente, validos, encargo.get("pregunta", "Expediente"))
        generate_advanced_presentation_artifacts(expediente, encargo, plan, resultado_final, validos)
    except Exception as e:
        print(f"  Warning: No se pudieron generar algunos artefactos avanzados: {e}")

    # Actualizar INDICE.md
    update_indice_md(issue_number, fecha, encargo["pregunta"], plan["nivel"], veredicto)

    print(f"✅ Proceso completo. Expediente finalizado en {expediente}/")


if __name__ == "__main__":
    main()
