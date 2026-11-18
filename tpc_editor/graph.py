"""Transactional commands on an explicit undirected graph."""
from copy import deepcopy
import math

from .document import new_document, validate_document, lattice_integer, is_direction


class CrossingRequired(ValueError):
    def __init__(self, points):
        super().__init__('新线段发生交叉，请选择连接、保持分离或取消')
        self.points = points


def _id(doc, kind, prefix):
    n = doc['next_id'][kind]
    doc['next_id'][kind] += 1
    return f'{prefix}{n:02d}'


def _node(doc, r, c):
    for key, node in doc['nodes'].items():
        if node['r'] == r and node['c'] == c:
            return key
    key = _id(doc, 'node', 'P')
    doc['nodes'][key] = {'r': r, 'c': c}
    return key


def _on(n, a, b):
    dr, dc = b['r']-a['r'], b['c']-a['c']
    return (n['r']-a['r'])*dc == (n['c']-a['c'])*dr and (
        min(a['r'], b['r']) <= n['r'] <= max(a['r'], b['r']) and
        min(a['c'], b['c']) <= n['c'] <= max(a['c'], b['c']))


def _split_ids(doc, u, v):
    a, b = doc['nodes'][u], doc['nodes'][v]
    points = []
    for nid, n in doc['nodes'].items():
        if _on(n, a, b):
            separate = any(abs(k['r']-n['r']) < 1e-9 and abs(k['c']-n['c']) < 1e-9
                           for k in doc['crossings'])
            if separate and nid not in (u, v):
                continue
            dist = (n['r']-a['r'])**2 + (n['c']-a['c'])**2
            points.append((dist, nid))
    return [nid for _, nid in sorted(points)]


def _normalize(doc):
    old = {frozenset((e['u'], e['v'])): eid for eid, e in doc['edges'].items()}
    edges = {}
    used = set()
    for e in list(doc['edges'].values()):
        ids = _split_ids(doc, e['u'], e['v'])
        for u, v in zip(ids, ids[1:]):
            key = frozenset((u, v))
            if key in used:
                continue
            used.add(key)
            eid = old.get(key) or _id(doc, 'edge', 'E')
            edges[eid] = {'u': u, 'v': v}
    doc['edges'] = edges
    for s in doc['strokes']:
        result = s['nodes'][:1]
        for u, v in zip(s['nodes'], s['nodes'][1:]):
            result.extend(_split_ids(doc, u, v)[1:])
        s['nodes'] = result


def _intersections(doc, u, v):
    from shapely.geometry import LineString
    a, b = doc['nodes'][u], doc['nodes'][v]
    line = LineString([(a['c'], a['r']), (b['c'], b['r'])])
    result = []
    for e in doc['edges'].values():
        if {u, v} & {e['u'], e['v']}:
            continue
        x, y = doc['nodes'][e['u']], doc['nodes'][e['v']]
        other = LineString([(x['c'], x['r']), (y['c'], y['r'])])
        inter = line.intersection(other)
        if inter.geom_type != 'Point' or inter.is_empty:
            continue
        r, c = float(inter.y), float(inter.x)
        # An explicit endpoint on an existing edge means a deliberate T junction.
        if any(abs(r-n['r']) < 1e-9 and abs(c-n['c']) < 1e-9 for n in (a, b, x, y)):
            continue
        if any(abs(r-k['r']) < 1e-9 and abs(c-k['c']) < 1e-9 for k in doc['crossings']):
            continue
        if not any(abs(r-k['r']) < 1e-9 and abs(c-k['c']) < 1e-9 for k in result):
            result.append({'r': r, 'c': c,
                           'connectable': abs(r-round(r)) < 1e-9 and abs(c-round(c)) < 1e-9})
    return result


def _prune_strokes(doc):
    pairs = {frozenset((e['u'], e['v'])) for e in doc['edges'].values()}
    strokes = []
    for s in doc['strokes']:
        chunk = []
        for nid in s['nodes']:
            if nid not in doc['nodes']:
                if chunk:
                    strokes.append({'id': _id(doc, 'stroke', 'S'), 'nodes': chunk})
                chunk = []
                continue
            if chunk and frozenset((chunk[-1], nid)) not in pairs:
                strokes.append({'id': _id(doc, 'stroke', 'S'), 'nodes': chunk})
                chunk = []
            chunk.append(nid)
        if chunk:
            strokes.append({'id': _id(doc, 'stroke', 'S'), 'nodes': chunk})
    doc['strokes'] = strokes
    doc['active_stroke'] = None


def apply_command(value, command):
    doc = validate_document(value)
    kind = command.get('type')
    if kind == 'new':
        return new_document()
    if kind == 'point':
        if not doc['parameters']['confirmed'] and command.get('require_confirmed'):
            raise ValueError('请先核对并确认晶胞与域壁点预设')
        r, c = lattice_integer(command['r']), lattice_integer(command['c'])
        from shapely.geometry import Polygon, Point
        from .document import xy
        if not Polygon(doc['boundary']).buffer(doc['parameters']['a']*1e-9).covers(Point(xy({'r': r, 'c': c}, doc['parameters']))):
            raise ValueError('路径点在设计边界之外')
        nid = _node(doc, r, c)
        active = next((s for s in doc['strokes'] if s['id'] == doc['active_stroke']), None)
        if active is None:
            active = {'id': _id(doc, 'stroke', 'S'), 'nodes': [nid]}
            doc['strokes'].append(active)
            doc['active_stroke'] = active['id']
        elif active['nodes'][-1] != nid:
            u = active['nodes'][-1]
            if not is_direction(doc['nodes'][u], doc['nodes'][nid]):
                raise ValueError('不在允许方向上，请点击一个拐点后继续')
            crosses = _intersections(doc, u, nid)
            decision = command.get('crossing')
            if crosses and decision not in ('connect', 'separate'):
                raise CrossingRequired(crosses)
            for cross in crosses:
                if decision == 'connect':
                    if not cross['connectable']:
                        raise ValueError('交点不是合法域壁格点，不能连接，请调整拐点')
                    _node(doc, round(cross['r']), round(cross['c']))
                else:
                    doc['crossings'].append({'r': cross['r'], 'c': cross['c'], 'mode': 'separate'})
            eid = _id(doc, 'edge', 'E')
            doc['edges'][eid] = {'u': u, 'v': nid}
            active['nodes'].append(nid)
        _normalize(doc)
    elif kind == 'end':
        doc['active_stroke'] = None
    elif kind == 'move':
        nid = command['id']
        if nid not in doc['nodes']:
            raise ValueError('节点不存在')
        doc['nodes'][nid] = {'r': lattice_integer(command['r']), 'c': lattice_integer(command['c'])}
        # Validate directions before topology is normalized.
        validate_document(doc)
        for eid, e in list(doc['edges'].items()):
            crosses = _intersections(doc, e['u'], e['v'])
            if crosses:
                raise ValueError('移动会产生新交叉，请删除相关线段后重新绘制并选择交叉关系')
        _normalize(doc)
    elif kind == 'delete':
        target = command['id']
        if target in doc['nodes']:
            del doc['nodes'][target]
            doc['edges'] = {k: e for k, e in doc['edges'].items() if target not in (e['u'], e['v'])}
        elif target in doc['edges']:
            del doc['edges'][target]
        else:
            raise ValueError('要删除的对象不存在')
        _prune_strokes(doc)
    elif kind == 'parameters':
        allowed = {'a', 'large_ratio', 'small_ratio', 'topology', 'origin', 'confirmed'}
        changes = command['values']
        if not isinstance(changes, dict) or set(changes)-allowed:
            raise ValueError('未知的晶胞参数')
        doc['parameters'].update(changes)
        if set(changes)-{'confirmed'}:
            doc['parameters']['confirmed'] = False
            doc['regions'] = []
    elif kind == 'boundary':
        doc['boundary'] = deepcopy(command['points'])
    elif kind == 'phase':
        from .geometry import build_scene
        if command['phase'] not in ('A', 'B'):
            raise ValueError('请选择 A 或 B 相')
        scene = build_scene(doc)
        face = next((f for f in scene['faces'] if f['id'] == command['region']), None)
        if face is None:
            raise ValueError('相区已改变，请重新选择')
        doc['regions'] = [{'phase': f['phase'], 'wkt': f['wkt']} for f in scene['faces']
                          if f['phase'] is not None and f['id'] != face['id']]
        doc['regions'].append({'phase': command['phase'], 'wkt': face['wkt']})
    else:
        raise ValueError('未知的编辑操作')
    result = validate_document(doc)
    if kind in ('point', 'move', 'delete', 'boundary') and result['regions']:
        from .geometry import build_scene
        # Commit only labels valid in this revision. Invalid historical geometry
        # must not regain authority when a later edit happens to recreate it.
        result['regions'] = [{'phase': f['phase'], 'wkt': f['wkt']}
                             for f in build_scene(result)['faces'] if f['phase'] is not None]
    return result
