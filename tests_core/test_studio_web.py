"""Hosted API: authentication, independent browser state and Passenger restarts."""
import base64
import copy
import io
import json
from concurrent.futures import ThreadPoolExecutor
from http.cookies import SimpleCookie

import cv2
import numpy as np
import pytest

from simplemotocam.studio_web import WebApplication
from simplemotocam.studio_engine import KINDS
from simplemotocam.studio import StudioSession
from simplemotocam.studio_backend import backend_catalog

PASSWORD = 'test-password-for-hosting-1234567890'


@pytest.fixture
def app(tmp_path):
    return WebApplication({'access_key': PASSWORD, 'allowed_hosts': ['vision.example.test'], 'backend':'current'}, tmp_path)


class Client:
    def __init__(self, app):
        self.app, self.cookie, self.token = app, '', ''

    def request(self, path='/api/bootstrap', data=None, raw=None, headers=None, auth=True, **extra):
        body = raw if raw is not None else json.dumps(data).encode() if data is not None else b''
        environ = {'REQUEST_METHOD':'POST' if data is not None or raw is not None else 'GET',
                   'HTTP_HOST':'vision.example.test', 'PATH_INFO':path, 'SCRIPT_NAME':'',
                   'wsgi.url_scheme':'https', 'wsgi.input':io.BytesIO(body), 'wsgi.errors':io.StringIO(),
                   'CONTENT_LENGTH':str(len(body)), 'HTTP_COOKIE':self.cookie, 'HTTP_X_STUDIO_TOKEN':self.token}
        if auth:
            environ['HTTP_AUTHORIZATION']='Basic '+base64.b64encode(('studio:'+PASSWORD).encode()).decode()
        environ.update(headers or {})
        environ.update(extra)
        response = {}
        def start(status, fields):
            response.update(status=int(status.split()[0]), headers=dict(fields))
        response['body'] = b''.join(self.app(environ, start))
        if 'Set-Cookie' in response['headers']:
            self.cookie = response['headers']['Set-Cookie'].split(';')[0]
        if response['headers'].get('Content-Type','').startswith('application/json'):
            response['json'] = json.loads(response['body'])
            self.token = response['json'].get('token', self.token)
        return response


def test_auth_https_host_and_origin(app):
    client = Client(app)
    assert client.request(auth=False)['status']==401
    assert client.request(headers={'HTTP_AUTHORIZATION':'Basic not-valid'})['status']==401
    assert client.request(HTTP_HOST='evil.test')['status']==403
    assert client.request(**{'wsgi.url_scheme':'http'})['status']==403
    assert client.request(headers={'HTTP_ORIGIN':'https://evil.test'})['status']==403
    response=client.request()
    assert response['status']==200
    assert 'Secure' in response['headers']['Set-Cookie']
    assert 'HttpOnly' in response['headers']['Set-Cookie']
    assert response['json']['hosting']['allowCode'] is False
    assert response['json']['catalog']['runtimes']['cpp']['available'] is False


def test_state_isolated_and_restored_between_worker_instances(app):
    a,b=Client(app),Client(app)
    state=a.request()['json']['state']
    b.request()
    state['name']='Private experiment A'
    assert a.request('/api/config',state)['status']==200
    assert b.request()['json']['state']['name']!='Private experiment A'
    first=a.request('/api/frame',{})['json']
    assert first['frame']==1 and not first['ready']
    a.app=WebApplication(app.settings,app.storage)
    second=a.request('/api/frame',{})['json']
    assert second['frame']==2 and second['ready']
    assert a.request()['json']['state']['name']=='Private experiment A'
    assert b.request('/api/frame',{})['json']['frame']==1
    assert a.request('/api/stop',{})['status']==200
    assert not a.request('/api/frame',{})['json']['ready']


def test_csrf_cannot_cross_sessions(app):
    a,b=Client(app),Client(app)
    a.request();b.request()
    assert a.request('/api/frame',{},headers={'HTTP_X_STUDIO_TOKEN':b.token})['status']==403
    assert a.request('/api/frame',{},headers={'HTTP_X_STUDIO_TOKEN':''})['status']==403


def test_public_files_are_allowlisted(app):
    client=Client(app)
    for path in ('/', '/app.js', '/manuals/learning/index.html'):
        assert client.request(path)['status']==200
    for path in ('/hosting.json','/private/session.sqlite3','/../studio.py','/manuals/../../LICENSE'):
        assert client.request(path)['status']==404


def test_subdirectory_mount_and_export(app):
    client=Client(WebApplication({**app.settings,'base_path':'/vision'},app.storage))
    assert client.request('/vision')['status']==308
    assert client.request('/unrelated')['status']==404
    assert client.request('/vision/')['status']==200
    state=client.request('/vision/api/bootstrap')['json']['state']
    assert client.request('/api/bootstrap',SCRIPT_NAME='/vision')['status']==200
    saved=client.request('/vision/api/save',state)
    assert saved['status']==200
    assert client.request('/vision/api/projects/'+saved['json']['id'])['json']['state']==state
    exported=client.request('/vision/api/export',state)
    assert exported['status']==200 and b'class StudioPipeline' in exported['body']
    assert 'Path=/vision' in exported['headers']['Set-Cookie']


def test_hosting_policy_cannot_be_bypassed_by_import_or_saved_blocks(app):
    client=Client(app)
    state=client.request()['json']['state']
    camera=copy.deepcopy(state);camera['source']['type']='camera'
    assert client.request('/api/config',camera)['status']==400
    custom={'id':'code','kind':'custom','enabled':True,'params':copy.deepcopy(KINDS['custom']['params'])}
    custom['params']['code']='def process(c,p):\n    return c["R"]'
    state['nodes'].append(custom)
    for endpoint,data in [('/api/config',state),('/api/save',state),('/api/library/save',{'state':state,'selected':'code','name':'code'})]:
        assert client.request(endpoint,data)['status']==400
    custom['enabled']=False
    assert client.request('/api/config',state)['status']==200
    assert client.request('/api/frame',{})['status']==200
    state['nodes'][3]['runtime']='cpp'
    assert client.request('/api/config',state)['status']==400


def test_upload_then_image_source_survives_new_worker(app):
    client=Client(app);state=client.request()['json']['state']
    ok,data=cv2.imencode('.png',np.full((40,50,3),80,np.uint8));assert ok
    uploaded=client.request('/api/upload',raw=data.tobytes(),headers={'HTTP_X_FILE_EXTENSION':'.png'})
    state['source']={'type':'image','camera':0,'asset':uploaded['json']['asset']}
    assert client.request('/api/config',state)['status']==200
    client.app=WebApplication(app.settings,app.storage)
    frame=client.request('/api/frame',{})
    assert frame['status']==200 and frame['json']['originalSize']==[50,40]
    assert client.request('/api/upload',raw=b'a',headers={'HTTP_X_FILE_EXTENSION':'.py'})['status']==400
    assert client.request('/api/upload',raw=b'a',CONTENT_LENGTH=str(101*1024*1024))['status']==413


def test_concurrent_workers_serialize_frame_history(app):
    client=Client(app);client.request()
    def frame(_):
        other=Client(WebApplication(app.settings,app.storage))
        other.cookie,other.token=client.cookie,client.token
        response=other.request('/api/frame',{})
        assert response['status']==200,response['body']
        return response['json']['frame']
    with ThreadPoolExecutor(max_workers=3) as pool:
        assert sorted(pool.map(frame,range(6)))==list(range(1,7))


def test_uploaded_video_advances_across_requests(app,tmp_path):
    path=tmp_path/'test.avi'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),5,(64,48))
    if not writer.isOpened():
        pytest.skip('MJPG encoder unavailable')
    for intensity in (30,120,220):
        writer.write(np.full((48,64,3),intensity,np.uint8))
    writer.release()
    client=Client(app);state=client.request()['json']['state']
    uploaded=client.request('/api/upload',raw=path.read_bytes(),headers={'HTTP_X_FILE_EXTENSION':'.avi'})
    state['source']={'type':'video','camera':0,'asset':uploaded['json']['asset']}
    assert client.request('/api/config',state)['status']==200
    means=[]
    for _ in range(3):
        client.app=WebApplication(app.settings,app.storage)
        result=client.request('/api/frame',{})
        assert result['status']==200,result['body']
        means.append(result['json']['stats']['R']['mean'])
    assert means[0]<means[1]<means[2]
    assert client.request('/api/frame',{})['json']['ended']


def test_settings_require_private_password_and_real_host(tmp_path):
    with pytest.raises(ValueError,match='access_key'):
        WebApplication({'access_key':'CHANGE_ME'},tmp_path)
    with pytest.raises(ValueError,match='allowed_hosts'):
        WebApplication({'access_key':PASSWORD},tmp_path)


@pytest.mark.parametrize('backend',['current','opencv24'])
def test_hosted_numeric_history_matches_the_local_engine(app,tmp_path,backend):
    if not backend_catalog()[backend]['available']:
        pytest.skip('optional legacy worker unavailable')
    client=Client(WebApplication({**app.settings,'backend':backend},app.storage))
    client.request()
    reference=StudioSession(tmp_path/'reference',backend=backend)
    try:
        for _ in range(3):
            expected=reference.frame()
            actual=client.request('/api/frame',{})
            assert actual['status']==200,actual['body']
            assert actual['json']['stats']==expected['stats']
            assert actual['json']['backend']==expected['backend']
    finally:
        reference.close()
