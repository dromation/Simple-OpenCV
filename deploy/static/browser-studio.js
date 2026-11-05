/* Browser-only API for the shared Studio interface. All data stays on this device. */
"use strict";
window.StaticStudio=(()=>{
 const clone=x=>structuredClone(x), backend={id:"opencv24",version:"2.4.13.7"};
 const backends={opencv24:{name:"OpenCV 2.4 · WebAssembly",version:"2.4.13.7",available:true,kinds:"*"},browser:{name:"OpenCV.js · browser",version:"4.13.0",available:true,kinds:"*"}};
 const probes=new Map();
 async function probeEngine(selected){
  if(!backends[selected?.id]||backends[selected.id].version!==selected.version)throw Error("Unsupported OpenCV engine/version");
  const result=await runWorker({action:"probe",backend:selected});
  if(result.version!==selected.version)throw Error("Unexpected OpenCV binary: "+result.version);
  probes.set(selected.id,result);return result;
 }
 let db,state,revision=0,index=0,previous=null,authorized=false,worker,requestId=0;
 let media=null,mediaKey="",mediaURL=null,stream=null;
 const pending=new Map(),canvas=document.createElement("canvas");
 const ctx=canvas.getContext("2d",{willReadFrequently:true});
 const uid=()=>Date.now().toString(36)+Array.from(crypto.getRandomValues(new Uint32Array(2)),x=>x.toString(16)).join("");
 const base=new URL(".",document.baseURI);
 const info={hosted:false,static:true,allowCode:true,allowCompilers:false,camera:true};
 const message=(sl,en)=>state?.view.locale==="sl"?sl:en;
 function store(name,mode,callback){return new Promise((resolve,reject)=>{
  const transaction=db.transaction(name,mode),request=callback(transaction.objectStore(name));
  transaction.oncomplete=()=>resolve(request.result);transaction.onerror=()=>reject(Error("Browser storage: "+transaction.error?.message));transaction.onabort=()=>reject(Error("Browser storage is full or unavailable; download your JSON project."));
 });}
 const get=(name,key)=>store(name,"readonly",s=>s.get(key));
 const put=(name,value,key)=>store(name,"readwrite",s=>s.put(value,key));
 const all=name=>store(name,"readonly",s=>s.getAll());
 function startWorker(){
  worker=new Worker(new URL("browser-worker.js",base));
  worker.onmessage=({data})=>{
   const p=pending.get(data.id);if(!p)return;
   if(data.timeout){clearTimeout(p.timer);p.timer=setTimeout(()=>failWorker("Block execution timed out"),Math.min(30,data.timeout)*1000);return;}
   clearTimeout(p.timer);pending.delete(data.id);data.error?p.reject(Error(data.error)):p.resolve(data);
  };
  worker.onerror=()=>failWorker("Cannot load browser worker / OpenCV engine. Upload the entire ZIP, including vendor/, not only index.html.");
 }
 function failWorker(error){worker?.terminate();worker=null;for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error(error));}pending.clear();}
 function runWorker(data,timeout=45000){
  if(!worker)startWorker();const id=++requestId;
  return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject,timer:setTimeout(()=>failWorker("Processing timed out; reduce image size or check your code."),timeout)});worker.postMessage({...data,id});});
 }
 function stop(){stream?.getTracks().forEach(track=>track.stop());stream=null;media?.pause?.();media=null;mediaKey="";if(mediaURL)URL.revokeObjectURL(mediaURL);mediaURL=null;previous=null;}
 function loaded(element,event){return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>finish(Error("Media load timed out / unsupported browser codec")),15000);
  function finish(error){clearTimeout(timer);element.removeEventListener(event,ok);element.removeEventListener("error",bad);error?reject(error):resolve();}
  const ok=()=>finish(),bad=()=>finish(Error("Browser cannot decode this image/video; try PNG, JPEG, MP4 or WebM. "+(element.error?.message||"")));
  element.addEventListener(event,ok,{once:true});element.addEventListener("error",bad,{once:true});
 });}
 async function capture(runCode){
  const source=state.source,key=source.type+":"+source.asset;
  if(source.type==="synthetic"){
   canvas.width=640;canvas.height=360;ctx.fillStyle="#505050";ctx.fillRect(0,0,640,360);ctx.strokeStyle="#585858";ctx.lineWidth=1;
   for(let x=0;x<640;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,360);ctx.stroke();}
   for(let y=0;y<360;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(640,y);ctx.stroke();}
   const x=Math.round(320+Math.sin(index*.035)*140.8),y=180;ctx.fillStyle="#d22d2d";ctx.fillRect(x-62,y-60,124,120);
   function circle(cx,cy,r,color){ctx.beginPath();ctx.fillStyle=color;ctx.arc(cx,cy,r,0,Math.PI*2);ctx.fill();}
   circle(x,y,40,"#919191");circle(x,y,28,"#1e1e1e");for(const dx of [-47,47])for(const dy of [-45,45])circle(x+dx,y+dy,7,"#191919");
   return {rgba:ctx.getImageData(0,0,640,360).data,width:640,height:360,originalSize:[640,360]};
  }
  if(mediaKey!==key){
   stop();
   if(source.type==="camera"){
    if(!runCode)return {needsSourceRun:true};
    if(!navigator.mediaDevices?.getUserMedia)throw Error("Camera requires HTTPS and browser permission.");
    stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:360}},audio:false});
    media=document.createElement("video");media.muted=true;media.playsInline=true;const wait=loaded(media,"loadeddata");media.srcObject=stream;await media.play();await wait;
   }else{
    const blob=await get("assets",source.asset);if(!blob)throw Error(message("Ponovno izberi sliko ali video za ta brskalnik.","Select this image/video again in this browser."));
    mediaURL=URL.createObjectURL(blob);media=document.createElement(source.type==="image"?"img":"video");
    if(source.type==="video"){media.muted=true;media.playsInline=true;media.preload="auto";}
    const wait=loaded(media,source.type==="image"?"load":"loadeddata");media.src=mediaURL;await wait;
   }
   mediaKey=key;
  }
  if(source.type==="video"){
   const target=index/30;if(target>=media.duration)return {ended:true};
   if(Math.abs(media.currentTime-target)>.001){const wait=loaded(media,"seeked");media.currentTime=target;await wait;}
  }
  const w=media.naturalWidth||media.videoWidth,h=media.naturalHeight||media.videoHeight;
  if(!w||!h)throw Error("No image data yet");const scale=Math.min(1,960/Math.max(w,h));canvas.width=Math.round(w*scale);canvas.height=Math.round(h*scale);ctx.drawImage(media,0,0,canvas.width,canvas.height);
  return {rgba:ctx.getImageData(0,0,canvas.width,canvas.height).data,width:canvas.width,height:canvas.height,originalSize:[w,h]};
 }
 function preview(values,w,h,signed,gain){
  const c=document.createElement("canvas");c.width=w;c.height=h;const context=c.getContext("2d"),image=context.createImageData(w,h);
  for(let i=0;i<values.length;i++){const v=Math.min(255,Math.max(0,255*(signed ? .5+values[i]*gain/2 : values[i]*gain)));image.data[4*i]=image.data[4*i+1]=image.data[4*i+2]=v;image.data[4*i+3]=255;}
  context.putImageData(image,0,0);return c.toDataURL("image/jpeg",.85);
 }
 function convertBuiltin(input){
  const next=clone(input);next.backend=clone(backends[input.backend?.id]?input.backend:backend);
  for(const n of next.nodes){if(n.kind!=="custom")n.runtime="javascript";else n.runtime??=input.backend?.id==="browser"?"javascript":"python";}
  return next;
 }
 async function catalog(){
  const result=clone(STATIC_DATA.catalog);
  result.backends=clone(backends);
  result.runtimes={javascript:{name:"JavaScript · browser",available:true,kinds:"*",api:1}};
  for(const [id,name]of [["python","Python"],["c","C"],["cpp","C++"],["java","Java"]])result.runtimes[id]={name:name+" · draft",available:false,kinds:["custom"],reason:"draftOnly",api:1};
  result.starters.javascript='function process(channels, params, shape) {\n  return channels[params.input].map(x => x * params.gain);\n}';
  result.entries=result.entries.filter(e=>e.type!=="api");
  for(const e of result.entries){if(e.state)e.state=convertBuiltin(e.state);delete e.backends;}
  for(const [id,probe]of probes)for(const name of probe.functions)result.entries.push({id:id+"api:"+name,type:"api",group:"apiGroup",backends:[id],label:"cv."+name,signature:"OpenCV "+probe.version+" · "+name,source:id==="opencv24"?"https://docs.opencv.org/2.4/":"https://docs.opencv.org/4.13.0/",note:"apiHint"});
  for(const record of await all("projects"))result.entries.push({id:"project:"+record.id,type:"example",additional:true,group:"savedGroup",label:record.state.name,state:record.state,note:"recipeHint"});
  for(const record of await all("blocks"))result.entries.push({id:"saved:"+record.id,type:"example",additional:true,group:"savedGroup",label:record.state.name,state:record.state,note:"recipeHint"});
  return result;
 }
 let initializing;
 async function initialize(){
  if(initializing)return initializing;
  initializing=(async()=>{
   db=await new Promise((resolve,reject)=>{
    const request=indexedDB.open("simplemotocam-static-v1:"+base.pathname,1);
    request.onupgradeneeded=()=>{for(const name of ["settings","assets","projects","blocks"])request.result.createObjectStore(name);};request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(Error("Browser storage unavailable. Enable site storage / leave private mode."));
   });
   const saved=await get("settings","working");state=SMEngine.validate(saved||convertBuiltin(STATIC_DATA.state),STATIC_DATA.blocks);
   await probeEngine(backend);
   if(state.backend.id!==backend.id)await probeEngine(state.backend);
   for(const lesson of window.SEQUENCE_DATA?.lessons||[])lesson.state=convertBuiltin(lesson.state);
   document.getElementById("staticLoading")?.remove();
  })();return initializing;
 }
 async function api(path,data){
  await initialize();
  if(path==="/api/bootstrap")return {state:clone(state),blocks:clone(STATIC_DATA.blocks),catalog:await catalog(),token:"browser-local",revision,hosting:info,projects:await api("/api/projects")};
  if(path==="/api/config"){
   let next=clone(data);
   const foreignEngine=!backends[next.backend?.id];
   const foreignCode=next.nodes?.some(n=>n.kind==="custom"&&n.enabled!==false&&(n.runtime|| (next.backend?.id==="browser"?"javascript":"python"))!=="javascript");
   if(foreignEngine||foreignCode){
    if(!confirm(message("Pripravim brskalniško kopijo? Nepodprt pogon se zamenja z OpenCV 2.4.13.7; Python/C/C++/Java koda ostane ohranjena kot izključen osnutek.","Create a browser copy? An unsupported engine changes to OpenCV 2.4.13.7; Python/C/C++/Java code is preserved as a disabled draft.")))throw Error("Browser conversion cancelled");
    next=convertBuiltin(next);
    for(const n of next.nodes)if(n.kind==="custom"&&n.runtime!=="javascript")n.enabled=false;
   }
   // Built-in blocks call the selected compiled engine; their host adapter is JavaScript.
   for(const n of next.nodes||[]){if(n.kind!=="custom")n.runtime="javascript";else n.runtime??=next.backend?.id==="browser"?"javascript":"python";}
   next=SMEngine.validate(next,STATIC_DATA.blocks);
   if(["image","video"].includes(next.source.type)&&!(await get("assets",next.source.asset)))throw Error("Media is not stored in this browser. Select it again.");
   const newBackend=JSON.stringify(next.backend)!==JSON.stringify(state.backend);
   const changed=newBackend||JSON.stringify(next.nodes)!==JSON.stringify(state.nodes)||JSON.stringify(next.source)!==JSON.stringify(state.source);
   const newSource=JSON.stringify(next.source)!==JSON.stringify(state.source);
   if(newBackend)await probeEngine(next.backend);
   await put("settings",next,"working");
   if(newSource){stop();index=0;}if(changed){previous=null;authorized=false;}
   state=next;revision++;return {state:clone(state),revision,...(newBackend?{catalog:await catalog()}:{})};
  }
  if(path==="/api/frame"){
   const hasCode=state.nodes.some(n=>n.kind==="custom"&&n.enabled&&n.params.code.trim());
   if(hasCode&&!authorized){if(!data?.runCode)return {needsCodeRun:true,revision};authorized=true;}
   const started=performance.now(),image=await capture(data?.runCode);if(image.ended||image.needsSourceRun)return {...image,revision};
   const result=await runWorker({action:"frame",...image,state,previous});
   const stats={};for(const [name,values]of Object.entries(result.values)){let min=Infinity,max=-Infinity,sum=0;for(const x of values){min=Math.min(min,x);max=Math.max(max,x);sum+=x;}stats[name]={min,max,mean:sum/values.length};}
   previous=result.previous;index++;
   return {revision,frame:index,ready:result.ready,backend:clone(state.backend),size:[image.width,image.height],originalSize:image.originalSize,stats,processingMs:Math.round(performance.now()-started),images:{camera:canvas.toDataURL("image/jpeg",.85),signal:preview(result.values[state.view.signal],image.width,image.height,state.view.signed,state.view.gain),result:preview(result.values[state.view.result],image.width,image.height,false,state.view.gain)}};
  }
  if(path==="/api/stop"){stop();return {stopped:true};}
  if(path==="/api/projects")return (await all("projects")).sort((a,b)=>b.savedAt.localeCompare(a.savedAt)).map(r=>({id:r.id,name:r.state.name,savedAt:r.savedAt}));
  if(path.startsWith("/api/projects/")){const r=await get("projects",decodeURIComponent(path.split("/").at(-1)));if(!r)throw Error("Project not found");return r;}
  if(path==="/api/save"){
   const record={id:uid(),savedAt:new Date().toISOString(),state:SMEngine.validate(data,STATIC_DATA.blocks)};await put("projects",record,record.id);return record;
  }
  if(path==="/api/library")return catalog();
  if(path==="/api/library/save"){
   const copy=clone(data.state),index=copy.nodes.findIndex(n=>n.id===data.selected);if(index<2)throw Error("Select an algorithm block");
   copy.nodes=copy.nodes.slice(0,index+1);const output=copy.nodes.at(-1).params.output||"R";copy.view.signal=copy.view.result=output;copy.name=data.name;
   const record={id:uid(),state:SMEngine.validate(copy,STATIC_DATA.blocks)};await put("blocks",record,record.id);return catalog();
  }
  if(path==="/api/export")return exportAlgorithm(SMEngine.validate(data,STATIC_DATA.blocks));
  throw Error("Unknown browser action: "+path);
 }
 async function upload(blob,extension){
  await initialize();if(blob.byteLength!==undefined)blob=new Blob([blob],{type:"image/png"});
  if(blob.size>100*1024*1024)throw Error("Media limit: 100 MB");
  const image=[".png",".jpg",".jpeg",".bmp",".webp"].includes(extension),video=[".mp4",".webm",".mov",".mkv",".avi"].includes(extension);
  if(!image&&!video)throw Error("Unsupported media type");const asset=uid()+extension;await put("assets",blob,asset);return {asset,type:image?"image":"video"};
 }
 function exportAlgorithm(state){
  return `// SimpleOpenCV browser algorithm · MIT. OpenCV ${state.backend.version}.\n// Place alongside browser-worker.js, browser-engine.js, browser-opencv24.js and vendor/.\n// Import processFrame from this ES module in a page served via HTTP(S).\nexport const STATE = ${JSON.stringify(state,null,2)};\nlet worker, sequence=0, previous=null;\nexport function reset(){previous=null;}\nexport function close(){worker?.terminate();worker=null;previous=null;}\nlet busy=false;\nexport async function processFrame(imageData){\n if(busy)throw Error('Await the previous frame');busy=true;\n try {\n if(!worker)worker=new Worker(new URL('./browser-worker.js',import.meta.url));\n const id=++sequence;\n const result=await new Promise((resolve,reject)=>{\n  let timer;const arm=seconds=>{clearTimeout(timer);timer=setTimeout(()=>{close();reject(Error('Block execution timed out'));},seconds*1000);};arm(45);\n  worker.onmessage=({data})=>{if(data.id!==id)return;if(data.timeout){arm(data.timeout);return;}clearTimeout(timer);data.error?reject(Error(data.error)):resolve(data);};\n  worker.onerror=()=>{clearTimeout(timer);close();reject(Error('Cannot load browser runtime'));};\n  worker.postMessage({id,action:'frame',state:STATE,rgba:imageData.data,width:imageData.width,height:imageData.height,previous});\n });\n previous=result.previous;return result.values;\n }finally{busy=false;}\n}\n`;
 }
 window.addEventListener("pagehide",()=>{stop();worker?.terminate();});
 async function resetWorkspace(){if(db){await put("settings",convertBuiltin(STATIC_DATA.state),"working");location.reload();}}
 document.getElementById("staticReset")?.addEventListener("click",()=>{if(confirm("Reset the current workspace? Saved projects and media are kept."))resetWorkspace();});
 return {api,upload,defaultRuntime:"javascript",exportName:"simpleopencv_algorithm.js",exportMime:"text/javascript",stop};
})();
