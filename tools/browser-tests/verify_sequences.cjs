const {chromium}=require('playwright');
const assert=require('node:assert/strict');const path=require('node:path');
const url=process.env.STUDIO_TEST_URL||'http://127.0.0.1:8766';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1512,height:1050}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  assert.equal(await page.locator('#opencvBackend').inputValue(),'opencv24');
  assert.equal(await page.locator('#library [data-entry^="example:"]').count(),0);
  assert.equal(await page.locator('#additionalAlgorithms').evaluate(e=>e.open),false);
  await page.click('#openAdditional');
  await page.fill('#additionalSearch','LinesScan3');
  assert.equal(await page.locator('#additionalList [data-entry="example:lines"]').count(),1);
  for(const width of [390,768,1512]){await page.setViewportSize({width,height:1050});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
  await page.screenshot({path:path.resolve(__dirname,'../../docs/images/studio-additional-algorithms.png'),fullPage:true});
  await page.click('#closeAdditional');
  await page.click('#guide');
  const frame=page.frameLocator('#classroomFrame');
  await frame.locator('[data-sequence="red-part"]').click();
  assert.equal(await frame.locator('#sequenceContent .sequence-chain li').count(),6);
  assert.match(await frame.locator('#sequenceContent').textContent(),/Joseph Howse/);
  assert.equal(await page.locator('#classroom').evaluate(e=>e.open),true);
  await page.screenshot({path:path.resolve(__dirname,'../../docs/images/studio-detection-classroom.png'),fullPage:true});
  for(const id of ['red-part','bright-regions','motion','lines','edges','uneven-light']){
   if(!await page.locator('#classroom').evaluate(e=>e.open))await page.click('#guide');
   await frame.locator(`[data-sequence="${id}"]`).click();
   await frame.locator('#loadSequence').click();
   await page.waitForFunction(()=>!document.querySelector('#classroom').open);
   await page.evaluate(async()=>{await queue;});
   assert.equal(await page.locator('body.error').count(),0,await page.locator('#status').textContent());
   assert.equal(await page.locator('#opencvBackend').inputValue(),'opencv24');
   const result=await page.evaluate(()=>api('/api/frame',{}));assert.equal(result.backend.version,'2.4.13.7');
   const channel=await page.evaluate(()=>state.view.result);assert(result.stats[channel].max>0,id);
  }
  await page.selectOption('#librarySelect','block:custom');await page.evaluate(async()=>{await queue;});
  await page.fill('#customCode','def process(c,p):\n    return cv24.run("gaussian", c["R"]-c["G"], size=3, sigma=1)');
  await page.click('#applyCode');await page.evaluate(async()=>{await queue;});assert.equal(await page.locator('body.error').count(),0);
  await page.click('#guide');await frame.locator('[data-sequence="lines"]').click();
  for(const lang of ['en','sl','ja','ar']){
   await frame.locator('#locale').selectOption(lang);await page.evaluate(async()=>{await queue;});
   assert.equal(await page.locator('#locale').inputValue(),lang);
   assert((await frame.locator('#sequenceContent h2').textContent()).length>3);
  }
  for(const width of [390,768,1512]){await page.setViewportSize({width,height:1050});assert(await frame.locator('html').evaluate(e=>e.scrollWidth<=innerWidth+1));}
  await frame.locator('#locale').selectOption('sl');await page.evaluate(async()=>{await queue;});
  await frame.locator('#topics button:not(.sequence-topic)').first().click();
  assert.equal(await frame.locator('#sequenceContent').isVisible(),false);
  assert.equal(await frame.locator('#lessonTitle').isVisible(),true);
  assert.deepEqual(errors,[]);
  console.log('Detection classroom: six real 2.4 recipes/scenes, sources, in-app load, custom native code, synchronized languages, 3 widths and foundation return passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
