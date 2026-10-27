#!/usr/bin/env node
// Revisa, previsualiza y renderiza un guion de vídeo docente (JSON) con el motor de ../motor.
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const MOTOR = pathToFileURL(path.join(AQUI, '..', 'motor', 'engine.html')).href;
const FORMATOS = { '16:9': { w: 1920, h: 1080 }, '9:16': { w: 1080, h: 1920 } };
const OBLIGATORIOS = {
  titulo: ['titulo'], puntos: ['puntos'], mensaje: ['puntos'], tabla: ['columnas', 'filas'],
  barras: ['datos'], cifra: ['valor'], pasos: ['pasos'], imagen: ['src'], referencias: ['refs'], cierre: [],
};
const MARCAS = path.join(AQUI, '..', 'marcas');

// "marca" en el guion: nombre de una carpeta de ../marcas o ruta a un marca.json.
// Las fuentes se incrustan en base64 porque una página file:// no puede cargarlas de otra carpeta.
function cargarMarca(valor, dir) {
  const candidatos = [path.resolve(dir, valor), path.resolve(dir, valor, 'marca.json'), path.join(MARCAS, valor, 'marca.json')];
  const fichero = candidatos.find(f => fs.existsSync(f) && fs.statSync(f).isFile());
  if (!fichero) throw new Error(`No encuentro la marca "${valor}" (busqué en ${candidatos.join(', ')}).`);
  const m = JSON.parse(fs.readFileSync(fichero, 'utf8'));
  const base = path.dirname(fichero);
  m.fuentes = (m.fuentes || []).map(f => ({ ...f, datos: fs.readFileSync(path.resolve(base, f.archivo)).toString('base64') }));
  for (const campo of ['nombre', 'estilos', 'temas']) if (!m[campo]) throw new Error(`La marca ${fichero} no define "${campo}".`);
  return m;
}
const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml' };

const AYUDA = `Uso: node video.mjs <revisar|previa|render> guion.json [opciones]

  revisar   valida el guion y ejecuta la auditoría (legibilidad, carga, tiempos)
  previa    revisar + hoja de contactos PNG (un fotograma por escena)
  render    revisar + vídeo MP4 (H.264) + subtítulos .srt

Opciones:
  --formato 16:9|9:16|ambos   por defecto, el del guion o 16:9
  --fps N                     solo render; por defecto 30
  --audio FICHERO             solo render; pista de audio que se mezcla
  --salida DIR                por defecto, <carpeta del guion>/salida
  --forzar                    renderiza aunque la auditoría tenga errores`;

function args(argv) {
  const o = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--forzar') o.forzar = true;
    else if (a.startsWith('--')) o[a.slice(2)] = argv[++i];
    else o._.push(a);
  }
  return o;
}

function validar(spec, dir) {
  const errores = [];
  if (!Array.isArray(spec.escenas) || spec.escenas.length === 0) return ['El guion necesita un array "escenas" no vacío.'];
  spec.escenas.forEach((e, i) => {
    const n = `Escena ${i + 1}`;
    if (!OBLIGATORIOS[e.tipo]) { errores.push(`${n}: tipo "${e.tipo}" desconocido (${Object.keys(OBLIGATORIOS).join(', ')}).`); return; }
    for (const campo of OBLIGATORIOS[e.tipo]) {
      const v = e[campo];
      if (v == null || v === '' || (Array.isArray(v) && v.length === 0)) errores.push(`${n} (${e.tipo}): falta "${campo}".`);
    }
    if (e.tipo === 'barras' && Array.isArray(e.datos)) e.datos.forEach((d, j) => {
      if (typeof d.etiqueta !== 'string' || typeof d.valor !== 'number') errores.push(`${n}: el dato ${j + 1} necesita "etiqueta" (texto) y "valor" (número).`);
    });
    if (e.tipo === 'imagen' && e.src) {
      const f = path.resolve(dir, e.src);
      const mime = MIME[path.extname(f).toLowerCase()];
      if (!fs.existsSync(f)) errores.push(`${n}: no existe la imagen ${f}.`);
      else if (!mime) errores.push(`${n}: formato de imagen no admitido (${Object.keys(MIME).join(', ')}).`);
      else e.__datos = `data:${mime};base64,${fs.readFileSync(f).toString('base64')}`;
    }
    if (e.duracion != null && !(e.duracion > 0)) errores.push(`${n}: "duracion" debe ser un número positivo.`);
  });
  return errores;
}

async function abrir(browser, spec, fmt) {
  const page = await browser.newPage({ viewport: { width: fmt.w, height: fmt.h } });
  await page.addInitScript(d => { window.__SPEC__ = d.spec; window.__FMT__ = d.fmt; }, { spec, fmt });
  await page.goto(MOTOR);
  const r = await page.evaluate(() => window.__READY__);
  if (!r.ok) throw new Error(`El motor no arrancó:\n${r.error}`);
  const info = await page.evaluate(() => {
    const a = window.__API__;
    return { total: a.total, escenas: a.escenas, subtitulos: a.subtitulos, auditoria: a.auditoria };
  });
  return { page, info };
}

const mmss = s => `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, '0')}`;

function informe(nombreFmt, info) {
  console.log(`\n[${nombreFmt}] ${info.escenas.length} escenas · ${mmss(info.total)}`);
  for (const e of info.escenas) console.log(`  ${String(e.n).padStart(2)}  ${e.tipo.padEnd(11)} ${mmss(e.ini)}  ${e.dur.toFixed(1)} s`);
  const err = info.auditoria.filter(a => a.nivel === 'error');
  const avi = info.auditoria.filter(a => a.nivel === 'aviso');
  for (const a of err) console.log(`  ERROR  ${a.escena ? `escena ${a.escena}: ` : ''}${a.msg}`);
  for (const a of avi) console.log(`  aviso  ${a.escena ? `escena ${a.escena}: ` : ''}${a.msg}`);
  if (!err.length && !avi.length) console.log('  Auditoría sin incidencias.');
  return err.length;
}

function srt(subs) {
  const ts = s => {
    const ms = Math.round(s * 1000);
    const p = (n, k = 2) => String(n).padStart(k, '0');
    return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`;
  };
  return subs.map((s, i) => `${i + 1}\n${ts(s.ini)} --> ${ts(s.fin)}\n${s.texto}\n`).join('\n');
}

async function renderizar(page, info, destino, fps, audio) {
  const n = Math.round(info.total * fps);
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    ...(audio ? ['-i', audio] : []),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps),
    ...(audio ? ['-c:a', 'aac', '-b:a', '160k', '-af', 'apad', '-shortest'] : ['-an']),
    '-movflags', '+faststart', destino,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const fin = once(ff, 'close');
  const t0 = Date.now();
  let ultimo = -1;
  for (let i = 0; i < n; i++) {
    const b64 = await page.evaluate(t => {
      window.__API__.seek(t);
      return document.getElementById('c').toDataURL('image/jpeg', 0.95).split(',')[1];
    }, i / fps);
    if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await once(ff.stdin, 'drain');
    const pct = Math.floor((i + 1) / n * 10);
    if (pct !== ultimo) { ultimo = pct; process.stdout.write(`\r  render ${pct * 10} %  (${i + 1}/${n} fotogramas)`); }
  }
  ff.stdin.end();
  const [code] = await fin;
  process.stdout.write(`  ${((Date.now() - t0) / 1000).toFixed(0)} s\n`);
  if (code !== 0) throw new Error(`ffmpeg terminó con código ${code}`);
}

async function main() {
  const o = args(process.argv.slice(2));
  const [orden, fichero] = o._;
  if (!['revisar', 'previa', 'render'].includes(orden) || !fichero) { console.log(AYUDA); process.exit(2); }
  const ruta = path.resolve(fichero);
  const dir = path.dirname(ruta);
  const nombre = path.basename(ruta, '.json');
  const spec = JSON.parse(fs.readFileSync(ruta, 'utf8'));
  const errores = validar(spec, dir);
  if (errores.length) { errores.forEach(e => console.log(`ERROR  ${e}`)); process.exit(1); }
  if (spec.marca) spec.__marca = cargarMarca(spec.marca, dir);

  const pedido = o.formato || spec.formato || '16:9';
  const formatos = pedido === 'ambos' ? ['16:9', '9:16'] : [pedido];
  for (const f of formatos) if (!FORMATOS[f]) { console.log(`Formato desconocido: ${f}`); process.exit(2); }
  const salida = path.resolve(o.salida || path.join(dir, 'salida'));
  const fps = Number(o.fps || 30);
  const audio = o.audio ? path.resolve(o.audio) : null;
  if (audio && !fs.existsSync(audio)) { console.log(`No existe el audio ${audio}`); process.exit(2); }

  const browser = await chromium.launch();
  let fallos = 0;
  try {
    for (const f of formatos) {
      const { page, info } = await abrir(browser, spec, FORMATOS[f]);
      const nErr = informe(f, info);
      fallos += nErr;
      if (orden === 'revisar') continue;
      if (nErr && !o.forzar) { console.log('  Corrige los errores (o usa --forzar) antes de generar.'); continue; }
      fs.mkdirSync(salida, { recursive: true });
      const base = path.join(salida, `${nombre}-${f.replace(':', 'x')}`);
      if (orden === 'previa') {
        const png = await page.evaluate(() => window.__API__.hoja());
        fs.writeFileSync(`${base}-hoja.png`, Buffer.from(png.split(',')[1], 'base64'));
        console.log(`  Hoja de contactos: ${base}-hoja.png`);
      } else {
        await renderizar(page, info, `${base}.mp4`, fps, audio);
        console.log(`  Vídeo: ${base}.mp4`);
        if (info.subtitulos.length) {
          fs.writeFileSync(`${base}.srt`, srt(info.subtitulos));
          console.log(`  Subtítulos: ${base}.srt`);
        }
      }
      await page.close();
    }
  } finally {
    await browser.close();
  }
  process.exit(fallos && !o.forzar ? 1 : 0);
}

main().catch(err => { console.error(err.message || err); process.exit(1); });
