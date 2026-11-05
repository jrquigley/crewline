import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const htmlPath = new URL('../public/index.html', import.meta.url);

/** Local interface-preview server. Deliberately has no scheduling/auth API. */
export function createPreviewServer() {
  return createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'no-referrer');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'");
    const head = req.method === 'HEAD';
    const send = (status, type, body) => { res.writeHead(status, { 'Content-Type': type }); res.end(head ? undefined : body); };
    if (!['GET', 'HEAD'].includes(req.method)) {
      res.setHeader('Allow', 'GET, HEAD'); send(405, 'text/plain; charset=utf-8', 'Method not allowed'); return;
    }
    const path = req.url?.split('?')[0];
    if (path === '/healthz') { send(200, 'application/json; charset=utf-8', JSON.stringify({ status:'ok', mode:'interface-preview', productionReady:false })); return; }
    if (path === '/favicon.ico') { res.writeHead(204); res.end(); return; }
    if (path !== '/' && path !== '/index.html') { send(404, 'text/plain; charset=utf-8', 'Not found'); return; }
    try { send(200, 'text/html; charset=utf-8', await readFile(htmlPath, 'utf8')); }
    catch { send(503, 'text/plain; charset=utf-8', 'Preview is not built. Run npm run build.'); }
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const host = process.env.HOST || '127.0.0.1';
  const port = Number(process.env.PORT || 3000);
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT must be an integer from 0 to 65535.');
  const server = createPreviewServer();
  server.on('error', error => { console.error('Preview server could not start:', error.message); process.exitCode = 1; });
  server.listen(port, host, () => console.log(`Crewline sample-data preview: http://${host}:${server.address().port}\nNo login, database, email, or calendar service is running.`));
  const close = () => server.close(() => process.exit(0));
  process.on('SIGINT', close); process.on('SIGTERM', close);
}
