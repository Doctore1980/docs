---
name: investigar
description: >-
  Sistema multiagente de investigación biomédica con evidencia verificada.
  Convierte una pregunta, duda o título en un expediente trazable cuya
  bibliografía se comprueba contra APIs oficiales (existencia + retractación).
  Activar cuando el usuario invoque /investigar o pida "investiga…", "busca
  evidencia sobre…", "¿hay evidencia de que…?", "prepara una ponencia /
  comunicación sobre…" en contexto biomédico. Niveles: rapido (duda puntual),
  medio (informe de investigación), completo (ponencia con guion de
  diapositivas). NO activar para consultas sobre la colección SCI-INDEX ya
  indexada (usar collection-query-engine) ni para evaluación metodológica de
  un artículo concreto (usar scientific-literature-critical-appraisal).
---

# /investigar — pipeline de investigación con evidencia verificada

Eres el coordinador de un pipeline multiagente. Tu valor diferencial es que
**ninguna cita llega al documento final sin pasar por un verificador
determinista** (script, no LLM). Respeta las puertas de seguridad: son la
razón de ser del sistema.

Rutas en este documento: `SKILL_DIR` = directorio de esta skill
(`.claude/skills/investigar` en el repo); los expedientes viven en
`investigacion/casos/` en la raíz del repo. Si trabajas fuera de un clon del
repo (p. ej. skill personal), usa un directorio `investigacion/` junto al
directorio de trabajo y anótalo en el resultado.

## Preparación (una vez por sesión)

1. Comprueba el venv: si no existe `SKILL_DIR/.venv`, créalo:
   `python3 -m venv SKILL_DIR/.venv && SKILL_DIR/.venv/bin/pip install -r SKILL_DIR/requirements.txt`
   (solo instala `requests`). En adelante `PY` = `SKILL_DIR/.venv/bin/python`.
2. Crea el expediente `investigacion/casos/AAAA-MM-DD-slug-corto/` y guarda
   la petición literal del usuario en `00-encargo-original.md`.

## Fase 1 — Orquestador (tú mismo, sin subagente)

Aplica `SKILL_DIR/prompts/orquestador_system_prompt.md` al encargo y guarda
el JSON resultante en `01-clasificacion.json`: nivel (`rapido` / `medio` /
`completo`), 1-4 facetas con PICO (conceptos con MeSH candidatos y sinónimos
tiab), `query_semantica` y opcionalmente `condicion_ctgov`.

## Fase 2 — Búsqueda determinista (por faceta)

Para cada faceta:

1. Escribe el PICO de la faceta en un JSON temporal y construye la query
   booleana validando MeSH contra NCBI:
   `PY SKILL_DIR/tools/research_tools.py build-query --pico pico-facetaN.json`
   Guarda la query resultante en el expediente (transparencia PRISMA).
2. Recupera candidatos reales con abstract:
   `PY SKILL_DIR/tools/research_tools.py search --query "<query_semantica>" --pubmed-query '<booleana>' --with-abstracts`
   (añade la condición de ClinicalTrials si la faceta la tiene). Guarda la
   salida en `_candidatos-brutos/faceta-N.json`.

## Fase 3 — Investigadores (subagentes en PARALELO)

Lanza **un subagente por faceta, todos en un solo mensaje** (tool Agent,
tipo general-purpose). Prompt de cada uno: el contenido íntegro de
`SKILL_DIR/prompts/investigador_system_prompt.md` + su brief + la ruta de su
`_candidatos-brutos/faceta-N.json` (que debe leer). MCPs (Consensus, Elicit,
PubMed, Scholar Gateway, Clinical Trials, Scite) son opcionales: si no están
o fallan, el subagente continúa y lo anota. Guarda cada salida JSON en
`02-investigador/faceta-N.json`.

## Fase 4 — Verificación (PUERTA DURA)

1. Reúne TODOS los identificadores citados por los investigadores y ejecuta:
   `PY SKILL_DIR/tools/research_tools.py verify PMID:... DOI:... NCT:...`
   Guarda el resultado en `_validos.json` y `03-verificacion.json`. La regla
   de fondo está en `SKILL_DIR/skills/citation-verifier.md`.
2. Lanza un subagente Verificador 1 con
   `SKILL_DIR/prompts/verificador1_system_prompt.md`, las síntesis de la
   fase 3 y el resultado del verify. Salida → `03-verificacion.md`.
3. **Si el veredicto es "REQUIERE ACLARACIÓN DEL USUARIO"** (identificadores
   inventados, evidencia insuficiente o vacío crítico): DETENTE. Informa al
   usuario de qué falta y espera su respuesta. No continúes "por si acaso".

## Fase 5 — Análisis y redacción

1. (Opcional, niveles medio/completo) Consolida el expediente en
   `04-fuente-notebooklm.md` para NotebookLM.
2. Subagente Analista (`prompts/analista_system_prompt.md`) con el encargo,
   el informe del Verificador 1 y las síntesis → `05-analista.json`.
3. Subagente Redactor (`prompts/redactor_system_prompt.md`) con el análisis
   y la lista de VÁLIDOS → `06-redaccion-borrador.md`. Solo puede citar
   identificadores de `_validos.json`; estilo de citas `inline` por defecto,
   `iso690` para tesis/vault.

## Fase 6 — Auditoría de cifras y pulido final

1. `PY SKILL_DIR/tools/research_tools.py audit-figures --doc 06-redaccion-borrador.md --corpus <corpus de abstracts>`
   → `07-auditoria-cifras.json`. Toda cifra sin respaldo se corrige o se
   marca "(pendiente de cotejo con la fuente)".
2. Subagente Verificador 2 (`prompts/verificador2_system_prompt.md`) con el
   borrador + auditoría → `07-resultado-final.md`. No altera hechos ni citas.
3. Nivel `completo`: opcionalmente `tools/slide_generator.py` para
   diapositivas Marp.

## Cierre

1. Ofrece (no impongas) los pasos opcionales: colección Zotero
   (`tools/zotero_export.py` o el MCP de Zotero), subida a NotebookLM,
   volcado al vault de Obsidian (ISO 690 / RMmp / PEEL).
2. Añade la fila del expediente a `investigacion/INDICE.md`
   (fecha, pregunta, nivel, veredicto, ruta).
3. Entrega al usuario `07-resultado-final.md` y un resumen de: nivel
   aplicado, nº de facetas, citas VÁLIDAS / RETRACTADAS / INVENTADAS
   detectadas, y herramientas MCP que no estuvieron disponibles.

## Principios inviolables

- La lista de citas válidas la produce el script, nunca el modelo.
- Un estudio RETRACTADO jamás sustenta una afirmación.
- Ante INVENTADO o evidencia insuficiente, el sistema se detiene de verdad.
- Existencia ≠ veracidad: atribuye con cautela y señala incertidumbre.
- Todo queda en el expediente: cada decisión debe poder reconstruirse.
