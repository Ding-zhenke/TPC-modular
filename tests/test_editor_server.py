"""Actual local HTTP adapter, including undo and workspace-only saving."""
import importlib.util
import json
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest


@pytest.fixture
def running(tmp_path):
    assert importlib.util.find_spec('tpc_editor.server'), 'Local editor service is missing'
    from tpc_editor.server import create_server
    server = create_server(tmp_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown(); server.server_close(); thread.join(timeout=5)


def request(server, route, data=None, token=True, origin=None):
    base = f'http://127.0.0.1:{server.server_port}'
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['X-TPC-Session'] = server.token
    if origin:
        headers['Origin'] = origin
    req = Request(base+route, data=None if data is None else json.dumps(data).encode(), headers=headers)
    try:
        with urlopen(req) as response:
            return response.status, response.headers, response.read()
    except HTTPError as err:
        return err.code, err.headers, err.read()


def test_resources_and_session_protection(running):
    code, headers, body = request(running, '/')
    assert code == 200 and '域壁' in body.decode()
    assert request(running, '/static/editor.js')[0] == 200
    assert request(running, '/api/state', token=False)[0] == 403
    assert request(running, '/api/command', {'type': 'end'}, origin='https://example.com')[0] == 403


def test_commands_undo_redo_and_malformed_input_are_transactional(running):
    assert request(running, '/api/command', {'type': 'point', 'r': 0, 'c': 0})[0] == 200
    assert request(running, '/api/command', {'type': 'point', 'r': 1, 'c': 2})[0] == 400
    state = json.loads(request(running, '/api/state')[2])
    assert len(state['document']['nodes']) == 1
    assert request(running, '/api/command', {'type': 'undo'})[0] == 200
    state = json.loads(request(running, '/api/state')[2])
    assert not state['document']['nodes']
    assert request(running, '/api/command', {'type': 'redo'})[0] == 200
    assert len(json.loads(request(running, '/api/state')[2])['document']['nodes']) == 1


def test_save_overwrite_path_escape_and_json_reload(running, tmp_path):
    assert request(running, '/api/save', {'name': '../private.json'})[0] == 400
    assert request(running, '/api/save', {'name': '设计.json'})[0] == 200
    saved = json.loads((tmp_path/'设计.json').read_text(encoding='utf-8'))
    assert saved['schema_version'] == 1
    assert request(running, '/api/save', {'name': '设计.json'})[0] == 409
    assert request(running, '/api/save', {'name': '设计.json', 'overwrite': True})[0] == 200
    assert request(running, '/api/replace', {'document': saved})[0] == 200
    saved['schema_version'] = 999
    assert request(running, '/api/replace', {'document': saved})[0] == 400


def test_exports_are_real_formats(running):
    for fmt, marker in [('json', b'{'), ('svg', b'<svg'), ('png', b'\x89PNG')]:
        code, headers, body = request(running, '/api/export?format='+fmt)
        assert code == 200
        assert body.startswith(marker)


def test_dxf_download_requires_resolved_geometry(running):
    assert request(running, '/api/export?format=dxf')[0] == 400
    state = json.loads(request(running, '/api/state')[2])
    doc = state['document']
    doc['parameters']['confirmed'] = True
    doc['regions'] = [{'wkt': state['scene']['faces'][0]['wkt'], 'phase': 'A'}]
    assert request(running, '/api/replace', {'document': doc})[0] == 200
    status, headers, body = request(running, '/api/export?format=dxf')
    assert status == 200 and headers.get_content_type() == 'image/vnd.dxf'
    assert b'LWPOLYLINE' in body
