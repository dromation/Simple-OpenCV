/* SimpleOpenCV download controls. The host only serves files. MIT. */
"use strict";
(()=>{
 const button=document.createElement("button");button.id="downloadApp";button.textContent="Download app";button.type="button";
 document.querySelector("header").insertBefore(button,document.getElementById("guide"));
 const dialog=document.createElement("dialog");dialog.id="downloads";dialog.setAttribute("aria-labelledby","downloadsTitle");
 dialog.innerHTML='<div class="classroom-head"><h2 id="downloadsTitle">Download SimpleOpenCV</h2><button type="button" id="closeDownloads" aria-label="Close" style="margin-left:auto">×</button></div><div style="padding:24px;max-width:720px"><p>Run SimpleOpenCV on your computer. Each download includes both OpenCV engines and opens the studio in your browser. No Python, Node.js or Go installation required.</p><div id="downloadChoices">Loading downloads…</div><p>Extract the entire archive before opening the application. Keep the launcher running while using the studio. Camera access requires browser permission.</p><p>These community builds are unsigned. macOS builds are not notarized.</p><p id="portableDetails"></p></div>';
 document.body.append(dialog);document.getElementById("closeDownloads").onclick=()=>dialog.close();
 button.onclick=async()=>{
  dialog.showModal();const choices=document.getElementById("downloadChoices");
  try{
   const response=await fetch("downloads/manifest.json");if(!response.ok)throw Error("Downloads are not included in this deployment. Upload the complete website package.");
   const manifest=await response.json();choices.replaceChildren();
   for(const item of manifest.assets){
    const row=document.createElement("p"),link=document.createElement("a"),hash=document.createElement("small");
    link.href=item.url;link.textContent=item.label+(item.size?" · "+(item.size/1048576).toFixed(1)+" MB":"");link.setAttribute("download",item.filename);
    hash.textContent=item.sha256?"SHA-256: "+item.sha256:"";hash.style.cssText="display:block;overflow-wrap:anywhere;font-size:10px";
    row.append(link,hash);choices.append(row);
   }
  }catch(error){choices.textContent=error.message;}
  document.getElementById("portableDetails").textContent=window.SimpleOpenCVHost?.portable?"Running portable version "+SimpleOpenCVHost.version+" · "+SimpleOpenCVHost.platform:"Website edition: processing runs in this browser.";
 };
 if(window.SimpleOpenCVHost?.portable){
  const quit=document.createElement("button");quit.id="quitPortable";quit.type="button";quit.textContent="Quit desktop app";
  document.querySelector("footer").append(quit);
  quit.onclick=async()=>{
   if(!confirm("Stop SimpleOpenCV? Export any project you want to keep as a file first."))return;
   window.StaticStudio?.stop();
   try{const response=await fetch("/__simpleopencv/quit",{method:"POST",headers:{"X-SimpleOpenCV-Token":SimpleOpenCVHost.shutdownToken}});if(!response.ok)throw Error("Could not stop the local launcher");document.body.replaceChildren();const p=document.createElement("p");p.textContent="SimpleOpenCV has stopped. You can close this tab.";p.style.padding="40px";document.body.append(p);}catch(error){alert(error.message);}
  };
 }
})();
