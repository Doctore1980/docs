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

## Video direction

- **Palette (de `frame.md`, por rol):** fondo `cream` #FAF8F4 en todo el vídeo; texto `ink` #0E2240; superficies secundarias `tile` #F2EEE6; acento `coral` #C2412A **escaso** — solo palabras clave en cursiva (como la web: «*preocupa*», «*no siempre*») y el superíndice «¹». Frames 1–2 son la única excepción tonal: el ruido usa ink al 30–60 % de opacidad y desenfoque, nunca colores nuevos ni rojos de alarma.
- **Tipografía por rol:** display/headline = Newsreader (serif, cursiva para el acento); interfaz de búsqueda y tarjetas de ruido = IBM Plex Sans; referencias, URL y etiquetas = IBM Plex Mono.
- **Gramática de movimiento:** curvas de cola larga (`power3` por defecto, suave antes que elástico). Sin narración: las revelaciones se ritman con la **lectura** del texto en pantalla — cada pieza entra cuando la anterior ya se ha podido leer (≈ 2,5 palabras/s), nunca todo a t=0.
- **Ritmo:** F1–F2 tensión creciente (densidad, acumulación); F3 el giro (colapso + respuesta); F4 clímax tipográfico; **F5 es el frame de respiro deliberadamente quieto**; F6 cierre con un único gesto (dibujo del monograma) y hold final.
- **Lista negativa:** nada de interfaz o logos de Google ni cabeceras de medios reales; nada de bata/quirófano/robot/stock médico; nada de gradientes «IA», bokeh flotante, sombras pesadas ni rojos de alarma; ningún modo fallido — ni **slideshow** (cargar todo y congelar) ni **salvapantallas** (todo flotando por su cuenta). Contenido importante dentro del 83 % superior.

<!-- Vídeo silencioso: sin SCRIPT.md, music: none, sin sfx. Todo el mensaje va en texto en pantalla (`onscreen`). -->

## Frame 1 — La búsqueda

- type: hook
- duration: 4.5s
- poster: 3.8s
- transition_in: cut
- status: animated
- scene: Una barra de búsqueda genérica sobre papel crema; alguien teclea su miedo
- onscreen: "psa alto es cancer" → borra «alto es cancer» → «6 es cáncer?»
- asset_candidates: (ninguno — barra de búsqueda genérica reconstruida en HTML, nunca la interfaz de Google)
- src: compositions/frames/01-busqueda.html
- blueprint: typewriter-reveal (Adapt)
- focal: barra de búsqueda genérica (reconstruida)
- roles: barra = focal · fondo crema = background

Adapt: se conserva el motor «alguien está tecleando» con edición a mitad de línea; no hay payoff de marca aquí (lo hereda F2 por corte).
Scene 1 (0.0–0.6s): papel crema vacío; una barra de búsqueda redondeada (hairline ink@20 %, icono de lupa en Plex Sans) aparece con un slide-up corto — centrada, ~55 % del ancho, en el tercio superior-medio. Caret parpadeando.
Scene 2 (0.6–2.4s): type-on con caret: «psa alto es cancer» carácter a carácter con ritmo humano irregular (Plex Sans, tamaño lead grande).
Scene 3 (2.4–3.4s): backspace-and-retype: borra «alto es cancer» y teclea «6 es cáncer?».
Scene 4 (3.4–4.5s): la consulta queda escrita; hold quieto con el caret parpadeando. Push-in muy lento de la cámara hacia la barra (prepara la invasión de F2).
- handoff_out: barra de búsqueda — centro x 960, y 430; scale 1.06; opacity 1; texto «psa 6 es cáncer?»; push-in lento continuo hacia el centro.

Gancho: el pensamiento real de un paciente con un análisis en la mano, tecleado y corregido como lo haría una persona. Sin marca todavía. La barra es neutra (sin logotipos de buscadores).

## Frame 2 — El ruido

- type: pain_point
- duration: 4.5s
- poster: 3.5s
- transition_in: cut
- status: animated
- scene: Titulares alarmistas genéricos se acumulan alrededor de la barra, desenfocados, cerrándose
- onscreen: «PSA alto: lo que nadie te cuenta» · «Síntomas que no debes ignorar» · «Foro: me salió un 6,2 y estoy aterrado» · «10 señales de alarma» · «¿Es demasiado tarde?»
- asset_candidates: (ninguno — tarjetas genéricas inventadas en HTML, sin cabeceras ni logos de medios reales)
- src: compositions/frames/02-ruido.html
- blueprint: compose (de overwhelm-surround: acumulación + cerco, sin el morph a avatar)
- focal: la barra de búsqueda (heredada de F1)
- roles: barra = focal · tarjetas de titulares = supporting · fondo crema = background

Compose: la claustrofobia viene de estar rodeado, no de un zoom; la barra no se mueve.
- handoff_in: barra de búsqueda — centro x 960, y 430; scale 1.06; opacity 1; texto «psa 6 es cáncer?»; push-in lento continuo.
Scene 1 (0.0–1.2s): la barra sigue en su sitio. Entran las dos primeras tarjetas de titular (blanco, hairline, Plex Sans) a izquierda y derecha, ligeramente rotadas, con desenfoque de fondo: «PSA alto: lo que nadie te cuenta», «Síntomas que no debes ignorar».
Scene 2 (1.2–2.8s): entran tres más en cascada desde los bordes, superponiéndose en capas de profundidad (cerca nítido / lejos desenfocado): «Foro: me salió un 6,2 y estoy aterrado», «10 señales de alarma», «¿Es demasiado tarde?».
Scene 3 (2.8–4.5s): todas las tarjetas se cierran desde todos los lados hacia la barra (entrada radial escalonada) y se duplican en fragmentos más pequeños y borrosos hasta casi taparla; la barra permanece. Hold sobre el estado saturado.
- handoff_out: nube de tarjetas apiñada alrededor de la barra — centro x 960, y 430; scale 1; opacity 1; barra casi oculta.

Agitación: el exceso de información sin fuente. Los titulares son deliberadamente genéricos y ficticios; el desenfoque y la densidad comunican ansiedad, no contenido.

## Frame 3 — La respuesta

- type: product_intro
- duration: 6s
- poster: 4.5s
- transition_in: cut
- status: animated
- scene: Los titulares colapsan hacia el centro y de ahí sale la ficha real de la web sobre PSA alto, con un push-in lento
- onscreen: (captura) «¿Te han dicho que tienes el PSA alto?» · «Un PSA alto es un hallazgo frecuente y no significa que tengas cáncer.»
- asset_candidates: assets/scroll-019.png — sección PSA real de la web («¿Te han dicho que tienes el PSA alto?»)
- src: compositions/frames/03-respuesta.html
- blueprint: constellation-hub (Adapt)
- focal: assets/scroll-019.png
- roles: scroll-019 = focal (sección PSA real, encuadre en el titular y el primer párrafo) · fondo crema = background

Adapt: se conserva el colapso del anillo sobre el núcleo; los «nodos» son las tarjetas de ruido de F2 y el núcleo revela la captura real en vez de una demo.
- handoff_in: nube de tarjetas apiñada alrededor de la barra — centro x 960, y 430; scale 1; opacity 1.
Scene 1 (0.0–1.4s): las tarjetas COLAPSAN hacia el centro en un solo gesto (cluster → punto), perdiendo opacidad mientras convergen; la barra se encoge con ellas. Signature move.
Scene 2 (1.4–3.2s): del punto central se expande una tarjeta con la captura real de la sección PSA (esquinas radius-lg, sombra card), ~70 % del ancho, centrada; se lee «¿Te han dicho que tienes el *PSA alto*?».
Scene 3 (3.2–6.0s): push-in lento (zoom-to-target) hacia el titular y la primera línea «Un PSA alto es un hallazgo frecuente y no significa que tengas cáncer.»; termina quieto sobre esa línea. Captura sin reconstruir ni retocar.

Puente: el ruido se ordena en una sola respuesta clara, la de tu portal. Primera aparición del producto; captura real, sin reconstruir la página.

## Frame 4 — La nota al pie

- type: feature_showcase
- duration: 7s
- poster: 5.5s
- transition_in: crossfade
- status: animated
- scene: Una frase editorial con superíndice; el «¹» se despliega en su referencia
- onscreen: «El PSA elevado no siempre significa cáncer.¹» → «¹ EAU Guidelines on Prostate Cancer, 2026 · §5.2.2» → «Cada texto cita guías y fuentes.»
- asset_candidates: (ninguno — tipografía pura: Newsreader + IBM Plex Mono)
- src: compositions/frames/04-nota-al-pie.html
- blueprint: kinetic-type-beats (Adapt)
- focal: la frase con superíndice (tipografía)
- roles: frase = focal · referencia = supporting · fondo crema = background

Adapt: se conserva «el movimiento son las palabras»; en lugar de swaps rápidos, la frase se construye por bloques y el superíndice se DESPLIEGA en su referencia (signature propio de este vídeo).
Scene 1 (0.0–2.0s): fondo crema limpio. Per-word staggered reveal de «El PSA elevado *no siempre* significa cáncer.» en Newsreader display, centrado-izquierda (asimétrico 70/30), tercio superior; «no siempre» en cursiva coral.
Scene 2 (2.0–2.8s): aparece el superíndice «¹» en coral con un pequeño pulso de escala; hold de lectura.
Scene 3 (2.8–4.8s): el «¹» se desplaza y se ABRE en una línea de referencia bajo la frase, separada por un hairline: «¹ EAU Guidelines on Prostate Cancer, 2026 · §5.2.2» en Plex Mono, que se escribe con una línea que se dibuja de izquierda a derecha (SVG self-draw del hairline + type-on de la referencia).
Scene 4 (4.8–7.0s): debajo, en Plex Sans lead, entra «Cada texto cita guías y fuentes.»; todo se mantiene quieto y legible hasta el final.

El corazón del vídeo: la evidencia se ve literalmente. «no siempre» en cursiva terracota (como los acentos de la web). Afirmación verificada contra EAU 2026 §5.2.2 («organ-specific but not cancer-specific»); pendiente de validación del autor.

## Frame 5 — La calma

- type: benefit_highlight
- duration: 4s
- poster: 3s
- transition_in: crossfade
- status: animated
- scene: Pantalla limpia y cálida; una sola pregunta con mucho aire
- onscreen: «¿Qué te preocupa?» (con «preocupa» en cursiva terracota) · sub: «Para entender lo que te pasa y decidir con calma.»
- asset_candidates: (ninguno — tipografía pura)
- src: compositions/frames/05-calma.html
- blueprint: titlecard-reveal (Reproduce)
- focal: «¿Qué te preocupa?»
- roles: título = focal · subtítulo = supporting · fondo crema = background

Scene 1 (0.0–1.4s): slide-up + crossfade suave de «¿Qué te *preocupa*?» en Newsreader display-cover, centrado; «preocupa» en cursiva coral. Mucho aire alrededor.
Scene 2 (1.4–2.4s): entra el subtítulo en Plex Sans lead, ink al 70 %: «Para entender lo que te pasa y decidir con calma.»
Scene 3 (2.4–4.0s): hold totalmente quieto (frame de respiro).

Respiro: el tono cambia de ansiedad a calma. Es la misma pregunta con la que se abre la web.

## Frame 6 — Cierre

- type: branding
- duration: 4.5s
- poster: 3.8s
- transition_in: cut
- status: animated
- scene: El monograma «D» se dibuja y se fija con el lema, nombre, cargo y URL
- onscreen: «Urología con evidencia» · «Dr. Mario Domínguez Esteban» · «Jefe de Sección de Uro-Oncología · Hospital Universitario Marqués de Valdecilla» · «drdominguezesteban.com»
- asset_candidates: assets/favicon.svg — monograma «D» (círculo navy, D crema)
- src: compositions/frames/06-cierre.html
- blueprint: logo-assemble-lockup (Adapt — variante Brand_Outro)
- focal: assets/favicon.svg
- roles: favicon = focal (monograma «D» círculo navy) · fondo crema = background

Adapt: Brand_Outro — la marca se dibuja y el wordmark se revela al lado; sin push-through (sería demasiado enérgico para el tono).
Scene 1 (0.0–1.2s): el círculo del monograma se dibuja (SVG self-draw del contorno) y se rellena navy; la «D» crema aparece dentro. Centro-izquierda.
Scene 2 (1.2–2.4s): a su derecha se revela «Urología con evidencia» en Newsreader headline (con «evidencia» en cursiva coral) y debajo «Dr. Mario Domínguez Esteban» en Plex Sans card-title.
Scene 3 (2.4–3.4s): entra la línea de cargo en Plex Sans body, ink al 70 %: «Jefe de Sección de Uro-Oncología · Hospital Universitario Marqués de Valdecilla».
Scene 4 (3.4–4.5s): la URL «drdominguezesteban.com» se revela con un wipe izquierda→derecha con borde coral, en Plex Mono, bajo un hairline; hold final y fade a crema en los últimos 0,4 s.

Marca y destino. En 1:1 este frame se parte en dos tiempos: (a) lema + URL; (b) nombre + cargo abreviado.
