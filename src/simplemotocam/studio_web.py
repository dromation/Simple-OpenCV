"""Authenticated WSGI deployment. No loopback server or global user session."""
import base64
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import secrets
import sqlite3
from contextlib import closing
from http import HTTPStatus
from http.cookies import SimpleCookie, CookieError
from types import SimpleNamespace

from .studio import StudioHandler, StudioSession, StudioPipeline
import numpy as np


class WebHandler(StudioHandler):
    """Reuse the local API's validation, numerical operations and file handling."""
    def __init__(self, session, token, environ, body, policy):
        self.server = SimpleNamespace(session=session, token=token)
        self.headers = {key[5:].replace('_', '-').title(): value for key, value in environ.items() if key.startswith('HTTP_')}
        self.headers['Content-Length'] = str(len(body))
        self.path = environ['PATH_INFO']
        self.rfile = io.BytesIO(body)
        self.policy = policy
        self.result = None

    def local_request(self):
        return True  # Authentication, host, HTTPS and Origin checked by WSGI.

    def send(self, status, data, content_type='application/json; charset=utf-8', filename=None):
        if isinstance(data, dict) and 'catalog' in data:
            data['hosting'] = self.policy
            self.limit_catalog(data['catalog'])
        elif isinstance(data, dict) and 'runtimes' in data:
            self.limit_catalog(data)
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
        headers = [('Content-Type', content_type)]
        if filename:
            headers.append(('Content-Disposition', 'attachment; filename="'+filename+'"'))
        self.result = status, headers, data

    def limit_catalog(self, catalog):
        for key, item in catalog['runtimes'].items():
            if not self.policy['allowCompilers'] and key not in ('python', 'javascript'):
                item['available'] = False


def guard_state(state, policy):
    if not isinstance(state, dict):
        raise ValueError('Expected an algorithm object')
    if state.get('source', {}).get('type') == 'camera':
        raise ValueError('The hosted edition uses demo scenes or uploaded images/videos; a server camera is not your browser camera.')
    for node in state.get('nodes', []):
        if not node.get('enabled', True):
            continue
        if node.get('kind') == 'custom' and node.get('params', {}).get('code', '').strip() and not policy['allowCode']:
            raise ValueError('Custom code execution is disabled on this hosting. Keep the block as a draft or export it for local execution.')
        if node.get('runtime', 'python') not in ('python', 'javascript') and not policy['allowCompilers']:
            raise ValueError('Compiler adapters are disabled on this hosting.')


class WebApplication:
    """Persistent per-browser state, serialized across Passenger workers by SQLite."""
    def __init__(self, settings, storage):
        self.settings = settings
        self.storage = Path(storage).resolve()
        self.storage.mkdir(parents=True, exist_ok=True)
        self.key = settings['access_key'].encode('utf-8')
        if len(self.key) < 24 or settings['access_key'].startswith('CHANGE_'):
            raise ValueError('Set access_key to a private random value of at least 24 characters in hosting.json.')
        self.username = settings.get('username', 'studio')
        self.mount = settings.get('base_path', '').rstrip('/')
        if self.mount and (not self.mount.startswith('/') or any(c not in '/-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' for c in self.mount)):
            raise ValueError('base_path must be empty or a URL path such as /vision')
        self.cookie_name = 'smc_' + hashlib.sha256(self.mount.encode()).hexdigest()[:10]
        self.policy = {'hosted': True, 'allowCode': settings.get('allow_code_execution') is True,
                       'allowCompilers': settings.get('allow_compilers') is True, 'camera': False}
        self.backend = settings.get('backend', 'opencv24')
        if self.backend not in ('opencv24', 'current'):
            raise ValueError('backend must be opencv24 or current')
        self.hosts = settings.get('allowed_hosts', [])
        if not self.hosts or any(not isinstance(h, str) or '/' in h or '\\' in h for h in self.hosts):
            raise ValueError('Set allowed_hosts to your actual domain names.')
        self.upload_limit = int(settings.get('max_upload_mb', 20)) * 1024 * 1024
        if not 1024 * 1024 <= self.upload_limit <= 100 * 1024 * 1024:
            raise ValueError('max_upload_mb must be between 1 and 100')

    def sign(self, value):
        return hmac.new(self.key, value.encode(), hashlib.sha256).hexdigest()

    def authorized(self, environ):
        try:
            method, encoded = environ.get('HTTP_AUTHORIZATION', '').split(' ', 1)
            if method.lower() != 'basic':
                return False
            supplied = base64.b64decode(encoded, validate=True)
            expected = (self.username+':').encode()+self.key
            return hmac.compare_digest(hashlib.sha256(supplied).digest(), hashlib.sha256(expected).digest())
        except (ValueError, TypeError):
            return False

    def session_id(self, environ):
        cookie = SimpleCookie()
        try:
            cookie.load(environ.get('HTTP_COOKIE', ''))
            value = cookie[self.cookie_name].value
            sid, signature = value.split('.')
            if len(sid) == 48 and all(c in '0123456789abcdef' for c in sid) and hmac.compare_digest(signature, self.sign('cookie:'+sid)):
                return sid
        except (KeyError, ValueError, CookieError):
            pass
        return secrets.token_hex(24)

    def __call__(self, environ, start_response):
        headers = []
        try:
            status, extra, body = self.dispatch(environ)
            headers.extend(extra)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            status, body = 400, json.dumps({'error': str(exc)}).encode()
            headers.append(('Content-Type', 'application/json; charset=utf-8'))
        except sqlite3.OperationalError:
            status, body = 503, b'{"error":"The session is busy; retry shortly."}'
            headers.extend([('Content-Type', 'application/json'), ('Retry-After', '2')])
        except Exception:
            import traceback
            traceback.print_exc(file=environ.get('wsgi.errors'))
            status, body = 500, b'{"error":"Hosting error; see the private Passenger log."}'
            headers.append(('Content-Type', 'application/json'))
        headers += [('Content-Length', str(len(body))), ('Cache-Control', 'no-store'),
                    ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'same-origin'),
                    ('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'")]
        start_response(str(status)+' '+HTTPStatus(status).phrase, headers)
        return [body]

    def dispatch(self, environ):
        host = environ.get('HTTP_HOST', '')
        secure = environ.get('wsgi.url_scheme') == 'https' or environ.get('HTTPS', '').lower() == 'on'
        if host not in self.hosts:
            return 403, [], b'Unknown domain'
        if not secure and self.settings.get('require_https', True):
            return 403, [], b'HTTPS is required. Enable SSL for this domain in cPanel.'
        if not self.authorized(environ):
            return 401, [('WWW-Authenticate', 'Basic realm="SimpleMotocam", charset="UTF-8"')], b'SimpleMotocam: sign in with the credentials from hosting.json.'
        method = environ.get('REQUEST_METHOD', 'GET')
        if method not in ('GET', 'POST'):
            return 405, [('Allow', 'GET, POST')], b'Method not allowed'
        origin = environ.get('HTTP_ORIGIN')
        if origin and origin != ('https' if secure else 'http')+'://'+host:
            return 403, [], b'Cross-origin request rejected'
        path = environ.get('PATH_INFO', '')
        # Passenger normally separates SCRIPT_NAME; also accept full PATH_INFO.
        if self.mount and not environ.get('SCRIPT_NAME'):
            if path == self.mount:
                return 308, [('Location', self.mount+'/')], b''
            if not path.startswith(self.mount+'/'):
                return 404, [], b'Not found'
            path = path[len(self.mount):]
        if not path:
            return 308, [('Location', self.mount+'/')], b''
        request = {**environ, 'PATH_INFO': path}
        if not path.startswith('/api/'):
            if method != 'GET':
                return 405, [], b'Method not allowed'
            handler = WebHandler(None, '', request, b'', self.policy)
            handler.do_GET()
            return handler.result
        length = int(environ.get('CONTENT_LENGTH') or 0)
        limit = self.upload_limit if path == '/api/upload' else 256 * 1024
        if method == 'POST' and (length <= 0 or length > limit):
            return 413, [('Content-Type', 'application/json')], json.dumps({'error': 'Request exceeds the hosting size limit.'}).encode()
        raw = environ['wsgi.input'].read(length) if method == 'POST' else b''
        if len(raw) != length and method == 'POST':
            raise ValueError('Incomplete request body')
        sid = self.session_id(environ)
        token = self.sign('csrf:'+sid)
        if method == 'POST' and not hmac.compare_digest(environ.get('HTTP_X_STUDIO_TOKEN', ''), token):
            return 403, [('Content-Type', 'application/json')], b'{"error":"Invalid session token; reload the application."}'
        if method == 'POST' and path in ('/api/config', '/api/save', '/api/library/save'):
            data = json.loads(raw)
            guard_state(data['state'] if path == '/api/library/save' else data, self.policy)
        folder = self.storage / sid
        folder.mkdir(exist_ok=True)
        session = None
        with closing(sqlite3.connect(folder/'session.sqlite3', timeout=15)) as database:
            database.execute('CREATE TABLE IF NOT EXISTS session (id INTEGER PRIMARY KEY, state TEXT, previous BLOB)')
            database.execute('BEGIN IMMEDIATE')
            try:
                session = StudioSession(folder, backend=self.backend)
                record = database.execute('SELECT state, previous FROM session WHERE id=1').fetchone()
                if record:
                    saved = json.loads(record[0])
                    guard_state(saved['state'], self.policy)
                    session.state = saved['state']
                    session.pipeline = StudioPipeline(session.state)
                    session.index = saved['index']
                    session.revision = saved['revision']
                    session.code_authorized = saved.get('codeAuthorized', False) and self.policy['allowCode']
                    if record[1]:
                        with np.load(io.BytesIO(record[1]), allow_pickle=False) as planes:
                            session.pipeline.previous = {name: planes[name].copy() for name in 'RGBA'}
                    if path == '/api/frame' and session.state['source']['type'] == 'video':
                        import cv2
                        session.capture = cv2.VideoCapture(str(folder/'uploads'/session.state['source']['asset']))
                        if not session.capture.isOpened():
                            raise ValueError('Cannot open uploaded video')
                        if session.index and not session.capture.set(cv2.CAP_PROP_POS_FRAMES, session.index):
                            raise ValueError('This video codec does not support hosted frame seeking; use another video format.')
                handler = WebHandler(session, token, request, raw, self.policy)
                handler.do_GET() if method == 'GET' else handler.do_POST()
                status, headers, body = handler.result
                saved = {'state': session.state, 'index': session.index, 'revision': session.revision, 'codeAuthorized': session.code_authorized}
                previous = None
                if session.pipeline.previous is not None:
                    output = io.BytesIO()
                    np.savez(output, **session.pipeline.previous)
                    previous = output.getvalue()
                database.execute('INSERT OR REPLACE INTO session VALUES (1, ?, ?)', (json.dumps(saved), previous))
                database.commit()
                cookie = f'{self.cookie_name}={sid}.{self.sign("cookie:"+sid)}; Path={self.mount or "/"}; HttpOnly; SameSite=Strict; Max-Age=2592000'
                headers.append(('Set-Cookie', cookie+('; Secure' if secure else '')))
                return status, headers, body
            finally:
                if session:
                    session.close()
