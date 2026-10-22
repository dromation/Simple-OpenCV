// Disposable server only: this test changes the algorithm.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const url=process.env.STUDIO_TEST_URL||'http://127.0.0.1:8766';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try {
  const page=await browser.newPage({viewport:{width:1512,height:1050}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
  const bootstrap=await(await page.request.get(url+'/api/bootstrap')).json();
  const initial=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../contrib/presets/temporal-motion.json'),'utf8'));
  const configured=await page.request.post(url+'/api/config',{headers:{'X-Studio-Token':bootstrap.token},data:initial});assert(configured.ok());
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  const settle=async(ok=true)=>{await page.evaluate(async()=>{await queue;});if(ok)assert.equal(await page.locator('body.error').count(),0,await page.locator('#status').textContent());};
  assert.equal(await page.locator('#opencvBackend option[value="opencv24"]').evaluate(e=>e.disabled),false);
  const before=await page.evaluate(()=>JSON.stringify(state.nodes));
  await page.selectOption('#opencvBackend','opencv24');await settle();
  assert.equal(await page.evaluate(()=>JSON.stringify(state.nodes)),before);
  assert.match(await page.locator('#backendBadge').textContent(),/2\.4\.13\.7/);
  let frame=await page.evaluate(()=>api('/api/frame',{}));assert.equal(frame.backend.version,'2.4.13.7');assert(frame.images);
  await page.fill('#search','Canny');
  assert.equal(await page.locator('#librarySelect option[value="api:Canny"]').count(),0);
  assert.equal(await page.locator('#librarySelect option[value="api24:Canny"]').count(),1);
  await page.fill('#search','');
  for(const kind of ['custom','components'])assert(await page.locator(`#librarySelect option[value="block:${kind}"]`).evaluate(e=>e.disabled));
  await page.selectOption('#libraryCategory','exampleGroup');
  assert(await page.locator('#librarySelect option[value="example:blob"]').evaluate(e=>e.disabled));
  await page.selectOption('#librarySelect','example:lines');await page.locator('#catalogBody button').click();await settle();
  assert.equal(await page.evaluate(()=>state.backend.id),'opencv24');
  const downloadEvent=page.waitForEvent('download');await page.click('#save');const download=await downloadEvent;await settle();
  const saved=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(saved.backend.version,'2.4.13.7');
  await page.selectOption('#opencvBackend','current');await settle();
  await page.evaluate(async s=>{await load(s);},saved);await settle();
  assert.equal(await page.locator('#opencvBackend').inputValue(),'opencv24');
  for(const width of [390,768,1512]){await page.setViewportSize({width,height:1050});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
  await page.selectOption('#locale','ar');await settle();assert.equal(await page.locator('html').getAttribute('dir'),'rtl');
  await page.selectOption('#locale','sl');await settle();
  await page.selectOption('#libraryCategory','all');
  await page.screenshot({path:path.resolve(__dirname,'../../docs/images/studio-opencv24.png'),fullPage:true});
  await page.selectOption('#opencvBackend','current');await settle();
  assert.equal(await page.locator('#librarySelect option[value="block:custom"]').evaluate(e=>e.disabled),false);
  await page.selectOption('#librarySelect','block:components');await settle();
  const incompatible=await page.evaluate(()=>JSON.stringify(state));
  await page.selectOption('#opencvBackend','opencv24');await settle(false);
  assert.equal(await page.locator('body.error').count(),1);
  assert.equal(await page.locator('#opencvBackend').inputValue(),'current');
  assert.equal(await page.evaluate(()=>JSON.stringify(state)),incompatible);
  // Restore a clean current-profile graph for the other browser suites.
  await page.evaluate(async s=>{await load(s);},initial);await settle();
  assert.deepEqual(errors,[]);
  console.log('Backend browser: genuine 2.4 frames, unchanged parameters, compatibility, API catalog, template, save/load, failed-switch preservation, RTL and 3 widths passed.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
