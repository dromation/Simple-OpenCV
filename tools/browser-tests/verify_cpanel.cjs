// Disposable cPanel WSGI preview; never point this at somebody's live domain.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const url=process.env.STUDIO_TEST_URL||'http://127.0.0.1:8770/vision/';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try {
  const context=await browser.newContext({httpCredentials:{username:'studio',password:process.env.STUDIO_TEST_PASSWORD},viewport:{width:1512,height:1050}});
  const page=await context.newPage();page.setDefaultTimeout(60000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  assert.equal(await page.evaluate(()=>hosting.hosted),true);
  assert.equal(await page.evaluate(()=>state.backend.id),'opencv24');
  const before=await page.evaluate(()=>state.nodes);
  await page.locator('#graph .node[data-id="source"]').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#parameters option[value="camera"]').count(),0);
  await page.click('#guide');await page.waitForFunction(()=>document.querySelector('#classroomFrame').contentDocument?.querySelector('#locale'));
  assert((await page.locator('#classroomFrame').getAttribute('src')).includes('/vision/manuals/learning/'));
  await page.click('#closeClassroom');
  await page.fill('#name','cPanel browser test');await page.locator('#name').press('Tab');await page.evaluate(()=>queue);
  const saved=await page.evaluate(()=>api('/api/save',state));assert.equal(saved.state.name,'cPanel browser test');
  const exported=await page.evaluate(()=>api('/api/export',state,true));assert(exported.includes('class StudioPipeline'));
  await page.reload();await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  assert.equal(await page.locator('#name').inputValue(),'cPanel browser test');
  assert.deepEqual(await page.evaluate(()=>state.nodes),before);
  const other=await browser.newContext({httpCredentials:{username:'studio',password:process.env.STUDIO_TEST_PASSWORD}});
  const otherPage=await other.newPage();await otherPage.goto(url);await otherPage.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  assert.notEqual(await otherPage.locator('#name').inputValue(),'cPanel browser test');await other.close();
  for(const width of [390,768,1512]){
   await page.setViewportSize({width,height:1050});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  }
  await page.screenshot({path:path.resolve(__dirname,'../../work/cpanel-browser.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  console.log('PASS packaged Linux cPanel app: real OpenCV 2.4, authentication, /vision mount, classroom, state reload, separate browser sessions, export and 3 widths.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
