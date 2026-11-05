/* Memory bridge to genuine OpenCV 2.4.13.7 core/imgproc. MIT. */
"use strict";
globalThis.SMOpenCV24=async()=>{
 const module=await OpenCV24Module();
 const version=module.UTF8ToString(module._sm_version());
 if(version!=="2.4.13.7")throw Error("Unexpected OpenCV 2.4 binary: "+version);
 const functions=["GaussianBlur","medianBlur","blur","bilateralFilter","filter2D","Laplacian","threshold","getDerivKernels","sepFilter2D","magnitude","Scharr","morphologyEx","Canny","adaptiveThreshold","compare","floodFill","HoughLinesP","line"];
 const roundEven=x=>{const n=Math.floor(x),r=x-n;return r===.5?n+n%2:Math.round(x);};
 function vision(kind,plane,w,h,params){
  if(!Number.isInteger(w)||!Number.isInteger(h)||w<1||h<1||w*h>16000000||plane.length!==w*h)throw Error("Invalid image dimensions");
  if(!/^[a-z_]+$/.test(kind))throw Error("Invalid operation name");
  let yaml="%YAML:1.0\n---\nkind: "+kind+"\n";
  for(const [key,value]of Object.entries(params)){
   if(!/^[A-Za-z]+$/.test(key))continue;
   if(typeof value==="number"&&Number.isFinite(value))yaml+=key+": "+value+"\n";
  }
  if(kind==="kernel")yaml+="kernel: !!opencv-matrix\n   rows: 3\n   cols: 3\n   dt: f\n   data: [ "+params.kernel.flat().join(", ")+" ]\n";
  const allocated=[],alloc=n=>{const ptr=module._malloc(n);if(!ptr)throw Error("OpenCV 2.4 memory limit exceeded");allocated.push(ptr);return ptr;};
  try{
   const length=w*h,input=alloc(length*4),bytes=alloc(length),output=alloc(length*4),text=alloc(module.lengthBytesUTF8(yaml)+1);
   module.HEAPF32.set(plane,input/4);
   if(["canny","otsu","adaptive"].includes(kind))module.HEAPU8.set(Uint8Array.from(plane,x=>roundEven(Math.min(1,Math.max(0,x))*255)),bytes);
   module.stringToUTF8(yaml,text,module.lengthBytesUTF8(yaml)+1);
   if(module._sm_process(input,bytes,h,w,text,output)!==0)throw Error(module.UTF8ToString(module._sm_error()));
   return module.HEAPF32.slice(output/4,output/4+length);
  }finally{for(const ptr of allocated)module._free(ptr);}
 }
 return {version,functions,vision};
};
