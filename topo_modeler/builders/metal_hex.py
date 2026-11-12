"""Native parametric geometry adapter; caller owns the reviewed CST session.

No CST imports, session creation, frequency settings, ports or solver actions.
Command submission does not certify zero-thickness boolean kernel behavior.
"""
import re
from mesh_grid.metal_hex.spec import MetalHexSpec


def build_metal_hex(app, spec=None, *, prefix='mh', component='metal_hex'):
    """Submit the approved straight AB geometry to a clean mm-unit CST app.

    app implements the public cst-automation modeling API. Only native
    expressions are used so rebuilding after parameter edits can regenerate
    the arrays. Use a fresh project for each distinct specification;
    do not append this repeatedly to a populated project.
    """
    spec = MetalHexSpec() if spec is None else spec
    if not isinstance(spec, MetalHexSpec):
        raise TypeError('spec must be MetalHexSpec')
    for name in (prefix, component):
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
            raise ValueError('prefix and component must be simple identifiers')
    if app.get_units('length') != 'mm':
        raise ValueError('Metal hex adapter requires a clean project with mm length units')
    # Validate real copper contact and dielectric support before any native write.
    from mesh_grid.metal_hex.geometry import build_geometry
    build_geometry(spec)
    app.activate_global_wcs()
    parameters = spec.cst_parameters()
    for name, value in parameters.items():
        app.para(name, value)
    copper, quartz = 'Copper (annealed)', 'Quartz (Fused) (lossy)'
    app.new_material(copper)
    app.new_material(quartz)
    curve = f'{prefix}_curves'
    app.new_curve(curve)
    names = {role: f'{prefix}_{role}' for role in ('rings', 'phase_a', 'phase_b', 'substrate')}
    if spec.layout == 'A_air':
        del names['phase_b']
    if spec.probes_enabled:
        names.update(probe_left=f'{prefix}_probe_left', probe_right=f'{prefix}_probe_right')

    def sheet(name, points):
        app.polyline(points, name=name, curve=curve)
        app.extrude(f'{curve}:{name}', name, 't', component=component, material=copper)

    def clip_rectangle(name, ylo, yhi):
        sheet(name, [['xl', ylo], ['xr', ylo], ['xr', yhi], ['xl', yhi], ['xl', ylo]])

    def array(name):
        app.rotation(name, [0, 0, 120], center=['0', 'r1', '0'], repetition=2,
                     component=component, copy=True, unite=True)
        app.translate(name, ['a', '0', '0'], component=component,
                      repetitions='int(nx)', copy=True, unite=True)
        # No zero-copy calls: CST rejects them for a one-period test design.
        if spec.y_half_periods//2:
            app.translate(name, ['0', 'dy', '0'], component=component,
                          repetitions='int(nu/2)', copy=True, unite=True)
        app.translate(name, ['0', '-dy', '0'], component=component,
                      repetitions='int(nd/2)', copy=True, unite=True)

    ring, inner = names['rings'], f'{prefix}_inner'
    for name, radius in [(ring, 'r1'), (inner, 'r1-d1')]:
        app.hexagon(radius, 't', center=[0, 0, 0], theta=[0, 0, 90],
                    name=name, curve=curve, component=component, material=copper)
    app.subtract(ring, inner, component1=component, component2=component)
    array(ring)
    clip = f'{prefix}_clip'
    clip_rectangle(clip, '0' if spec.layout == 'A_air' else '-ym', 'ym')
    app.intersect(ring, clip, component1=component, component2=component)

    points = [['p1*cosd(30)', 'p1*sind(30)'], ['0', '0'], ['0', '-p1'],
              ['p1*cosd(-30)', 'p1*sind(-30)'], ['p1*cosd(30)', 'p1*sind(30)']]
    for role in ('phase_a', 'phase_b'):
        if role not in names:
            continue
        name = names[role]
        sheet(name, points)
        app.translate(name, ['-a/2', 'r1/2', '0'], component=component)
        app.rotation(name, [0, 0, 120], repetition=2, component=component,
                     copy=True, unite=True)
        if role == 'phase_a':
            app.rotation(name, [0, 0, 180], component=component)
        array(name)
        is_upper = (role == 'phase_a') == (spec.layout != 'BA')
        clip_rectangle(clip, '0' if is_upper else '-ym', 'ym' if is_upper else '0')
        app.intersect(name, clip, component1=component, component2=component)
    if spec.centered:
        for role in ('rings', 'phase_a', 'phase_b'):
            if role in names:
                app.translate(names[role], ['sx', '0', '0'], component=component)
    if spec.probes_enabled:
        left_points = [['xe','yf-wp/2'], ['xb','yf-wp/2'], ['xt','yf-wt/2'],
                       ['xt','yf+wt/2'], ['xb','yf+wp/2'], ['xe','yf+wp/2']]
        for role, sign in [('probe_left',''), ('probe_right','-')]:
            points = [[sign+x,y] for x,y in left_points]
            sheet(names[role], points+[points[0]])
    app.square('-bx' if spec.centered else 'xl', 'bx' if spec.centered else 'xr+a/2',
               '-wa' if spec.layout=='A_air' else '-ym', 'ym', '-h', '0', names['substrate'],
               component=component, material=quartz)
    return dict(component=component, shapes=names, parameters=parameters,
                evidence='native geometry commands submitted; CST readback unverified')
