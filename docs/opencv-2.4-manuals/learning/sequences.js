// Original detection exercises; the application receives only a registered lesson ID.
let activeSequence=null;
const sequenceText=key=>window.SEQUENCE_DATA.catalogs[locale]?.strings[key]||window.SEQUENCE_DATA.catalogs.en.strings[key]||key;
function sequenceElement(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function sequenceDownload(content,name,type='application/json'){
 const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function sequencePython(item){
 return '# Python 3 orchestrator; processing is pinned to genuine OpenCV 2.4.13.7.\n# Requires SimpleMotocam and its native OpenCV 2.4 worker.\nimport json\nfrom simplemotocam.studio_engine import StudioPipeline, demo_frame\n\nstate = json.loads(r\'\'\''+JSON.stringify(item.state,null,2)+'\'\'\')\npipeline = StudioPipeline(state)\n# Replace demo_frame with your BGR image or consecutive camera frames.\nfor index in range(2):\n    channels, ready = pipeline.process(demo_frame(index, 320, 240))\n    result = channels[state["view"]["result"]]\n    print(index, ready, result.min(), result.max())\n';
}
const basicRender=render;
render=function(){
 basicRender();
 document.querySelector(".scope").textContent=sequenceText("ui.primary")+" · "+sequenceText("ui.intro");
 const nav=get('topics');
 nav.append(sequenceElement('h3',sequenceText('ui.sequences')));
 for(const item of window.SEQUENCE_DATA.lessons){
  const button=sequenceElement('button',sequenceText(item.id+'.title'),'sequence-topic');button.type='button';button.dataset.sequence=item.id;
  if(activeSequence===item.id)button.setAttribute('aria-current','page');
  button.onclick=()=>{activeSequence=item.id;render();};nav.append(button);
 }
 let panel=get('sequenceContent');
 if(!panel){panel=sequenceElement('section',undefined,'sequence-content');panel.id='sequenceContent';get('content').append(panel);}
 for(const child of get('content').children)child.hidden=child===panel?!activeSequence:!!activeSequence;
 if(!activeSequence)return;
 nav.querySelectorAll('button:not(.sequence-topic)').forEach(b=>b.removeAttribute('aria-current'));
 const item=window.SEQUENCE_DATA.lessons.find(s=>s.id===activeSequence);
 document.title=sequenceText(item.id+'.title')+' · OpenCV 2.4';
 panel.replaceChildren(sequenceElement('span','OPENCV 2.4.13.7','eyebrow'),sequenceElement('h2',sequenceText(item.id+'.title')),sequenceElement('p',sequenceText('ui.intro')));
 const chain=sequenceElement('ol',undefined,'sequence-chain');
 item.state.nodes.forEach(node=>{const li=sequenceElement('li');const label=window.SEQUENCE_DATA.labels?.[locale]?.[node.kind==='source'?'source':node.kind+'Block']||node.kind;li.append(sequenceElement('strong',label));const settings=Object.entries(node.params).filter(([k])=>!['input','output'].includes(k)).map(([k,v])=>k+' = '+(typeof v==='string'?v:JSON.stringify(v))).join(' · ');if(settings)li.append(sequenceElement('code',settings));const channel=node.params.output;if(channel)li.append(sequenceElement('small',(node.params.input||'RGB')+' → '+channel));chain.append(li);});panel.append(chain);
 const actions=sequenceElement('div',undefined,'sequence-actions');const load=sequenceElement('button',sequenceText('ui.load'));load.id='loadSequence';load.type='button';load.disabled=window.parent===window;load.onclick=()=>window.parent.postMessage({type:'learning-load-sequence',id:item.id},location.origin);actions.append(load);
 const save=sequenceElement('button',sequenceText('ui.download'));save.type='button';save.onclick=()=>sequenceDownload(JSON.stringify(item.state,null,2),item.id+'-opencv24.json');actions.append(save);
 if(item.sample){const a=sequenceElement('a',sequenceText('ui.sample'));a.href=item.sample;a.download=item.id+'.png';actions.append(a);}panel.append(actions);
 if(window.parent===window)panel.append(sequenceElement('p',sequenceText('ui.offline'),'note'));
 for(const field of ['goal','order','tune','expected','caution']){panel.append(sequenceElement('h3',sequenceText('ui.'+field)),sequenceElement('p',sequenceText(item.id+'.'+field)));}
 panel.append(sequenceElement('pre',item.formula,'sequence-formula'));
 if(item.sample){const img=sequenceElement('img');img.src=item.sample;img.alt=sequenceText(item.id+'.expected');img.className='sequence-scene';panel.append(img);}
 const code=sequenceElement('details');code.append(sequenceElement('summary',sequenceText('ui.code')),sequenceElement('p',sequenceText('ui.codeNote')),sequenceElement('pre',sequencePython(item)));const codeSave=sequenceElement('button',TEXT[locale].download);codeSave.onclick=()=>sequenceDownload(sequencePython(item),item.id+'-opencv24.py','text/x-python');code.append(codeSave);panel.append(code);
 panel.append(sequenceElement('h3',sequenceText('ui.sources')));
 const sources=sequenceElement('ul');for(const source of item.sources){const li=sequenceElement('li');if(source.url){const a=sequenceElement('a',source.title);a.href=source.url;a.target='_blank';a.rel='noopener';li.append(a);}else li.textContent=source.title+' · '+source.file+' · pp. '+source.pages+' · PDF '+source.pdfPages;sources.append(li);}panel.append(sources,sequenceElement('p',sequenceText('ui.bookNote'),'note'));
 if(!['sl','en'].includes(locale)){const original=sequenceElement('details');original.open=true;original.append(sequenceElement('summary',TEXT[locale].original));for(const field of ['goal','order','tune','expected','caution']){const p=sequenceElement('p',window.SEQUENCE_DATA.catalogs.en.strings[item.id+'.'+field]);p.lang='en';p.dir='ltr';original.append(p);}panel.append(original);}
};
get('topics').addEventListener('click',event=>{if(event.target.closest('button')&&!event.target.closest('[data-sequence]'))activeSequence=null;},true);
window.addEventListener('message',event=>{if(event.origin===location.origin&&event.source===window.parent&&event.data?.type==='studio-learning-context'&&event.data.topic){activeSequence=null;render();}});
render();
