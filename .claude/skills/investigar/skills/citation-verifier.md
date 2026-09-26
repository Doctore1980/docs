# Skill: citation-verifier

## Propósito
Verificar que cualquier identificador bibliográfico citado (DOI, PMID, NCT)
corresponde a un registro real, antes de que ese dato se use como base de
un análisis, una redacción o una afirmación clínica.

## Criterio (obligatorio, sin excepción)
- PMID: debe resolver contra PubMed (E-utilities ESummary).
- NCT: debe resolver contra ClinicalTrials.gov API v2.
- DOI: debe resolver contra Crossref (`GET https://api.crossref.org/works/{doi}`,
  200 = existe, 404 = no existe) o, si no está registrado en Crossref,
  contra el registro de handles de doi.org (retractación no evaluable).
- Retractación: PMIDs contra PubMed ("Retracted Publication"); DOIs contra
  las notas de retractación de Crossref. Un identificador retractado nunca
  sustenta una afirmación. Implementación: `tools/research_tools.py verify`.

Si un identificador no resuelve (la API responde que no existe), el dato
asociado se descarta por completo — no se reformula, no se "arregla", se
elimina. Si la API no respondió (`exists: null`), no se concluye nada: se
repite la verificación, y mientras no resuelva no se cita.

## Regla de origen
Ningún identificador puede citarse si no proviene de una búsqueda real
ejecutada en esta sesión de trabajo (la búsqueda determinista de
`research_tools.py search` —PubMed, ClinicalTrials.gov, Europe PMC,
Semantic Scholar, OpenAlex—, los conectores MCP consultados por el
Investigador, o la biblioteca Zotero del usuario). Un identificador que aparece en un borrador
pero no en la lista de fuentes originales de la etapa de investigación se
marca como CRÍTICO — es la señal más fuerte de invención por parte de un
modelo de lenguaje.

## Nivel de evidencia (para acompañar, no sustituir, la verificación de identidad)
guía clínica > metaanálisis/revisión sistemática > ensayo clínico >
estudio observacional > abstract de congreso > preprint

## Salida esperada
Una tabla o lista con, para cada identificador evaluado: el identificador,
si resolvió o no, y si aparecía en la lista de fuentes originales. Sin
excepciones silenciosas: todo hallazgo se reporta, aunque sea negativo.
