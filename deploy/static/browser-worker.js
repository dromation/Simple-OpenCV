"use strict";
importScripts("browser-engine.js", "vendor/opencv.js");
const ready=new Promise((resolve,reject)=>{
 const started=Date.now();
 const check=()=>{if(globalThis.cv?.Mat)resolve();else if(Date.now()-started>45000)reject(Error("OpenCV.js initialization timed out"));else setTimeout(check,20);};check();
});
self.onmessage=async({data})=>{
 try{
  await ready;
  if(data.action==="probe"){
   const version=/OpenCV\s+([0-9.]+)/.exec(cv.getBuildInformation())?.[1];
   self.postMessage({id:data.id,version,functions:Object.keys(cv).filter(k=>typeof cv[k]==="function")});return;
  }
  const result=await SMEngine.process(data.rgba,data.width,data.height,data.state,data.previous,cv,seconds=>self.postMessage({id:data.id,timeout:seconds}));
  self.postMessage({id:data.id,...result});
 }catch(error){self.postMessage({id:data.id,error:typeof error==="number"&&cv.exceptionFromPtr?cv.exceptionFromPtr(error).msg:String(error?.message||error)});}
};
