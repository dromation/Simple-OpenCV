const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const url=process.env.STUDIO_TEST_URL||'http://127.0.0.1:8766';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try {
  const page=await browser.newPage({viewport:{width:1512,height:1050}});const errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
  const bootstrap=await(await page.request.get(url+'/api/bootstrap')).json();
  const initial=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../contrib/presets/temporal-motion.json'),'utf8'));
  initial.backend={id:'opencv24',version:'2.4.13.7'};
  await page.request.post(url+'/api/config',{headers:{'X-Studio-Token':bootstrap.token},data:initial});
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  await page.click('#addEmpty');await page.evaluate(()=>queue);
  async function apply(){
   const [response]=await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/frame') && r.request().postDataJSON()?.runCode===true),page.click('#applyCode')]);
   const data=await response.json();await page.evaluate(()=>queue);return data;
  }
  for(const language of ['c','cpp','java']) {
   assert(await page.evaluate(l=>catalog.runtimes[l].available,language),language+' compiler required for this browser check');
   await page.selectOption('#blockRuntime',language);await page.evaluate(()=>queue);
   await page.click('#insertStarter');
   const starter=await page.locator('#customCode').inputValue();
   assert(starter.includes('process('));assert(await page.locator('#applyCode').isEnabled());
   await page.selectOption('[data-parameter="input"]','R');await page.evaluate(()=>queue);
   await page.fill('[data-parameter="gain"]','2');await page.locator('[data-parameter="gain"]').press('Tab');await page.evaluate(()=>queue);
   let result=await apply();assert(!result.error,JSON.stringify(result));
   const output=await page.evaluate(()=>state.nodes.at(-1).params.output);
   assert(Math.abs(result.stats[output].max-2*result.stats.R.max)<1e-6,language);
   assert.equal(await page.evaluate(()=>state.backend.id),'opencv24');
   await page.fill('#customCode',starter+'\nthis is invalid source');
   result=await apply();assert.match(result.error,/compilation/);
   await page.waitForFunction(()=>document.querySelector('#codeEditorStatus').textContent.includes('compilation'));
   await page.fill('#customCode',starter);result=await apply();assert(!result.error);
  }
  const saved=await page.evaluate(()=>api('/api/save',state));
  assert.equal(saved.state.nodes.at(-1).runtime,'java');
  assert(saved.state.nodes.at(-1).codeDrafts.c.includes('process('));
  assert(saved.state.nodes.at(-1).codeDrafts.cpp.includes('process('));
  await page.screenshot({path:path.resolve(__dirname,'../../docs/images/studio-compiled-code.png'),fullPage:true});
  await page.click('#closeCodeEditor');
  await page.reload();await page.waitForFunction(()=>typeof catalog!=='undefined' && catalog);
  await page.locator('#graph .node').last().locator('[data-action="edit-code"]').click();
  assert.equal(await page.locator('#blockRuntime').inputValue(),'java');
  assert.deepEqual(errors,[]);
  console.log('PASS C/C++/Java editor: real compilation, numeric output, diagnostics/recovery, per-language drafts, save/reload, OpenCV 2.4 unchanged');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
