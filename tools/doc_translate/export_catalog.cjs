// Extract only prose. Code, formulae and source links never enter translation.
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'../..');
const guide=path.join(root,'docs/opencv-2.4-manuals/learning');
const ctx={window:{}};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(guide,'lessons.js'),'utf8'),ctx);
const app=fs.readFileSync(path.join(guide,'app.js'),'utf8');
vm.runInContext(app.slice(0,app.indexOf('// [symbol/translation key'))+'\nwindow.SOURCE_TEXT=TEXT;',ctx);
const fields=['title','summary','variables','example','caution','contract'];
fs.mkdirSync(path.join(guide,'i18n'),{recursive:true});
for(const locale of ['en','sl']){
 const strings={};
 for(const [key,value] of Object.entries(ctx.window.SOURCE_TEXT[locale]))strings['ui.'+key]=value;
 for(const lesson of ctx.window.LESSONS)for(const field of fields)strings[`lesson.${lesson.id}.${field}`]=lesson[field][locale];
 fs.writeFileSync(path.join(guide,'i18n',locale+'.json'),JSON.stringify({locale,status:'project-authored',strings},null,2)+'\n');
}
console.log('Exported English source and Slovenian prose; code and formulae excluded.');
