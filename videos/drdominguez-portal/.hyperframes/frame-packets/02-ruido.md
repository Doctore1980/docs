# Frame packet: 02-ruido

## Project inputs

- Project: /home/user/docs/videos/drdominguez-portal
- Design tokens: /home/user/docs/videos/drdominguez-portal/frame.md
- RULES_DIR: /home/user/docs/.agents/skills/hyperframes-animation/rules

## Assigned storyboard block

## Frame 2 — El ruido

- type: pain_point
- duration: 4.5s
- poster: 3.5s
- transition_in: cut
- status: outline
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
