"use strict";
importScripts("browser-engine.js");
const engines=new Map();
function engine(backend){
 const expected={opencv24:"2.4.13.7",browser:"4.13.0"};
 if(!backend||expected[backend.id]!==backend.version)throw Error("Unsupported OpenCV engine/version");
 if(!engines.has(backend.id))engines.set(backend.id,(async()=>{
  if(backend.id==="opencv24"){
   importScripts("vendor/opencv24/opencv24.js","browser-opencv24.js");
   return SMOpenCV24();
  }
  importScripts("vendor/opencv.js");
  await new Promise((resolve,reject)=>{
   const started=Date.now();
   const check=()=>{if(globalThis.cv?.Mat)resolve();else if(Date.now()-started>45000)reject(Error("OpenCV.js initialization timed out"));else setTimeout(check,20);};check();
  });
  const version=/OpenCV\s+([0-9.]+)/.exec(cv.getBuildInformation())?.[1];
  if(version!==backend.version)throw Error("Unexpected OpenCV.js binary: "+version);
  return {version,functions:Object.keys(cv).filter(k=>typeof cv[k]==="function"),vision:(...args)=>SMEngine.vision(cv,...args)};
 })());
 return engines.get(backend.id);
}
self.onmessage=async({data})=>{
 try{
  const runtime=await engine(data.state?.backend||data.backend);
  if(data.action==="probe"){
   self.postMessage({id:data.id,version:runtime.version,functions:runtime.functions});return;
  }
  const result=await SMEngine.process(data.rgba,data.width,data.height,data.state,data.previous,runtime,seconds=>self.postMessage({id:data.id,timeout:seconds}));
  self.postMessage({id:data.id,...result});
 }catch(error){self.postMessage({id:data.id,error:typeof error==="number"&&globalThis.cv?.exceptionFromPtr?cv.exceptionFromPtr(error).msg:String(error?.message||error)});}
};
