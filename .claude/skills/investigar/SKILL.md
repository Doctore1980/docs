---
name: investigar
description: 'Investigación biomédica con evidencia verificada. Convierte una pregunta, duda o título en un expediente trazable cuya bibliografía comprueba un script contra PubMed, Crossref y ClinicalTrials.gov (existencia y retractación). Activar con /investigar o cuando el usuario pida "investiga…", "busca evidencia sobre…", "¿qué dice la literatura de…?", "prepara una ponencia sobre…". Frecuente en urología, uro-oncología e IA en salud, pero sirve para cualquier tema biomédico. Niveles: rapido (duda puntual), medio (informe), completo (ponencia con guion de diapositivas). No usar para evaluar la metodología de un artículo concreto ni para consultar una colección ya indexada.'
---

# /investigar — investigación con evidencia verificada

Coordinas un proceso por etapas cuyo valor está en una garantía: ninguna cita
llega al documento final sin que un script, y no un modelo, haya comprobado
contra su fuente oficial que existe y que no consta retractada. Tu juicio
decide qué buscar y cómo sintetizar; los estados de las citas y las puertas los
decide `tools/research_tools.py`, y su veredicto no se reinterpreta.

Dónde vive cada regla, para no duplicarla:

- Este fichero: el orden de las etapas, los comandos y qué hacer ante cada puerta.
- `prompts/*.md`: la rúbrica de cada rol. Pásala íntegra al subagente o síguela
  tú; no la resumas aquí ni en el encargo.
- `tools/research_tools.py`: estados de verificación, lista citable, control de
  citas y auditoría de cifras.

## Entorno

`SKILL_DIR` es el directorio de este fichero.

- **Python (`PY`)**: usa `~/Dev/investigacion-agentica/.venv/bin/python` si
  existe. Si no, `python3` cuando `import requests` funcione; en otro caso crea
  un venv en el directorio de trabajo e instala `SKILL_DIR/requirements.txt`.
- **Expedientes (`CASOS`)**: `~/Dev/investigacion-agentica/casos/` si existe; si
  no, `./investigacion/casos/` en el directorio de trabajo, y al terminar
  entrega al usuario los ficheros del expediente, porque fuera del equipo local
  no se conservan.
- **Subagentes**: si dispones de una herramienta para lanzarlos, úsala donde se
  indica. Si no, ejecuta tú cada rol, uno tras otro, con la misma rúbrica.
- **MCP y conectores** (Consensus, Elicit, Scite, PubMed, Zotero, NotebookLM,
  Obsidian): son complementos. El proceso funciona sin ninguno; los que falten
  se anotan en el expediente y en el resumen final.

## Expediente y reanudación

Crea `CASOS/AAAA-MM-DD-slug/` (en adelante `DIR`) con las subcarpetas
`01b-busqueda/`, `_candidatos/` y `02-investigador/`, y guarda el encargo
literal en `00-encargo-original.md`. Cada etapa deja su fichero numerado: es el
registro de lo hecho. Si el expediente ya existe, continúa desde la primera
etapa cuyo fichero falte en lugar de empezar de nuevo.

## Etapas

### 1. Clasificación y estrategia (tú)

Aplica `prompts/orquestador_system_prompt.md` → `01-clasificacion.json`: nivel,
tipo de pregunta y de una a cuatro facetas con sus conceptos de búsqueda.
Respeta el nivel que pida el usuario.

### 2. Búsqueda reproducible (script, por faceta)

Escribe los conceptos de la faceta en `01b-busqueda/faceta-N.json` como
`{"concepts": [...]}` y ejecuta:

```
PY SKILL_DIR/tools/research_tools.py build-query --pico DIR/01b-busqueda/faceta-N.json > DIR/01b-busqueda/faceta-N-query.json
PY SKILL_DIR/tools/research_tools.py search --query "<query_semantica>" --from-build DIR/01b-busqueda/faceta-N-query.json --with-abstracts > DIR/_candidatos/faceta-N.json
```

Añade `--condition "<condicion_ctgov>"` si la faceta la tiene. `build-query`
valida cada descriptor MeSH contra NCBI y deja la estrategia booleana para el
expediente. Si `pubmed_count` es 0 o desmesurado, ajusta los conceptos y repite.

El campo `fuentes` de la salida dice qué fuentes respondieron. Una con error
(HTTP 429, cuota agotada, sin red) no aportó candidatos: anótala para el resumen
final en lugar de leer su silencio como ausencia de estudios. Semantic Scholar y
OpenAlex aceptan claves gratuitas en `SEMANTIC_SCHOLAR_API_KEY` y
`OPENALEX_API_KEY`; sin ellas suelen devolver 429 desde IP compartidas.

### 3. Investigadores (un subagente por faceta, todos en el mismo mensaje)

A cada uno: `prompts/investigador_system_prompt.md` íntegro, la descripción de
su faceta, el tipo de pregunta, su brief y la ruta de
`_candidatos/faceta-N.json`, que debe leer. Es trabajo de selección y síntesis:
en Claude Code lánzalos con `model: "sonnet"` y reserva el modelo de la sesión
para las etapas 5 a 7. Guarda cada salida en `02-investigador/faceta-N.json`.

**3b. Guías y literatura gris** (nivel `completo`, o si el usuario lo pide, y
solo si hay búsqueda web): un subagente adicional localiza guías clínicas y
documentos de sociedades que las APIs no indexan. Guarda
`02b-deepresearch.json` como
`{"items": [{"organismo", "anio", "titulo", "url", "extracto", "identifier"}]}`,
donde `extracto` es texto literal de la fuente e `identifier` solo aparece si
el hallazgo es un estudio con PMID o DOI.

### 4. Puerta de verificación (script)

```
PY SKILL_DIR/tools/research_tools.py gate --caso DIR
```

Lee los identificadores de los JSON de las etapas 3 y 3b, de modo que nunca
pasan por la línea de comandos, los verifica y escribe `03-verificacion.json` y
`_validos.json`. Solo lo que esté en `_validos.json` es citable. El código de
salida manda:

- **0**: continúa.
- **2**: hay identificadores `NO_ENCONTRADO` o `MAL_FORMADO`, o no hay nada que
  verificar. Detente y cuéntale al usuario cuáles son y de qué faceta salieron.
  Si tras verlo decide seguir sin ellos, continúa con `_validos.json` tal como
  quedó.
- **3**: quedan `INCONCLUSO` aunque el script ya reintentó una vez. Es un fallo
  técnico, no una cita inventada. Repite el comando una vez más pasados unos
  minutos; si persiste, detente y explica qué fuente no responde. Si casi todo
  queda `INCONCLUSO`, lo más probable es que el entorno no tenga salida a
  internet hacia esas APIs: dilo así y no redactes.

Un `INCONCLUSO` cuyo detalle es "retractación no evaluable" (DOI ajeno a
Crossref, típico de preprints) no se arregla reintentando: queda fuera de la
lista citable salvo que el usuario decida otra cosa.

Con la puerta superada, lanza el Verificador 1
(`prompts/verificador1_system_prompt.md`) con las síntesis y
`03-verificacion.json` → `03-verificacion.md`. Si su veredicto es REQUIERE
ACLARACIÓN, detente y pregunta al usuario antes de redactar.

### 5. Análisis

`prompts/analista_system_prompt.md` con el encargo, `03-verificacion.md` y las
síntesis → `05-analista.json`. En niveles `medio` y `completo`, consolida antes
el encargo, las síntesis y el informe de verificación en
`04-fuente-notebooklm.md`.

### 6. Redacción

`prompts/redactor_system_prompt.md` con el análisis, el nivel y
`_validos.json` → `06-redaccion-borrador.md`.

### 7. Pulido y puertas finales (script)

```
PY SKILL_DIR/tools/research_tools.py audit-figures --doc DIR/06-redaccion-borrador.md --caso DIR > DIR/07-auditoria-cifras.json
```

Lanza el Verificador 2 (`prompts/verificador2_system_prompt.md`) con el
borrador y la auditoría → `07-resultado-final.md`. Después comprueba el
documento ya pulido:

```
PY SKILL_DIR/tools/research_tools.py check-citations --doc DIR/07-resultado-final.md --validos DIR/_validos.json
PY SKILL_DIR/tools/research_tools.py audit-figures --doc DIR/07-resultado-final.md --caso DIR > DIR/07-auditoria-cifras.json
```

`check-citations` debe salir con 0: si encuentra una cita fuera de la lista,
retírala del texto junto con lo que afirmaba y repite. En la auditoría no
pueden quedar entradas en `cifras_a_cotejar` salvo las reescritas como
pendientes de cotejo, que el script lista aparte en
`marcadas_pendiente_cotejo`. Corrige como máximo dos rondas; si sigue sin pasar,
entrega el documento señalando qué queda sin resolver.

Si el encargo pide ISO 690, convierte ahora las citas a Apellido-Año conservando
el identificador en la lista de referencias. En nivel `completo` puedes generar
diapositivas con `tools/slide_generator.py`.

## Cierre

1. Entrega `07-resultado-final.md` y un resumen: nivel, facetas, recuento por
   estado (`VALIDO`, `RETRACTADO`, `NO_ENCONTRADO`, `INCONCLUSO`), cifras
   pendientes de cotejo, y fuentes de búsqueda y herramientas que no estuvieron
   disponibles.
2. Añade una fila a `INDICE.md`, junto a la carpeta `casos/`: fecha, pregunta,
   nivel, veredicto y ruta.
3. Ofrece, sin imponer, las integraciones disponibles en la sesión:
   - **Zotero**: colección con los VALIDOS mediante el MCP de Zotero (en lotes
     de unos diez) o, en su defecto, `tools/zotero_export.py`, que genera RIS y
     CSL-JSON y no sube registros con metadatos incompletos.
   - **NotebookLM**: subir `04-fuente-notebooklm.md` como fuente.
   - **Obsidian**: nota en el vault `AI_Knowledge_System` siguiendo las normas
     de su `Claude.md` (ISO 690, RMmp, PEEL).
   - **SCI-INDEX**: si las skills `zotero-bridge` y `sci-index-processor` están
     en la sesión, indexar los VALIDOS en esa colección.
4. En local, si durante el caso el usuario corrigió algo o expresó una
   preferencia, invoca la skill `update-claude-memory` con ese contexto.

## Límites que conviene decir al usuario

- Que una cita exista no prueba que respalde la afirmación. Si Scite está
  disponible, contrasta con él las afirmaciones clave.
- "Sin retractación" significa que no consta en PubMed ni en Crossref en la
  fecha registrada en `03-verificacion.json`.
- Las guías citadas por URL no pasan por el verificador de identificadores.
