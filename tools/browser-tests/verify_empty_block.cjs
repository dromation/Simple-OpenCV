// Disposable session only: arbitrary-language drafts must survive save/reload.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const url=process.env.STUDIO_TEST_URL||'http://127.0.0.1:8766';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try {
  const page=await browser.newPage({viewport:{width:1512,height:1050}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  async function settle(){await page.evaluate(()=>queue);}
  await page.click('#addEmpty');await settle();
  assert.equal(await page.locator('#customCode').inputValue(),'');
  assert.equal(await page.locator('#blockRuntime option[value="cpp"]').evaluate(e=>e.disabled),false);
  await page.selectOption('#blockRuntime','cpp');await settle();
  assert(await page.locator('#applyCode').isDisabled());
  const cpp='// Work in progress\nfloat process(float x) { return x * 2; }';
  await page.fill('#customCode',cpp);await page.click('#saveCodeDraft');await settle();
  await page.fill('#customLanguage','rust');await page.click('#setCustomLanguage');await settle();
  assert.equal(await page.locator('#customCode').inputValue(),'');
  const rust='fn process(input: &[f32]) -> Vec<f32> { input.to_vec() }';
  await page.fill('#customCode',rust);await page.click('#saveCodeDraft');await settle();
  const record=await page.evaluate(()=>api('/api/save',state));
  let node=record.state.nodes.at(-1);
  assert.equal(node.enabled,false);assert.equal(node.runtime,'rust');assert.equal(node.params.code,rust);
  assert.equal(node.codeDrafts.cpp,cpp);
  await page.reload();await page.waitForFunction(()=>typeof catalog!=='undefined' && catalog);
  await page.evaluate(s=>load(s),record.state);await settle();
  await page.locator('#graph .node').last().click();
  assert.equal(await page.locator('#customCode').inputValue(),rust);
  await page.selectOption('#blockRuntime','cpp');await settle();
  assert.equal(await page.locator('#customCode').inputValue(),cpp);
  await page.selectOption('#blockRuntime','python');await settle();
  const python='def process(c,p):\n    return (c["R"]-c["G"])*p["gain"]';
  await page.fill('#customCode',python);await page.click('#applyCode');await settle();
  const stats=await page.evaluate(async()=>{let r=await api('/api/frame',{runCode:true});return r.stats[state.nodes.at(-1).params.output];});
  assert(stats.max>0.6);
  // A syntax-incomplete Python draft remains saveable and bypassed.
  await page.fill('#customCode','def process(');await page.click('#saveCodeDraft');await settle();
  assert.equal(await page.locator('body.error').count(),0);
  const draft=await page.evaluate(()=>api('/api/save',state));
  assert.equal(draft.state.nodes.at(-1).params.code,'def process(');
  await page.fill('#customLanguage','rust');await page.click('#setCustomLanguage');await settle();
  assert.equal(await page.locator('#customCode').inputValue(),rust);
  for(const width of [390,768,1512]){await page.setViewportSize({width,height:1050});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
  await page.screenshot({path:path.resolve(__dirname,'../../docs/images/studio-empty-block.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  console.log('PASS empty block: arbitrary languages, persistent drafts, bypass, Python execution, incomplete code, responsive layout');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
