# mejorar-prompt

Mod de Claude Code que reescribe el borrador de tu prompt antes de enviarlo. Hay tres modos:

- **General**: objetivo, contexto, entregable, formato y criterios de éxito.
- **Creativo**: audiencia, tono, formato, alternativas y lo que se debe evitar.
- **Científico**: pregunta PICO cuando procede, jerarquía de fuentes (guías EAU/AUA/NCCN/ESMO, RS/MA, ensayos), sin referencias inventadas, IC 95 % y nivel de evidencia.

El prompt mejorado sustituye al borrador en la caja de texto, pero **no se envía**: lo revisas y lo envías tú. Nunca inventa datos: lo que falte aparece como `[COMPLETAR: …]`, y los datos que parezcan identificar a pacientes se sustituyen por marcadores.

## Uso

- **Botones**: escribe el borrador y pulsa **General**, **Creativo** o **Científico** en la barra «Mejorar prompt», encima de la caja de texto. **↶ Deshacer** recupera el original y **×** oculta la barra.
- **Comando**: `/mejorar cientifico <texto>`, `/mejorar creativo <texto>` o `/mejorar <texto>` (modo general). `/mejorar deshacer` restaura el original, `/mejorar mostrar` vuelve a enseñar la barra y `/mejorar` sin argumentos muestra la ayuda.

## Instalación

En una sesión de Claude Code en el terminal:

```
/plugin install mejorar-prompt --marketplace doctore1980/docs
```

Responde `y` para añadir el catálogo y elige el ámbito de usuario. Desde un shell: `claude plugin install mejorar-prompt --marketplace doctore1980/docs`. En la app de escritorio: **+** junto a la caja de texto, luego **Plugins**, **Add marketplace** con `doctore1980/docs` y después **Add plugin**.

Si el repositorio es privado, tu ordenador necesita una credencial de GitHub configurada (clave SSH, o `gh auth login` seguido de `gh auth setup-git`).

## Ajustes

El modelo que reescribe se define en `hooks/register.tsx` (`MODELO = 'sonnet'`). Cámbialo a `'opus'` si quieres más calidad o a `'haiku'` si prefieres más rapidez. Cada mejora consume una llamada al modelo con tus credenciales.

Solo funciona en Claude Code (terminal, escritorio, VS Code), no en el chat web de claude.ai.
