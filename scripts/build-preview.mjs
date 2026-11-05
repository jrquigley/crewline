import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const source = await readFile(join(root, 'prototype/crewline.fragment.html'), 'utf8');
// The source is also the editable in-chat design reference. Export the same UI
// as a normal document, replacing optional host-only design tools.
let fragment = source.replace(/^if\(globalThis\.Tweak\).*$/m, '');
const symbols = { 'calendar-days':'▦', users:'♙', inbox:'▤', 'sliders-horizontal':'☷',
  blocks:'▧', 'building-2':'▥', plus:'+', 'user-plus':'+', sun:'☀', hand:'＋',
  'arrow-left':'←', 'arrow-up-right':'↗', 'chevron-right':'›', 'chart-no-axes-column':'▥',
  'triangle-alert':'⚠', check:'✓', sparkles:'✦', layers:'▱', 'calendar-plus':'▦',
  smartphone:'▯', house:'⌂', 'circle-user-round':'○', 'contact-round':'▣', 'clock-3':'◷',
  'lock-keyhole':'▣', 'map-pin':'⌖' };
fragment = fragment.replace(
  /const icon=\(name\)=>[^\n]+;/,
  `const symbols=${JSON.stringify(symbols)};\nconst icon=(name)=>\`<span class="cl-icon cl-symbol" aria-hidden="true">\${symbols[name]||'•'}</span>\`;`
);
// Memory-only sample state. A refresh resets the preview. This is not an auth
// or persistence layer; production data must be served by authenticated APIs.
const document = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark"><meta name="robots" content="noindex,nofollow">
<title>Crewline — Event staff scheduling preview</title>
<style>html{color-scheme:light dark}body{margin:0;background:light-dark(#fff,#161a18);padding:16px}#crewline{max-width:1280px;margin:0 auto}#crewline .cl-demo{padding-right:0}#crewline .cl-symbol{width:20px;min-width:20px;justify-content:center;font-style:normal;font-size:19px;line-height:1}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid light-dark(#256748,#ade0bd);outline-offset:3px}@media(max-width:580px){body{padding:10px}}</style>
<script>window.openai={widgetState:null,setWidgetState:async function(state){this.widgetState=state}};</script>
</head><body>
${fragment}
</body></html>
`;
const target = join(root, 'public/index.html');
if (process.argv.includes('--check')) {
  const existing = await readFile(target, 'utf8').catch(() => '');
  if (existing !== document) { console.error('public/index.html is stale. Run npm run build.'); process.exitCode = 1; }
  else console.log('Preview build is current.');
} else { await writeFile(target, document); console.log('Built public/index.html'); }
