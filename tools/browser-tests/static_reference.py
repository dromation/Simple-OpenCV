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
for kind in KINDS:
    if kind in ('source','channels','difference','custom'):continue
    state=default_state();state['backend']={'id':'current','version':backend_catalog()['current']['version']}
    params=copy.deepcopy(KINDS[kind]['params'])
    if 'input' in params:params['input']='R'
    if kind=='algebra':params['expression']='clip(wR*(R-G)+sqrt(abs(B-0.5)),-1,1)'
    state['nodes']=state['nodes'][:2]+[{'id':'tested','kind':kind,'params':params,'enabled':True}]
    state['view']['signal']=state['view']['result']=params['output']
    output,_=StudioPipeline(state).process(rgb[:,:,::-1].copy())
    tests.append({'kind':kind,'state':state,'output':output[params['output']].ravel().tolist()})
(ROOT/'work').mkdir(exist_ok=True)
writer=cv2.VideoWriter(str(ROOT/'work/static-video.webm'),cv2.VideoWriter_fourcc(*'VP80'),30,(64,48))
if not writer.isOpened():raise RuntimeError('Numerical test fixture requires the VP8 encoder')
for i in range(30):
    image=np.zeros((48,64,3),np.uint8);image[:,:,i//10]=200
    writer.write(image)
writer.release()
(ROOT/'work/static-reference.json').write_text(json.dumps({'width':31,'height':23,'rgba':rgba.ravel().tolist(),'tests':tests}),encoding='utf-8')
print('Prepared',len(tests),'numerical reference blocks.')
