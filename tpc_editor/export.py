"""Dimensioned exports of the exact geometry shown by the editor."""
from io import BytesIO, StringIO
from html import escape

from .geometry import build_scene

COLORS = {'A': '#b96879', 'B': '#387f86', None: '#94a0ae'}
FILLS = {'A': '#f6e5e9', 'B': '#e0f1f1', None: '#f1f3f5'}


def render_dxf(doc):
    """Export checked layout geometry in millimetres, using editor world coordinates."""
    import ezdxf

    scene = build_scene(doc)
    if not scene['ready']:
        raise ValueError('DXF 导出前请完成几何检查：' + scene['checks'][0]['message'])
    drawing = ezdxf.new('R2010', units=ezdxf.units.MM)
    for layer in ('BOUNDARY', 'HOLES_A', 'HOLES_B', 'DOMAIN_WALL'):
        drawing.layers.new(layer)
    model = drawing.modelspace()
    boundary = doc['boundary']
    if boundary[0] == boundary[-1]:
        boundary = boundary[:-1]
    model.add_lwpolyline(boundary, close=True, dxfattribs={'layer': 'BOUNDARY'})
    for hole in scene['holes']:
        model.add_lwpolyline(hole['vertices'], close=True,
                             dxfattribs={'layer': 'HOLES_' + hole['phase']})
    for edge in scene['edges'].values():
        model.add_line(*edge['xy'], dxfattribs={'layer': 'DOMAIN_WALL'})
    stream = StringIO()
    drawing.write(stream)
    return stream.getvalue().encode(drawing.output_encoding)


def render_svg(doc, scene=None):
    scene = scene or build_scene(doc)
    xmin, ymin, xmax, ymax = scene['bounds']
    p = doc['parameters']
    scale = min(1000/max(xmax-xmin, 1e-9), 650/max(ymax-ymin, 1e-9))
    width, height = (xmax-xmin)*scale, (ymax-ymin)*scale
    canvas_w = max(1100, width+100)
    chart_x = (canvas_w-width)/2
    total_h = height+220+((len(scene['nodes'])+2)//3)*18
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w:.3f} {total_h:.3f}" width="{canvas_w:.0f}" height="{total_h:.0f}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<g font-family="Microsoft YaHei, sans-serif" fill="#243342">',
           '<text x="50" y="28" font-size="18">TPC · 域壁路径结构图</text>',
           f'<text x="50" y="50" font-size="12">{ "参数几何预览 · 检查通过" if scene["ready"] else "草稿 · 存在待确认/待处理项目"}</text>']

    def point(pt):
        return (chart_x+(pt[0]-xmin)*scale, 75+(ymax-pt[1])*scale)

    def path(rings):
        parts = []
        for ring in rings:
            parts.append('M'+' L'.join(f'{x:.4f},{y:.4f}' for x,y in map(point, ring))+' Z')
        return ' '.join(parts)

    for f in scene['faces']:
        out.append(f'<path d="{path(f["rings"])}" fill="{FILLS[f["phase"]]}" fill-rule="evenodd"/>')
    for hole in scene['holes']:
        out.append(f'<path d="{path([hole["vertices"]])}" fill="{ "#d44635" if hole["conflict"] else COLORS[hole["phase"]]}"/>')
    out.append(f'<path d="{path([doc["boundary"]])}" fill="none" stroke="#52606d" stroke-width="1"/>')
    for eid, e in scene['edges'].items():
        (x1,y1), (x2,y2) = map(point, e['xy'])
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#283f5b" stroke-width="2" stroke-dasharray="5 3"/>')
    for nid, n in scene['nodes'].items():
        x,y = point(n['xy'])
        out.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#283f5b"/><text x="{x+6}" y="{y-6}" font-size="11">{escape(nid)}</text>')
    base = height+102
    out.extend([
        f'<path d="M{chart_x},{base-8} v8 h{width} v-8" fill="none" stroke="#52606d"/>',
        f'<text x="50" y="{base+18}" font-size="12">宽 {xmax-xmin:.6g} mm · 高 {ymax-ymin:.6g} mm · A 粉 / B 青</text>',
        f'<text x="50" y="{base+38}" font-size="12">a={p["a"]:.6g} mm · 大孔={p["a"]*p["large_ratio"]:.6g} mm · 小孔={p["a"]*p["small_ratio"]:.6g} mm · {p["topology"]}</text>',
        f'<text x="50" y="{base+58}" font-size="11">边缘保留整孔，未放置 {len(scene["omitted_holes"])} 个越界孔 · 节点为域壁路径点，非 CST 端口</text>',
    ])
    for i, (nid, n) in enumerate(scene['nodes'].items()):
        x = 50+(i%3)*((canvas_w-100)/3)
        y = base+80+(i//3)*18
        out.append(f'<text x="{x:.2f}" y="{y}" font-size="10">{nid}: r={n["r"]},c={n["c"]}; ({n["xy"][0]:.4g},{n["xy"][1]:.4g}) mm</text>')
    out.append('</g></svg>')
    return ''.join(out)


def render_png(doc):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.patches import PathPatch, Polygon as PatchPolygon
    from matplotlib.path import Path
    from matplotlib import font_manager
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient
    scene = build_scene(doc)
    names = {f.name for f in font_manager.fontManager.ttflist}
    font = next((n for n in ['Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC'] if n in names), 'DejaVu Sans')
    fig = Figure(figsize=(12, 8), dpi=160)
    FigureCanvasAgg(fig)
    ax = fig.add_axes([0.08, 0.22, 0.86, 0.68])
    for f in scene['faces']:
        poly = orient(Polygon(f['rings'][0], f['rings'][1:]))
        verts, codes = [], []
        for ring in [poly.exterior, *poly.interiors]:
            pts = list(ring.coords)
            verts.extend(pts)
            codes.extend([Path.MOVETO]+[Path.LINETO]*(len(pts)-2)+[Path.CLOSEPOLY])
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=FILLS[f['phase']], edgecolor='none'))
    for hole in scene['holes']:
        ax.add_patch(PatchPolygon(hole['vertices'], facecolor='#d44635' if hole['conflict'] else COLORS[hole['phase']], edgecolor='none'))
    ax.add_patch(PatchPolygon(doc['boundary'], fill=False, edgecolor='#52606d', linewidth=0.8))
    for edge in scene['edges'].values():
        ax.plot(*zip(*edge['xy']), '--', color='#283f5b', linewidth=1)
    for nid, n in scene['nodes'].items():
        ax.plot(*n['xy'], 'o', color='#283f5b', markersize=3)
        ax.annotate(nid, n['xy'], xytext=(5,5), textcoords='offset points', fontsize=8)
    xmin,ymin,xmax,ymax = scene['bounds']
    ax.set_xlim(xmin-(xmax-xmin)*0.02, xmax+(xmax-xmin)*0.02)
    ax.set_ylim(ymin-(ymax-ymin)*0.02, ymax+(ymax-ymin)*0.02)
    ax.set_aspect('equal')
    ax.set_xlabel('x / mm'); ax.set_ylabel('y / mm')
    p = doc['parameters']
    fig.text(0.08, 0.95, 'TPC · 域壁路径结构图', fontsize=16, fontfamily=font)
    status = '参数几何预览 · 检查通过' if scene['ready'] else '草稿 · 存在待确认/待处理项目'
    fig.text(0.08, 0.91, status, fontsize=10, fontfamily=font)
    text = (f'a={p["a"]:.6g} mm; 大孔={p["large_ratio"]*p["a"]:.6g} mm; 小孔={p["small_ratio"]*p["a"]:.6g} mm; {p["topology"]}\n'
            f'宽={xmax-xmin:.6g} mm; 高={ymax-ymin:.6g} mm; A 粉 / B 青; 外边缘保留整孔，未放置 {len(scene["omitted_holes"])} 个越界孔\n'
            '节点为域壁路径点，非 CST 端口；本图不代表电磁求解结果。')
    coords = ['%s: (%d,%d) → (%.4g,%.4g) mm' % (key, n['r'], n['c'], *n['xy']) for key,n in scene['nodes'].items()]
    if coords:
        text += '\n'+'\n'.join('   '.join(coords[i:i+3]) for i in range(0, len(coords), 3))
    fig.text(0.08, 0.13, text, va='top', fontsize=8, fontfamily=font)
    result = BytesIO()
    fig.savefig(result, format='png', bbox_inches='tight')
    return result.getvalue()
