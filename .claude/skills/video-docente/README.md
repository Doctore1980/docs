# video-docente

Motor de microvídeos docentes: un guion JSON se convierte en MP4 y subtítulos SRT.

- **Determinista.** Cada fotograma es función pura del tiempo (`seek(t)` en `motor/engine.js`):
  sin timers ni aleatoriedad, así que dos renders son idénticos.
- **Plantillas de escena docentes.** Título, lista, mensajes clave, tabla, barras, cifra,
  pasos, imagen y referencias. La maquetación ajusta el tamaño del texto al espacio
  disponible sin bajar del mínimo legible.
- **Auditoría automática.** Detecta texto que no cabe, contraste insuficiente,
  sobrecarga de la escena, tiempos de lectura insuficientes y narración redundante.
- **Dos formatos.** 16:9 (clase, campus virtual) y 9:16 (móvil, con zonas seguras para las
  interfaces de las redes).

## Instalación

Requiere Node 18+ y ffmpeg (en macOS, `brew install node ffmpeg`).

```bash
cd .claude/skills/video-docente
npm install
npx playwright install chromium
```

## Uso

```bash
node tools/video.mjs revisar ejemplos/gleason-isup.json
node tools/video.mjs previa  ejemplos/gleason-isup.json --formato ambos
node tools/video.mjs render  ejemplos/gleason-isup.json --formato 16:9 [--audio voz.m4a] [--fps 30]
```

En Claude Code, `/video-docente` lleva el flujo completo: encargo, contenido verificado,
guion, revisión, hoja de contactos con tu visto bueno, render y verificación.

## Estructura

```
SKILL.md            flujo y esquema del guion (lo lee Claude)
motor/engine.html   página de render
motor/engine.js     plantillas, animación (muelles), auditoría y hoja de contactos
motor/fuentes/      Inter (SIL OFL 1.1)
tools/video.mjs     CLI: validación, Playwright y ffmpeg
ejemplos/           guiones de ejemplo con datos verificados
```

## Limitaciones conocidas

- No genera voz ni música. Se puede añadir una pista con `--audio`; el ritmo de cada
  escena se calcula por lectura, no por la duración del audio.
- Los subtítulos se cortan por frases y comas; con frases largas sin puntuación, el corte
  puede caer en un sitio mejorable.
- No hay animación libre (anatomía, instrumental): solo plantillas.
