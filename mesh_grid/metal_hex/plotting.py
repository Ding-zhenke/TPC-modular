"""Parameter-driven, equal-aspect previews of the real offline copper polygons."""
import json
from pathlib import Path

from .geometry import build_geometry


def _polygons(geometry):
    if geometry.is_empty:
        return
    if geometry.geom_type == 'Polygon':
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for part in geometry.geoms:
            yield from _polygons(part)


def _paint(ax, geometry, color):
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import PathPatch
    from shapely.geometry.polygon import orient
    for polygon in _polygons(geometry):
        vertices, codes = [], []
        for ring in [orient(polygon).exterior, *orient(polygon).interiors]:
            coords = list(ring.coords)
            vertices.extend(coords)
            codes.extend([MplPath.MOVETO] + [MplPath.LINETO]*(len(coords)-2) + [MplPath.CLOSEPOLY])
        ax.add_patch(PathPatch(MplPath(vertices, codes), fc=color, ec='none'))


def export_preview(spec, output_dir):
    """Write PNG, editable-text SVG and a JSON spec/measurement record.

    Uses local matplotlib settings only; does not select a backend or show a UI.
    Colors distinguish construction roles, not different copper materials.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle
    geometry = build_geometry(spec)
    spec = geometry.spec
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = 'metal_hex_' + spec.layout.lower()
    files = {ext: output_dir / f'{stem}.{ext}' for ext in ('png', 'svg', 'json')}
    copper, a_color, b_color, quartz, probe_color = '#a8622b', '#218b91', '#6459a5', '#eaf0f4', '#cd6246'
    with plt.rc_context({'font.family': 'DejaVu Sans', 'font.size': 9, 'svg.fonttype': 'none'}):
        fig = plt.figure(figsize=(13, 9), constrained_layout=True)
        try:
            grid = fig.add_gridspec(2, 3, width_ratios=[1.3, 1, 1])
            overview = fig.add_subplot(grid[:, 0])
            axes = [overview, fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[0, 2])]
            _paint(overview, geometry.substrate, quartz)
            for geom, color in [(geometry.rings, copper), (geometry.phase_a, a_color),
                                (geometry.phase_b, b_color), (geometry.probe_left, probe_color),
                                (geometry.probe_right, probe_color)]:
                _paint(overview, geom, color)
            xl, yl, xr, yr = spec.substrate_bounds
            overview.add_patch(Rectangle((xl, yl), xr-xl, yr-yl, fill=False, ec='#23313e', lw=.8))
            p0, p1 = spec.domain_wall
            overview.plot([p0[0], p1[0]], [0, 0], '--', color='#c44848', lw=1)
            for point, label, align in [(p0, 'P01', 'left'), (p1, 'P02', 'right')]:
                overview.plot(*point, 'o', color='#c44848', ms=3)
                overview.annotate(label, point, xytext=(0, 7), textcoords='offset points',
                                  ha=align, fontsize=8, bbox=dict(fc='white', ec='none', pad=1))
            overview.set_xlim(xl-.1*spec.lattice_constant, xr+.1*spec.lattice_constant)
            overview.set_ylim(yl-.1*spec.lattice_constant, yr+.1*spec.lattice_constant)
            if spec.centered:
                overview.axvline(0, color='#80929f', lw=.6, ls=':')
            title = {'AB': 'A above, B below', 'BA': 'B above, A below',
                     'A_air': 'A above, no lower crystal / quartz support'}[spec.layout]
            overview.set_title(title)
            for ax, motif, title, color in zip(axes[1:], [geometry.unit_a, geometry.unit_b],
                                              ['Unit A', 'Unit B'], [a_color, b_color]):
                _paint(ax, geometry.unit_ring, copper)
                _paint(ax, motif, color)
                r = spec.ring_radius*1.12
                ax.set_xlim(-r, r); ax.set_ylim(-r, r)
                ax.set_title(title)
            if spec.layout == 'A_air':
                ax = axes[2]
                ax.clear()
                r = spec.ring_radius*1.12
                ax.add_patch(Rectangle((-r, -r), 2*r, 2*r, fc=quartz, ec='none'))
                ax.set_xlim(-r, r); ax.set_ylim(-r, r)
                ax.set_title('Air side: no copper / quartz retained')
            for ax in axes:
                ax.set_aspect('equal'); ax.set_xlabel('x / mm'); ax.set_ylabel('y / mm')
                ax.spines[['top', 'right']].set_visible(False)
            text_ax = fig.add_subplot(grid[1, 1:]); text_ax.axis('off')
            text = (
                f'a = {spec.lattice_constant:g} mm; h = {spec.substrate_thickness:g} mm; t = 0\n'
                f'Outer radius = a / sqrt(3) = {spec.ring_radius:.6f} mm\n'
                f'Radial inset = {spec.ring_inset:g} mm; single-ring width = {spec.single_ring_width:.6f} mm\n'
                f'Pad ratio = {spec.pad_ratio:g}; pad length = {spec.pad_length:.6f} mm\n'
                f'X length/a = {spec.x_periods}; Y half-height/a = {spec.y_half_periods}\n'
                f'Substrate: {xr-xl:.6f} x {yr-yl:.6f} mm\n'
                f'Placement: {"centred at x=0" if spec.centered else "legacy notebook"}\n')
            if spec.probes_enabled:
                text += (f'Lt = {spec.taper_length:g}; Ln = {spec.neck_length:g}; Wp = {spec.port_width:g} mm\n'
                         f'Wt = {spec.tip_width:g}; Li = {spec.probe_insertion:g}; yf = {spec.probe_y:g} mm\n'
                         f'Outer quartz margin = {spec.substrate_margin:g} mm\n')
            if spec.layout == 'A_air':
                text += f'Air-side quartz width Wa = {spec.air_substrate_width:g} mm\n'
            text += ('\n'
                'Copper sheets at z = 0; quartz at -h <= z <= 0.\n'
                'P01/P02 are domain-wall nodes, not CST ports.\n'
                'Probe dimensions are adjustable initial values.\n'
                'Ground reference belongs to the caller template.\n'
                'CST rebuild/readback/solve remain unverified.')
            text_ax.text(0, 1, text, va='top', linespacing=1.55, fontsize=8.5)
            handles = [Patch(fc=copper, label='Copper rings'), Patch(fc=a_color, label='A pads')]
            if spec.layout != 'A_air':
                handles.append(Patch(fc=b_color, label='B pads'))
            handles.append(Patch(fc=quartz, label='Quartz'))
            if spec.probes_enabled:
                handles.append(Patch(fc=probe_color, label='Copper tapers'))
            text_ax.legend(handles=handles,
                           loc='lower left', ncol=2, frameon=False)
            fig.suptitle(f'Metal hexagonal lattice / {spec.layout} geometry', fontsize=15)
            fig.savefig(files['png'], dpi=180)
            fig.savefig(files['svg'])
        finally:
            plt.close(fig)
    files['json'].write_text(json.dumps(geometry.summary(), ensure_ascii=False, indent=2), encoding='utf-8')
    return files
