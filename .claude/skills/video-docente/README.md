# video-docente

Motor de microvídeos docentes: un guion JSON se convierte en MP4 y subtítulos SRT.

- **Determinista.** Cada fotograma es función pura del tiempo (`seek(t)` en `motor/engine.js`):
  sin timers ni aleatoriedad, así que dos renders son idénticos.
- **Plantillas de escena docentes.** Título, lista, mensajes clave, tabla, barras, cifra,
  pasos, imagen y referencias. La maquetación ajusta el tamaño del texto al espacio
  disponible sin bajar del mínimo legible.
- **Auditoría automática.** Detecta texto que no cabe, contraste insuficiente,
  sobrecarga de la escena, tiempos de lectura insuficientes y narración redundante.
- **Marcas.** Colores, tipografías, sello y cabecera fija definidos en `marcas/<nombre>/`.
  Incluye la marca de drdominguezesteban.com.
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
node tools/video.mjs previa  ejemplos/gleason-isup-marca.json --formato ambos   # con marca
```

En Claude Code, `/video-docente` lleva el flujo completo: encargo, contenido verificado,
guion, revisión, hoja de contactos con tu visto bueno, render y verificación.

## Estudio web

`estudio/plantilla.html` es una página autocontenida con el mismo motor: encargo a Claude,
editor del guion, vista previa con transporte, auditoría y exportación (MP4 codificado en
el navegador con WebCodecs, hoja de contactos, subtítulos y guion). Para regenerarla tras
cambiar el motor, las marcas o el ejemplo:

```bash
node tools/construir-estudio.mjs   # escribe estudio/dist/estudio.html
```

Después se vuelve a publicar como artefacto en la misma URL.

## Estructura

```
SKILL.md            flujo y esquema del guion (lo lee Claude)
motor/engine.html   página de render
motor/engine.js     plantillas, animación (muelles), auditoría y hoja de contactos
motor/fuentes/      Inter (SIL OFL 1.1), fuente de respaldo
marcas/             identidades visuales (marca.json + fuentes)
tools/video.mjs     CLI: validación, Playwright y ffmpeg
tools/construir-estudio.mjs  genera el estudio web
estudio/            plantilla del estudio web (dist/ se genera)
ejemplos/           guiones de ejemplo con datos verificados
```

## Limitaciones conocidas

- No genera voz ni música. Se puede añadir una pista con `--audio`; el ritmo de cada
  escena se calcula por lectura, no por la duración del audio.
- Los subtítulos se cortan por frases y comas; con frases largas sin puntuación, el corte
  puede caer en un sitio mejorable.
- No hay animación libre (anatomía, instrumental): solo plantillas.
- La marca usa un sello vectorial con iniciales; todavía no admite un logotipo en imagen.
