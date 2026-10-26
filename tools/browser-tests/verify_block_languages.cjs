// Use a disposable server: this deliberately replaces the active algorithm.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const url=process.env.STUDIO_TEST_URL||'http://127.0.0.1:8766';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try {
  const page=await browser.newPage({viewport:{width:1512,height:1050}});
  page.setDefaultTimeout(60000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
  const boot=await(await page.request.get(url+'/api/bootstrap')).json();
  const initial=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../contrib/presets/temporal-motion.json'),'utf8'));
  initial.backend={id:'opencv24',version:'2.4.13.7'};initial.view.locale='sl';
  // Use spatial color algebra so the first frame has meaningful nonzero results.
  initial.nodes.find(n=>n.kind==='algebra').params.expression='wR*R + wG*G + wB*B';
  const configured=await page.request.post(url+'/api/config',{headers:{'X-Studio-Token':boot.token},data:initial});
  assert(configured.ok(),await configured.text());
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  async function settle(){await page.evaluate(()=>queue);assert.equal(await page.locator('body.error').count(),0,await page.locator('#status').textContent());}
  for(const [kind,language] of [['algebra','c'],['gaussian','cpp'],['sobel','java']]){
   const id=await page.evaluate(k=>state.nodes.find(n=>n.kind===k).id,kind);
   await page.locator('#graph .node[data-id="'+id+'"]').focus();
   await page.keyboard.press('Enter');
   assert.equal(await page.locator('#blockRuntime option[value="'+language+'"]').evaluate(e=>e.disabled),false);
   await page.selectOption('#blockRuntime',language);await settle();
   assert.equal(await page.evaluate(k=>state.nodes.find(n=>n.kind===k).runtime,kind),language);
   assert.match(await page.locator('#parameters .note').last().textContent(),kind==='algebra'?/prevedena koda/:/skupnega pogona OpenCV/);
  }
  for(const backend of ['current','opencv24']){
   await page.selectOption('#opencvBackend',backend);await settle();
   const result=await page.evaluate(()=>api('/api/frame',{}));assert(!result.error,JSON.stringify(result));
   assert(result.stats.S.max>0);assert(result.stats.edges.max>0);
   assert.equal(await page.evaluate(()=>state.backend.id),backend);
   assert.equal(await page.locator('#blockRuntime').inputValue(),'java');
   assert.match(await page.locator('#parameters').textContent(),/Java · JDK → OpenCV/);
  }
  const before=await page.evaluate(()=>structuredClone(state));
  const saved=await page.evaluate(()=>api('/api/save',state));
  assert.deepEqual(saved.state.nodes,before.nodes);
  const exported=await page.request.post(url+'/api/export',{headers:{'X-Studio-Token':boot.token},data:before});
  assert(exported.ok(),await exported.text());
  const script=await exported.text();assert.match(script,/def run_language_block/);assert.match(script,/class EngineBridge/);
  await page.reload();await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);await settle();
  assert.deepEqual(await page.evaluate(()=>state.nodes),before.nodes);
  const sobel=before.nodes.find(n=>n.kind==='sobel');await page.locator('#graph .node[data-id="'+sobel.id+'"]').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#blockRuntime').inputValue(),'java');
  await page.screenshot({path:path.resolve(__dirname,'../../docs/images/studio-block-languages.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  console.log('PASS mixed C algebra / C++ Gaussian / Java Sobel: compilation, both OpenCV engines, nonzero output, truthful UI, save/reload and exported adapters');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
