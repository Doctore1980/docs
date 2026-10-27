---
name: video-docente
description: 'Microvídeos docentes a partir de un guion JSON: escenas de título, lista, tabla, barras, cifra clave, diagrama de pasos, imagen, mensajes clave y referencias, con subtítulos de narración, en 16:9 y 9:16. Renderizado determinista (MP4 H.264 + SRT) con auditoría automática de legibilidad, carga cognitiva y tiempos de lectura. Activar con /video-docente o cuando el usuario pida "haz un vídeo docente/explicativo sobre…", "convierte esta clase/estas diapositivas en vídeo", "microvídeo para residentes/alumnos/pacientes". No usar para editar vídeo grabado (quirúrgico, consulta) ni para animación anatómica compleja.'
---

# /video-docente: microvídeos docentes con renderizado determinista

Tú escribes el guion en JSON y el motor lo convierte en vídeo. El motor maqueta, anima y
audita; tú decides el contenido, el orden y el ritmo. Si la auditoría marca un error,
corrige el guion: no lo fuerces con `--forzar` salvo petición expresa del usuario.

`SKILL_DIR` es el directorio de este fichero. La CLI es `node SKILL_DIR/tools/video.mjs`.

## Entorno

- Node 18+, `ffmpeg` y Playwright con Chromium. Si `require('playwright')` falla desde
  `SKILL_DIR`, ejecuta `npm install && npx playwright install chromium` en `SKILL_DIR`.
- Proyectos del usuario: `./videos-docentes/<slug>/guion.json`. La salida va a
  `./videos-docentes/<slug>/salida/`.
- Las fuentes (Inter, OFL) van incluidas en `motor/fuentes/`, así que el render no
  depende de las fuentes del sistema.

## Flujo con puertas

1. **Encargo.** Fija un único objetivo de aprendizaje ("al terminar, el residente sabe…"),
   la audiencia (alumnos, residentes, pacientes), el formato (16:9 para clase o campus,
   9:16 para móvil o redes), la duración objetivo (por defecto 60–120 s) y las fuentes.
   Pregunta solo lo que falte y cambie el resultado.
2. **Contenido verificado.** Cada cifra o afirmación clínica lleva su fuente
   comprobable (guía, ensayo o RS/MA), verificada con PubMed u otra herramienta específica.
   Para temas amplios, usa antes `/investigar`. Lo que no verifiques no entra en
   pantalla. Cierra con una escena `referencias` en formato Vancouver.
3. **Guion.** Escribe `guion.json` siguiendo el esquema de abajo. Una idea por escena.
4. **Revisar.** Ejecuta `node SKILL_DIR/tools/video.mjs revisar guion.json`. Repite hasta
   que no haya errores y decide, uno a uno, si cada aviso se corrige o se justifica.
5. **Previa.** Ejecuta `node SKILL_DIR/tools/video.mjs previa guion.json --formato ambos`.
   Abre la hoja de contactos con Read y compruébala con esta lista, no con una nota global:
   - ¿Se entiende cada escena sin narración?
   - ¿Hay huecos grandes o elementos apiñados?
   - ¿Lo destacado es lo que el objetivo de aprendizaje necesita?
   - ¿El orden construye el razonamiento?

   Haz como mucho dos rondas de corrección. Después **enseña la hoja al usuario y espera
   su visto bueno** antes del render.
6. **Render.** Ejecuta `node SKILL_DIR/tools/video.mjs render guion.json [--formato …] [--audio pista.m4a]`.
   El resultado es un MP4 (H.264, yuv420p, 30 fps) y, si hay narración, un `.srt`.
7. **Verificar.** Comprueba duración y resolución con `ffprobe`. Extrae una tira de
   fotogramas intermedios (en revelaciones y en cambios de escena) y mírala: la hoja de
   contactos solo muestra estados finales, no movimiento ni subtítulos.
8. **Entregar.** Entrega el vídeo, el `.srt` y el `guion.json`. Indica qué has comprobado
   y qué no; por ejemplo, el audio no se revisa automáticamente.

## Esquema del guion

Campos globales, todos opcionales:

- `marca`: nombre de una carpeta de `SKILL_DIR/marcas/` (por ejemplo
  `"drdominguezesteban"`) o ruta a un `marca.json`. Aplica colores, tipografías, sello,
  cabecera fija y escena de cierre. **Úsala por defecto en los vídeos del usuario.**
- `formato`: `"16:9"` o `"9:16"`.
- `ritmo`: `"pausado"`, `"normal"` o `"rapido"` (2,0 / 2,5 / 3,2 palabras por segundo).
- `pie`: rótulo discreto superior, por ejemplo el curso o la sección. Con marca, va a la
  derecha de la cabecera fija y se omite si no cabe (habitual en 9:16).
- `progreso`: `false` oculta la barra de progreso.
- `tema`: `{ "base": "claro" | "oscuro", "colores": { "acento": "#…" } }`. Con marca,
  `base` elige su variante clara u oscura. La auditoría rechaza el texto con contraste
  inferior a 4,5:1.

Cada escena lleva `tipo`. Además admite, de forma opcional:

- `narracion`: texto que se muestra como subtítulo y marca el ritmo de la escena.
- `duracion`: segundos; sustituye al cálculo automático de lectura.
- `antetitulo`: rótulo breve en versalitas monoespaciadas encima del título, por ejemplo
  el área o la fuente de los datos.

En cualquier texto, `*palabras*` marca énfasis: cursiva y color de acento en los titulares
de la marca, y seminegrita en el texto corrido. Úsalo con moderación: una o dos palabras
por titular, como en la web.

| tipo | campos | notas |
|---|---|---|
| `titulo` | `titulo`, `subtitulo?`, `autor?` | portada |
| `puntos` | `titulo?`, `puntos[]` | se revelan al ritmo de lectura; 6 como máximo |
| `mensaje` | `titulo?`, `puntos[]` | lista numerada; título por defecto "Mensajes clave" |
| `tabla` | `titulo?`, `columnas[]`, `filas[][]`, `destacar?` | `destacar`: filas en base 1 |
| `barras` | `titulo?`, `datos[{etiqueta, valor}]`, `unidad?`, `max?`, `destacar?`, `referencia?{valor, etiqueta}`, `fuente?` | barras horizontales con cifra animada |
| `cifra` | `valor`, `texto`, `titulo?`, `fuente?` | cifra grande; se anima si es numérica |
| `pasos` | `titulo?`, `pasos[]` | horizontal en 16:9 con ≤ 4 pasos; si no, vertical |
| `imagen` | `src`, `titulo?`, `credito` | ruta relativa al guion; png, jpg, webp o svg |
| `referencias` | `refs[]`, `titulo?` | Vancouver |
| `cierre` | `titulo?`, `subtitulo?`, `web?` | sello, nombre, lema y web de la marca; sin marca, exige `titulo` |

Hay dos ejemplos completos y verificados: `SKILL_DIR/ejemplos/gleason-isup.json`, sin
marca, y `SKILL_DIR/ejemplos/gleason-isup-marca.json`, con marca y cierre.

## Marcas

Cada marca es una carpeta en `SKILL_DIR/marcas/<nombre>/` con un `marca.json` y sus
fuentes, para que el render sea idéntico en cualquier equipo. El `marca.json` define:

- `nombre`, `lema`, `web` y `sello.texto`: iniciales del sello vectorial.
- `fuentes[]`: `familia`, `archivo` (woff2/otf/ttf), `peso` (`"400"` o rango `"300 700"`)
  y `estilo`.
- `estilos`: `titulo`, `cabecera`, `cifra`, `texto`, `fuerte` y `mono`. Cada uno lleva
  `familia`, `peso` y, de forma opcional, `cursiva` (el énfasis usa cursiva), `track`
  (espaciado en em) y `mayus`.
- `temas.claro` y `temas.oscuro`: `fondo`, `tinta`, `titular`, `suave`, `primario`,
  `acento`, `acentoTexto`, `relleno`, `linea` y `tenue`.

La marca `drdominguezesteban` se extrajo de la web del usuario: variables CSS de los modos
claro y oscuro, fuentes autoalojadas con licencia SIL OFL y sello «DE». Para crear otra
marca, parte de la web o del manual de identidad y comprueba la licencia de cada fuente
antes de incluirla. Los glifos que falten en las fuentes de la marca (por ejemplo `≤` o
`→`) se dibujan con Inter.

## Criterios pedagógicos que aplica la auditoría

Siguen los principios de aprendizaje multimedia: segmentación, señalización, coherencia
y redundancia.

- Una idea por escena; más de 55 palabras en pantalla genera un aviso.
- Como máximo 6 puntos por lista y 16 palabras por punto.
- La narración explica; no lee el texto en pantalla. Si lo repite casi literalmente,
  la auditoría avisa.
- Escenas de 45 s como máximo y vídeo total de 5 min como máximo; si se superan,
  conviene hacer varios microvídeos.
- El texto nunca baja del tamaño mínimo legible en móvil. Si no cabe, es un error:
  divide la escena.

## Privacidad y derechos

- Solo imágenes propias anonimizadas, sintéticas o con licencia que permita su uso.
  `credito` es obligatorio. Nunca uses imágenes clínicas con datos identificativos
  (caras, nombres, números de historia, fechas en DICOM).
- Música o voz solo si el usuario tiene los derechos. La voz sintética (por ejemplo,
  ElevenLabs) consume créditos del usuario: pide confirmación antes.
