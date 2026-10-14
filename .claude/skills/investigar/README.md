# investigacion-agentica

Sistema multiagente de investigación con **evidencia verificada**, orquestado de forma
nativa desde Claude Code. Convierte una pregunta, duda o título en un **expediente
trazable** cuya bibliografía ha sido comprobada, contra APIs oficiales, para garantizar
que **existe de verdad y no está retractada**.

Sirve para cualquier tema; el caso más frecuente es urología / uro-oncología e IA aplicada
a salud, pero no está limitado a eso.

## Cómo se usa (desde Claude Code)

Escribe en el chat:

```
/investigar ¿Hay evidencia de que el PSMA-PET mejore la detección de recaída bioquímica en cáncer de próstata?
```

o simplemente "investiga…", "busca evidencia sobre…", "prepara una ponencia sobre…".
No hace falta entrar en GitHub ni lanzar nada por terminal: el `SKILL.md` de esta
carpeta registra el comando y coordina todo el proceso. La skill se activa
automáticamente en cualquier sesión de Claude Code abierta sobre este repositorio;
para tenerla en todas tus sesiones, súbela también a tu biblioteca de skills de
claude.ai (Ajustes → Capacidades → Skills) o cópiala a `~/.claude/skills/investigar/`.

## Qué hace, paso a paso

El detalle operativo está en `SKILL.md`; aquí, el resumen:

1. **Clasificación** — nivel (`rapido` / `medio` / `completo`), tipo de pregunta y 1-4 facetas.
2. **Búsqueda reproducible** (script) — query booleana con MeSH validado contra NCBI y
   candidatos con abstract de PubMed, Europe PMC, Semantic Scholar, OpenAlex y
   ClinicalTrials.gov.
3. **Investigadores** (subagentes en paralelo) — seleccionan y sintetizan; los MCP
   (Consensus, Elicit, Scite…) son complementos opcionales. En nivel `completo`, un
   subagente adicional busca guías y literatura gris.
4. **Puerta de verificación** (script `gate`) — comprueba existencia y retractación de
   cada identificador citado y escribe `_validos.json`, la única lista citable. Si algo
   no existe o no se pudo comprobar, **el proceso se detiene y te avisa**. Después, el
   Verificador 1 revisa coherencia y suficiencia de la evidencia.
5. **Analista** — integra los hallazgos entre facetas.
6. **Redactor** — redacta según el nivel citando solo identificadores VÁLIDOS.
7. **Pulido y puertas finales** — auditoría de cifras, Verificador 2 y, sobre el texto
   final, `check-citations` y una segunda auditoría de cifras.

Al final, opcionalmente: colección en **Zotero**, fuente para **NotebookLM**, nota en el
vault de **Obsidian** o indexado en **SCI-INDEX**.

## El ancla determinista (lo que da confianza)

`tools/research_tools.py` no usa ningún LLM. Es la fuente de verdad:

```bash
PY=./.venv/bin/python   # o python3 si ya tiene requests

# Query PubMed booleana desde los conceptos, validando los MeSH contra NCBI
$PY tools/research_tools.py build-query --pico faceta-1.json > faceta-1-query.json

# Candidatos con abstract (booleana a PubMed, texto libre a los motores semánticos)
$PY tools/research_tools.py search --query "PSMA PET recurrence" --from-build faceta-1-query.json --with-abstracts

# Puerta: verifica todo lo citado en el expediente y escribe _validos.json
$PY tools/research_tools.py gate --caso investigacion/casos/AAAA-MM-DD-slug

# Citas del documento contra VALIDOS, y auditoría de cifras contra las fuentes del expediente
$PY tools/research_tools.py check-citations --doc 07-resultado-final.md --validos _validos.json
$PY tools/research_tools.py audit-figures --doc 07-resultado-final.md --caso investigacion/casos/AAAA-MM-DD-slug

# Comprobación suelta
$PY tools/research_tools.py verify PMID:29137830 DOI:10.1056/NEJMoa1910038 NCT:NCT03036150
```

Cada identificador recibe un estado:

| Estado | Significado | ¿Citable? |
|---|---|---|
| `VALIDO` | Existe y no consta retractado en PubMed ni en Crossref | Sí |
| `RETRACTADO` | Existe pero está retractado | No |
| `NO_ENCONTRADO` | La fuente oficial responde que no existe (señal de invención) | No; `gate` se detiene |
| `MAL_FORMADO` | No tiene forma de PMID, NCT ni DOI | No; `gate` se detiene |
| `INCONCLUSO` | La API no respondió, o la retractación no es evaluable (DOI fuera de Crossref) | No; se reintenta |

Un fallo de la API (por ejemplo, un 429 de NCBI) da `INCONCLUSO`, nunca `NO_ENCONTRADO`,
y una consulta de retractación fallida nunca deja pasar un artículo como `VALIDO`. Los DOI
que no están en Crossref se confirman contra doi.org. El campo `fuentes` de `search` dice
qué fuentes respondieron.

## Instalación (una vez, la skill la hace sola si falta)

```bash
cd .claude/skills/investigar
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Claves opcionales (gratuitas) para las fuentes semánticas. Sin ellas, OpenAlex y
Semantic Scholar usan un cupo compartido que a menudo está agotado (HTTP 429); la
búsqueda sigue con PubMed, Europe PMC y ClinicalTrials.gov y lo indica en el campo
`fuentes` de la salida:

```bash
export OPENALEX_API_KEY=...            # https://help.openalex.org/api/authentication/
export SEMANTIC_SCHOLAR_API_KEY=...    # https://www.semanticscholar.org/product/api#api-key-form
```

## Pruebas

Pruebas sin red (las APIs se simulan) de la verificación, la puerta, la búsqueda y la
auditoría de cifras. Cada una fija un fallo que ya ocurrió en un expediente real:

```bash
cd .claude/skills/investigar
python3 -m unittest discover -s tests -v
```

## Estructura

```
.claude/skills/investigar/    # la skill
├── SKILL.md                  # registra /investigar y fija etapas, comandos y puertas
├── tools/
│   ├── research_tools.py     # ancla determinista: búsqueda, verificación, puertas, cifras
│   ├── zotero_export.py      # export RIS / CSL-JSON (+ sync opcional a Zotero web API)
│   └── slide_generator.py    # (opcional) diapositivas Marp para nivel "completo"
├── prompts/                  # rúbricas de cada rol
├── tests/                    # pruebas sin red de tools/
└── .venv/                    # (local, no versionado)

investigacion/                # en la raíz del repo (excluido del sitio en .mintignore)
├── casos/                    # expedientes generados
├── INDICE.md                 # registro de expedientes
└── legacy/                   # enfoque anterior (subprocess + GitHub Actions), como referencia
```

## Principios

- Ninguna cita sin verificar; la lista de válidos la produce un script, no el modelo.
- Los estudios retractados nunca sustentan una afirmación.
- La puerta de seguridad frena de verdad ante invención o evidencia insuficiente.
- Verificar existencia ≠ verificar veracidad: se atribuye con cautela y se señala la incertidumbre.
- Todo queda guardado en el expediente para poder reconstruir cada decisión.

## Nota sobre `legacy/`

La versión original disparaba el pipeline por GitHub Actions y llamaba a `claude` por
subprocess. Se ha sustituido por orquestación nativa (subagentes reales + tus MCPs), que
elimina la fragilidad del CLI y aprovecha tus conectores autenticados. El código antiguo se
conserva en `investigacion/legacy/` solo como referencia histórica: ya no se ejecuta con los
prompts y herramientas actuales (módulos renombrados y formato PICO del Orquestador).
