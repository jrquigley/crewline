const assert=require('node:assert/strict');
const {once}=require('node:events');
// Optional development tooling; not a runtime application dependency.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
const {createPreviewServer}=await import('../server/index.mjs');
const server=createPreviewServer();server.listen(0,'127.0.0.1');await once(server,'listening');
let browser;
try{
browser=await chromium.launch({headless:true,...(process.env.BROWSER_CHANNEL?{channel:process.env.BROWSER_CHANNEL}:{})});
const page=await browser.newPage({viewport:{width:1024,height:1200},colorScheme:'light'});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto(`http://127.0.0.1:${server.address().port}`);const f=page;
await f.locator('#cl-app h1').waitFor();assert.match(await f.locator('.cl-statline').innerText(),/Events/);
await f.locator('[data-event="jazz"]').click();await f.locator('[data-act="fix-rules"]').click();
assert.equal(await f.locator('.cl-note.warn').count(),0);
await f.locator('[data-act="edit-shift"][data-id="jazz-during"]').click();
await f.locator('select[name="staff"]').selectOption('jordan');await f.locator('[data-form="shift"] [data-act="submit"]').click();assert.match(await f.locator('.cl-formerror').innerText(),/Missing Guest welcome/);
await f.locator('input[name="end"]').fill('21:30');await f.locator('select[name="staff"]').selectOption('alex');await f.locator('[data-form="shift"] [data-act="submit"]').click();
await f.locator('[data-mode="staff"]').click();assert.match(await f.locator('.cl-nextshift').innerText(),/6pm–9:15pm/);
await f.locator('[data-mode="manager"]').click();await f.locator('[data-act="publish"]').click();await f.locator('[data-act="confirm-publish"]').click();
await f.locator('[data-mode="staff"]').click();assert.match(await f.locator('.cl-nextshift').innerText(),/6pm–9:30pm/);
await f.locator('[data-staffpage="open"]').click();await f.locator('[data-act="claim"]').first().click();assert.match(await f.locator('#cl-toast').innerText(),/waiting for manager/);
await f.locator('[data-mode="manager"]').click();await f.locator('[data-page="requests"]').click();await f.locator('[data-act="approve-claim"]').click();assert.match(await f.locator('#cl-toast').innerText(),/approved/);
await f.locator('[data-page="schedule"]').click();await f.locator('[data-event="jazz"]').click();await f.locator('[data-act="add-coverage"]').click();
await f.locator('[data-form="coverage"] [name="dept"]').selectOption('Production');await f.locator('[data-form="coverage"] [name="skill"]').fill('AV technician');await f.locator('[data-form="coverage"] [name="count"]').fill('2');await f.locator('[data-form="coverage"] [data-act="submit"]').click();assert.equal(await f.locator('.cl-slot').count(),5);
await f.locator('[data-page="schedule"]').click();await f.locator('[data-act="new-event"]').click();await f.locator('[name="name"]').fill('Winter fundraiser');await f.locator('[data-act="submit"]').click();assert.equal(await f.locator('.cl-slot').count(),3);
await f.locator('[data-mode="staff"]').click();await f.locator('.cl-mobile-nav [data-staffpage="me"]').click();await f.locator('[data-staffpage="details"]').click();await f.locator('[name="email"]').fill('alex.new@example.com');await f.locator('[data-act="submit"]').click();assert.match(await f.locator('.cl-note.warn').innerText(),/Verification pending/);
await f.locator('.cl-mobile-nav [data-staffpage="me"]').click();await f.locator('[data-staffpage="availability"]').click();assert.equal(await f.locator('[data-av-date]').isVisible(),false);await f.locator('[data-av-kind]').selectOption('date');assert.equal(await f.locator('[data-av-day]').isVisible(),false);
await f.locator('[data-mode="manager"]').click();await f.locator('[data-page="staff"]').click();await f.locator('[data-person="casey"]').click();await f.locator('[data-act="termination"]').click();await f.locator('[data-act="confirm-termination"]').click();assert.match(await f.locator('#cl-app').innerText(),/Historical shifts · retained/);assert.match(await f.locator('#cl-app').innerText(),/Autumn benefit/);
await f.locator('[data-mode="staff"]').click();await f.locator('[data-filter="staffId"]').selectOption('casey');assert.equal(await f.locator('h1').innerText(),'Access ended');assert.equal(await f.locator('.cl-mobile-nav').count(),0);await f.locator('[data-filter="staffId"]').selectOption('alex');
const overflow=[];
for(const width of [1024,360,320]){
await page.setViewportSize({width,height:1200});
for(const mode of ['manager','staff']){
await f.locator('[data-mode="'+mode+'"]').click();
const views=mode==='manager'?['schedule','staff','requests','settings','modules']:['home','schedule','me'];
for(const view of views){await f.locator(mode==='manager'?'[data-page="'+view+'"]':'.cl-mobile-nav [data-staffpage="'+view+'"]').first().click();const size=await page.evaluate(()=>[document.documentElement.clientWidth,document.documentElement.scrollWidth]);if(size[1]>size[0]+1)overflow.push({width,mode,view,size});}
}
}
assert.deepEqual(overflow,[]);assert.deepEqual(errors,[]);
await page.emulateMedia({colorScheme:'dark'});await f.locator('[data-mode="manager"]').click();await f.locator('[data-page="schedule"]').click();assert.equal(await f.locator('h1').innerText(),'Schedule');
console.log('Browser smoke passed: assignments, draft isolation, publishing, requests, mixed-department coverage, Event creation, contact verification, availability, offboarding/history, 24 responsive page/viewport checks and no runtime errors.');
}finally{if(browser)await browser.close();server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;});
