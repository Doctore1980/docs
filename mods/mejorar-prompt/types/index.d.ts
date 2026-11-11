export type Modo = 'general' | 'creativo' | 'cientifico'

declare module 'claude-code' {
  interface PluginState {
    'mejorar-prompt': {
      /** Modo en curso mientras se reescribe; null en reposo. */
      ocupado: Modo | null
      /** Borrador original antes de la última mejora, para deshacer. */
      original: string | null
      /** Barra plegada por la persona. */
      oculta: boolean
      /** Texto escrito en el panel. */
      borradorPanel: string
      /** Última mejora, para mostrarla en el panel. */
      resultado: { modo: Modo; texto: string } | null
    }
  }
}
