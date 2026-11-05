const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const url=process.env.STUDIO_TEST_URL||'http://127.0.0.1:8780/SimpleMotocam-HTML/';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),args:['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']});
 try{
  const context=await browser.newContext({permissions:['camera']}),page=await context.newPage();page.setDefaultTimeout(60000);page.on('dialog',d=>d.accept());
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  const fixture=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../work/static-reference.json'),'utf8'));
  const results=await page.evaluate(async fixture=>{
   const worker=new Worker(new URL('browser-worker.js',document.baseURI));let id=0;
   const run=data=>new Promise((resolve,reject)=>{const current=++id;const timer=setTimeout(()=>reject(Error('Worker timeout')),30000);worker.onmessage=({data})=>{if(data.id!==current||data.timeout)return;clearTimeout(timer);data.error?reject(Error(data.error)):resolve(data);};worker.postMessage({...data,id:current,action:'frame'});});
   const results=[];
   try{
    for(const test of fixture.tests){
     const state=structuredClone(test.state);state.backend={id:'browser',version:'4.13.0'};state.nodes.forEach(n=>n.runtime='javascript');
     const actual=await run({state,rgba:new Uint8ClampedArray(fixture.rgba),width:fixture.width,height:fixture.height,previous:null});
     const values=actual.values[state.view.result];let max=0;for(let i=0;i<values.length;i++)max=Math.max(max,Math.abs(values[i]-test.output[i]));results.push({kind:test.kind,max});
    }
   }finally{worker.terminate();}
   return results;
  },fixture);
  for(const result of results)assert(result.max<3e-5,JSON.stringify(result));
  // User-entered algebra stays a restricted parser, not JavaScript eval.
  for(const expression of ['globalThis.fetch("x")','R.constructor','R**R','sqrt(R,G)','R;alert(1)']){
   assert(await page.evaluate(text=>{try{SMEngine.expression(text,new Set(['R','G']));return false;}catch{return true;}},expression));
  }
  const exponent=await page.evaluate(()=>SMEngine.expression('-R**2',new Set(['R'])));assert.equal(exponent.k,'neg');
  // Image is persisted in IndexedDB, then reused by a fresh page.
  await page.evaluate(async()=>{
   const c=document.createElement('canvas');c.width=64;c.height=48;const x=c.getContext('2d');x.fillStyle='#ff0000';x.fillRect(0,0,64,48);
   const blob=await new Promise(resolve=>c.toBlob(resolve));const asset=await uploadMedia(blob,'.png');
   const next=structuredClone(state);next.source={...next.source,type:'image',asset:asset.asset};await load(next);
  });
  let stats=await page.evaluate(()=>api('/api/frame',{}));assert.equal(stats.stats.R.max,1);assert.equal(stats.stats.G.max,0);
  await page.reload();await page.waitForFunction(()=>document.querySelector('#status').dataset.frame);
  stats=await page.evaluate(()=>api('/api/frame',{}));assert.deepEqual(stats.size,[64,48]);assert.equal(stats.stats.R.min,1);
  // Export is actually imported and executed, using only static worker files.
  const exported=await page.evaluate(()=>api('/api/export',state));
  const moduleURL=new URL('test-export.js',url).href;await page.route(moduleURL,route=>route.fulfill({contentType:'text/javascript',body:exported}));
  const parity=await page.evaluate(async({moduleURL,fixture})=>{
   const module=await import(moduleURL),image={data:new Uint8ClampedArray(fixture.rgba),width:fixture.width,height:fixture.height};
   const first=await module.processFrame(image),changed={...image,data:image.data.slice()};changed.data[0]=(changed.data[0]+71)%256;
   const second=await module.processFrame(changed);module.close();
   return {first:Array.from(first.dR),second:Array.from(second.dR),r:Array.from(second.R),red:changed.data[0]};
  },{moduleURL,fixture});
  assert(parity.first.every(x=>x===0));assert(parity.second.slice(1).every(x=>x===0));
  assert(Math.abs(parity.second[0]-(parity.red-fixture.rgba[0])/255)<1e-7);assert(Math.abs(parity.r[0]-parity.red/255)<1e-7);
  // Camera is fake browser input, never the real device in this automated test.
  await page.evaluate(async()=>{const next=structuredClone(state);next.source={type:'camera',camera:0,asset:''};await load(next);});
  const pending=await page.evaluate(()=>api('/api/frame',{}));assert(pending.needsSourceRun);
  const camera=await page.evaluate(()=>api('/api/frame',{runCode:true}));assert(camera.size[0]>0);await page.evaluate(()=>api('/api/stop',{}));
  await page.locator('#media').setInputFiles(path.resolve(__dirname,'../../work/static-video.webm'));await page.evaluate(()=>queue);
  assert.equal(await page.locator('body.error').count(),0,await page.locator('#status').textContent());
  const video=await page.evaluate(async()=>{
   const first=await api('/api/frame',{}),second=await api('/api/frame',{});return {a:first.frame,b:second.frame,size:second.size};
  });assert.equal(video.b,video.a+1);assert.deepEqual(video.size,[64,48]);
  // Legacy imports preserve foreign code as a disabled draft, with explicit confirmation.
  const imported=await page.evaluate(async()=>{
   const next=structuredClone(STATIC_DATA.state);next.backend={id:'opencv24',version:'2.4.13.7'};
   next.nodes.push({id:'legacy-code',kind:'custom',enabled:true,params:{...STATIC_DATA.blocks.custom.params,code:'def process(c,p):\n    return c["R"]'}});
   const result=await api('/api/config',next);return result.state.nodes.at(-1);
  });assert.equal(imported.runtime,'python');assert.equal(imported.enabled,false);assert(imported.params.code.startsWith('def process'));
  // Teaching sequence image is also loaded through local files, never an API upload.
  await page.evaluate(()=>loadDetectionSequence(SEQUENCE_DATA.lessons.find(x=>x.sample).id));await page.evaluate(()=>queue);
  assert.equal(await page.locator('body.error').count(),0,await page.locator('#status').textContent());
  assert.equal(await page.evaluate(()=>state.source.type),'image');
  console.log('PASS 24 browser blocks versus native numerical reference; restricted algebra; image persistence; executable JS export; explicit browser camera.');
  console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
