"""
Generador de Presentaciones Marp/Reveal.js y Prompts Visuales IA -- Fase 2 Avanzada
Transforma informes de investigación en guiones de diapositivas y prompts de imagen para IA generativa.
"""

import os
import json
import re


def generate_marp_presentation(encargo: dict, plan: dict, resultado_final: str, valid_identifiers: list[str]) -> str:
    """Construye un documento Markdown compatible con Marp / Slidev / Reveal.js."""
    pregunta = encargo.get("pregunta", "Informe de Investigación")
    nivel = plan.get("nivel", "medio")

    slides = []

    # Slide 1: Portada
    slides.append(f"""---
marp: true
theme: default
paginate: true
header: "investigacion-agentica | Uro-Oncología & IA"
footer: "Evidencia Verificada | {valid_identifiers[0] if valid_identifiers else 'Bibliografía Replicable'}"
style: |
  section {{
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    background-color: #0f172a;
    color: #f8fafc;
  }}
  h1 {{
    color: #38bdf8;
  }}
  h2 {{
    color: #818cf8;
  }}
---

# {pregunta}

### Encargo de Investigación | Nivel: `{nivel.upper()}`

---
""")

    # Slide 2: Resumen Ejecutivo y Objetivos
    slides.append("""## 📌 Objetivos y Resumen de la Evidencia

- **Propósito**: Evaluación crítica de la literatura científica disponible.
- **Fuentes Consultadas**: PubMed, ClinicalTrials.gov, Europe PMC, Semantic Scholar, OpenAlex.
- **Rigor Bibliográfico**: Identificadores validados determinísticamente a nivel de API.

💡 *Sugerencia Visual: Diagrama de flujo de fuentes científicas convergentes hacia el centro.*
<!-- _note: Presentar el marco del encargo destacando que la evidencia citada está 100% verificada contra bases oficiales. -->

---
""")

    # Extraer secciones del resultado final para generar diapositivas por cada apartado
    secciones = re.split(r"\n(?=##? )", resultado_final)
    for i, sec in enumerate(secciones):
        if not sec.strip():
            continue
        lines = sec.strip().split("\n")
        title = lines[0].lstrip("#").strip()
        body = "\n".join(lines[1:12])  # Limitar líneas por diapositiva para no saturar

        slides.append(f"""## 📊 {title}

{body}

---
""")

    # Slide Final: Referencias Verificadas
    ref_list = "\n".join([f"- `{ident}`" for ident in valid_identifiers[:8]])
    slides.append(f"""## 📚 Referencias Bibliográficas Verificadas

{ref_list}

💡 *Todas las citas corresponden a registros existentes y validados.*

---
""")

    return "\n".join(slides)


def generate_visual_prompts(encargo: dict, plan: dict) -> str:
    """Genera prompts detallados optimizados para Midjourney v6, DALL-E 3, Nanobanana y Canva Magic."""
    pregunta = encargo.get("pregunta", "")

    prompts_doc = []
    prompts_doc.append(f"# 🎨 Prompts Visuales para IA Generativa (DALL-E 3 / Midjourney / Nanobanana)\n")
    prompts_doc.append(f"**Investigación**: {pregunta}\n")

    prompts_doc.append("""## 1. Banner Principal / Portada de la Ponencia

**Plataforma sugerida**: Midjourney v6 / DALL-E 3
**Prompt**:
> `Cinematic photorealistic 8k image of advanced medical artificial intelligence in urology, prostate MRI scanning with holographic blue heatmap overlays, medical data analytics dashboard, dark sleek futuristic laboratory background, volumetric lighting, Octane render, --ar 16:9 --v 6.0`

---

## 2. Diagrama Infográfico de Evidencia Científica

**Plataforma sugerida**: Midjourney / Canva Magic Studio
**Prompt**:
> `Clean modern medical infographic layout, vector diagram showing scientific evidence hierarchy from clinical trials to meta-analysis, dark navy background with cyan and purple gradient accents, minimalist design, UI/UX dashboard style --ar 16:9`

---

## 3. Esquema Anatómico / Diagnóstico por Imagen

**Plataforma sugerida**: DALL-E 3 / Nanobanana
**Prompt**:
> `3D medical illustration of prostate gland cross section with high-resolution multiparametric MRI lesion highlighting, professional medical textbook quality, ultra-detailed tissue texture, isolated on dark background, clear lighting, no text`

---

## 4. Diapositiva de Conclusiones y Resumen Clínico

**Plataforma sugerida**: Canva Magic / DALL-E 3
**Prompt**:
> `Abstract medical technology graphic representing clinical decision support system, glowing digital brain integrated with stethoscope and DNA helix, professional medical conference poster style, deep blue and electric teal color palette --ar 16:9`
""")

    return "\n".join(prompts_doc)


def generate_advanced_presentation_artifacts(expediente_dir: str, encargo: dict, plan: dict, resultado_final: str, valid_identifiers: list[str]) -> tuple[str, str]:
    """Genera la presentación Marp y los prompts visuales dentro de la carpeta del expediente."""
    marp_content = generate_marp_presentation(encargo, plan, resultado_final, valid_identifiers)
    marp_path = f"{expediente_dir}/09-presentacion-diapositivas.md"
    with open(marp_path, "w", encoding="utf-8") as f:
        f.write(marp_content)

    prompts_content = generate_visual_prompts(encargo, plan)
    prompts_path = f"{expediente_dir}/10-prompts-visuales-ia.md"
    with open(prompts_path, "w", encoding="utf-8") as f:
        f.write(prompts_content)

    return marp_path, prompts_path
