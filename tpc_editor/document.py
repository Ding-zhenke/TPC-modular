"""Versioned, JSON-native editor documents; no screen coordinates are stored."""
from copy import deepcopy
import math

PRESET = 'silicon-triangular-holes-v1'


def new_document():
    a = 0.2425
    h = math.sqrt(3) * a / 2
    return {
        'schema_version': 1, 'preset': PRESET, 'preset_version': 1,
        'units': 'mm', 'coordinates': 'axial-r-c-v1',
        'parameters': {'a': a, 'large_ratio': 0.65, 'small_ratio': 0.35,
                       'topology': 'AB', 'origin': [0.0, 0.0], 'confirmed': False},
        'boundary': [[-8*a, -4*h], [8*a, -4*h], [8*a, 4*h], [-8*a, 4*h]],
        'nodes': {}, 'edges': {}, 'strokes': [], 'crossings': [],
        'regions': [], 'active_stroke': None,
        'next_id': {'node': 1, 'edge': 1, 'stroke': 1},
    }


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('坐标和参数必须是有限数值')
    return float(value)


def lattice_integer(value):
    n = number(value)
    if n != int(n) or abs(n) > 10000:
        raise ValueError('域壁路径坐标必须是整数，且绝对值不超过 10000')
    return int(n)


def xy(node, parameters):
    a = parameters['a']
    ox, oy = parameters['origin']
    return [ox + (node['c'] + node['r']/2)*a,
            oy + node['r']*math.sqrt(3)*a/2]


def is_direction(n1, n2):
    dr, dc = n2['r']-n1['r'], n2['c']-n1['c']
    return (dr != 0 or dc != 0) and (dr == 0 or dc == 0 or dr == -dc)


def validate_document(value):
    from shapely.geometry import Polygon
    doc = deepcopy(value)
    if not isinstance(doc, dict) or doc.get('schema_version') != 1:
        raise ValueError('不支持的设计文件版本')
    if (doc.get('preset') != PRESET or doc.get('preset_version') != 1 or
            doc.get('units') != 'mm' or doc.get('coordinates') != 'axial-r-c-v1'):
        raise ValueError('不支持的晶胞预设、单位或坐标约定')
    try:
        p = doc['parameters']
        if not 0 < number(p['a']) < 10000:
            raise ValueError('晶格常数必须大于零')
        if not 0 < number(p['small_ratio']) <= number(p['large_ratio']) < 1:
            raise ValueError('孔边长比例需要满足 0 < 小孔 ≤ 大孔 < 1')
        if p['topology'] not in ('AB', 'BA') or not isinstance(p['confirmed'], bool):
            raise ValueError('无效的 AB/BA 设置或确认状态')
        if len(p['origin']) != 2:
            raise ValueError('原点需要两个坐标')
        for n in p['origin']:
            number(n)
        boundary = doc['boundary']
        if not 3 <= len(boundary) <= 256:
            raise ValueError('边界需要 3–256 个顶点')
        for pt in boundary:
            if len(pt) != 2:
                raise ValueError('边界顶点需要两个坐标')
            for n in pt:
                number(n)
        poly = Polygon(boundary)
        if not poly.is_valid or poly.area < (p['a']*0.01)**2:
            raise ValueError('外边界必须是非自交且具有面积的闭合多边形')
        bx = poly.bounds
        if (bx[2]-bx[0])*(bx[3]-bx[1])/p['a']**2 > 5000:
            raise ValueError('设计范围过大，请将面积缩小到 5000 个晶格面积以内')
        if not isinstance(doc['nodes'], dict) or len(doc['nodes']) > 2000:
            raise ValueError('节点数不得超过 2000')
        seen = set()
        for node_id, n in doc['nodes'].items():
            if not isinstance(node_id, str) or not node_id.startswith('P') or not node_id[1:].isdigit():
                raise ValueError('节点编号必须为 P 加数字')
            pos = lattice_integer(n['r']), lattice_integer(n['c'])
            if pos in seen:
                raise ValueError('重复位置节点应使用同一个节点编号')
            seen.add(pos)
        if not isinstance(doc['edges'], dict) or len(doc['edges']) > 4000:
            raise ValueError('线段数不得超过 4000')
        pairs = set()
        for eid, e in doc['edges'].items():
            if not isinstance(eid, str) or not eid.startswith('E') or not eid[1:].isdigit():
                raise ValueError('线段编号必须为 E 加数字')
            if e['u'] not in doc['nodes'] or e['v'] not in doc['nodes']:
                raise ValueError('线段引用了不存在的节点')
            if not is_direction(doc['nodes'][e['u']], doc['nodes'][e['v']]):
                raise ValueError('线段必须沿三角晶格六个允许方向，且长度大于零')
            key = frozenset((e['u'], e['v']))
            if key in pairs:
                raise ValueError('设计文件包含重复线段')
            pairs.add(key)
        stroke_ids = set()
        for stroke in doc['strokes']:
            if stroke['id'] in stroke_ids:
                raise ValueError('重复路径段编号')
            stroke_ids.add(stroke['id'])
            if not stroke['nodes'] or any(n not in doc['nodes'] for n in stroke['nodes']):
                raise ValueError('路径段引用无效节点')
            for u, v in zip(stroke['nodes'], stroke['nodes'][1:]):
                if frozenset((u, v)) not in pairs:
                    raise ValueError('路径段引用了不存在的连接')
        if doc['active_stroke'] is not None and doc['active_stroke'] not in stroke_ids:
            raise ValueError('当前路径段不存在')
        for kind, prefix, ids in [('node', 'P', doc['nodes']), ('edge', 'E', doc['edges']),
                                  ('stroke', 'S', stroke_ids)]:
            counter = lattice_integer(doc['next_id'][kind])
            if counter < 1 or any(not s.startswith(prefix) or not s[1:].isdigit() or
                                  int(s[1:]) >= counter for s in ids):
                raise ValueError('对象编号计数器与设计不一致')
        for cross in doc['crossings']:
            number(cross['r']); number(cross['c'])
            if cross['mode'] != 'separate':
                raise ValueError('无效的交叉关系')
        for region in doc['regions']:
            if region['phase'] not in ('A', 'B'):
                raise ValueError('晶相只能为 A 或 B')
            if not isinstance(region['wkt'], str) or len(region['wkt']) > 100000:
                raise ValueError('无效的相区几何')
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError('设计文件缺少必需字段或数据类型不正确') from exc
    return doc
