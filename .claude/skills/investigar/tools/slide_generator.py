"""
Generador de Presentaciones Marp/Reveal.js y Prompts Visuales IA -- Fase 2 Avanzada
Transforma informes de investigación en guiones de diapositivas y prompts de imagen para IA generativa.
"""

import os
import json
import re


LINEAS_POR_DIAPOSITIVA = 12


def generate_marp_presentation(encargo: dict, plan: dict, resultado_final: str, valid_identifiers: list[str],
                               fuentes: list[str] | None = None) -> str:
    """Construye un documento Markdown compatible con Marp / Slidev / Reveal.js."""
    pregunta = encargo.get("pregunta", "Informe de Investigación")
    nivel = plan.get("nivel", "medio")

    slides = []

    # Slide 1: Portada
    slides.append(f"""---
marp: true
theme: default
paginate: true
header: "investigacion-agentica | Evidencia verificada"
footer: "{len(valid_identifiers)} referencias verificadas (existencia y retractación)"
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
    # Solo las fuentes que de verdad respondieron (campo `fuentes` de la busqueda).
    fuentes_txt = ", ".join(fuentes) if fuentes else "ver `_candidatos-brutos/` del expediente"
    slides.append(f"""## 📌 Objetivos y Resumen de la Evidencia

- **Propósito**: Evaluación crítica de la literatura científica disponible.
- **Fuentes Consultadas**: {fuentes_txt}.
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
        cuerpo = lines[1:]
        # Una seccion larga se reparte en varias diapositivas en vez de recortarse.
        trozos = [cuerpo[j:j + LINEAS_POR_DIAPOSITIVA]
                  for j in range(0, len(cuerpo), LINEAS_POR_DIAPOSITIVA)] or [[]]
        for k, trozo in enumerate(trozos):
            sufijo = f" ({k + 1}/{len(trozos)})" if len(trozos) > 1 else ""
            body = "\n".join(trozo)
            slides.append(f"""## 📊 {title}{sufijo}

{body}

---
""")

    # Slide Final: Referencias Verificadas
    ref_list = "\n".join([f"- `{ident}`" for ident in valid_identifiers])
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

    # Plantillas neutras: el tema lo pone la pregunta, no una especialidad fija.
    # Revisa y concreta cada prompt con la anatomia/tecnica del encargo.
    prompts_doc.append(f"""## 1. Banner Principal / Portada de la Ponencia

**Plataforma sugerida**: Midjourney v6 / DALL-E 3
**Prompt**:
> `Cinematic photorealistic medical conference banner illustrating: "{pregunta}", clean scientific aesthetic, dark navy background, volumetric lighting, no text --ar 16:9 --v 6.0`

---

## 2. Diagrama Infográfico de Evidencia Científica

**Plataforma sugerida**: Midjourney / Canva Magic Studio
**Prompt**:
> `Clean modern medical infographic layout, vector diagram showing scientific evidence hierarchy from clinical trials to meta-analysis, dark navy background with cyan and purple gradient accents, minimalist design --ar 16:9`

---

## 3. Esquema Anatómico / Mecanismo

**Plataforma sugerida**: DALL-E 3 / Nanobanana
**Prompt**:
> `3D medical illustration of the anatomy or mechanism involved in: "{pregunta}", professional medical textbook quality, isolated on dark background, clear lighting, no text`

---

## 4. Diapositiva de Conclusiones y Resumen Clínico

**Plataforma sugerida**: Canva Magic / DALL-E 3
**Prompt**:
> `Abstract medical graphic summarizing clinical evidence and decision-making, professional conference slide style, deep blue and teal palette, no text --ar 16:9`
""")

    return "\n".join(prompts_doc)


def generate_advanced_presentation_artifacts(expediente_dir: str, encargo: dict, plan: dict, resultado_final: str,
                                             valid_identifiers: list[str],
                                             fuentes: list[str] | None = None) -> tuple[str, str]:
    """Genera la presentación Marp y los prompts visuales dentro de la carpeta del expediente.

    `fuentes`: fuentes de busqueda que respondieron (campo `fuentes` de `search`).
    """
    marp_content = generate_marp_presentation(encargo, plan, resultado_final, valid_identifiers, fuentes)
    marp_path = f"{expediente_dir}/09-presentacion-diapositivas.md"
    with open(marp_path, "w", encoding="utf-8") as f:
        f.write(marp_content)

    prompts_content = generate_visual_prompts(encargo, plan)
    prompts_path = f"{expediente_dir}/10-prompts-visuales-ia.md"
    with open(prompts_path, "w", encoding="utf-8") as f:
        f.write(prompts_content)

    return marp_path, prompts_path
