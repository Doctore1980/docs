# Paquete de Investigación: Mejora de la detección precoz del cáncer de próstata mediante inteligencia artificial

**Fecha**: 2026-08-01 · **Nivel**: completo · **Tipo**: Ponencia

## Facetas investigadas

- **faceta-1**: IA aplicada a RM multiparamétrica (RMmp) para detección y clasificación de cáncer de próstata clínicamente significativo (CAD, deep learning).
- **faceta-2**: IA/ML sobre biomarcadores séricos, PSA, densidad PSA y calculadoras de riesgo para detección precoz.
- **faceta-3**: IA en patología digital y biopsia: detección de cáncer y gradación de Gleason en histopatología.
- **faceta-4**: Validación clínica prospectiva, cribado y desempeño diagnóstico global de la IA en detección precoz.

## Síntesis de evidencia por faceta

### faceta-1
La evidencia converge en que los modelos de deep learning (CNN, nnU-Net) sobre RMmp/bpMRI alcanzan un rendimiento diagnostico para csPCa comparable al de radiologos expertos: el metaanalisis de Andrade 2026 (10 estudios, 2586 pacientes) reporta sensibilidad agrupada IA 0.90 vs 0.89 en radiologos y especificidad 0.69 vs 0.60, con AUC 0.88 vs 0.85, sugiriendo una ligera ventaja de la IA en especificidad pero con intervalos de confianza solapados. El estudio PI-CAI (Lancet Oncology 2024), el trabajo confirmatorio de referencia, demostro que un sistema de IA no fue inferior a la lectura radiologica segun PI-RADS, apuntando a una posible reduccion de RM interpretadas por humano y de biopsias innecesarias. Estudios de validacion multicentrica/multiescaner (Eur Radiol 2025) y modelos totalmente automatizados (Radiology 2024) refuerzan la reproducibilidad, aunque persisten limitaciones: alta heterogeneidad entre estudios, escasez de validacion externa prospectiva, dependencia de la calidad/secuencias de adquisicion, y el problema del cancer invisible en RM. La mayoria de la evidencia es observacional/retrospectiva; faltan ECA que demuestren impacto clinico real en reduccion de biopsias y desenlaces de paciente.

**Vacíos/Contradicciones**: Vacio principal: ausencia de ensayos clinicos aleatorizados que demuestren que la IA sobre RMmp reduce biopsias innecesarias y mejora desenlaces del paciente; casi toda la evidencia es observacional/retrospectiva. Contradiccion/limitacion: aunque la IA iguala o supera ligeramente a los radiologos en metricas agrupadas, la alta heterogeneidad entre estudios y la escasa validacion externa prospectiva impiden afirmar superioridad; la ganancia en especificidad tiene intervalos de confianza solapados. Persisten dudas sobre generalizabilidad entre escaneres/protocolos, dependencia de la calidad de adquisicion, cancer clinicamente significativo invisible en RM, y falta de estandarizacion en la definicion de ground truth histopatologico. No se identificaron guias clinicas formales que recomienden la IA como sustituto del radiologo.

**Estudios seleccionados:**
- [✅ verificado] `DOI:10.1016/s1470-2045(24)00220-1` — Artificial intelligence and radiologists in prostate cancer detection on MRI (PI-CAI): an international, paired, non-inferiority, confirmatory study (estudio de validacion confirmatorio multicentrico (comparativo pareado, no inferioridad))
  - Estudio de referencia: un sistema de IA no fue inferior a radiologos con PI-RADS para detectar csPCa en una gran cohorte internacional; sustento clave para IA como lector independiente o de apoyo.
- [✅ verificado] `DOI:10.1007/s00330-026-12465-z` — Artificial-intelligence models vs. radiologists in the detection of clinically significant prostate cancer on mpMRI: a meta-analysis (metaanalisis/revision sistematica)
  - Metaanalisis (10 estudios, 2586 pacientes): IA comparable a radiologos, sensibilidad 0.90 vs 0.89 y especificidad 0.69 vs 0.60; nivel de evidencia mas alto disponible en esta faceta. Corroborado via Consensus.
- [✅ verificado] `DOI:10.7759/cureus.97160` — Artificial Intelligence in MRI for Urologic Oncology: A Systematic Review of Diagnostic Accuracy and Clinical Utility (revision sistematica)
  - Sintetiza precision diagnostica y utilidad clinica de la IA en RM urologica, incluyendo prostata; util para enmarcar rendimiento y barreras de traslacion.
- [✅ verificado] `PMID:39105640` — Fully Automated Deep Learning Model to Detect Clinically Significant Prostate Cancer at MRI (observacional (estudio de rendimiento diagnostico))
  - Modelo totalmente automatizado en Radiology; demuestra deteccion de csPCa sin intervencion manual, relevante para flujo de trabajo y reproducibilidad.
- [✅ verificado] `PMID:40016318` — AI-powered prostate cancer detection: a multi-centre, multi-scanner validation study (estudio de validacion multicentrico)
  - Validacion multicentro/multiescaner en Eur Radiol; aborda generalizabilidad, punto critico para adopcion clinica.
- [✅ verificado] `PMID:38388243` — Deep learning model for the detection of prostate cancer and classification of clinically significant disease using multiparametric MRI in comparison to PI-RADs score (observacional (comparativo con PI-RADS))
  - Comparacion directa DL vs puntuacion PI-RADS para deteccion y clasificacion de csPCa; nucleo de la faceta.
- [✅ verificado] `PMID:41359160` — Evaluation of AI for prostate cancer detection in biparametric-MRI screening population data (observacional (estudio comparativo))
  - Evalua IA sobre bpMRI en poblacion de cribado; pertinente para pacientes sin biopsia previa y reduccion de estudios.
- [✅ verificado] `PMID:36409317` — Predicting clinically significant prostate cancer with a deep learning approach: a multicentre retrospective study (observacional multicentrico retrospectivo)
  - Enfoque DL multicentro para prediccion de csPCa; aporta datos de rendimiento en varias sedes.
- [✅ verificado] `PMID:36825823` — Deep-Learning Models for Detection and Localization of Visible Clinically Significant Prostate Cancer on Multi-Parametric MRI (observacional)
  - Deteccion y localizacion de csPCa visible en RMmp; relevante para guiar biopsia dirigida.
- [✅ verificado] `PMID:34786615` — Deep learning-assisted prostate cancer detection on bi-parametric MRI: minimum training data size requirements and effect of prior knowledge (observacional (estudio metodologico))
  - Analiza requisitos de datos de entrenamiento y conocimiento previo en bpMRI; util para interpretar limitaciones y reproducibilidad.
- [✅ verificado] `DOI:10.3390/curroncol33030151` — Artificial Intelligence in Prostate MRI: Comparison of an AI-Based Software and an Experienced Radiologist for Detecting Clinically Significant Prostate Cancer (observacional (comparativo IA vs radiologo))
  - Comparacion cabeza a cabeza de software de IA frente a radiologo experto; evidencia directa sobre equivalencia diagnostica.
- [✅ verificado] `DOI:10.3390/cancers18010028` — Using Artificial Intelligence as a Risk Prediction Model in Patients with Equivocal Multiparametric Prostate MRI Findings (observacional)
  - IA como modelo de prediccion de riesgo en hallazgos RMmp equivocos (PI-RADS 3); directamente ligado a evitar biopsias innecesarias.
- [✅ verificado] `PMID:33773964` — Artificial Intelligence in Magnetic Resonance Imaging-based Prostate Cancer Diagnosis: Where Do We Stand in 2021? (revision narrativa)
  - Revision de referencia (Eur Urol Focus) que contextualiza el estado y limitaciones de la IA en RM de prostata.
- [✅ verificado] `PMID:40613800` — Enhancing Prostate Cancer Classification: A Comprehensive Review of Multiparametric MRI and Deep Learning Integration (revision)
  - Revision reciente centrada en integracion RMmp + deep learning para clasificacion; util como marco actualizado.

### faceta-2
La evidencia sobre modelos de machine learning que integran PSA, densidad de PSA, biomarcadores y datos clinicos para detectar cancer de prostata clinicamente significativo (CaPcs) y evitar biopsias innecesarias es abundante pero dominada por estudios observacionales retrospectivos y monocentricos, con pocos disenos multicentricos y ninguna guia clinica ni metaanalisis especifico dentro de los candidatos. Los modelos ML (regresion logistica-lasso, gradient boosting, TabNet, stacking no lineal) mejoran de forma consistente la discriminacion frente al PSA aislado y frente a calculadoras clasicas, y varios generan calculadoras de riesgo online (p.ej. PMID:39537107). Un vacio importante es que los candidatos recuperados apenas contienen validacion prospectiva de biomarcadores comerciales concretos como PHI o 4Kscore integrados en modelos ML; la mayoria usa PSA, derivados y marcadores sericos/urinarios genericos o metabolomica. Existe heterogeneidad metodologica y riesgo de sobreajuste (muestras pequenas, validacion externa limitada), lo que limita la transferibilidad clinica pese a AUC reportados altos.

**Vacíos/Contradicciones**: Vacio principal: entre los candidatos no hay guias clinicas ni metaanalisis/revisiones sistematicas especificos de modelos ML sobre biomarcadores sericos, ni validacion prospectiva de PHI o 4Kscore integrados en modelos ML (el brief los menciona pero no aparecen estudios dedicados en la lista). Predominan disenos retrospectivos monocentricos con validacion externa escasa, lo que genera riesgo de sobreajuste y AUC probablemente optimistas. Posible contradiccion latente: la mejora de discriminacion frente al PSA es consistente, pero no hay evidencia de alto nivel de que estos modelos reduzcan biopsias innecesarias en la practica sin perder CaP significativos. Muchos candidatos del fichero eran radiomica/RM, enfermedad metastasica o supervivencia (fuera de faceta) y se descartaron.

**Estudios seleccionados:**
- [✅ verificado] `PMID:39537107` — A Novel Machine Learning-based Predictive Model of Clinically Significant Prostate Cancer and Online Risk Calculator. (estudio observacional (multicentrico))
  - Modelo ML multicentrico para CaPcs con calculadora de riesgo online; ejemplo directo de la faceta (combinar variables clinicas y PSA para decidir biopsia).
- [✅ verificado] `PMID:36059701` — Machine learning model for the prediction of prostate cancer in patients with low prostate-specific antigen levels: A multicenter retrospective analysis. (estudio observacional (multicentrico retrospectivo))
  - Aborda el escenario de PSA bajo, relevante para evitar biopsias innecesarias mediante ML con datos clinicos y PSA.
- [✅ verificado] `PMID:39905119` — Integrating radiological and clinical data for clinically significant prostate cancer detection with machine learning techniques. (estudio observacional)
  - Integra datos clinicos (incluye PSA/densidad) con ML para deteccion de CaPcs; encaja en modelos multimodales de decision de biopsia.
- [✅ verificado] `DOI:10.3389/fonc.2022.941349` — Machine Learning-Based Models Enhance the Prediction of Prostate Cancer. (estudio observacional)
  - Compara modelos ML frente a metodos clasicos mostrando mejora en la prediccion de CaP a partir de variables clinicas y sericas.
- [✅ verificado] `DOI:10.3389/fendo.2026.1757255` — Development and validation of a clinical nomogram based on lasso-logistic regression for predicting prostate cancer with PSA 4-20.0 ng/mL: a retrospective study. (estudio observacional (retrospectivo))
  - Nomograma lasso-logistico en la zona gris de PSA 4-20 ng/mL; nucleo de la faceta (riesgo y decision de biopsia).
- [✅ verificado] `DOI:10.1007/s12672-026-04777-9` — Meta learning optimized TabNet for small sample repeat prostate biopsy prediction. (estudio observacional)
  - Modelo ML (TabNet) para predecir resultado de rebiopsia; directamente orientado a evitar biopsias repetidas innecesarias.
- [✅ verificado] `DOI:10.1038/s41698-026-01406-0` — Identification of biomarkers for non-invasive diagnosis and risk stratification in prostate cancer using NMR-based metabolomics and machine learning. (estudio observacional)
  - Biomarcadores metabolomicos sericos combinados con ML para diagnostico no invasivo y estratificacion de riesgo.
- [✅ verificado] `DOI:10.62347/qtaw5624` — Diagnostic utility of serum prostate-specific antigen and circulating inflammatory markers for differentiating prostate cancer from benign prostatic hyperplasia. (estudio observacional)
  - PSA serico mas marcadores inflamatorios circulantes para discriminar CaP de HBP; relevante para paneles de biomarcadores sericos.
- [✅ verificado] `DOI:10.3389/fonc.2026.1762494` — Role of urinary leukocytes in the risk stratification of prostate cancer using nonlinear stacking learning strategy: a bi-cohort diagnostic study. (estudio observacional (bicohorte diagnostico))
  - Estrategia de stacking no lineal con biomarcadores urinarios para estratificar riesgo; complementa biomarcadores sericos con ML.
- [✅ verificado] `DOI:10.3390/diagnostics11020354` — Artificial Intelligence and Machine Learning in Prostate Cancer Patient Management-Current Trends and Future Perspectives. (revision narrativa)
  - Panoramica de aplicaciones de IA/ML en el manejo del CaP; util como marco de contexto, no aporta datos primarios.
- [✅ verificado] `DOI:10.7759/cureus.96226` — Artificial Intelligence Across the Prostate Cancer Pathway: Screening, Imaging, Pathology, and Biomarkers. (revision narrativa)
  - Revision reciente que cubre cribado y biomarcadores con IA; contextualiza el papel de los modelos sericos y de riesgo.

### faceta-3
La evidencia en patología computacional para cáncer de próstata (CaP) está madurando desde estudios metodológicos hacia validaciones diagnósticas de gran escala. El referente de calidad de datos y benchmarking es el reto PANDA (Nat Med 2021), que reunió miles de biopsias multicéntricas para detección y gradación Gleason con rendimiento a nivel de patólogo; lo precede el algoritmo de Google validado para el Gleason scoring (npj Digit Med 2019). En el terreno de la validación clínica y despliegue, la evaluación independiente del sistema de Paige Prostate (Mod Pathol 2021) demostró alta exactitud diagnóstica en cohortes externas, alineándose con su condición de primer sistema de IA en patología con marcado regulatorio (FDA De Novo). Toda la gradación se ancla en el consenso ISUP 2019, referencia normativa imprescindible para interpretar los grupos de grado que los algoritmos predicen. Persisten señales de precaución: la crítica del 'gemelo digital' del patólogo (Sci Rep 2024) y el impacto del preprocesado (detección de tejido) sobre el rendimiento muestran fragilidad de generalización, y las revisiones sistemática/scoping recientes coinciden en heterogeneidad metodológica y escasez de validaciones prospectivas e impacto clínico real.

**Vacíos/Contradicciones**: Predomina la evidencia observacional/de exactitud diagnostica y validaciones retrospectivas; faltan ensayos prospectivos y estudios de impacto clinico (efecto sobre decisiones, sobrediagnostico o carga de trabajo del patologo). Existe tension entre metricas de rendimiento a nivel de patologo (PANDA, Paige, cribiforme) y las advertencias de fragilidad/generalizacion (critica del gemelo digital, impacto del preprocesado). Solo un sistema (tipo Paige Prostate) cuenta con via regulatoria clara; el resto son prototipos de investigacion. La heterogeneidad de patrones de referencia y la dependencia del ISUP 2019 introducen variabilidad no resuelta en la etiqueta de entrenamiento.

**Estudios seleccionados:**
- [✅ verificado] `DOI:10.1097/pas.0000000000001497` — The 2019 International Society of Urological Pathology (ISUP) Consensus Conference on Grading of Prostatic Carcinoma (guia clinica / consenso)
  - Marco normativo de gradación (grupos de grado ISUP/Gleason) sobre el que se define el patron oro que todo algoritmo de grading debe reproducir.
- [✅ verificado] `DOI:10.1038/s41591-021-01620-2` — Artificial intelligence for diagnosis and Gleason grading of prostate cancer: the PANDA challenge (validacion diagnostica multicentrica (observacional))
  - Benchmark internacional de referencia; miles de biopsias, detección y gradación Gleason con rendimiento comparable a patologos y validación externa.
- [✅ verificado] `DOI:10.1038/s41746-019-0112-2` — Development and validation of a deep learning algorithm for improving Gleason scoring of prostate cancer (estudio de validacion diagnostica (observacional))
  - Algoritmo de Google que mejora la concordancia del Gleason scoring frente a patologos generales; hito temprano de grading automatizado.
- [✅ verificado] `DOI:10.1038/s41379-021-00794-x` — An independent assessment of an artificial intelligence system for prostate cancer detection shows strong diagnostic accuracy (estudio de validacion diagnostica externa (observacional))
  - Validación independiente del sistema tipo Paige Prostate (primer sistema con marcado regulatorio FDA); alta exactitud en deteccion sobre cohortes externas.
- [✅ verificado] `PMID:37627935` — Deep Learning Methodologies Applied to Digital Pathology in Prostate Cancer: A Systematic Review (revision sistematica)
  - Sintesis sistematica de metodos de deep learning en patologia digital de CaP; util para panorama de rendimiento y limitaciones metodologicas.
- [✅ verificado] `PMID:41808601` — Artificial intelligence for detection, grading, and prognostication in prostate cancer pathology: A scoping review (revision (scoping))
  - Mapa reciente (2026) de deteccion, gradacion y pronostico por IA en patologia de CaP; identifica vacios de validacion prospectiva.
- [✅ verificado] `PMID:40623883` — Development and retrospective validation of an artificial intelligence system for diagnostic assessment of prostate biopsies: study protocol (estudio de validacion (protocolo))
  - Protocolo de desarrollo y validacion retrospectiva de un sistema de IA para evaluacion diagnostica de biopsias prostaticas; ejemplo de diseno de validacion clinica.
- [✅ verificado] `PMID:38438436` — Critical evaluation of artificial intelligence as a digital twin of pathologists for prostate cancer pathology (observacional)
  - Evaluacion critica de las limitaciones de la IA como sustituto del patologo; aporta contrapeso a las metricas optimistas de exactitud.
- [✅ verificado] `DOI:10.1038/s41598-026-52148-9` — The impact of tissue detection on diagnostic artificial intelligence algorithms in prostate digital pathology (observacional)
  - Muestra como el preprocesado (deteccion de tejido) condiciona el rendimiento diagnostico; relevante para reproducibilidad y generalizacion.
- [✅ verificado] `DOI:10.1016/j.euros.2026.03.016` — Finding Holes: Pathologist-Level Performance Using AI for Cribriform Morphology Detection in Prostate Cancer (observacional (exactitud diagnostica))
  - IA a nivel de patologo para detectar morfologia cribiforme, patron de alto valor pronostico dificil de reproducir entre observadores.
- [✅ verificado] `PMID:38953042` — A selective CutMix approach improves generalizability of deep learning-based grading and risk assessment of prostate cancer (observacional (metodologico))
  - Tecnica de aumento de datos para mejorar la generalizacion del grading; aborda directamente el problema de robustez entre centros.
- [✅ verificado] `PMID:32555410` — Histologic tissue components provide major cues for machine learning-based prostate cancer detection and grading on prostatectomy specimens (observacional)
  - Analiza que componentes tisulares guian la deteccion/gradacion por ML en piezas de prostatectomia; util para interpretabilidad.
- [✅ verificado] `DOI:10.1038/s41586-024-07894-z` — A pathology foundation model for cancer diagnosis and prognosis prediction (observacional (modelo fundacional))
  - Modelo fundacional de patologia aplicable a diagnostico/pronostico pan-cancer; marca la tendencia hacia modelos generalistas que incluyen CaP.
- [✅ verificado] `DOI:10.1136/bmjonc-2026-001102` — Foundation models in computational pathology: methods, applications and clinical implications (revision)
  - Revision de modelos fundacionales en patologia computacional; contexto metodologico y de implicaciones clinicas para la faceta de biopsia.

### faceta-4
La evidencia disponible sobre IA en detección precoz de cáncer de próstata está dominada por revisiones (sistemáticas y narrativas) y estudios retrospectivos/observacionales; existe un vacío marcado de validación prospectiva y de ensayos aleatorizados con desenlaces poblacionales de cribado. Los estudios con dato clínico primario (p. ej. micro-ecografía asistida por IA en biopsia, o modelos de deep learning multimodal en la zona gris del PSA) son retrospectivos o de un único centro, con validación externa limitada, lo que expone a sesgo de selección y a problemas de generalización. Un estudio de registro sobre ClinicalTrials.gov confirma que el desarrollo se concentra en fases tempranas y que faltan ensayos prospectivos de impacto sobre el cribado. Existen marcos metodológicos consolidados para evaluar IA clínica (CONSORT-AI, SPIRIT-AI, DECIDE-AI) que aún se aplican poco en este dominio. En los candidatos NO se identifica ningún ensayo NCT específico de detección/cribado de CaP mediante IA: los NCT recuperados son de tratamiento farmacológico o radioterápico, reforzando el vacío de validación prospectiva.

**Vacíos/Contradicciones**: Vacío principal: ausencia de validación prospectiva y de ensayos aleatorizados de impacto en cribado poblacional de CaP con IA. Entre los candidatos NO figura ningún ensayo NCT específico de detección/cribado por IA (todos los NCT recuperados son de tratamiento farmacológico o radioterápico), lo que confirma la falta de evidencia prospectiva dirigida. Los estudios con dato clínico son retrospectivos o de un solo centro, con validación externa escasa, riesgo de sesgo de selección y dudas de generalización a poblaciones y equipos distintos. Existen marcos metodológicos maduros (CONSORT-AI, SPIRIT-AI, DECIDE-AI) infrautilizados en este dominio. La evidencia es, por tanto, prometedora pero inmadura: predominan revisiones sobre resultados prospectivos de alto nivel.

**Estudios seleccionados:**
- [✅ verificado] `PMID:41228295` — Improving Early Prostate Cancer Detection Through Artificial Intelligence: Evidence from a Systematic Review (revisión sistemática)
  - Revisión sistemática centrada explícitamente en la detección precoz de CaP con IA; sintetiza desempeño diagnóstico y señala limitaciones de la evidencia. Referencia nuclear de la faceta.
- [✅ verificado] `DOI:10.1177/00469580261457387` — AI in Prostate Cancer Screening & Diagnosis: A Registry-Based Study of ClinicalTrials.gov Trials (observacional (estudio de registro))
  - Analiza el panorama de ensayos registrados de IA en cribado/diagnóstico de CaP; evidencia directa del estado (y escasez) de validación prospectiva en curso.
- [✅ verificado] `DOI:10.1002/bco2.70133` — AI-enhanced micro-ultrasound improves detection of clinically significant prostate cancer at biopsy (observacional / estudio clínico diagnóstico)
  - Dato clínico primario de desempeño diagnóstico de IA en detección de CaP clínicamente significativo; relevante para eficacia diagnóstica real, aunque con alcance limitado.
- [✅ verificado] `DOI:10.3389/fonc.2026.1763766` — Construction and validation of a multimodal MRI-based deep learning model for early differential diagnosis of prostate cancer in the PSA gray zone: a retrospective cohort study (observacional (cohorte retrospectiva))
  - Modelo de deep learning validado internamente en la zona gris del PSA; ilustra el patrón de validación retrospectiva y el vacío de validación externa/prospectiva.
- [✅ verificado] `PMID:31200839` — Multi-institutional Clinical Tool for Predicting High-risk Lesions on 3Tesla Multiparametric Prostate MRI (observacional (estudio multicéntrico))
  - Herramienta multi-institucional de predicción sobre mpMRI; aporta evidencia de validación multicéntrica (mitiga parcialmente sesgo de un solo centro).
- [✅ verificado] `DOI:10.3390/tomography12050062` — The Role of Artificial Intelligence in the Characterization and Outcome Prediction of Prostate Cancer: A Systematic Review (revisión sistemática)
  - RS sobre caracterización y predicción de desenlaces con IA en CaP; útil para el desempeño diagnóstico global y sus limitaciones de generalización.
- [✅ verificado] `DOI:10.7759/cureus.96226` — Artificial Intelligence Across the Prostate Cancer Pathway: Screening, Imaging, Pathology, and Biomarkers (revisión narrativa)
  - Panorámica de IA a lo largo de la ruta del CaP, incluyendo cribado; contextualiza el estado de la validación por dominios.
- [✅ verificado] `DOI:10.3390/curroncol33030166` — Current Applications and Future Directions of Artificial Intelligence in Prostate Cancer Diagnosis: A Narrative Review (revisión narrativa)
  - Revisión de aplicaciones actuales y direcciones futuras de IA en diagnóstico de CaP; discute retos de traslación clínica.
- [✅ verificado] `DOI:10.1038/s41591-020-1034-x` — Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension (guía metodológica)
  - Estándar para reportar ensayos de intervenciones con IA; marco de referencia para juzgar la calidad de la validación prospectiva.
- [✅ verificado] `DOI:10.1038/s41591-020-1037-7` — Guidelines for clinical trial protocols for interventions involving artificial intelligence: the SPIRIT-AI extension (guía metodológica)
  - Estándar para protocolos de ensayos de IA; complementa CONSORT-AI y orienta el diseño de la validación prospectiva ausente en este dominio.
- [✅ verificado] `DOI:10.1038/s41591-022-01772-9` — Reporting guideline for the early-stage clinical evaluation of decision support systems driven by artificial intelligence: DECIDE-AI (guía metodológica)
  - Marco para la evaluación clínica en fase temprana de sistemas de apoyo a la decisión con IA; pertinente dado que la mayoría de herramientas de detección de CaP están en fases pre-prospectivas.
- [✅ verificado] `DOI:10.1016/s0140-6736(24)00651-2` — The Lancet Commission on prostate cancer: planning for the surge in cases (revisión / documento de consenso)
  - Contexto poblacional y de cribado del CaP a escala global; encuadra el impacto potencial (y las necesidades) de la detección precoz asistida por IA.
- [✅ verificado] `DOI:10.1038/s41585-022-00638-6` — Serum PSA-based early detection of prostate cancer in Europe and globally: past, present and future (revisión narrativa)
  - Base del cribado por PSA y sus limitaciones; comparador de referencia frente al que la IA debe demostrar valor añadido en detección precoz.

## Informe de verificación

# Informe del Verificador 1 (verificación de hechos)

**Fecha**: 2026-08-01  
**Identificadores citados (únicos)**: 51  
**Válidos**: 51 · **Retractados**: 0 · **Inventados**: 0

## Identificadores inventados (CRÍTICO si hay alguno)
Ninguno. Los 51 identificadores citados por los investigadores resuelven contra su API oficial (PubMed E-utilities / Crossref / ClinicalTrials.gov).

## Identificadores retractados
Ninguno detectado. La comprobación determinista de retractación (marcador PubMed "Retracted Publication") no marcó ningún PMID.
Nota de rigor: 31 identificadores son DOI, para los que la retractación no se comprueba vía PubMed; se recomienda un cruce con Scite para confirmación a nivel DOI.

## Contradicciones entre facetas
Sin contradicciones de hecho entre facetas; son ejes complementarios (imagen, biomarcadores, patología, validación). El Analista integrará matices de rendimiento.

## Suficiencia de la evidencia
Suficiente para una ponencia. Buena cobertura en RMmp (metaanálisis + estudios), patología digital (PANDA, validaciones, consenso ISUP) y validación metodológica (CONSORT-AI/SPIRIT-AI/DECIDE-AI). El punto débil real —y honesto para la charla— es la escasez de validación PROSPECTIVA e impacto en cribado poblacional.

## Veredicto
**APTO PARA CONTINUAR**