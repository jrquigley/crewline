const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.TEST_BASE_URL||'http://127.0.0.1:8300';
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw new Error('Browser tests require an isolated loopback test deployment.');
const email=process.env.TEST_ADMIN_EMAIL||'admin@example.test',password=process.env.TEST_ADMIN_PASSWORD;
if(!password)throw new Error('Set TEST_ADMIN_PASSWORD for the isolated test administrator.');
const out=path.resolve(process.env.TEST_OUTPUT||'.local/browser');fs.mkdirSync(out,{recursive:true});
const errors=[],failed=[],overflows=[],accessibility=[];
const audit=async(page,label)=>{
  if(!process.env.AXE_PATH)return;
  // DevTools injection keeps the production Content Security Policy intact.
  await page.evaluate(fs.readFileSync(process.env.AXE_PATH,'utf8'));
  const result=await page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return{violations:r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),passes:r.passes.length,incomplete:r.incomplete.length};});
  accessibility.push({label,...result});
  fs.writeFileSync(path.join(out,'accessibility.json'),JSON.stringify(accessibility,null,2));
};
const login=async(page,address,pass)=>{await page.goto(base+'/login/');await page.getByLabel('Email address',{exact:true}).fill(address);await page.getByLabel('Password',{exact:true}).fill(pass);await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.waitForURL(url=>!url.pathname.startsWith('/login/'));};
const fit=async(page,label)=>{const size=await page.evaluate(()=>({w:innerWidth,scroll:document.documentElement.scrollWidth}));if(size.scroll>size.w+1)overflows.push({label,...size});};
(async()=>{
const browser=await chromium.launch({headless:true,...(process.env.BROWSER_CHANNEL?{channel:process.env.BROWSER_CHANNEL}:{})});
try{
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});const page=await context.newPage();
const monitor=p=>{p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.url().startsWith(base+'/static/')&&r.status()>=400)failed.push({url:r.url(),status:r.status()});});};monitor(page);
await page.goto(base+'/manage/');assert.equal(new URL(page.url()).pathname,'/login/');
for(const width of [1440,1024,820,768,390,320]){await page.setViewportSize({width,height:width<500?920:1000});await page.screenshot({path:path.join(out,'login-'+width+'.png'),fullPage:true});await fit(page,'login-'+width);}
await audit(page,'login-phone');
await page.setViewportSize({width:1440,height:1000});await login(page,email,password);assert.equal(await page.locator('h1').innerText(),'Schedule');
await audit(page,'manager-dashboard');
for(const width of [1440,1024,820,768,390,320]){
await page.setViewportSize({width,height:width<500?920:1000});
for(const route of ['/manage/','/manage/staff/','/manage/events/new/','/manage/requests/','/manage/hours/','/manage/settings/','/my/account/']){await page.goto(base+route);assert.equal((await page.locator('h1').count())>0,true,route);await fit(page,route+'-'+width);}
await page.goto(base+'/manage/');await page.screenshot({path:path.join(out,'manager-'+width+'.png'),fullPage:true});}
for(const route of ['/manage/staff/','/manage/events/new/','/manage/requests/','/manage/hours/','/manage/settings/','/my/account/']){await page.goto(base+route);await audit(page,route);}
await page.setViewportSize({width:1440,height:1000});await page.goto(base+'/manage/events/new/');
// Use the workspace's local tomorrow, never the CI runner's timezone.
const iso=(await page.getByLabel('Start',{exact:true}).inputValue()).slice(0,10);const title='Browser coverage '+Date.now();
await page.getByLabel('Event name',{exact:true}).fill(title);await page.getByLabel('Start',{exact:true}).fill(iso+'T10:00');await page.getByLabel('Finish',{exact:true}).fill(iso+'T12:00');await page.getByRole('button',{name:'Create event & add people'}).click();
assert.match(await page.locator('h1').innerText(),/Browser coverage/);const eventUrl=page.url();
const shiftUrls=await page.locator('a[href^="/manage/shifts/"]').evaluateAll(links=>links.map(a=>a.href));assert.equal(shiftUrls.length,3);
for(const [i,name] of ['Avery Lane','Bennett Reed','Dana Ellis'].entries()){
await page.goto(shiftUrls[i]);const select=page.getByLabel('Person for this shift');const value=await select.locator('option').filter({hasText:name}).getAttribute('value');await select.selectOption(value);await page.getByRole('button',{name:'Save assignment'}).click();assert.equal(page.url(),eventUrl,await page.locator('main').innerText());
}
await page.getByRole('link',{name:'Review & publish'}).click();await page.getByRole('button',{name:'Publish schedule'}).click();
await page.screenshot({path:path.join(out,'event-desktop.png'),fullPage:true});
await page.goto(base+'/manage/staff/');await page.locator('.employee-card').filter({hasText:'Avery Lane'}).click();const employeeUrl=page.url();
await page.getByRole('button',{name:'Create private sign-in link'}).click();const invitation=await page.locator('#invite-link').inputValue();
const staffContext=await browser.newContext({viewport:{width:390,height:920},reducedMotion:'reduce'});const staff=await staffContext.newPage();monitor(staff);const staffPassword='Browser-test-only-silver-cedar-79!';
await staff.goto(invitation);await staff.getByLabel('New password',{exact:true}).fill(staffPassword);await staff.getByLabel('New password confirmation',{exact:true}).fill(staffPassword);await staff.getByRole('button',{name:'Save password'}).click();await login(staff,'avery.lane@crewline.example',staffPassword);
await staff.screenshot({path:path.join(out,'staff-home-390.png'),fullPage:true});assert.equal(await staff.locator('.next-shift-card').count(),1);await audit(staff,'staff-home-phone');
await staff.goto(invitation);assert.equal(await staff.locator('h1').innerText(),'This link is unavailable');
for(const width of [390,320,768]){
await staff.setViewportSize({width,height:1000});
for(const route of ['/my/','/my/schedule/','/my/team/','/my/time-off/','/my/availability/','/my/account/','/my/open-shifts/','/my/calendar/']){await staff.goto(base+route);assert.equal(await staff.locator('h1').count(),1,route);await fit(staff,route+'-'+width);}
}
await staff.setViewportSize({width:390,height:920});
for(const route of ['/my/schedule/','/my/team/','/my/time-off/','/my/availability/','/my/account/','/my/open-shifts/','/my/calendar/']){await staff.goto(base+route);await audit(staff,route);}
await staff.goto(base+'/my/calendar/');await staff.getByRole('button',{name:'Create private calendar link'}).click();const feed=await staff.locator('#calendar-link').inputValue();let r=await staff.request.get(feed);assert.equal(r.status(),200);assert.match(await r.text(),/BEGIN:VCALENDAR/);assert.doesNotMatch(await r.text(),/Bennett Reed/);
await staff.goto(base+'/my/');const before=await staff.locator('.next-shift-card h2').innerText();
await page.goto(shiftUrls[0]);await page.locator('details.advanced').evaluate(el=>el.open=true);await page.getByLabel('Finish',{exact:true}).fill(iso+'T10:30');await page.getByRole('button',{name:'Save assignment'}).click();
await staff.reload();assert.equal(await staff.locator('.next-shift-card h2').innerText(),before);
await page.goto(eventUrl);await page.getByRole('link',{name:'Review & publish'}).click();await page.getByRole('button',{name:'Publish schedule'}).click();await staff.reload();assert.notEqual(await staff.locator('.next-shift-card h2').innerText(),before);
await staff.goto(base+'/my/time-off/');await staff.getByLabel('First day',{exact:true}).fill(iso);await staff.getByLabel('Last day',{exact:true}).fill(iso);await staff.getByLabel('Note for your manager (optional)',{exact:true}).fill('Fictional browser test');await staff.getByRole('button',{name:'Send time-off request'}).click();assert.match(await staff.locator('.messages').innerText(),/Request sent/);
await page.goto(base+'/manage/requests/');await page.locator('.request-row').filter({hasText:'Fictional browser test'}).getByRole('button',{name:'Approve time off'}).click();assert.match(await page.locator('.messages').innerText(),/approved/);
await page.goto(employeeUrl);await page.getByRole('link',{name:'End employment and access'}).click();await page.getByRole('button',{name:'End employment & revoke access'}).click();assert.match(await page.locator('main').innerText(),/Retained schedule history/);assert.match(await page.locator('main').innerText(),/Browser coverage/);
await staff.goto(base+'/my/');assert.equal(new URL(staff.url()).pathname,'/login/');r=await staff.request.get(feed);assert.equal(r.status(),401);
assert.deepEqual(overflows,[]);assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
assert.deepEqual(accessibility.filter(a=>a.violations.length),[],'Automated accessibility violations; see accessibility.json');
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({passed:true,responsiveChecks:72,flows:['login','csrf browser forms','event creation','assignment','publication','private one-use invitation','staff login','private calendar','draft isolation','time off approval','offboarding','calendar revocation'],errors,failedAssets:failed,overflows},null,2));
console.log('Authenticated browser workflows passed; no runtime errors, missing assets or horizontal overflow. Evidence saved to '+out);
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
