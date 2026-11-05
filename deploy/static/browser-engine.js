/* SimpleOpenCV browser numerical engine. MIT. No server or Python required. */
"use strict";
globalThis.SMEngine = (() => {
 const f=Math.fround, own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
 const functions={abs:[Math.abs,1],sqrt:[Math.sqrt,1],minimum:[Math.min,2],maximum:[Math.max,2],clip:[(x,a,b)=>Math.min(Math.max(x,a),b),3]};
 function expression(text,names){
  if(typeof text!=="string"||text.length>500)throw Error("Expression: maximum 500 characters");
  const tokens=[];let pos=0,count=0;
  while(pos<text.length){
   const m=/^\s*(?:(\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|([A-Za-z][A-Za-z0-9_]*)|(\*\*|[+*/(),-]))/.exec(text.slice(pos));
   if(!m){if(!text.slice(pos).trim())break;throw Error("Invalid mathematical syntax");}
   tokens.push(m[1]?{type:"number",value:Number(m[1])}:m[2]?{type:"name",value:m[2]}:{type:m[3]});pos+=m[0].length;
   if(tokens.length>150)throw Error("Expression too complex");
  }
  let index=0;
  const peek=()=>tokens[index]?.type, take=()=>tokens[index++];
  const node=n=>{if(++count>100)throw Error("Expression too complex");return n;};
  function primary(){
   const t=take();if(!t)throw Error("Incomplete expression");
   if(t.type==="number"){if(!Number.isFinite(t.value)||Math.abs(t.value)>1e6)throw Error("Constant out of range");return node({k:"constant",v:f(t.value)});}
   if(t.type==="("){const n=add();if(take()?.type!==")")throw Error("Missing closing parenthesis");return n;}
   if(t.type==="name"){
    if(peek()==="("){
     if(!own(functions,t.value))throw Error("Unsupported function: "+t.value);
     take();const args=[add()];while(peek()===","){take();args.push(add());}
     if(take()?.type!==")"||args.length!==functions[t.value][1])throw Error("Wrong function arguments");
     return node({k:"call",v:t.value,args});
    }
    if(!names.has(t.value))throw Error("Unavailable channel: "+t.value);
    return node({k:"name",v:t.value});
   }
   throw Error("Only channel names, arithmetic and mathematical functions are allowed");
  }
  function power(){let n=primary();if(peek()==="**"){take();const right=unary();let v=right.k==="constant"?right.v:right.k==="neg"&&right.a.k==="constant"?-right.a.v:NaN;if(!Number.isFinite(v)||Math.abs(v)>4)throw Error("Powers require a constant exponent in [-4,4]");n=node({k:"**",a:n,b:right});}return n;}
  function unary(){if(peek()==="+"||peek()==="-"){const sign=take().type;const a=unary();return sign==="-"?node({k:"neg",a}):a;}return power();}
  function multiply(){let n=unary();while(peek()==="*"||peek()==="/"){const k=take().type;n=node({k,a:n,b:unary()});}return n;}
  function add(){let n=multiply();while(peek()==="+"||peek()==="-"){const k=take().type;n=node({k,a:n,b:multiply()});}return n;}
  const tree=add();if(index!==tokens.length)throw Error("Unexpected expression token");return tree;
 }
 function evaluate(n,values,p,i){
  if(n.k==="constant")return n.v;
  if(n.k==="name")return own(p,n.v)?f(p[n.v]):values[n.v][i];
  if(n.k==="neg")return f(-evaluate(n.a,values,p,i));
  if(n.k==="call")return f(functions[n.v][0](...n.args.map(a=>evaluate(a,values,p,i))));
  const a=evaluate(n.a,values,p,i),b=evaluate(n.b,values,p,i);
  return f(n.k==="+"?a+b:n.k==="-"?a-b:n.k==="*"?a*b:n.k==="/"?a/b:a**b);
 }
 function number(value,min,max,label,integer=false){if(typeof value!=="number"||!Number.isFinite(value)||value<min||value>max||(integer&&!Number.isInteger(value)))throw Error(label+": invalid number");return value;}
 function validate(input,definitions){
  const state=structuredClone(input);
  if(state.schema!==1||typeof state.name!=="string"||!state.name.trim()||state.name.length>100)throw Error("Invalid project name/schema");
  if(!state.backend||({opencv24:"2.4.13.7",browser:"4.13.0"})[state.backend.id]!==state.backend.version)throw Error("Choose OpenCV 2.4.13.7 or OpenCV.js 4.13.0");
  if(!["synthetic","image","video","camera"].includes(state.source?.type))throw Error("Invalid source");
  if(!Array.isArray(state.nodes)||state.nodes.length<2||state.nodes.length>32||state.nodes[0].kind!=="source"||state.nodes[1].kind!=="channels")throw Error("Start with source and RGB channels; maximum 32 blocks");
  const names=new Set(["R","G","B","A"]),ids=new Set(),unique=new Set();
  for(const n of state.nodes){
   if(!own(definitions,n.kind)||!/^[-A-Za-z0-9_]{1,40}$/.test(n.id)||ids.has(n.id))throw Error("Invalid block/id");ids.add(n.id);
   if(["source","channels","difference"].includes(n.kind)){if(unique.has(n.kind))throw Error("Duplicate "+n.kind);unique.add(n.kind);}
   n.enabled??=true;if(typeof n.enabled!=="boolean")throw Error("Invalid enabled flag");
   n.runtime??="javascript";
   if(n.runtime!=="javascript"&&(n.kind!=="custom"||n.enabled))throw Error(n.runtime+" is a draft language in the browser edition; choose JavaScript to execute");
   const defaults=definitions[n.kind].params;
   if(!n.params||Object.keys(n.params).some(k=>!own(defaults,k)))throw Error("Unknown block parameters");
   n.params={...structuredClone(defaults),...n.params};const p=n.params;
   if(!n.enabled&&!own(p,"input"))throw Error("This block cannot be bypassed");
   if(own(p,"input")&&!names.has(p.input))throw Error("Unavailable input: "+p.input);
   if(n.kind==="difference")for(const c of "RGBA")names.add("d"+c);
   if(n.kind==="algebra")expression(p.expression,new Set([...names,"wR","wG","wB"]));
   const bounds={wR:[-10,10],wG:[-10,10],wB:[-10,10],sigma:[.1,10],margin:[.001,.5],threshold:[-10,10],red:[0,1],green:[0,1],blue:[0,1],colorSigma:[.001,10],low:[0,255],high:[0,255],offset:[-255,255],minArea:[1,1e6,true],votes:[1,10000,true],minLength:[1,10000,true],maxGap:[0,10000,true],iterations:[1,10,true],timeout:[.1,30],gain:[-100,100]};
   for(const [key,[min,max,integer]]of Object.entries(bounds))if(own(p,key))number(p[key],min,max,key,integer);
   if(own(p,"size")&&!(n.kind==="median"?[3,5]:n.kind==="sobel"?[3,5,7]:[3,5,7,9,11,13,15]).includes(p.size))throw Error("Invalid kernel size");
   if(n.kind==="kernel"&&(!Array.isArray(p.kernel)||p.kernel.length!==3||p.kernel.some(row=>!Array.isArray(row)||row.length!==3||row.some(x=>typeof x!=="number"||!Number.isFinite(x)||Math.abs(x)>100))))throw Error("Use a finite 3×3 kernel in [-100,100]");
   if(n.kind==="canny"&&p.low>p.high)throw Error("Canny: low must not exceed high");
   if(n.kind==="custom"&&(typeof p.code!=="string"||p.code.length>20000))throw Error("Code: maximum 20000 characters");
   if(own(p,"output")){if(!/^[A-Za-z][A-Za-z0-9_]{0,30}$/.test(p.output)||names.has(p.output))throw Error("Output names must be unique channels");names.add(p.output);}
  }
  if(!names.has(state.view?.signal)||!names.has(state.view?.result))throw Error("Unavailable preview channel");
  number(state.view.gain,.1,100,"Display gain");return state;
 }
 const roundEven=x=>{const n=Math.floor(x),r=x-n;return r===.5?n+(n%2):Math.round(x);};
 function vision(cv,kind,plane,w,h,p){
  const allocated=[],keep=m=>(allocated.push(m),m),out=keep(new cv.Mat());
  try{
   let source=keep(cv.matFromArray(h,w,cv.CV_32FC1,plane));
   const size=new cv.Size(p.size||3,p.size||3),anchor=new cv.Point(-1,-1),border=cv.BORDER_REFLECT_101;
   if(["canny","otsu","adaptive","components","hough"].includes(kind)){
    const bytes=Uint8Array.from(plane,x=>["components","hough"].includes(kind)?(x>0?255:0):roundEven(Math.min(1,Math.max(0,x))*255));
    source=keep(cv.matFromArray(h,w,cv.CV_8UC1,bytes));
   }
   switch(kind){
    case "gaussian":cv.GaussianBlur(source,out,size,p.sigma,p.sigma,border);break;
    case "median":cv.medianBlur(source,out,p.size);break;
    case "box":cv.blur(source,out,size,anchor,border);break;
    case "bilateral":cv.bilateralFilter(source,out,p.size,p.colorSigma,p.sigma,border);break;
    case "kernel":{const kernel=keep(cv.matFromArray(3,3,cv.CV_32FC1,p.kernel.flat()));cv.filter2D(source,out,-1,kernel,anchor,0,border);break;}
    case "laplacian":cv.Laplacian(source,out,cv.CV_32F,1,1,0,border);break;
    case "sobel":case "scharr":{
     const dx=keep(new cv.Mat()),dy=keep(new cv.Mat());
     if(kind==="scharr"){cv.Scharr(source,dx,cv.CV_32F,1,0,1/32,0,border);cv.Scharr(source,dy,cv.CV_32F,0,1,1/32,0,border);}
     else {const scale=1/2**(2*p.size-3);cv.Sobel(source,dx,cv.CV_32F,1,0,p.size,scale,0,border);cv.Sobel(source,dy,cv.CV_32F,0,1,p.size,scale,0,border);}
     return Float32Array.from(dx.data32F,(x,i)=>Math.hypot(x,dy.data32F[i]));
    }
    case "canny":cv.Canny(source,out,p.low,p.high,3,true);break;
    case "otsu":cv.threshold(source,out,0,255,cv.THRESH_BINARY|cv.THRESH_OTSU);break;
    case "adaptive":cv.adaptiveThreshold(source,out,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,cv.THRESH_BINARY,p.size,p.offset);break;
    case "components":{
     const labels=keep(new cv.Mat()),stats=keep(new cv.Mat()),centers=keep(new cv.Mat());
     cv.connectedComponentsWithStats(source,labels,stats,centers,8,cv.CV_32S);
     return Float32Array.from(labels.data32S,label=>label>0&&stats.data32S[label*stats.cols+cv.CC_STAT_AREA]>=p.minArea?1:0);
    }
    case "hough":{
     const lines=keep(new cv.Mat());cv.HoughLinesP(source,lines,1,Math.PI/180,p.votes,p.minLength,p.maxGap);
     const mask=keep(cv.Mat.zeros(h,w,cv.CV_8UC1));
     for(let i=0;i<lines.data32S.length;i+=4)cv.line(mask,new cv.Point(lines.data32S[i],lines.data32S[i+1]),new cv.Point(lines.data32S[i+2],lines.data32S[i+3]),new cv.Scalar(255),1);
     return Float32Array.from(mask.data,x=>x/255);
    }
    default:{
     const modes={erode:cv.MORPH_ERODE,dilate:cv.MORPH_DILATE,opening:cv.MORPH_OPEN,closing:cv.MORPH_CLOSE,morph_gradient:cv.MORPH_GRADIENT};
     if(!own(modes,kind))throw Error("Unsupported operation: "+kind);
     const kernel=keep(cv.Mat.ones(p.size,p.size,cv.CV_8U));
     cv.morphologyEx(source,out,modes[kind],kernel,anchor,p.iterations,cv.BORDER_CONSTANT,cv.morphologyDefaultBorderValue());
    }
   }
   return ["canny","otsu","adaptive"].includes(kind)?Float32Array.from(out.data,x=>x/255):new Float32Array(out.data32F);
  } finally {for(const m of allocated.reverse())m.delete();}
 }
 async function process(rgba,w,h,state,previous,cv,progress=()=>{}){
  const length=w*h,values=Object.create(null);
  for(const c of "RGBA")values[c]=new Float32Array(length);
  for(let i=0;i<length;i++){const r=values.R[i]=rgba[4*i]/255,g=values.G[i]=rgba[4*i+1]/255,b=values.B[i]=rgba[4*i+2]/255;values.A[i]=Math.min(1,Math.min(r,g,b,1-r,1-g,1-b)/.05);}
  const original=Object.fromEntries(Object.entries(values).map(([k,v])=>[k,v.slice()]));
  const ready=!!previous&&previous.R.length===length&&previous.width===w&&previous.height===h;
  for(const n of state.nodes){
   const k=n.kind,p=n.params;if(["source","channels"].includes(k))continue;
   if(k==="difference"){for(const c of "RGBA")values["d"+c]=Float32Array.from(values[c],(x,i)=>ready?x-previous[c][i]:0);continue;}
   let out;
   if(!n.enabled)out=values[p.input].slice();
   else if(k==="custom"){
    if(!p.code.trim())out=values[p.input].slice();
    else {progress(p.timeout);const scoped=Object.fromEntries(Object.entries(values).map(([name,v])=>[name,v.slice()]));out=await new Function("channels","params","shape",'"use strict";\n'+p.code+'\nreturn process(channels,params,shape);')(scoped,p,[h,w]);progress(15);}
   }else if(k==="algebra"){
    const tree=expression(p.expression,new Set([...Object.keys(values),"wR","wG","wB"]));
    out=Float32Array.from({length},(_,i)=>evaluate(tree,values,{wR:p.wR,wG:p.wG,wB:p.wB},i));
   }else if(k==="threshold"&&state.backend.id==="opencv24")out=cv.vision(k,values[p.input],w,h,p);
   else if(["confidence","luminance","color_distance","invert","threshold"].includes(k)){
    out=Float32Array.from({length},(_,i)=>{
     const r=values.R[i],g=values.G[i],b=values.B[i];
     if(k==="confidence")return Math.min(1,Math.min(r,g,b,1-r,1-g,1-b)/p.margin);
     if(k==="luminance")return .299*r+.587*g+.114*b;
     if(k==="color_distance")return Math.hypot(r-p.red,g-p.green,b-p.blue)/Math.sqrt(3);
     return k==="invert"?1-values[p.input][i]:values[p.input][i]>p.threshold?1:0;
    });
   }else out=cv.vision(k,values[p.input],w,h,p);
   if(!out||out.length!==length)throw Error(n.id+": return H × W values");
   out=Float32Array.from(out);if(!out.every(Number.isFinite))throw Error(n.id+": nonfinite output; check division, roots and code");values[p.output]=out;
  }
  return {values,previous:{...original,width:w,height:h},ready};
 }
 return {expression,validate,process,vision};
})();
