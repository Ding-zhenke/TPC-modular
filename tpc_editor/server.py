"""Loopback-only HTTP adapter for one offline editor session."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import secrets
import threading
from urllib.parse import urlsplit, parse_qs

from .document import new_document, validate_document
from .graph import apply_command, CrossingRequired
from .geometry import build_scene

STATIC = Path(__file__).with_name('static')


class Session:
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.document = new_document()
        self.scene = build_scene(self.document)
        self.undo, self.redo = [], []
        self.saved = self.document
        self.filename = 'TPC域壁设计.json'
        self.lock = threading.RLock()

    def state(self):
        return {'document': self.document, 'scene': self.scene,
                'undo': bool(self.undo), 'redo': bool(self.redo),
                'dirty': self.document != self.saved, 'filename': self.filename,
                'workspace': str(self.workspace)}

    def replace(self, document):
        value = validate_document(document)
        scene = build_scene(value)
        if value != self.document:
            self.undo.append(self.document)
            self.undo = self.undo[-100:]
            self.redo.clear()
            self.document, self.scene = value, scene

    def command(self, command):
        kind = command.get('type')
        if kind in ('undo', 'redo'):
            src, dst = (self.undo, self.redo) if kind == 'undo' else (self.redo, self.undo)
            if src:
                value = src[-1]
                scene = build_scene(value)
                src.pop(); dst.append(self.document)
                self.document, self.scene = value, scene
        else:
            self.replace(apply_command(self.document, command))

    def save(self, name, overwrite=False):
        if (not isinstance(name, str) or len(name) > 120 or name in ('.', '..') or
                any(c in name for c in '/\\:\x00') or not name.lower().endswith('.json')):
            raise ValueError('请输入工作目录内的 JSON 文件名，不含路径')
        target = (self.workspace/name).resolve()
        if target.parent != self.workspace:
            raise ValueError('保存文件必须位于当前工作目录')
        payload = json.dumps(self.document, ensure_ascii=False, indent=2)
        # Exclusive creation is the overwrite gate, including concurrent saves.
        with target.open('w' if overwrite else 'x', encoding='utf-8') as stream:
            stream.write(payload)
        self.saved = deepcopy(self.document)
        self.filename = name
        return str(target)


class Handler(BaseHTTPRequestHandler):
    server_version = 'TPC-Editor/0.1'

    def log_message(self, *args):
        pass

    def _send(self, status, content, content_type='application/json; charset=utf-8'):
        if isinstance(content, (dict, list)):
            content = json.dumps(content, ensure_ascii=False, allow_nan=False).encode('utf-8')
        elif isinstance(content, str):
            content = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'")
        self.end_headers()
        self.wfile.write(content)

    def _allowed(self, api=False):
        expected = f'127.0.0.1:{self.server.server_port}'
        origin = self.headers.get('Origin')
        if self.headers.get('Host') != expected or (origin and origin != 'http://'+expected):
            self._send(403, {'error': '仅允许从当前本机编辑器访问'})
            return False
        if api and not secrets.compare_digest(self.headers.get('X-TPC-Session', ''), self.server.token):
            self._send(403, {'error': '编辑器会话无效，请重新打开窗口'})
            return False
        return True

    def do_GET(self):
        path = urlsplit(self.path)
        if not self._allowed(path.path.startswith('/api/')):
            return
        try:
            with self.server.session.lock:
                if path.path == '/':
                    html = (STATIC/'index.html').read_text(encoding='utf-8')
                    self._send(200, html.replace('__TPC_BOOTSTRAP__', json.dumps({'token': self.server.token})), 'text/html; charset=utf-8')
                elif path.path in ('/static/editor.css', '/static/editor.js'):
                    file = STATIC/path.path.rsplit('/', 1)[-1]
                    kind = 'text/css' if file.suffix == '.css' else 'text/javascript'
                    self._send(200, file.read_bytes(), kind+'; charset=utf-8')
                elif path.path == '/api/state':
                    self._send(200, self.server.session.state())
                elif path.path == '/api/export':
                    from .export import render_dxf, render_svg, render_png
                    doc, scene = self.server.session.document, self.server.session.scene
                    fmt = parse_qs(path.query).get('format', ['json'])[0]
                    if fmt == 'json':
                        self._send(200, json.dumps(doc, ensure_ascii=False, indent=2))
                    elif fmt == 'svg':
                        self._send(200, render_svg(doc, scene), 'image/svg+xml; charset=utf-8')
                    elif fmt == 'png':
                        self._send(200, render_png(doc), 'image/png')
                    elif fmt == 'dxf':
                        self._send(200, render_dxf(doc), 'image/vnd.dxf')
                    else:
                        raise ValueError('仅支持 JSON、SVG、PNG 和 DXF 导出')
                else:
                    self._send(404, {'error': '没有此页面'})
        except (ValueError, OSError) as exc:
            self._send(400, {'error': str(exc)})

    def do_POST(self):
        if not self._allowed(True):
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4*1024*1024:
                raise ValueError('请求大小无效，设计文件不得超过 4 MB')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError('请求必须为对象')
            route = urlsplit(self.path).path
            with self.server.session.lock:
                session = self.server.session
                if route == '/api/command':
                    session.command(data)
                elif route == '/api/replace':
                    session.replace(data['document'])
                elif route == '/api/save':
                    path = session.save(data['name'], data.get('overwrite') is True)
                    self._send(200, dict(session.state(), saved_path=path))
                    return
                elif route == '/api/stop':
                    self._send(200, {'stopped': True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                else:
                    self._send(404, {'error': '没有此操作'})
                    return
                self._send(200, session.state())
        except CrossingRequired as exc:
            self._send(409, {'error': str(exc), 'crossings': exc.points})
        except FileExistsError:
            self._send(409, {'error': '文件已存在，请另存或明确选择覆盖', 'exists': True})
        except (ValueError, KeyError, TypeError, OSError) as exc:
            self._send(400, {'error': str(exc)})


def create_server(workspace, port=0):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.token = secrets.token_urlsafe(32)
    server.session = Session(workspace)
    return server
