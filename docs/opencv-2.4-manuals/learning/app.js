'use strict';
const TEXT = {
 sl:{machineNotice:'Samodejni prevod — strokovni in jezikovni pregled še ni opravljen. Enačbe in koda so ohranjene; pri nejasnostih primerjaj angleški izvirnik.',original:'Pokaži angleški izvirnik',skip:'Preskoči na vsebino',title:'Od enačbe do slike',subtitle:'Razlaga, matematika in programski primeri.',explanationLanguage:'Jezik razlage',programLanguage:'Programski jezik',scope:'Večjezični učni dodatek SimpleMotocam: 8 tem, 21 jezikov razlage in 4 programski jeziki. Uradni priročniki ostajajo v angleščini; izbira jezika jih ne prevaja. C, C++ in Java prikazujejo izseke za OpenCV 2.4, Python pa preverjene primere v našem okolju OpenCV 4.14.',topics:'Učne teme',intro:'Uvod in priročniki',equation:'Matematični zapis',worked:'Številčni primer',code:'Programski zapis',download:'Shrani primer',try:'Preizkusi številke',labNote:'Drsniki računajo učni primer v brskalniku. Koda zgoraj ohrani začetne vrednosti; drsniki ne spreminjajo aplikacije ali kode. Enote in predpostavke so opisane v posamezni temi.',reset:'Ponastavi primer',reading:'Nadaljnje branje',source:'Izvor funkcije ali modela',tutorials:'Vaje · uradni PDF (EN)',userGuide:'Uporabniški vodič · PDF (EN)',reference:'Referenčni priročnik · PDF (EN)',footer:'Učni dodatek projekta SimpleMotocam · 21. 10. 2026 · Izvirni priročniki OpenCV so ohranjeni. Vodič deluje brez interneta; povezave na spletne vire potrebujejo povezavo.',pythonStatus:'Samostojen primer Python 3, numerično preverjen v okolju projekta z OpenCV 4.14.0. Ni bil izveden z OpenCV 2.4.',fragmentStatus:'Učni izsek za OpenCV 2.4; ni samostojen program in ni bil preveden. Zagotovi opisane vhode, ustrezne importe/glave in inicializacijo knjižnice. Navodila: README.sl.md.',saved:'Primer shranjen',old:'Prej',current:'Zdaj',center:'Srednji piksel',neighbors:'Osem sosedov',left:'Leva vrednost',right:'Desna vrednost',previousA:'Prejšnji A',margin:'Meja m',magnitude:'Velikost M'},
 en:{machineNotice:'Machine translation — technical and language review is pending. Equations and code are preserved; compare the English original when in doubt.',original:'Show English original',skip:'Skip to content',title:'From equation to image',subtitle:'Explanations, mathematics and code examples.',explanationLanguage:'Explanation language',programLanguage:'Programming language',scope:'A multilingual SimpleMotocam learning companion: 8 topics, 21 explanation languages and 4 programming languages. Official manuals remain in English; the language selector does not translate them. C, C++ and Java show OpenCV 2.4 fragments; Python shows examples verified in our OpenCV 4.14 environment.',topics:'Learning topics',intro:'Introduction and manuals',equation:'Mathematical model',worked:'Worked example',code:'Code example',download:'Save example',try:'Try the numbers',labNote:'Sliders calculate a learning example in your browser. The code above retains its initial values; sliders do not change the application or its code. Units and assumptions are explained in each topic.',reset:'Reset example',reading:'Further reading',source:'Function or model source',tutorials:'Tutorials · official PDF (EN)',userGuide:'User guide · PDF (EN)',reference:'Reference manual · PDF (EN)',footer:'SimpleMotocam learning companion · 21 Oct 2026 · Original OpenCV manuals are preserved. The guide works offline; web source links require an internet connection.',pythonStatus:'Standalone Python 3 example, numerically verified in the project environment with OpenCV 4.14.0. It has not been run with OpenCV 2.4.',fragmentStatus:'OpenCV 2.4 learning fragment; not a standalone program and not compiled. Supply the documented inputs, imports/headers and library initialisation. See README.en.md.',saved:'Example saved',old:'Previous',current:'Current',center:'Centre pixel',neighbors:'Eight neighbours',left:'Left value',right:'Right value',previousA:'Previous A',margin:'Margin m',magnitude:'Magnitude M'}
};
// [symbol/translation key, min, max, step, initial value]
const PARAMS = {
 channels:[['R',0,255,1,204],['G',0,255,1,102],['B',0,255,1,51]],
 difference:[['old',0,1,.01,.8],['current',0,1,.01,.2]],
 algebra:[['dR',-1,1,.01,.3],['dG',-1,1,.01,-.2],['dB',-1,1,.01,.1],['wR',-2,2,.1,1],['wG',-2,2,.1,-1],['wB',-2,2,.1,.5]],
 confidence:[['R',0,1,.005,.025],['G',0,1,.005,.5],['B',0,1,.005,.5],['margin',.005,.5,.005,.05],['previousA',0,1,.01,.2],['magnitude',0,1.74,.01,.4]],
 filter:[['center',0,1,.01,1],['neighbors',0,1,.01,0]],
 gradient:[['left',0,1,.01,0],['right',0,1,.01,1]],
 threshold:[['M',0,1,.01,.3],['τ',0,1,.01,.2]],
 scale:[['Lref (mm)',1,50,.1,10],['pref (px)',1,400,1,200],['p (px)',1,100,1,30],['us (mm/px)',0,.01,.0001,.001],['up (px)',0,2,.1,.5]]
};
const LANGUAGES=window.TRANSLATIONS.languages;
const PROSE_FIELDS=['summary','variables','example','caution','contract'];
for(const language of LANGUAGES){
 const id=language.id,catalog=window.TRANSLATIONS.catalogs[id];
 if(!TEXT[id])TEXT[id]={};
 for(const [key,value] of Object.entries(catalog.strings)){
  if(key.startsWith('ui.'))TEXT[id][key.slice(3)]=value;
  else {const [,lessonId,field]=key.split('.');const lesson=window.LESSONS.find(l=>l.id===lessonId);if(lesson&&['title',...PROSE_FIELDS].includes(field))lesson[field][id]=value;}
 }
}
const languageInfo=id=>LANGUAGES.find(l=>l.id===id);
// Isolate exact technical/math spans inside RTL prose without inserting HTML.
const escapedRuns=window.TRANSLATIONS.protectedRuns.map(s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'));
const protectedPattern=new RegExp('(?<![A-Za-z0-9_])(?:'+escapedRuns.join('|')+')(?![A-Za-z0-9_])','g');
function setProse(element,text){
 element.replaceChildren();let position=0;
 for(const match of text.matchAll(protectedPattern)){
  element.append(document.createTextNode(text.slice(position,match.index)));
  const span=document.createElement('bdi');span.dir='ltr';span.textContent=match[0];element.append(span);position=match.index+match[0].length;
 }
 element.append(document.createTextNode(text.slice(position)));
}
const get = id => document.getElementById(id);
get('locale').replaceChildren(...LANGUAGES.map(lang=>{const option=document.createElement('option');option.value=lang.id;option.textContent=lang.name;option.lang=lang.tag;option.dir=lang.dir;return option;}));
let locale='sl', program='python', current='channels', originalLocale=null;
const values=Object.fromEntries(window.LESSONS.map(l=>[l.id,Object.fromEntries(PARAMS[l.id].map(p=>[p[0],p[4]]))]));
try {const s=JSON.parse(localStorage.getItem('simplemotocam-learning')||'null');if(s){if(TEXT[s.locale])locale=s.locale;if(['python','cpp','c','java'].includes(s.program))program=s.program;}} catch (_) {}
const hash=location.hash.slice(1);if(window.LESSONS.some(l=>l.id===hash))current=hash;
function remember(){try{localStorage.setItem('simplemotocam-learning',JSON.stringify({locale,program}));}catch(_) {}}
function format(n){return new Intl.NumberFormat(languageInfo(locale).tag,{maximumFractionDigits:4}).format(n);}
function calculate(id,v){
 switch(id){
 case 'channels': return {Rn:v.R/255,Gn:v.G/255,Bn:v.B/255};
 case 'difference':return {'ΔR':v.current-v.old,'|ΔR|':Math.abs(v.current-v.old)};
 case 'algebra':return {S:v.wR*v.dR+v.wG*v.dG+v.wB*v.dB,M:Math.hypot(v.dR,v.dG,v.dB)};
 case 'confidence':{const h=Math.min(v.R,v.G,v.B,1-v.R,1-v.G,1-v.B), A=Math.max(0,Math.min(1,h/v.margin));return {h,A,Q:Math.min(A,v.previousA)*v.magnitude};}
 case 'filter':return {Y:(v.center+8*v.neighbors)/9};
 case 'gradient':{const Gx=(v.right-v.left)/2;return {Gx,Gy:0,E:Math.abs(Gx)};}
 case 'threshold':return {mask:v.M>v['τ']?1:0};
 case 'scale':{const s=v['Lref (mm)']/v['pref (px)'];return {'s (mm/px)':s,'L (mm)':s*v['p (px)'],'uL (mm)':Math.hypot(v['p (px)']*v['us (mm/px)'],s*v['up (px)'])};}
 default:throw Error('Unknown lesson');
 }
}
// Expose pure mathematics for verification without touching the application.
window.learningMath=calculate;
function updateResult(){get('result').textContent=Object.entries(calculate(current,values[current])).map(([k,v])=>`${k} = ${format(v)}`).join('   ·   ');}
function renderParameters(){const parent=get('parameters');parent.replaceChildren();PARAMS[current].forEach(([key,min,max,step],index)=>{const label=document.createElement('label'),name=document.createElement('span'),val=document.createElement('span'),input=document.createElement('input');name.textContent=TEXT[locale][key]||key;val.className='value';val.textContent=format(values[current][key]);input.type='range';input.id=`param-${index}`;input.min=min;input.max=max;input.step=step;input.value=values[current][key];label.htmlFor=input.id;input.addEventListener('input',()=>{values[current][key]=Number(input.value);val.textContent=format(Number(input.value));updateResult();});label.append(name,val,input);parent.append(label);});updateResult();}
function render(){const t=TEXT[locale],lesson=window.LESSONS.find(l=>l.id===current);document.documentElement.lang=languageInfo(locale).tag;document.documentElement.dir=languageInfo(locale).dir;document.title=`${lesson.title[locale]} · SimpleMotocam`;get('locale').value=locale;get('program').value=program;document.querySelectorAll('[data-i18n]').forEach(e=>setProse(e,t[e.dataset.i18n]));const nav=get('topics');nav.setAttribute('aria-label',t.topics);nav.replaceChildren();window.LESSONS.forEach((l,i)=>{const b=document.createElement('button');b.type='button';b.textContent=`${String(i+1).padStart(2,'0')}  ${l.title[locale]}`;if(l.id===current)b.setAttribute('aria-current','page');b.addEventListener('click',()=>{current=l.id;history.replaceState(null,'',`#${current}`);render();});nav.append(b);});get('number').textContent=`${String(window.LESSONS.indexOf(lesson)+1).padStart(2,'0')} / 08`;get('lessonTitle').textContent=lesson.title[locale];for(const key of ['summary','variables','example','caution','contract'])setProse(get(key),lesson[key][locale]);get('formula').textContent=lesson.formula;get('code').textContent=lesson[program];get('compatibility').textContent=program==='python'?t.pythonStatus:t.fragmentStatus;get('source').href=lesson.source;get('translationNotice').hidden=window.TRANSLATIONS.catalogs[locale].status!=='machine-unreviewed';get('original').hidden=locale==='en';if(originalLocale!==locale){get('original').open=window.TRANSLATIONS.catalogs[locale].status==='machine-unreviewed';originalLocale=locale;}get('originalContent').replaceChildren(...['title',...PROSE_FIELDS].map(field=>{const p=document.createElement('p');p.textContent=lesson[field].en;return p;}));renderParameters();remember();}
get('locale').addEventListener('change',e=>{locale=e.target.value;render();});get('program').addEventListener('change',e=>{program=e.target.value;render();});get('reset').addEventListener('click',()=>{values[current]=Object.fromEntries(PARAMS[current].map(p=>[p[0],p[4]]));renderParameters();});get('download').addEventListener('click',()=>{const lesson=window.LESSONS.find(l=>l.id===current);const url=URL.createObjectURL(new Blob([lesson[program]+'\n'],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=current+({python:'.py',cpp:'.cpp.txt',c:'.c.txt',java:'.java.txt'}[program]);a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});window.addEventListener('hashchange',()=>{const id=location.hash.slice(1);if(window.LESSONS.some(l=>l.id===id)){current=id;render();}});render();
