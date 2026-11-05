const {chromium}=require('playwright'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
const url=process.env.STUDIO_TEST_URL||'http://127.0.0.1:8780/SimpleMotocam-HTML/';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try{
  const context=await browser.newContext({viewport:{width:1512,height:1050}}),page=await context.newPage();page.setDefaultTimeout(60000);
  const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));page.on('dialog',d=>d.accept());
  page.on('console',m=>{if(m.type()==='error')console.log('Browser:',m.text());});
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  assert.equal(await page.evaluate(()=>state.backend.id),'browser');assert.equal(await page.locator('#staticLoading').count(),0);
  assert.match(await page.locator('#backendBadge').textContent(),/OpenCV.js 4.13.0/);
  assert.equal(await page.evaluate(()=>Object.keys(blocks).length),28);
  assert(requests.every(r=>!new URL(r).pathname.includes('/api/')));
  assert(requests.every(r=>new URL(r).origin===new URL(url).origin));
  for(const kind of await page.evaluate(()=>Object.keys(blocks).filter(k=>!['source','channels','difference','custom'].includes(k)))){
   const result=await page.evaluate(async kind=>{
    const next=structuredClone(STATIC_DATA.state);next.backend={id:'browser',version:'4.13.0'};
    const p=structuredClone(STATIC_DATA.blocks[kind].params);if('input' in p)p.input='R';if(kind==='algebra')p.expression='clip(R-G,-1,1)';
    next.nodes=next.nodes.slice(0,2).concat({id:'test',kind,params:p,enabled:true,runtime:'javascript'});next.nodes.slice(0,2).forEach(n=>n.runtime='javascript');
    next.view.signal=next.view.result=p.output;
    try{await StaticStudio.api('/api/config',next);return await StaticStudio.api('/api/frame',{});}catch(e){return {error:e.message};}
   },kind);
   assert(!result.error,kind+': '+result.error);assert(Number.isFinite(Object.values(result.stats).at(-1).max));
  }
  await page.reload();await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  await page.click('#addEmpty');await page.evaluate(()=>queue);
  assert.equal(await page.locator('#blockRuntime').inputValue(),'javascript');await page.click('#insertStarter');
  const starter=await page.locator('#customCode').inputValue();assert(starter.includes('function process'));
  await page.click('#applyCode');await page.evaluate(()=>queue);assert.equal(await page.locator('body.error').count(),0,await page.locator('#status').textContent());
  await page.fill('#customCode','function process(c,p){while(true){}}');await page.fill('[data-parameter="timeout"]','0.2');await page.locator('[data-parameter="timeout"]').press('Tab');await page.evaluate(()=>queue);
  await page.click('#applyCode');await page.evaluate(()=>queue);assert.match(await page.locator('#status').textContent(),/timed out/);
  await page.fill('#customCode',starter);await page.fill('[data-parameter="timeout"]','5');await page.locator('[data-parameter="timeout"]').press('Tab');await page.evaluate(()=>queue);
  await page.click('#applyCode');await page.evaluate(()=>queue);assert.equal(await page.locator('body.error').count(),0);
  await page.click('#closeCodeEditor');
  await page.fill('#name','Static browser project');await page.locator('#name').press('Tab');await page.evaluate(()=>queue);
  const saved=await page.evaluate(()=>api('/api/save',state));assert.equal(saved.state.name,'Static browser project');
  const exported=await page.evaluate(()=>api('/api/export',state));assert(exported.includes('export async function processFrame'));
  await page.reload();await page.waitForFunction(()=>typeof state!=='undefined'&&state?.name==='Static browser project');assert.equal(await page.locator('#name').inputValue(),'Static browser project');
  await page.click('#guide');await page.waitForFunction(()=>document.querySelector('#classroomFrame').contentDocument?.querySelector('#locale'));
  await page.click('#closeClassroom');await page.selectOption('#locale','ja');await page.evaluate(()=>queue);assert.equal(await page.locator('html').getAttribute('lang'),'ja-JP');
  await page.selectOption('#locale','sl');await page.evaluate(()=>queue);
  await page.click('#step');await page.evaluate(()=>queue);
  for(const width of [390,768,1512]){await page.setViewportSize({width,height:1050});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
  fs.mkdirSync(path.resolve(__dirname,'../../work'),{recursive:true});
  await page.screenshot({path:path.resolve(__dirname,'../../work/static-browser.png'),fullPage:true});
  assert.deepEqual(errors,[]);assert(requests.every(r=>!new URL(r).pathname.includes('/api/')));
  console.log('PASS static index.html: local assets only, all 28 kinds, custom JS, timeout/recovery, save/reload/export, classroom, language changes and three widths.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
