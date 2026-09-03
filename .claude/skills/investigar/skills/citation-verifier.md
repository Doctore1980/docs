# Skill: citation-verifier

## Propósito
Verificar que cualquier identificador bibliográfico citado (DOI, PMID, NCT)
corresponde a un registro real, antes de que ese dato se use como base de
un análisis, una redacción o una afirmación clínica.

## Criterio (obligatorio, sin excepción)
- PMID: debe resolver contra PubMed (E-utilities EFetch/ESummary).
- NCT: debe resolver contra ClinicalTrials.gov API v2.
- DOI: debe resolver contra Crossref (`GET https://api.crossref.org/works/{doi}`,
  200 = existe, 404 = no existe).

Si un identificador no resuelve, el dato asociado se descarta por completo —
no se reformula, no se "arregla", se elimina.

## Regla de origen
Ningún identificador puede citarse si no proviene de una búsqueda real
ejecutada en esta sesión de trabajo (PubMed, ClinicalTrials.gov, o la
biblioteca Zotero del usuario). Un identificador que aparece en un borrador
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
