// Use a disposable server: this test deliberately replaces the active recipe.
const {chromium}=require("playwright");
const assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path");
const url=process.env.STUDIO_TEST_URL||"http://127.0.0.1:8766";
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
 try {
  const page=await browser.newPage({viewport:{width:1512,height:1050}});
  const errors=[];page.on("pageerror",e=>errors.push(e.message));page.on("dialog",d=>d.accept());
  let bootstrap=await(await page.request.get(url+"/api/bootstrap")).json();
  const initial=JSON.parse(fs.readFileSync(path.resolve(__dirname,"../../contrib/presets/temporal-motion.json"),"utf8"));
  await page.request.post(url+"/api/config",{headers:{"X-Studio-Token":bootstrap.token},data:initial});
  await page.goto(url);await page.waitForFunction(()=>document.querySelector("#status").dataset.frame);
  const settle=async()=>{await page.evaluate(async()=>{await queue;});assert.equal(await page.locator("body.error").count(),0,await page.locator("#status").textContent());};
  const apply=async()=>{const done=page.waitForResponse(r=>r.url()===url+"/api/frame");await page.click("#applyCode");await done;await page.evaluate(async()=>{await queue;});};
  await page.fill("#search","Canny");
  assert.equal(await page.locator('#librarySelect option[value="block:canny"]').count(),1);
  assert.equal(await page.locator('#librarySelect option[value="api:Canny"]').count(),1);
  await page.selectOption("#librarySelect","api:Canny");
  assert(await page.locator("#catalogDetail").evaluate(e=>e.open));
  assert.match(await page.locator("#catalogBody pre").textContent(),/Canny/);
  await page.click("#closeCatalog");
  await page.selectOption("#librarySelect","block:canny");await settle();
  assert.equal(await page.locator('#blockRuntime option[value="javascript"]').evaluate(e=>e.disabled),true);
  assert.equal(await page.locator('#blockRuntime option[value="cpp"]').evaluate(e=>e.disabled),true);
  await page.fill("#search","");
  await page.selectOption("#libraryCategory","functionGroup");
  assert.equal(await page.locator("#library .library-card").count(),5);
  await page.selectOption("#librarySelect","function:maximum");await settle();
  assert.equal(await page.locator('[data-parameter="expression"]').inputValue(),"maximum(R,G)");
  await page.selectOption("#libraryCategory","customGroup");
  await page.selectOption("#librarySelect","block:custom");await settle();
  assert.equal(await page.locator("#customCode").inputValue(),"");
  const python='def process(channels, params):\n    return (channels["R"] - channels["G"]) * params["gain"]';
  await page.fill("#customCode",python);await apply();await settle();
  let numerical=await page.evaluate(()=>api("/api/frame",{runCode:true}));
  const resultName=await page.locator('[data-parameter="output"]').inputValue();
  assert(numerical.stats[resultName].max>0.6);
  await page.fill("#blockName","Browser custom RGB");await page.click("#saveBlock");await settle();
  await page.selectOption("#libraryCategory","savedGroup");
  assert((await page.locator("#library").textContent()).includes("Browser custom RGB"));
  await page.selectOption("#blockRuntime","javascript");await settle();
  assert.equal(await page.locator("#customCode").inputValue(),"");
  await page.fill("#customCode",'function process(c,p,shape){return c.R.map((r,i)=>(r-c.G[i])*p.gain);}');
  await apply();await settle();
  numerical=await page.evaluate(()=>api("/api/frame",{runCode:true}));assert(numerical.stats[resultName].max>0.6);
  await page.selectOption("#blockRuntime","python");await settle();
  assert.equal(await page.locator("#customCode").inputValue(),python);
  // Applying bad output gives an error; correcting it recovers without losing the graph.
  await page.fill("#customCode",'def process(c,p):\n    return np.zeros((1,1))');
  await apply();
  assert.equal(await page.locator("body.error").count(),1);
  await page.fill("#customCode",python);await apply();await settle();
  const count=await page.locator("#graph .node").count();
  await page.reload();await page.waitForFunction(()=>typeof catalog!=="undefined" && catalog && document.querySelector("#graph .node"));await settle();
  assert.equal(await page.locator("#graph .node").count(),count);
  await page.selectOption("#libraryCategory","exampleGroup");
  for(const id of ["color-distance","blob","lines","motion","contrast"]){
   await page.selectOption("#librarySelect","example:"+id);
   assert(await page.locator("#catalogDetail").evaluate(e=>e.open));
   await page.locator("#catalogBody button").click();await settle();
   assert.equal(await page.locator("#resultImage").getAttribute("src").then(s=>s.startsWith("data:image/jpeg")),true);
  }
  await page.selectOption("#libraryCategory","referenceGroup");
  await page.selectOption("#librarySelect","reference:SI_Eksperimenti_Strojnega_Vida:LinesScan3");
  assert.match(await page.locator("#catalogBody a").getAttribute("href"),/33ac150/);
  await page.click("#closeCatalog");
  for(const width of [390,768,1512]){
   await page.setViewportSize({width,height:1050});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  }
  await page.setViewportSize({width:1512,height:1050});
  await page.selectOption("#libraryCategory","all");
  await page.screenshot({path:path.resolve(__dirname,"../../docs/images/studio-library.png"),fullPage:true});
  assert.deepEqual(errors,[]);
  console.log("Library browser: search, categories, full catalog, functions, Python/JS code, numeric results, runtime compatibility, saved blocks, reload, 5 adaptations and 3 widths passed.");
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
