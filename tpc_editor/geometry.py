"""Derive regions, lattice points and actual hole polygons from a document."""
import hashlib
import math

from .document import validate_document, xy


def _polygon_data(poly):
    return [list(map(list, poly.exterior.coords))] + [list(map(list, ring.coords)) for ring in poly.interiors]


def _phase(poly, snapshots, tolerance):
    from shapely import wkt
    owners = []
    for snapshot in snapshots:
        try:
            old = wkt.loads(snapshot['wkt'])
            if old.geom_type != 'Polygon' or not old.is_valid:
                raise ValueError('相区快照必须是有效多边形')
            if old.buffer(tolerance).covers(poly):
                owners.append(snapshot['phase'])
        except Exception as exc:
            raise ValueError('无法读取设计文件中的相区几何') from exc
    return owners[0] if len(owners) == 1 else None


def _holes(doc, domain, faces, tol):
    import numpy as np
    from shapely.geometry import Point, Polygon
    from mesh_grid.tri_grid import TopoPath, generate_crystal_holes, equilateral_triangle_vertices
    p = doc['parameters']
    a, (ox, oy) = p['a'], p['origin']
    h = math.sqrt(3)*a/2
    xmin, ymin, xmax, ymax = domain.bounds
    ix0 = math.floor((xmin-ox)/a)-2
    iy0 = math.floor((ymin-oy)/(2*h))-2
    nx = math.ceil((xmax-ox)/a)-ix0+2
    ny = math.ceil((ymax-oy)/(2*h))-iy0+2
    grid = generate_crystal_holes(TopoPath([(0, 0), (0, max(1, nx))], a),
                                 topology=p['topology'], large_size=a*p['large_ratio'],
                                 small_size=a*p['small_ratio'], xup=nx, yup=2*ny, ydn=0)
    centers = grid['centers'] + np.array([ox+ix0*a, oy+iy0*2*h])
    kept, omitted, conflicts = [], [], []
    seen = set()
    exterior = domain.buffer(tol)
    for center, up in zip(centers, grid['is_up']):
        key = (round(float(center[0])/a, 9), round(float(center[1])/a, 9), bool(up))
        if key in seen:
            continue
        seen.add(key)
        pt = Point(center)
        if not exterior.covers(pt):
            continue
        owners = [f for f in faces if f['_poly'].covers(pt)]
        face = owners[0] if len(owners) == 1 else None
        phase = face['phase'] if face else None
        up_small = (p['topology'] == 'AB') == (phase != 'B')
        size = a*(p['small_ratio'] if bool(up) == up_small else p['large_ratio'])
        vertices = equilateral_triangle_vertices(center, size, 0 if up else 180).tolist()
        polygon = Polygon(vertices)
        hole = {'center': list(map(float, center)), 'vertices': vertices, 'size': size,
                'up': bool(up), 'phase': phase, 'conflict': False}
        if not exterior.covers(polygon):
            omitted.append(hole)
            continue
        if face is None or (face['phase'] and not face['_poly'].buffer(tol).covers(polygon)):
            hole['conflict'] = True
            conflicts.append(hole['center'])
        kept.append(hole)
    return kept, omitted, conflicts


def build_scene(value):
    from shapely.geometry import Polygon, Point, LineString
    from shapely.ops import polygonize, unary_union
    doc = validate_document(value)
    p = doc['parameters']
    a = p['a']
    tol = a*1e-8
    domain = Polygon(doc['boundary'])
    checks = []

    def check(code, message, target=None, level='error', **extra):
        checks.append(dict(code=code, message=message, target=target, level=level, **extra))

    nodes = {key: dict(n, xy=xy(n, p)) for key, n in doc['nodes'].items()}
    lines, edges = [], {}
    for key, n in nodes.items():
        if not domain.buffer(tol).covers(Point(n['xy'])):
            check('outside', f'{key} 在设计边界外，请移动节点或扩大边界', key)
    for eid, e in doc['edges'].items():
        line = LineString([nodes[e['u']]['xy'], nodes[e['v']]['xy']])
        lines.append(line)
        edges[eid] = dict(e, xy=list(map(list, line.coords)), length=float(line.length),
                          periods=max(abs(nodes[e['v']]['r']-nodes[e['u']]['r']),
                                      abs(nodes[e['v']]['c']-nodes[e['u']]['c'])))
        if not domain.buffer(tol).covers(line):
            check('outside_edge', f'{eid} 穿出设计边界', eid)
    network = unary_union([domain.boundary]+[line.intersection(domain) for line in lines])
    polys = [poly for poly in polygonize(network)
             if domain.covers(poly.representative_point()) and poly.area > tol**2]
    polys.sort(key=lambda poly: (poly.centroid.x, poly.centroid.y))
    faces = []
    for poly in polys:
        fid = 'R'+hashlib.sha256(poly.normalize().wkb).hexdigest()[:10]
        phase = _phase(poly, doc['regions'], tol)
        face = {'id': fid, 'phase': phase, 'rings': _polygon_data(poly),
                'center': list(poly.representative_point().coords[0]), 'area': float(poly.area),
                'wkt': poly.wkt, '_poly': poly}
        faces.append(face)
        if phase is None:
            check('unassigned', '区域尚未指定晶相，请选择 A 或 B', fid)
    adjacent = []
    for (eid, e), line in zip(edges.items(), lines):
        owners = [i for i, f in enumerate(faces) if f['_poly'].boundary.intersection(line).length > tol]
        if len(owners) < 2:
            check('dangling', f'{eid} 没有分隔出两侧区域：请延伸到边界、连接其他路径或闭合', eid)
        for j, first in enumerate(owners):
            for second in owners[j+1:]:
                adjacent.append((first, second))
                f, g = faces[first], faces[second]
                if f['phase'] is not None and f['phase'] == g['phase']:
                    check('same_phase', f'{eid} 两侧均为 {f["phase"]} 相，不构成 A/B 域壁', eid)
    colors = {}
    for start in range(len(faces)):
        if start in colors:
            continue
        colors[start] = 0
        todo = [start]
        while todo:
            current = todo.pop()
            neighbors = [v if u == current else u for u, v in adjacent if current in (u, v)]
            for other in neighbors:
                if other in colors and colors[other] == colors[current]:
                    if not any(c['code'] == 'two_phase_conflict' for c in checks):
                        check('two_phase_conflict', '当前分区无法一致分配 A/B 两相，请调整分叉布局', faces[current]['id'])
                elif other not in colors:
                    colors[other] = 1-colors[current]
                    todo.append(other)
    # Inspect the geometry independently of decisions present in an imported JSON.
    if lines:
        from shapely.strtree import STRtree
        tree = STRtree(lines)
        edge_ids = list(edges)
        for i, line in enumerate(lines):
            for j in tree.query(line, predicate='intersects'):
                j = int(j)
                if j <= i:
                    continue
                left, right = edges[edge_ids[i]], edges[edge_ids[j]]
                inter = line.intersection(lines[j])
                if inter.geom_type == 'Point':
                    shared = {left['u'], left['v']} & {right['u'], right['v']}
                    if shared:
                        continue
                    marker = any(Point(xy(c, p)).distance(inter) < tol for c in doc['crossings'])
                    if not marker:
                        check('unresolved_crossing', '导入的路径有未决定连接关系的交叉，请重新绘制相关线段',
                              edge_ids[i], xy=list(inter.coords[0]))
                elif inter.length > tol:
                    check('overlap', '导入的线段存在重叠，请重新绘制以拆分去重', edge_ids[i])
    # Only live geometric crossings are reported; stale markers are not evidence.
    live_crossings = []
    for cross in doc['crossings']:
        ptxy = xy(cross, p)
        point = Point(ptxy)
        owners = [eid for eid, line in zip(edges, lines) if line.distance(point) < tol and
                  point.distance(Point(line.coords[0])) > tol and point.distance(Point(line.coords[-1])) > tol]
        if len(owners) >= 2:
            live_crossings.append(dict(cross, xy=ptxy))
            check('separate_crossing', '路径在此交叉且保持分离：同层物理交叉尚未解决', owners[0], xy=ptxy)
    holes, omitted, conflicts = _holes(doc, domain, faces, tol)
    if conflicts:
        check('interface_hole', f'{len(conflicts)} 个孔位于域壁上或跨过内部相区，请调整路径/晶胞参数',
              xy=conflicts[0], points=conflicts)
    if not p['confirmed']:
        check('unconfirmed', '当前为示例参数，请核对晶胞与域壁点预设后确认', level='warning')
    xmin, ymin, xmax, ymax = domain.bounds
    h = math.sqrt(3)*a/2
    snap = []
    for r in range(math.floor((ymin-p['origin'][1])/h)-1, math.ceil((ymax-p['origin'][1])/h)+2):
        for c in range(math.floor((xmin-p['origin'][0])/a-r/2)-1,
                       math.ceil((xmax-p['origin'][0])/a-r/2)+2):
            pt = xy({'r': r, 'c': c}, p)
            if domain.buffer(tol).covers(Point(pt)):
                snap.append({'r': r, 'c': c, 'xy': pt})
    for f in faces:
        del f['_poly']
    return {'nodes': nodes, 'edges': edges, 'faces': faces, 'holes': holes,
            'omitted_holes': omitted, 'snap_points': snap, 'crossings': live_crossings,
            'checks': checks, 'bounds': [xmin, ymin, xmax, ymax],
            'ready': not checks and p['confirmed'], 'unit': 'mm',
            'preset_source': 'mesh_grid.tri_grid.phase_diagram.generate_crystal_holes',
            'boundary_rule': '只保留完整孔；跨出外边界的孔不放置'}
