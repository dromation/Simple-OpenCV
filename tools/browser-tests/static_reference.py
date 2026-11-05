"""Deterministic numerical fixture for the browser engine; no saved user media."""
import copy
import json
from pathlib import Path
import sys
import numpy as np
import cv2
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from simplemotocam.studio_engine import KINDS,default_state,StudioPipeline
from simplemotocam.studio_backend import backend_catalog

rng=np.random.default_rng(7)
rgb=rng.integers(0,256,(23,31,3),dtype=np.uint8)
rgba=np.concatenate((rgb,np.full((23,31,1),255,np.uint8)),axis=2)
tests=[]
backends=backend_catalog()
if not backends['opencv24']['available']:raise RuntimeError('Build the genuine native OpenCV 2.4 worker before preparing parity fixtures')
images={'noise':rgb}
shapes=np.zeros((95,127,3),np.uint8)
shapes[10:60,10:65]=180;shapes[20:45,22:50]=0  # component containing a hole
shapes[72,5:119]=255;shapes[4:90,110]=255      # lines longer than Hough's defaults
shapes[88,2]=255;shapes[87,3]=255             # diagonal connectivity
images['shapes']=shapes
cases=[(kind,{}) for kind in KINDS if kind not in ('source','channels','difference','custom')]
cases += [('sobel',{'size':size}) for size in (5,7)]
cases += [('gaussian',{'size':15,'sigma':2.3}),('median',{'size':5}),('bilateral',{'size':5,'sigma':1.7,'colorSigma':.2}),('adaptive',{'size':11,'offset':-3}),('opening',{'size':5,'iterations':2}),('components',{'minArea':2}),('hough',{'votes':10,'minLength':20,'maxGap':3}),('kernel',{'kernel':[[0,1,0],[1,-4,1],[0,1,0]]})]
for engine in ('opencv24','current'):
 for image_name,image in images.items():
  for kind,override in cases:
    state=default_state();state['backend']={'id':engine,'version':backends[engine]['version']}
    params=copy.deepcopy(KINDS[kind]['params']);params.update(override)
    if 'input' in params:params['input']='R'
    if kind=='algebra':params['expression']='clip(wR*(R-G)+sqrt(abs(B-0.5)),-1,1)'
    state['nodes']=state['nodes'][:2]+[{'id':'tested','kind':kind,'params':params,'enabled':True}]
    state['view']['signal']=state['view']['result']=params['output']
    output,_=StudioPipeline(state).process(image[:,:,::-1].copy())
    if kind=='hough' and image_name=='shapes':assert np.count_nonzero(output[params['output']])>50
    tests.append({'kind':kind,'image':image_name,'engine':engine,'state':state,'output':output[params['output']].ravel().tolist()})
(ROOT/'work').mkdir(exist_ok=True)
writer=cv2.VideoWriter(str(ROOT/'work/static-video.webm'),cv2.VideoWriter_fourcc(*'VP80'),30,(64,48))
if not writer.isOpened():raise RuntimeError('Numerical test fixture requires the VP8 encoder')
for i in range(30):
    image=np.zeros((48,64,3),np.uint8);image[:,:,i//10]=200
    writer.write(image)
writer.release()
(ROOT/'work/static-reference.json').write_text(json.dumps({'width':31,'height':23,'rgba':rgba.ravel().tolist(),'images':{name:{'width':image.shape[1],'height':image.shape[0],'rgba':np.concatenate((image,np.full((*image.shape[:2],1),255,np.uint8)),axis=2).ravel().tolist()} for name,image in images.items()},'tests':tests}),encoding='utf-8')
print('Prepared',len(tests),'numerical reference blocks.')
