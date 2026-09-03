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
No hace falta entrar en GitHub ni lanzar nada por terminal: la skill `investigar`
(`~/.claude/skills/investigar/SKILL.md`) coordina todo el proceso.

## Qué hace, paso a paso

1. **Orquestador** — clasifica el nivel (`rapido` / `medio` / `completo`) y descompone en 1-4 facetas.
2. **Investigadores** (subagentes en paralelo) — buscan en fuentes deterministas (PubMed,
   ClinicalTrials.gov, Europe PMC, Semantic Scholar, OpenAlex) y enriquecen con tus MCPs
   (Consensus, Elicit, PubMed, Clinical Trials) cuando aportan.
3. **Verificador 1** (ancla determinista + puerta real) — comprueba existencia y
   retractación de cada cita. Si algo está **inventado** o la evidencia es **insuficiente**,
   **el sistema se detiene y te avisa**. No sigue a ciegas.
4. **Paquete NotebookLM** — consolida el expediente en un fichero listo para NotebookLM.
5. **Analista** — integra los hallazgos entre facetas y clasifica por certidumbre.
6. **Redactor** — redacta adaptado al nivel (citas `inline` o `ISO 690` para tesis/vault).
7. **Verificador 2 / Humanizador** — pule estilo y rigor clínico sin tocar los hechos.

Al final, opcionalmente: crea una **colección en Zotero**, sube la fuente a **NotebookLM**,
o vuelca la nota al **vault de Obsidian** (respetando ISO 690 / RMmp / PEEL).

## El ancla determinista (lo que da confianza)

`tools/research_tools.py` no usa ningún LLM. Es la fuente de verdad:

```bash
# Construir query PubMed booleana desde PICO, validando los MeSH contra NCBI
./.venv/bin/python tools/research_tools.py build-query --pico pico.json

# Buscar candidatos reales, con abstract, en carril doble (booleana a PubMed + texto libre a semánticos)
./.venv/bin/python tools/research_tools.py search --query "PSMA PET recurrence" \
  --pubmed-query '("Prostatic Neoplasms"[Mesh]) AND ("Positron-Emission Tomography"[Mesh])' --with-abstracts

# Verificar existencia + retractación
./.venv/bin/python tools/research_tools.py verify PMID:9500320 DOI:10.1056/NEJMoa1910038

# Auditar cifras del documento final contra los abstracts citados
./.venv/bin/python tools/research_tools.py audit-figures --doc 07-resultado-final.md --corpus corpus.json
```

La búsqueda parte de un **PICO** (el Orquestador propone conceptos con descriptores MeSH y
sinónimos); un paso determinista **valida cada MeSH contra NCBI** y arma una query booleana
reproducible que queda guardada en el expediente (transparencia tipo PRISMA).

`verify` distingue tres estados: **VÁLIDO** (existe, no retractado), **RETRACTADO**
(existe pero retractado — nunca se usa como apoyo) e **INVENTADO** (no existe — señal de
alucinación). Solo los VÁLIDOS pueden citarse en el documento final.

## Instalación (una vez)

```bash
cd ~/Documents/investigacion-agentica
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Estructura

```
investigacion-agentica/
├── tools/
│   ├── research_tools.py     # ancla determinista: search + verify (existencia + retractación)
│   ├── zotero_export.py      # export RIS / CSL-JSON (+ sync opcional a Zotero web API)
│   └── slide_generator.py    # (opcional) diapositivas Marp para nivel "completo"
├── prompts/                  # rúbricas de cada rol del pipeline
├── casos/                    # expedientes generados
├── INDICE.md                 # registro de expedientes
├── legacy/                   # enfoque anterior (subprocess + GitHub Actions), como referencia
└── .venv/
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
conserva en `legacy/` por si quieres consultarlo.
