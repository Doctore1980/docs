---
format: 1920x1080
duration: 30s
message: "Información urológica clara y basada en evidencia para entender lo que te pasa y decidir con calma"
arc: BAB — before (ruido) → bridge (la web) → after (evidencia y calma) → marca
audience: "Pacientes y público general; en LinkedIn también colegas"
mode: collaborative
music: none
language: es
additional_formats: ["1080x1080 (LinkedIn, adaptación tras aprobar el máster 16:9)"]
---

<!-- Vídeo silencioso: sin SCRIPT.md, music: none, sin sfx. Todo el mensaje va en texto en pantalla (`onscreen`). -->

## Frame 1 — La búsqueda

- type: hook
- blueprint: typewriter-reveal
- duration: 4.5s
- poster: 3.8s
- transition_in: cut
- status: outline
- scene: Una barra de búsqueda genérica sobre papel crema; alguien teclea su miedo
- onscreen: "psa alto es cancer" → borra «alto es cancer» → «6 es cáncer?»
- asset_candidates: none (barra de búsqueda genérica reconstruida; nunca la interfaz de Google)
- src: compositions/frames/01-busqueda.html

Gancho: el pensamiento real de un paciente con un análisis en la mano, tecleado y corregido como lo haría una persona. Sin marca todavía. La barra es neutra (sin logotipos de buscadores).

## Frame 2 — El ruido

- type: pain_point
- blueprint: overwhelm-surround
- duration: 4.5s
- poster: 3.5s
- transition_in: cut
- status: outline
- scene: Titulares alarmistas genéricos se acumulan alrededor de la barra, desenfocados, cerrándose
- onscreen: «PSA alto: lo que nadie te cuenta» · «Síntomas que no debes ignorar» · «Foro: me salió un 6,2 y estoy aterrado» · «10 señales de alarma» · «¿Es demasiado tarde?»
- asset_candidates: none (tarjetas genéricas inventadas; sin cabeceras ni logos de medios reales)
- src: compositions/frames/02-ruido.html

Agitación: el exceso de información sin fuente. Los titulares son deliberadamente genéricos y ficticios; el desenfoque y la densidad comunican ansiedad, no contenido.

## Frame 3 — La respuesta

- type: product_intro
- blueprint: constellation-hub
- duration: 6s
- poster: 4.5s
- transition_in: cut
- status: outline
- scene: Los titulares colapsan hacia el centro y de ahí sale la ficha real de la web sobre PSA alto, con un push-in lento
- onscreen: (captura) «¿Te han dicho que tienes el PSA alto?» · «Un PSA alto es un hallazgo frecuente y no significa que tengas cáncer.»
- asset_candidates: capture/screenshots/scroll-019.png (sección PSA de la web), capture/screenshots/scroll-006.png (FAQ «Me han dado un PSA alto. ¿Tengo cáncer?», alternativa)
- src: compositions/frames/03-respuesta.html

Puente: el ruido se ordena en una sola respuesta clara, la de tu portal. Primera aparición del producto; captura real, sin reconstruir la página.

## Frame 4 — La nota al pie

- type: feature_showcase
- blueprint: kinetic-type-beats
- duration: 7s
- poster: 5.5s
- transition_in: crossfade
- status: outline
- scene: Una frase editorial con superíndice; el «¹» se despliega en su referencia
- onscreen: «El PSA elevado no siempre significa cáncer.¹» → «¹ EAU Guidelines on Prostate Cancer, 2026 · §5.2.2» → «Cada texto cita guías y fuentes.»
- asset_candidates: none (tipografía pura: Newsreader + IBM Plex Mono)
- src: compositions/frames/04-nota-al-pie.html

El corazón del vídeo: la evidencia se ve literalmente. «no siempre» en cursiva terracota (como los acentos de la web). Afirmación verificada contra EAU 2026 §5.2.2 («organ-specific but not cancer-specific»); pendiente de validación del autor.

## Frame 5 — La calma

- type: benefit_highlight
- blueprint: titlecard-reveal
- duration: 4s
- poster: 3s
- transition_in: crossfade
- status: outline
- scene: Pantalla limpia y cálida; una sola pregunta con mucho aire
- onscreen: «¿Qué te preocupa?» (con «preocupa» en cursiva terracota) · sub: «Para entender lo que te pasa y decidir con calma.»
- asset_candidates: none
- src: compositions/frames/05-calma.html

Respiro: el tono cambia de ansiedad a calma. Es la misma pregunta con la que se abre la web.

## Frame 6 — Cierre

- type: branding
- blueprint: logo-assemble-lockup
- duration: 4.5s
- poster: 3.8s
- transition_in: cut
- status: outline
- scene: El monograma «D» se dibuja y se fija con el lema, nombre, cargo y URL
- onscreen: «Urología con evidencia» · «Dr. Mario Domínguez Esteban» · «Jefe de Sección de Uro-Oncología · Hospital Universitario Marqués de Valdecilla» · «drdominguezesteban.com»
- asset_candidates: capture/assets/favicon.svg (monograma «D», círculo navy)
- src: compositions/frames/06-cierre.html

Marca y destino. En 1:1 este frame se parte en dos tiempos: (a) lema + URL; (b) nombre + cargo abreviado.
