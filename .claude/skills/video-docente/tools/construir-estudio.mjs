#!/usr/bin/env node
// Genera estudio/dist/estudio.html: la plantilla del estudio web con el motor, las marcas,
// la fuente de respaldo y el guion de ejemplo incrustados (una sola página autocontenida).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const leer = (...p) => fs.readFileSync(path.join(RAIZ, ...p), 'utf8');
const b64 = f => fs.readFileSync(f).toString('base64');

const inter = [[400, 'Inter-Regular.otf'], [600, 'Inter-SemiBold.otf'], [700, 'Inter-Bold.otf']]
  .map(([peso, f]) => `@font-face { font-family: "InterVD"; font-weight: ${peso}; src: url(data:font/otf;base64,${b64(path.join(RAIZ, 'motor', 'fuentes', f))}) format("opentype"); }`)
  .join('\n');

const marcas = {};
for (const nombre of fs.readdirSync(path.join(RAIZ, 'marcas'))) {
  const dir = path.join(RAIZ, 'marcas', nombre);
  const fichero = path.join(dir, 'marca.json');
  if (!fs.existsSync(fichero)) continue;
  const m = JSON.parse(fs.readFileSync(fichero, 'utf8'));
  m.fuentes = (m.fuentes || []).map(f => ({ ...f, datos: b64(path.resolve(dir, f.archivo)) }));
  marcas[nombre] = m;
}

const ejemplo = JSON.parse(leer('ejemplos', 'gleason-isup-marca.json'));
const motor = leer('motor', 'engine.js');
if (/<\/script/i.test(motor)) throw new Error('engine.js contiene "</script": no se puede incrustar.');

const html = leer('estudio', 'plantilla.html')
  .split('/*__INTER__*/').join(inter)
  .split('/*__MOTOR__*/').join(motor)
  .split('/*__MARCAS__*/').join(JSON.stringify(marcas))
  .split('/*__EJEMPLO__*/').join(JSON.stringify(ejemplo));

const salida = path.join(RAIZ, 'estudio', 'dist', 'estudio.html');
fs.mkdirSync(path.dirname(salida), { recursive: true });
fs.writeFileSync(salida, html);
console.log(`${salida} (${(Buffer.byteLength(html) / 1048576).toFixed(2)} MB; marcas: ${Object.keys(marcas).join(', ')})`);
