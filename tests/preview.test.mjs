import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { readFile, readdir } from 'node:fs/promises';
import vm from 'node:vm';
import { createPreviewServer } from '../server/index.mjs';

let server, base;
before(async () => { server=createPreviewServer();server.listen(0,'127.0.0.1');await once(server,'listening');base=`http://127.0.0.1:${server.address().port}`; });
after(async () => { server.closeAllConnections();await new Promise(resolve=>server.close(resolve)); });
test('serves the Event scheduling preview',async()=>{const r=await fetch(base);assert.equal(r.status,200);assert.match(r.headers.get('content-type'),/text\/html/);const html=await r.text();assert.match(html,/<title>Crewline/);assert.match(html,/New Event/);assert.match(html,/Event name/);assert.match(html,/SAMPLE DATA/);});
test('health endpoint identifies the preview honestly',async()=>{const r=await fetch(base+'/healthz');assert.deepEqual(await r.json(),{status:'ok',mode:'interface-preview',productionReady:false});});
test('HEAD returns headers without a body',async()=>{const r=await fetch(base,{method:'HEAD'});assert.equal(r.status,200);assert.equal(await r.text(),'');});
test('private source, docs and traversal paths are not served',async()=>{for(const path of ['/docs/HANDOFF.md','/prototype/crewline.fragment.html','/.env','/../package.json','/%2e%2e/package.json','/missing'])assert.equal((await fetch(base+path)).status,404,path);});
test('unsupported mutations are rejected',async()=>{const r=await fetch(base,{method:'POST',body:'{}'});assert.equal(r.status,405);assert.equal(r.headers.get('allow'),'GET, HEAD');});
test('preview has no network connectors, caching or embedding',async()=>{const r=await fetch(base);assert.equal(r.headers.get('cache-control'),'no-store');assert.equal(r.headers.get('x-frame-options'),'DENY');assert.match(r.headers.get('content-security-policy'),/connect-src 'none'/);assert.equal(r.headers.get('x-content-type-options'),'nosniff');});
test('all inline scripts parse',async()=>{const html=await readFile(new URL('../public/index.html',import.meta.url),'utf8');const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];assert.ok(scripts.length>=2);for(const [i,m] of scripts.entries())assert.doesNotThrow(()=>new vm.Script(m[1]),`script ${i}`);});
test('product source contains only the agreed Event terminology',async()=>{const oldTerm=new RegExp('\\b'+String.fromCharCode(103,105,103)+'s?\\b','i');for(const f of ['../prototype/crewline.fragment.html','../public/index.html'])assert.doesNotMatch(await readFile(new URL(f,import.meta.url),'utf8'),oldTerm);});
test('documentation links resolve within the repository',async()=>{const root=new URL('../',import.meta.url);const files=['README.md','AGENTS.md','CLAUDE.md',...(await readdir(new URL('docs/',root))).filter(x=>x.endsWith('.md')).map(x=>'docs/'+x)];for(const file of files){const content=await readFile(new URL(file,root),'utf8');for(const m of content.matchAll(/\]\(([^)]+)\)/g)){const href=m[1].split('#')[0];if(!href||/^[a-z]+:/i.test(href))continue;await assert.doesNotReject(readFile(new URL(href,new URL(file,root))),file+' → '+href);}}});
