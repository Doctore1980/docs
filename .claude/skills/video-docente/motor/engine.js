'use strict';
/* Motor de vídeo docente.
   Cada fotograma es función pura del tiempo: __API__.seek(t) pinta el instante t.
   Sin timers, sin transiciones CSS, sin aleatoriedad: dos renders son idénticos.
   La maquetación se calcula una vez al iniciar; seek() solo anima lo ya colocado. */
(function () {
  const spec = window.__SPEC__;
  const fmt = window.__FMT__ || { w: 1920, h: 1080 };
  const W = fmt.w, H = fmt.h, VERT = H > W;
  const canvas = document.getElementById('c');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d');

  const U = Math.min(W, H) / 100;          // unidad de diseño: 1 % del lado corto
  const FAM = 'InterVD';
  const LH = 1.25;                          // interlineado
  const SALIDA = 0.4;                       // segundos de fundido al cambiar de escena
  const PAUSA = 1.2;                        // reposo tras la última revelación

  const TEMAS = {
    claro:  { fondo: '#F7F6F2', tinta: '#16202A', suave: '#56616B', acento: '#0B6E8C', relleno: '#E4ECEF', linea: '#C3CDD3', tenue: '#9AA9B3' },
    oscuro: { fondo: '#0F1720', tinta: '#F2F4F5', suave: '#A3AEB8', acento: '#5CC8E0', relleno: '#1B2733', linea: '#33414E', tenue: '#4E5F6E' },
  };
  const tema = spec.tema || {};
  const C = Object.assign({}, TEMAS[tema.base] || TEMAS.claro, tema.colores || {});
  const WPS = { pausado: 2.0, normal: 2.5, rapido: 3.2 }[spec.ritmo || 'normal'] || 2.5;
  const T = { titulo: 8.8 * U, cabecera: 6 * U, cuerpo: 5.2 * U, subtitulo: 3.6 * U, peq: 3 * U };
  const MIN = 2.6 * U;                      // tamaño mínimo legible en móvil

  const auditoria = [];
  const aviso = (escena, msg) => auditoria.push({ nivel: 'aviso', escena, msg });
  const error = (escena, msg) => auditoria.push({ nivel: 'error', escena, msg });

  // Zona segura: márgenes y, en 9:16, franjas que tapan las interfaces de las redes.
  const hayNarracion = spec.escenas.some(e => e.narracion);
  const M = VERT ? { l: 0.075 * W, r: 0.075 * W, t: 0.13 * H, b: 0.2 * H }
                 : { l: 0.07 * W, r: 0.07 * W, t: 0.1 * H, b: 0.1 * H };
  const ZONA = { x: M.l, y: M.t, w: W - M.l - M.r, h: H - M.t - M.b };
  const BANDA = hayNarracion ? 2 * T.subtitulo * LH + 3 * U : 0;
  const CAJA = { x: ZONA.x, y: ZONA.y, w: ZONA.w, h: ZONA.h - (hayNarracion ? BANDA + 2.5 * U : 0) };
  const FONDO_CAJA = CAJA.y + CAJA.h;
  const ANCHO_LECTURA = VERT ? CAJA.w : Math.min(CAJA.w, 0.8 * W);  // líneas de lectura cómoda

  // ---------- utilidades ----------
  const clamp01 = x => Math.max(0, Math.min(1, x));
  const palabras = s => (String(s || '').trim().match(/\S+/g) || []).length;
  const lectura = s => palabras(s) / WPS;
  const fuente = (size, peso) => `${peso} ${size}px "${FAM}"`;
  function medir(txt, size, peso) { ctx.font = fuente(size, peso); return ctx.measureText(String(txt)).width; }
  function partir(txt, size, peso, maxW) {
    ctx.font = fuente(size, peso);
    const ws = String(txt).trim().split(/\s+/).filter(Boolean);
    const lines = []; let cur = ''; let ancha = false;
    for (const w of ws) {
      const prueba = cur ? cur + ' ' + w : w;
      if (ctx.measureText(prueba).width <= maxW) cur = prueba;
      else { if (cur) lines.push(cur); cur = w; if (ctx.measureText(w).width > maxW) ancha = true; }
    }
    if (cur) lines.push(cur);
    return { lines, ancha };
  }
  // Prueba tamaños decrecientes desde size0 hasta min y devuelve el primero que cabe.
  function ajustar(size0, min, maquetar) {
    let s = size0, r;
    for (;;) {
      r = maquetar(s);
      if (r.cabe || s <= min) break;
      s = Math.max(min, s * 0.95);
    }
    r.size = s;
    return r;
  }
  const decimales = v => { const m = String(v).match(/[.,](\d+)/); return m ? m[1].length : 0; };
  const num = (v, dec) => v.toFixed(dec).replace('.', ',');
  function luminancia(hex) {
    const n = parseInt(hex.slice(1), 16);
    const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(v => {
      v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function contraste(a, b) {
    const [x, y] = [luminancia(a), luminancia(b)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  }

  // ---------- movimiento: muelles en forma cerrada ----------
  const critico = (t, w) => t <= 0 ? 0 : 1 - Math.exp(-w * t) * (1 + w * t);
  function muelle(t, w, z) {
    if (t <= 0) return 0;
    const wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
  }

  // ---------- elementos ----------
  const texto = (o) => Object.assign({ k: 'texto', peso: 400, color: C.tinta, align: 'left', mov: 'sube' }, o);
  const altoTexto = (lines, size) => lines.length * size * LH;

  function pintar(e, t, esc) {
    const tau = t - e.at;
    if (tau < 0) return;
    const s = critico(tau, 11);
    ctx.save();
    ctx.globalAlpha *= clamp01(tau / 0.3);
    if (e.k === 'texto') {
      const dy = e.mov === 'nada' ? 0 : (1 - s) * 2.4 * U;
      ctx.font = fuente(e.size, e.peso);
      ctx.fillStyle = e.color;
      ctx.textAlign = e.align;
      ctx.textBaseline = 'middle';
      let lines = e.lines;
      if (e.cuenta) {
        const c = e.cuenta;
        lines = [c.pre + num(c.a * critico(tau, 4.5), c.dec) + c.suf];
      }
      lines.forEach((ln, i) => ctx.fillText(ln, e.x, e.y + (i + 0.5) * e.size * LH + dy));
    } else if (e.k === 'rect') {
      const w = e.crece === 'x' ? e.w * Math.max(0, muelle(tau, 9, 0.72)) : e.w;
      const dy = e.crece ? 0 : (1 - s) * 2.4 * U;
      ctx.beginPath();
      ctx.roundRect(e.x, e.y + dy, w, e.h, Math.min(e.r || 0, w / 2, e.h / 2));
      if (e.fill) { ctx.fillStyle = e.fill; ctx.fill(); }
      if (e.stroke) { ctx.strokeStyle = e.stroke; ctx.lineWidth = e.lw; ctx.stroke(); }
    } else if (e.k === 'punto') {
      ctx.beginPath();
      ctx.arc(e.x, e.y, e.r * Math.max(0, muelle(tau, 12, 0.6)), 0, Math.PI * 2);
      ctx.fillStyle = e.fill; ctx.fill();
    } else if (e.k === 'flecha') {
      const p = critico(tau, 10);
      const x = e.x1 + (e.x2 - e.x1) * p, y = e.y1 + (e.y2 - e.y1) * p;
      const ang = Math.atan2(e.y2 - e.y1, e.x2 - e.x1), cab = 2.4 * U;
      ctx.strokeStyle = ctx.fillStyle = e.color;
      ctx.lineWidth = e.lw; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(e.x1, e.y1); ctx.lineTo(x - Math.cos(ang) * cab * 0.6, y - Math.sin(ang) * cab * 0.6); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x - cab * Math.cos(ang - 0.45), y - cab * Math.sin(ang - 0.45));
      ctx.lineTo(x - cab * Math.cos(ang + 0.45), y - cab * Math.sin(ang + 0.45));
      ctx.closePath(); ctx.fill();
    } else if (e.k === 'discontinua') {
      ctx.strokeStyle = e.color; ctx.lineWidth = e.lw;
      ctx.setLineDash([1.2 * U, 0.9 * U]);
      ctx.beginPath(); ctx.moveTo(e.x1, e.y1); ctx.lineTo(e.x1, e.y1 + (e.y2 - e.y1) * critico(tau, 8)); ctx.stroke();
    } else if (e.k === 'imagen') {
      const z = 1 + 0.04 * clamp01(t / esc.dur);      // acercamiento lento y constante
      const cx = e.x + e.w / 2, cy = e.y + e.h / 2;
      ctx.beginPath(); ctx.roundRect(e.x, e.y, e.w, e.h, 1.2 * U); ctx.clip();
      ctx.drawImage(e.img, cx - e.w * z / 2, cy - e.h * z / 2, e.w * z, e.h * z);
    }
    ctx.restore();
  }

  // ---------- piezas comunes ----------
  function cabecera(els, txt, at, n) {
    if (!txt) return CAJA.y;
    const r = ajustar(T.cabecera, T.cuerpo, s => {
      const p = partir(txt, s, 700, CAJA.w);
      return { cabe: p.lines.length <= 2 && !p.ancha, p };
    });
    if (!r.cabe) error(n, 'El título de la escena no cabe en dos líneas: acórtalo.');
    els.push({ k: 'rect', x: CAJA.x, y: CAJA.y, w: 9 * U, h: 0.7 * U, r: 0.35 * U, fill: C.acento, crece: 'x', at });
    const y = CAJA.y + 2.2 * U;
    els.push(texto({ lines: r.p.lines, size: r.size, peso: 700, x: CAJA.x, y, at: at + 0.08 }));
    return y + altoTexto(r.p.lines, r.size) + 3.5 * U;
  }
  const inicioContenido = t => 0.6 + Math.min(lectura(t), 1.0);
  // Coloca un bloque de alto h en el hueco [y0, FONDO_CAJA], algo por encima del centro.
  const centrar = (y0, h) => y0 + Math.max(0, (FONDO_CAJA - y0 - h) * 0.4);
  const noCabe = (n, que) => error(n, `${que} no cabe ni al tamaño mínimo legible: reduce el texto o divide la escena.`);

  // ---------- plantillas de escena ----------
  // Cada plantilla devuelve { els, fin }: elementos con su instante de aparición
  // y el momento en que el espectador ha terminado de leer lo último revelado.
  const PLANTILLAS = {
    titulo(e, n) {
      const els = [];
      const ancho = VERT ? CAJA.w : CAJA.w * 0.82;
      const r = ajustar(T.titulo * 1.1, T.cabecera, s => {
        const pt = partir(e.titulo, s, 700, ancho);
        const ps = e.subtitulo ? partir(e.subtitulo, s * 0.5, 400, ancho) : { lines: [] };
        const pa = e.autor ? partir(e.autor, T.peq, 400, ancho) : { lines: [] };
        const h = 3 * U + altoTexto(pt.lines, s) + (ps.lines.length ? 2.5 * U + altoTexto(ps.lines, s * 0.5) : 0)
          + (pa.lines.length ? 4 * U + altoTexto(pa.lines, T.peq) : 0);
        return { cabe: h <= CAJA.h && pt.lines.length <= 4 && !pt.ancha && !ps.ancha, pt, ps, pa, h };
      });
      if (!r.cabe) noCabe(n, 'El título');
      const s = r.size;
      let y = CAJA.y + (CAJA.h - r.h) / 2;
      els.push({ k: 'rect', x: CAJA.x, y, w: 12 * U, h: 0.8 * U, r: 0.4 * U, fill: C.acento, crece: 'x', at: 0.15 });
      y += 3 * U;
      els.push(texto({ lines: r.pt.lines, size: s, peso: 700, x: CAJA.x, y, at: 0.3 }));
      y += altoTexto(r.pt.lines, s);
      let cur = 0.3 + lectura(e.titulo);
      if (r.ps.lines.length) {
        y += 2.5 * U;
        els.push(texto({ lines: r.ps.lines, size: s * 0.5, color: C.suave, x: CAJA.x, y, at: cur }));
        y += altoTexto(r.ps.lines, s * 0.5);
        cur += lectura(e.subtitulo);
      }
      if (r.pa.lines.length) {
        y += 4 * U;
        els.push(texto({ lines: r.pa.lines, size: T.peq, peso: 600, color: C.suave, x: CAJA.x, y, at: cur }));
        cur += lectura(e.autor);
      }
      return { els, fin: cur };
    },

    puntos(e, n, numerado) {
      const els = [];
      const y0 = cabecera(els, e.titulo, 0.2, n);
      let cur = inicioContenido(e.titulo);
      const items = e.puntos;
      const sang = numerado ? 7 * U : 4.8 * U;
      const maxH = FONDO_CAJA - y0;
      const r = ajustar(T.cuerpo, MIN, s => {
        const ps = items.map(t => partir(t, s, 400, ANCHO_LECTURA - sang));
        const gap = 1.0 * s;
        const h = ps.reduce((a, p) => a + altoTexto(p.lines, s), 0) + gap * (items.length - 1);
        return { cabe: h <= maxH && !ps.some(p => p.ancha), ps, gap, h };
      });
      if (!r.cabe) noCabe(n, 'La lista');
      let y = centrar(y0, r.h);
      items.forEach((t, i) => {
        const p = r.ps[i];
        if (numerado) els.push(texto({ lines: [String(i + 1)], size: r.size, peso: 700, color: C.acento, x: CAJA.x, y, at: cur }));
        else els.push({ k: 'punto', x: CAJA.x + 1 * U, y: y + r.size * LH / 2, r: 0.85 * U, fill: C.acento, at: cur });
        els.push(texto({ lines: p.lines, size: r.size, x: CAJA.x + sang, y, at: cur + 0.05 }));
        y += altoTexto(p.lines, r.size) + r.gap;
        cur += Math.max(0.9, lectura(t));
      });
      if (items.length > 6) aviso(n, `${items.length} puntos en una escena: más de 6 sobrecarga la memoria de trabajo; divídela.`);
      items.forEach((t, i) => { if (palabras(t) > 16) aviso(n, `El punto ${i + 1} tiene ${palabras(t)} palabras: en pantalla, mejor ≤ 16.`); });
      return { els, fin: cur };
    },

    mensaje(e, n) { return PLANTILLAS.puntos(Object.assign({ titulo: 'Mensajes clave' }, e), n, true); },

    tabla(e, n) {
      const els = [];
      const y0 = cabecera(els, e.titulo, 0.2, n);
      let cur = inicioContenido(e.titulo);
      const cols = e.columnas, filas = e.filas, nc = cols.length;
      filas.forEach((f, i) => { if (f.length !== nc) error(n, `La fila ${i + 1} tiene ${f.length} celdas y hay ${nc} columnas.`); });
      const destacar = new Set([].concat(e.destacar || []).map(i => i - 1));
      const pad = 1.6 * U, sep = 3 * U, maxH = FONDO_CAJA - y0;
      const r = ajustar(T.cuerpo, MIN, s => {
        const disp = CAJA.w - sep * (nc - 1) - 2 * pad - 1 * U;
        const nat = cols.map((c, j) => Math.max(medir(c, s, 600), ...filas.map(f => medir(f[j] ?? '', s, 400))) + 1);
        const tot = nat.reduce((a, b) => a + b, 0);
        let anchos;
        if (tot <= disp) anchos = nat.map(x => x + (disp - tot) / nc);
        else {
          const a = nat.map(x => Math.max(disp * 0.15, disp * x / tot));
          const k = disp / a.reduce((p, q) => p + q, 0);
          anchos = a.map(x => x * k);
        }
        const cab = cols.map((c, j) => partir(c, s, 600, anchos[j]));
        const cel = filas.map(f => f.map((v, j) => partir(v ?? '', s, 400, anchos[j])));
        const alto = ps => Math.max(...ps.map(p => p.lines.length)) * s * LH + 2 * pad;
        const hCab = alto(cab), hs = cel.map(alto);
        const h = hCab + hs.reduce((a, b) => a + b, 0);
        const ancha = cab.concat(...cel).some(p => p.ancha);
        return { cabe: h <= maxH && !ancha, anchos, cab, cel, hCab, hs, h };
      });
      if (!r.cabe) noCabe(n, 'La tabla');
      const s = r.size;
      const xs = []; let acc = CAJA.x + pad + 1 * U;
      r.anchos.forEach(a => { xs.push(acc); acc += a + sep; });
      let y = centrar(y0, r.h);
      r.cab.forEach((p, j) => els.push(texto({ lines: p.lines, size: s, peso: 600, color: C.suave, x: xs[j], y: y + pad, at: cur })));
      y += r.hCab;
      els.push({ k: 'rect', x: CAJA.x, y: y - 0.15 * U, w: CAJA.w, h: 0.3 * U, fill: C.linea, crece: 'x', at: cur });
      cur += 0.6;
      r.cel.forEach((fila, i) => {
        const h = r.hs[i];
        if (destacar.has(i)) {
          els.push({ k: 'rect', x: CAJA.x, y, w: CAJA.w, h, r: 0.8 * U, fill: C.relleno, at: cur });
          els.push({ k: 'rect', x: CAJA.x, y, w: 0.8 * U, h, r: 0.4 * U, fill: C.acento, at: cur });
        } else if (i < r.cel.length - 1) {
          els.push({ k: 'rect', x: CAJA.x, y: y + h - 0.08 * U, w: CAJA.w, h: 0.16 * U, fill: C.linea, at: cur });
        }
        fila.forEach((p, j) => els.push(texto({ lines: p.lines, size: s, peso: destacar.has(i) ? 600 : 400, x: xs[j], y: y + pad, at: cur + 0.04 * j })));
        y += h;
        cur += Math.max(0.9, lectura(filas[i].join(' ')));
      });
      if (filas.length > 7) aviso(n, `${filas.length} filas: una tabla de más de 7 filas cuesta leerla en vídeo.`);
      return { els, fin: cur };
    },

    barras(e, n) {
      const els = [];
      const y0 = cabecera(els, e.titulo, 0.2, n);
      let cur = inicioContenido(e.titulo);
      const datos = e.datos, uni = e.unidad || '';
      const ref = e.referencia;
      const max = e.max ?? Math.max(...datos.map(d => d.valor), ref ? ref.valor : 0);
      const dec = Math.max(...datos.map(d => decimales(d.valor)));
      const destacar = new Set([].concat(e.destacar || []).map(i => i - 1));
      const pf = e.fuente ? partir(e.fuente, T.peq, 400, CAJA.w) : { lines: [] };
      const hF = pf.lines.length ? altoTexto(pf.lines, T.peq) + 2.5 * U : 0;
      const hRef = ref ? T.peq * LH + 1 * U : 0;
      const maxH = FONDO_CAJA - y0 - hF - hRef;
      const r = ajustar(T.cuerpo, MIN, s => {
        const etW = Math.min(CAJA.w * 0.38, Math.max(...datos.map(d => medir(d.etiqueta, s, 600))) + 1);
        const valW = Math.max(...datos.map(d => medir(num(d.valor, dec) + uni, s, 700))) + 2 * U;
        const ets = datos.map(d => partir(d.etiqueta, s, 600, etW));
        const barH = Math.min(8 * U, s * 1.6);
        const hs = ets.map(p => Math.max(altoTexto(p.lines, s), barH));
        const gap = 0.8 * s;
        const h = hs.reduce((a, b) => a + b, 0) + gap * (datos.length - 1);
        return { cabe: h <= maxH && !ets.some(p => p.ancha), etW, valW, ets, barH, hs, gap, h };
      });
      if (!r.cabe) noCabe(n, 'El gráfico');
      const s = r.size;
      const x0 = CAJA.x + r.etW + 3 * U;
      const areaW = CAJA.w - r.etW - 3 * U - r.valW;
      let y = centrar(y0, r.h + hRef + hF) + hRef;
      const yIni = y;
      datos.forEach((d, i) => {
        const h = r.hs[i], cy = y + h / 2;
        const color = destacar.size === 0 || destacar.has(i) ? C.acento : C.tenue;
        els.push(texto({ lines: r.ets[i].lines, size: s, peso: 600, align: 'right', x: CAJA.x + r.etW, y: cy - altoTexto(r.ets[i].lines, s) / 2, at: cur }));
        const bw = Math.max(0.6 * U, areaW * d.valor / max);
        els.push({ k: 'rect', x: x0, y: cy - r.barH / 2, w: bw, h: r.barH, r: 0.6 * U, fill: color, crece: 'x', at: cur + 0.05 });
        els.push(texto({ lines: [''], cuenta: { a: d.valor, dec, pre: '', suf: uni }, size: s, peso: 700, color: C.tinta, mov: 'nada', x: x0 + bw + 1.5 * U, y: cy - s * LH / 2, at: cur + 0.05 }));
        y += h + r.gap;
        cur += Math.max(0.7, lectura(d.etiqueta) + 0.4);
      });
      if (ref) {
        const xr = x0 + areaW * ref.valor / max;
        els.push({ k: 'discontinua', x1: xr, y1: yIni - 0.5 * U, y2: y - r.gap + 0.5 * U, color: C.suave, lw: 0.3 * U, at: 0.7 });
        if (ref.etiqueta) els.push(texto({ lines: [ref.etiqueta], size: T.peq, color: C.suave, align: 'left', x: xr + 0.8 * U, y: yIni - hRef, at: 0.7 }));
      }
      if (pf.lines.length) els.push(texto({ lines: pf.lines, size: T.peq, color: C.suave, x: CAJA.x, y: FONDO_CAJA - altoTexto(pf.lines, T.peq), at: cur, mov: 'nada' }));
      if (datos.length > 8) aviso(n, `${datos.length} barras: más de 8 dificulta la comparación.`);
      return { els, fin: cur + 1.0 };
    },

    cifra(e, n) {
      const els = [];
      const y0 = cabecera(els, e.titulo, 0.2, n);
      const disp = FONDO_CAJA - y0;
      const ancho = VERT ? CAJA.w : CAJA.w * 0.8;
      const rv = ajustar(22 * U, 8 * U, s => ({ cabe: medir(e.valor, s, 700) <= CAJA.w && s * LH <= disp * 0.5 }));
      if (!rv.cabe) noCabe(n, 'La cifra');
      const rt = ajustar(T.cuerpo, MIN, s => {
        const p = partir(e.texto || '', s, 400, ancho);
        const pf = e.fuente ? partir(e.fuente, T.peq, 400, ancho) : { lines: [] };
        const h = rv.size * LH + 2 * U + altoTexto(p.lines, s) + (pf.lines.length ? 2.5 * U + altoTexto(pf.lines, T.peq) : 0);
        return { cabe: h <= disp && !p.ancha, p, pf, h };
      });
      if (!rt.cabe) noCabe(n, 'El texto de la cifra');
      let y = centrar(y0, rt.h);
      let at = e.titulo ? inicioContenido(e.titulo) : 0.3;
      const m = String(e.valor).match(/^([^\d-]*)(-?\d+(?:[.,]\d+)?)(.*)$/);
      const cuenta = m ? { pre: m[1], a: parseFloat(m[2].replace(',', '.')), dec: decimales(m[2]), suf: m[3] } : null;
      els.push(texto({ lines: [String(e.valor)], cuenta, size: rv.size, peso: 700, color: C.acento, x: CAJA.x, y, at, mov: cuenta ? 'nada' : 'sube' }));
      y += rv.size * LH + 2 * U;
      at += 1.3;
      els.push(texto({ lines: rt.p.lines, size: rt.size, x: CAJA.x, y, at }));
      y += altoTexto(rt.p.lines, rt.size);
      at += lectura(e.texto);
      if (rt.pf.lines.length) els.push(texto({ lines: rt.pf.lines, size: T.peq, color: C.suave, x: CAJA.x, y: y + 2.5 * U, at, mov: 'nada' }));
      return { els, fin: at + 0.5 };
    },

    pasos(e, n) {
      const els = [];
      const y0 = cabecera(els, e.titulo, 0.2, n);
      let cur = inicioContenido(e.titulo);
      const items = e.pasos, k = items.length;
      const horiz = !VERT && k <= 4;
      const pad = 2.4 * U, gap = horiz ? 8 * U : 6.5 * U, maxH = FONDO_CAJA - y0;
      const r = ajustar(T.cuerpo, MIN, s => {
        if (horiz) {
          const bw = (CAJA.w - gap * (k - 1)) / k;
          const ps = items.map(t => partir(t, s, 600, bw - 2 * pad));
          const bh = Math.max(...ps.map(p => altoTexto(p.lines, s))) + 2 * pad;
          return { cabe: bh <= maxH && !ps.some(p => p.ancha), ps, bw, bhs: ps.map(() => bh), h: bh };
        }
        const bw = CAJA.w;
        const ps = items.map(t => partir(t, s, 600, bw - 2 * pad));
        const bhs = ps.map(p => altoTexto(p.lines, s) + 2 * pad);
        const h = bhs.reduce((a, b) => a + b, 0) + gap * (k - 1);
        return { cabe: h <= maxH && !ps.some(p => p.ancha), ps, bw, bhs, h };
      });
      if (!r.cabe) noCabe(n, 'El diagrama');
      const s = r.size;
      let x = CAJA.x, y = centrar(y0, r.h);
      items.forEach((t, i) => {
        const bh = r.bhs[i], p = r.ps[i];
        els.push({ k: 'rect', x, y, w: r.bw, h: bh, r: 1.5 * U, fill: C.relleno, stroke: C.acento, lw: 0.35 * U, at: cur });
        els.push(texto({ lines: p.lines, size: s, peso: 600, align: 'center', x: x + r.bw / 2, y: y + (bh - altoTexto(p.lines, s)) / 2, at: cur + 0.05 }));
        cur += Math.max(0.9, lectura(t));
        if (i < k - 1) {
          if (horiz) els.push({ k: 'flecha', x1: x + r.bw + 1 * U, y1: y + bh / 2, x2: x + r.bw + gap - 1 * U, y2: y + bh / 2, color: C.acento, lw: 0.7 * U, at: cur });
          else els.push({ k: 'flecha', x1: x + r.bw / 2, y1: y + bh + 0.8 * U, x2: x + r.bw / 2, y2: y + bh + gap - 0.8 * U, color: C.acento, lw: 0.7 * U, at: cur });
          cur += 0.35;
          if (horiz) x += r.bw + gap; else y += bh + gap;
        }
      });
      if (k > 7) aviso(n, `${k} pasos: más de 7 es difícil de seguir en una sola escena.`);
      return { els, fin: cur };
    },

    imagen(e, n) {
      const els = [];
      const y0 = cabecera(els, e.titulo, 0.2, n);
      const pc = e.credito ? partir(e.credito, T.peq, 400, CAJA.w) : { lines: [] };
      const hC = pc.lines.length ? altoTexto(pc.lines, T.peq) + 1.5 * U : 0;
      const img = IMAGENES.get(n);
      const aw = CAJA.w, ah = FONDO_CAJA - y0 - hC;
      const k = Math.min(aw / img.naturalWidth, ah / img.naturalHeight);
      const w = img.naturalWidth * k, h = img.naturalHeight * k;
      const x = CAJA.x + (VERT ? (aw - w) / 2 : 0), y = y0 + (ah - h) / 2;
      const at = e.titulo ? 0.5 : 0.2;
      els.push({ k: 'imagen', img, x, y, w, h, at });
      if (pc.lines.length) els.push(texto({ lines: pc.lines, size: T.peq, color: C.suave, x: CAJA.x, y: y + h + 1.5 * U, at: at + 0.3, mov: 'nada' }));
      else aviso(n, 'La imagen no tiene "credito": indica autoría o licencia.');
      if (k > 1.5) aviso(n, 'La imagen se amplía más de 1,5×: puede verse pixelada.');
      return { els, fin: at + lectura(e.titulo) + 3 };
    },

    referencias(e, n) {
      const els = [];
      const y0 = cabecera(els, e.titulo || 'Referencias', 0.2, n);
      const refs = e.refs, maxH = FONDO_CAJA - y0;
      const r = ajustar(T.peq * 1.15, MIN, s => {
        const numW = medir(`${refs.length}.`, s, 600) + 1.5 * U;
        const ps = refs.map(t => partir(t, s, 400, CAJA.w - numW));
        const gap = 0.7 * s;
        const h = ps.reduce((a, p) => a + altoTexto(p.lines, s), 0) + gap * (refs.length - 1);
        return { cabe: h <= maxH && !ps.some(p => p.ancha), ps, numW, gap };
      });
      if (!r.cabe) noCabe(n, 'La lista de referencias');
      let y = y0;
      refs.forEach((t, i) => {
        const at = 0.7 + i * 0.15;
        els.push(texto({ lines: [`${i + 1}.`], size: r.size, peso: 600, color: C.acento, x: CAJA.x, y, at }));
        els.push(texto({ lines: r.ps[i].lines, size: r.size, color: C.tinta, x: CAJA.x + r.numW, y, at }));
        y += altoTexto(r.ps[i].lines, r.size) + r.gap;
      });
      return { els, fin: 0.7 + 3 + 1.0 * refs.length };
    },
  };

  // ---------- subtítulos de la narración ----------
  // Divide la narración en subtítulos: frase a frase y, si una frase supera 13 palabras,
  // en partes equilibradas cuyo corte se desplaza a la coma o pausa más cercana.
  function trozos(txt, n) {
    const frases = String(txt).trim().match(/[^.?!]+[.?!]*/g) || [];
    const out = [];
    for (const f of frases) {
      const ws = f.trim().split(/\s+/).filter(Boolean);
      if (!ws.length) continue;
      const partes = Math.ceil(ws.length / 13);
      let desde = 0;
      for (let i = 1; i < partes; i++) {
        const ideal = Math.round(ws.length * i / partes);
        let corte = ideal;
        for (let d = 0; d <= 3; d++) {
          if (/[,:;]$/.test(ws[ideal - d - 1] || '') && ideal - d - desde >= 4) { corte = ideal - d; break; }
          if (/[,:;]$/.test(ws[ideal + d - 1] || '') && ws.length - (ideal + d) >= 3) { corte = ideal + d; break; }
        }
        out.push(ws.slice(desde, corte).join(' '));
        desde = corte;
      }
      out.push(ws.slice(desde).join(' '));
    }
    let t = 0.3;
    return out.map(c => {
      const r = ajustar(T.subtitulo, MIN, s => { const p = partir(c, s, 400, ZONA.w - 4 * U); return { cabe: p.lines.length <= 2 && !p.ancha, p }; });
      if (!r.cabe) error(n, `Un fragmento de narración no cabe en dos líneas: "${c.slice(0, 40)}…"`);
      const d = Math.max(1.2, palabras(c) / WPS);
      const o = { ini: t, fin: t + d, texto: c, lines: r.p.lines, size: r.size };
      t += d;
      return o;
    });
  }

  function redundancia(narr, pantalla) {
    const norm = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').match(/[a-z0-9]{4,}/g) || [];
    const a = norm(narr), b = new Set(norm(pantalla));
    if (a.length < 8) return 0;
    return a.filter(w => b.has(w)).length / a.length;
  }

  // ---------- construcción del guion ----------
  const IMAGENES = new Map();
  let ESC = [], TOTAL = 0;

  function construir() {
    for (const [nombre, a, b] of [['tinta', C.tinta, C.fondo], ['suave', C.suave, C.fondo], ['acento', C.acento, C.fondo], ['tinta sobre relleno', C.tinta, C.relleno]]) {
      const c = contraste(a, b);
      if (c < 4.5) error(0, `Contraste insuficiente (${c.toFixed(1)}:1) para el color ${nombre}; el mínimo WCAG AA es 4,5:1.`);
    }
    let ini = 0;
    spec.escenas.forEach((e, i) => {
      const n = i + 1;
      const tipo = e.tipo === 'mensaje' ? 'mensaje' : e.tipo;
      const r = PLANTILLAS[tipo](e, n);
      const tz = e.narracion ? trozos(e.narracion, n) : [];
      const finNarr = tz.length ? tz[tz.length - 1].fin : 0;
      const recomendada = Math.max(r.fin + PAUSA, finNarr + 0.6, 3) + SALIDA;
      let dur = recomendada;
      if (e.duracion != null) {
        dur = e.duracion;
        if (dur + 0.05 < recomendada) aviso(n, `Duración fijada ${dur} s; para leerla hacen falta unos ${recomendada.toFixed(1)} s.`);
      }
      dur = Math.round(dur * 10) / 10;
      for (const el of r.els) {
        if (el.k === 'texto' && el.size < MIN - 0.5) error(n, `Texto a ${(el.size / U).toFixed(1)} u: por debajo del mínimo legible.`);
        if (el.at > dur - SALIDA) aviso(n, 'Hay elementos que aparecen después de que empiece el fundido de salida.');
      }
      const enPantalla = JSON.stringify([e.titulo, e.subtitulo, e.puntos, e.filas, e.columnas, e.texto, e.pasos, e.datos && e.datos.map(d => d.etiqueta)]);
      if (palabras(enPantalla.replace(/[\[\]",{}]/g, ' ')) > 55) aviso(n, 'Más de 55 palabras en pantalla: divide la escena o pasa texto a la narración.');
      if (e.narracion && redundancia(e.narracion, enPantalla) > 0.8) aviso(n, 'La narración repite casi literalmente el texto en pantalla (principio de redundancia): úsala para explicar, no para leer.');
      if (dur > 45) aviso(n, `Escena de ${dur.toFixed(0)} s: por encima de ~45 s conviene segmentar.`);
      ESC.push({ n, tipo: e.tipo, ini, dur, els: r.els, trozos: tz });
      ini += dur;
    });
    TOTAL = ini;
    if (TOTAL > 300) aviso(0, `Duración total ${Math.round(TOTAL)} s: por encima de 5 min, mejor varios microvídeos.`);
  }

  function indice(t) {
    for (let i = 0; i < ESC.length; i++) if (t < ESC[i].ini + ESC[i].dur) return i;
    return ESC.length - 1;
  }

  function seek(t) {
    ctx.save();
    ctx.globalAlpha = 1;
    ctx.fillStyle = C.fondo;
    ctx.fillRect(0, 0, W, H);
    const i = indice(t), esc = ESC[i], lt = t - esc.ini;
    ctx.globalAlpha = i < ESC.length - 1 ? 1 - clamp01((lt - (esc.dur - SALIDA)) / SALIDA) : 1;
    for (const el of esc.els) pintar(el, lt, esc);
    const tz = esc.trozos.find(c => lt >= c.ini && lt < c.fin);
    if (tz) {
      const by = ZONA.y + ZONA.h - BANDA;
      ctx.fillStyle = C.relleno;
      ctx.beginPath(); ctx.roundRect(ZONA.x, by, ZONA.w, BANDA, 1.2 * U); ctx.fill();
      ctx.font = fuente(tz.size, 400); ctx.fillStyle = C.tinta; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      const y0 = by + (BANDA - altoTexto(tz.lines, tz.size)) / 2;
      tz.lines.forEach((ln, j) => ctx.fillText(ln, ZONA.x + ZONA.w / 2, y0 + (j + 0.5) * tz.size * LH));
    }
    ctx.restore();
    // Elementos permanentes: pie y barra de progreso.
    if (spec.pie) {
      ctx.font = fuente(T.peq, 600); ctx.fillStyle = C.suave; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillText(spec.pie, ZONA.x, VERT ? M.t - 7 * U : M.t / 2);
    }
    if (spec.progreso !== false) {
      const py = VERT ? M.t - 3.5 * U : H - M.b / 2, ph = 0.45 * U;
      ctx.fillStyle = C.linea; ctx.fillRect(ZONA.x, py, ZONA.w, ph);
      ctx.fillStyle = C.acento; ctx.fillRect(ZONA.x, py, ZONA.w * clamp01(t / TOTAL), ph);
    }
  }

  // Hoja de contactos: un fotograma por escena, ya revelada y antes del fundido.
  function hoja(cols) {
    cols = cols || (VERT ? 5 : 3);
    const tw = VERT ? 300 : 520, th = Math.round(tw * H / W), lab = 40, gap = 16;
    const filas = Math.ceil(ESC.length / cols);
    const c2 = document.createElement('canvas');
    c2.width = cols * tw + (cols + 1) * gap;
    c2.height = filas * (th + lab) + (filas + 1) * gap;
    const g = c2.getContext('2d');
    g.fillStyle = '#20262C'; g.fillRect(0, 0, c2.width, c2.height);
    ESC.forEach((esc, i) => {
      seek(esc.ini + esc.dur - SALIDA - 0.05);
      const x = gap + (i % cols) * (tw + gap), y = gap + Math.floor(i / cols) * (th + lab + gap);
      g.drawImage(canvas, x, y, tw, th);
      g.font = `600 20px "${FAM}"`; g.fillStyle = '#E8ECEF'; g.textBaseline = 'middle';
      const mmss = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
      g.fillText(`${esc.n} · ${esc.tipo} · ${mmss(esc.ini)}–${mmss(esc.ini + esc.dur)}`, x, y + th + lab / 2);
    });
    return c2.toDataURL('image/png');
  }

  async function iniciar() {
    await Promise.all([400, 600, 700].map(p => document.fonts.load(`${p} 40px "${FAM}"`)));
    for (const p of [400, 600, 700]) if (!document.fonts.check(`${p} 40px "${FAM}"`)) throw new Error(`No se cargó la fuente Inter ${p}`);
    await Promise.all(spec.escenas.map(async (e, i) => {
      if (e.tipo !== 'imagen') return;
      const img = new Image();
      img.src = e.__datos;
      await img.decode();
      IMAGENES.set(i + 1, img);
    }));
    construir();
    seek(0);
    return {
      seek, hoja, W, H,
      total: TOTAL,
      escenas: ESC.map(e => ({ n: e.n, tipo: e.tipo, ini: e.ini, dur: e.dur })),
      subtitulos: ESC.flatMap(e => e.trozos.map(c => ({ ini: e.ini + c.ini, fin: e.ini + Math.min(c.fin, e.dur), texto: c.texto }))),
      auditoria,
    };
  }

  window.__READY__ = iniciar()
    .then(api => { window.__API__ = api; return { ok: true }; })
    .catch(err => ({ ok: false, error: String((err && err.stack) || err) }));
})();
