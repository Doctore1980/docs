import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Modo } from '../types'

// Modelo que reescribe. 'sonnet' equilibra calidad y rapidez; cámbialo a 'opus'
// si prefieres más calidad en el modo científico, o a 'haiku' para más rapidez.
const MODELO = 'sonnet'
const LIMITE_MS = 90_000

const ocupado = atom({ plugin: 'mejorar-prompt', key: 'ocupado' } as const, null)
const original = atom({ plugin: 'mejorar-prompt', key: 'original' } as const, null)
const oculta = atom({ plugin: 'mejorar-prompt', key: 'oculta' } as const, false)

const ETIQUETA: Record<Modo, string> = {
  general: 'General',
  creativo: 'Creativo',
  cientifico: 'Científico',
}

const REGLAS_COMUNES = `Eres un editor de prompts. Recibes el BORRADOR de un prompt que una persona va a enviar a un asistente de IA y devuelves una versión mejorada de ese mismo prompt.

Reglas obligatorias:
- NO respondas al prompt ni ejecutes la tarea: solo reescríbelo.
- Conserva la intención, el idioma y el registro del borrador. Si está en español, responde en español.
- No inventes datos, cifras, resultados, nombres, referencias, DOI ni citas. Si falta información que cambiaría sustancialmente el resultado, inserta un marcador visible [COMPLETAR: qué falta] en lugar de suponerla.
- Si el borrador contiene datos que parezcan identificar a un paciente o a una persona privada (nombre, NHC, DNI, fecha de nacimiento, dirección, teléfono), sustitúyelos por marcadores genéricos como [PACIENTE], [EDAD], [FECHA].
- Mantén la longitud proporcional: un borrador de una línea no debe convertirse en una página. Añade solo lo que mejore el resultado.
- Escribe el prompt en segunda persona, dirigido al asistente, con instrucciones claras y verificables.
- Devuelve ÚNICAMENTE el prompt mejorado, sin preámbulos, sin comentarios, sin comillas ni bloques de código que lo envuelvan.`

const REGLAS_MODO: Record<Modo, string> = {
  general: `Modo GENERAL. Asegura, cuando aplique:
- Objetivo concreto y entregable esperado.
- Contexto mínimo necesario (quién lo usará y para qué).
- Formato de salida (lista, tabla, texto, archivo) y extensión aproximada.
- Criterios de éxito o restricciones relevantes.
- Que el asistente pregunte solo si falta algo crítico; si no, que declare sus supuestos.`,

  creativo: `Modo CREATIVO. Asegura, cuando aplique:
- Audiencia, propósito y canal (charla, redes sociales, cartel, relato, nombre, eslogan…).
- Tono y voz deseados, con uno o dos adjetivos precisos; referencias de estilo si el borrador las sugiere.
- Restricciones de formato (longitud, número de caracteres, estructura).
- Pedir varias alternativas diferenciadas (por defecto 3) en vez de una sola.
- Lo que debe evitarse (clichés, tecnicismos, tono comercial…).
- Libertad explícita para proponer enfoques inesperados, sin sacrificar la exactitud de los hechos.`,

  cientifico: `Modo CIENTÍFICO / CLÍNICO. Asegura, cuando aplique:
- Pregunta formulada con precisión; si es clínica, en formato PICO (población, intervención, comparador, desenlace) o el marco adecuado (diagnóstico, pronóstico, etiología).
- Nivel de rigor exigido y tipo de fuentes: guías clínicas (EAU, AUA, NCCN, ESMO) con versión y año, revisiones sistemáticas y metaanálisis, ensayos registrados y estudios originales revisados por pares, en ese orden de preferencia.
- Que distinga hechos comprobados, inferencias y opiniones; que indique nivel de evidencia y limitaciones.
- Que no invente referencias ni DOI y que enlace o cite las fuentes de las afirmaciones importantes (estilo Vancouver salvo que el borrador indique otro).
- Para estadística: estimaciones con IC 95 % y tamaño del efecto además del p-valor, supuestos del método y distinción entre análisis exploratorio y confirmatorio.
- Formato de salida (resumen estructurado, tabla, informe) y extensión.
- Que declare su grado de confianza y lo que no ha podido verificar.
- No añadas un PICO, estadística o guías si el borrador no trata de eso: aplica solo lo pertinente.`,
}

function leerModo(palabra: string): Modo | undefined {
  const p = palabra
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
  if (p === 'general' || p === 'g' || p === 'generico') return 'general'
  if (p === 'creativo' || p === 'c' || p === 'creativa') return 'creativo'
  if (p === 'cientifico' || p === 's' || p === 'ciencia' || p === 'clinico') return 'cientifico'
  return undefined
}

function limpiar(texto: string): string {
  let t = texto.trim()
  const bloque = t.match(/^```[a-zA-Z]*\n([\s\S]*?)\n```$/)
  if (bloque?.[1] !== undefined) t = bloque[1].trim()
  return t
}

const AYUDA = `Uso: /mejorar <modo> <texto del prompt>
Modos: general (g), creativo (c), cientifico (s)
Ejemplo: /mejorar cientifico resume la evidencia de la linfadenectomía en la cistectomía radical
El prompt mejorado queda en la caja de texto para que lo revises y lo envíes tú.
También puedes escribir el borrador y pulsar los botones de la barra «Mejorar prompt».`

async function mejorar($: EngineInterface, modo: Modo, texto: string): Promise<string | undefined> {
  const borrador = texto.trim()
  if (borrador === '') {
    $.ui.toast('Escribe primero un borrador en la caja de texto.')
    return undefined
  }
  if ((await read($, ocupado)) !== null) {
    $.ui.toast('Ya hay una mejora en curso.')
    return undefined
  }

  await update($, ocupado, () => modo)
  $.ui.status(`Mejorando prompt (${ETIQUETA[modo]})…`)
  try {
    const r = await $.model.complete({
      model: MODELO,
      system: [{ text: `${REGLAS_COMUNES}\n\n${REGLAS_MODO[modo]}` }],
      prompt: `BORRADOR:\n<<<\n${borrador}\n>>>`,
      maxTokens: 3000,
      timeoutMs: LIMITE_MS,
    })
    if (!r.isAnswered) {
      $.ui.toast(`No se pudo mejorar el prompt (${r.reason}).`)
      return undefined
    }
    const mejorado = limpiar(r.text)
    if (mejorado === '') {
      $.ui.toast('El modelo devolvió una respuesta vacía.')
      return undefined
    }
    await update($, original, () => borrador)
    const lleno = await $.prompt.fill({ text: mejorado, mode: 'replace' })
    if (!lleno.isFilled) {
      $.ui.toast('No se pudo escribir en la caja de texto.')
      return mejorado
    }
    $.ui.toast(`Prompt mejorado (${ETIQUETA[modo]}). Revísalo antes de enviar.`)
    return mejorado
  } finally {
    await update($, ocupado, () => null)
    $.ui.status(undefined)
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'mejorar',
      description: 'Mejora un prompt (general, creativo o científico) y lo deja en la caja de texto sin enviarlo',
      argumentHint: '<general|creativo|cientifico> <texto>',
    })
    return next(e)
  })

  on('command.run', { command: 'mejorar' }, async ($, e) => {
    const args = e.args.trim()
    if (args === '' || args === 'ayuda' || args === 'help') {
      return { text: AYUDA, isTextDisplayOnly: true }
    }
    if (args === 'deshacer') {
      const previo = await read($, original)
      if (previo === null) return { text: 'No hay ningún borrador anterior que recuperar.', isTextDisplayOnly: true }
      await $.prompt.fill({ text: previo, mode: 'replace' })
      return { text: 'Borrador original restaurado en la caja de texto.', isTextDisplayOnly: true }
    }
    if (args === 'mostrar') {
      await update($, oculta, () => false)
      return { text: 'Barra «Mejorar prompt» visible.', isTextDisplayOnly: true }
    }

    const [primera, ...resto] = args.split(/\s+/)
    const modoLeido = leerModo(primera ?? "")
    const modo: Modo = modoLeido ?? 'general'
    const texto = modoLeido ? resto.join(' ') : args
    if (texto.trim() === '') {
      return { text: `Falta el texto del prompt.\n\n${AYUDA}`, isTextDisplayOnly: true }
    }

    const mejorado = await mejorar($, modo, texto)
    return {
      text: mejorado
        ? `Prompt mejorado en modo ${ETIQUETA[modo]}: está en la caja de texto. «/mejorar deshacer» recupera el original.`
        : 'No se ha podido mejorar el prompt.',
      isTextDisplayOnly: true,
    }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || (await read($, oculta))) return next(e)

    const { Box, Button, Text } = $.ui.resolve(e)
    const enCurso = await read($, ocupado)
    const hayOriginal = (await read($, original)) !== null

    if (enCurso !== null) {
      return (
        <Box>
          <Text dimColor>Mejorando prompt ({ETIQUETA[enCurso]})…</Text>
        </Box>
      )
    }

    const pulsar = (modo: Modo) => async () => {
      const { text } = await $.prompt.read()
      await mejorar($, modo, text)
    }

    return (
      <Box>
        <Text dimColor>Mejorar prompt: </Text>
        <Button key="general" label="General" onPress={pulsar('general')} />
        <Text> </Text>
        <Button key="creativo" label="Creativo" onPress={pulsar('creativo')} />
        <Text> </Text>
        <Button key="cientifico" label="Científico" onPress={pulsar('cientifico')} />
        {hayOriginal && <Text> </Text>}
        {hayOriginal && (
          <Button
            key="deshacer"
            label="↶ Deshacer"
            onPress={async () => {
              const previo = await read($, original)
              if (previo !== null) await $.prompt.fill({ text: previo, mode: 'replace' })
              await update($, original, () => null)
            }}
          />
        )}
        <Text> </Text>
        <Button key="ocultar" label="×" onPress={() => update($, oculta, () => true)} />
      </Box>
    )
  })
}
